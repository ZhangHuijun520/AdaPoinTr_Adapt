"""Purpose-specific BCSP artificial preflight. No training/installation entry.

Only main() can enter CUDA, and requires separately materialized authorization.
CPU contracts call small helpers, never the real model or a CUDA API.
"""
from __future__ import annotations

import argparse
import contextlib
import ctypes
import gc
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import json
import os
from pathlib import Path
import random
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import types

SCOPE_SHA = '65d23c2a6b067e0e7f9c08615063996a0c4b8ebbc74d35643db77e1b30d2ab17'
PREFIXES = ('models', 'utils', 'tools', 'extensions')
NEVER_IMPORT = {'tools.runner', 'tools.bcsp_runtime'}
PAYLOAD = {'.npz', '.npy', '.nrrd', '.nii', '.stl', '.ply', '.pth', '.pt', '.ckpt'}
SMI_TIMEOUT = 10.0
SMI_REAP_TIMEOUT = 2.0
MONITOR_POLL_WAIT = 2.0
DIAGNOSTIC_BYTES = 2048
MONITOR_EVENT_LIMIT = 3000
_MONITOR = None


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def exact(path, digest, size=None):
    p = Path(path)
    require(p.is_file() and not any(x.is_symlink() for x in (p, *p.parents)), 'linked/missing file: ' + str(p))
    require(size is None or p.stat().st_size == size, 'size: ' + str(p))
    require(sha(p) == digest, 'sha256: ' + str(p))
    return p


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def emit_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def claim_output(output):
    """Launcher may have created only launch.log; PID creation consumes the worker slot."""
    output = Path(output)
    require(not any(x.is_symlink() for x in (output, *output.parents)), 'linked output')
    if output.exists():
        require(output.is_dir() and {p.name for p in output.iterdir()} == {'launch.log'},
                'output not fresh launcher-only directory')
        require((output / 'launch.log').is_file() and not (output / 'launch.log').is_symlink(), 'launch log type')
    else:
        output.mkdir(parents=True, exist_ok=False)
    with (output / 'worker.pid').open('x', encoding='ascii') as f:
        f.write(str(os.getpid()) + '\n')


def source_map(scope):
    out = {r['relative_target']: r for r in scope['bindings']['candidate']}
    for r in scope['bindings']['isolated_model_project_sources']:
        require(r['relative_path'] not in out, 'duplicate source')
        out[r['relative_path']] = r
    require(len(out) == 18, 'finite source count')
    return out


def authorize(request_path, request_sha, authorization_path, runtime_path):
    request = read_json(exact(request_path, request_sha))
    auth = read_json(authorization_path)
    runtime = read_json(runtime_path)
    require(request['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION', 'request status')
    require(request['scope_sha256'] == SCOPE_SHA, 'scope identity')
    require(auth.get('request_sha256') == request_sha and auth.get('explicit_user_authorization') is True,
            'separate explicit authorization required')
    require(set(auth) == {'schema', 'request_sha256', 'explicit_user_authorization', 'user_authorization_text'},
            'authorization fields; reverse runtime binding forbidden')
    require(auth['schema'] == 'bcsp-preflight-authorization-v1' and bool(auth['user_authorization_text'].strip()),
            'authorization evidence')
    require(runtime == {'schema': 'bcsp-preflight-runtime-v1', 'request_sha256': request_sha,
                        'authorization_sha256': sha(authorization_path)}, 'runtime single-way binding')
    return request


def namespace_packages(root):
    for name in PREFIXES:
        require(name not in sys.modules, 'project package already imported: ' + name)
        m = types.ModuleType(name)
        m.__path__ = [str(root / name)]
        m.__spec__ = importlib.machinery.ModuleSpec(name, loader=None, is_package=True)
        m.__spec__.submodule_search_locations = m.__path__
        sys.modules[name] = m


class FiniteProjectImports(importlib.abc.MetaPathFinder):
    def __init__(self, root, records):
        self.root, self.records = Path(root), records

    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] not in PREFIXES or fullname in PREFIXES:
            return None
        require(fullname not in NEVER_IMPORT, 'training import denied: ' + fullname)
        stem = fullname.replace('.', '/')
        choices = [stem + '.py', stem + '/__init__.py']
        match = [s for s in choices if s in self.records]
        require(len(match) == 1, 'unbound project import: ' + fullname)
        r = self.records[match[0]]
        exact(self.root / match[0], r['sha256'], r['bytes'])
        return None


class FilePolicy:
    """Small dedicated allow-root policy, not a dependency inventory scanner."""
    def __init__(self, read_roots, output):
        self.roots = tuple(Path(p).resolve() for p in read_roots)
        self.output = Path(output).resolve()

    def check(self, filename, write=False):
        if isinstance(filename, int):
            return
        p = Path(os.fsdecode(filename))
        require(not any(x.is_symlink() for x in (p, *p.parents)), 'link access: ' + str(p))
        p = p.resolve()
        require(not ({'.ssh', '.aws', '.credentials', '.git'} & set(p.parts)) and p.name not in {'.netrc', '.env'},
                'secret access: ' + str(p))
        require(p.suffix.lower() not in PAYLOAD and not p.name.lower().endswith('.nii.gz'),
                'payload/checkpoint access: ' + str(p))
        owned = p == self.output or self.output in p.parents
        require(owned if write else owned or any(p == r or r in p.parents for r in self.roots),
                'write/read boundary: ' + str(p))

    def audit(self, event, args):
        if event == 'open':
            mode, flags = args[1], args[2]
            write = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or bool(
                flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            self.check(args[0], write)
        elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.truncate'}:
            self.check(args[0], True)
        elif event in {'os.rename', 'os.link', 'os.symlink'}:
            raise RuntimeError('filesystem mutation denied: ' + event)
        elif event.startswith('socket.') or event in {'os.system', 'os.exec', 'os.posix_spawn'}:
            raise RuntimeError('network/build/process denied: ' + event)
        elif event == 'subprocess.Popen':
            require(args[0] == '/usr/bin/nvidia-smi' and all(str(x).startswith('--') for x in args[1][1:]),
                    'only fixed read-only nvidia-smi permitted')


def configure_numeric(torch):
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    torch.set_float32_matmul_precision('highest')
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    assert_numeric(torch)


def assert_numeric(torch):
    require(torch.are_deterministic_algorithms_enabled() and not torch.is_deterministic_algorithms_warn_only_enabled(),
            'strict deterministic mode')
    require(torch.get_float32_matmul_precision() == 'highest' and not torch.backends.cuda.matmul.allow_tf32
            and not torch.backends.cudnn.allow_tf32 and torch.backends.cudnn.deterministic
            and not torch.backends.cudnn.benchmark, 'TF32/cuDNN contract')


def tensor_sha(t):
    t = t.detach().cpu().contiguous()
    return hashlib.sha256(ctypes.string_at(t.data_ptr(), t.numel() * t.element_size())).hexdigest()


def state_sha(model, parameters_only=False):
    tensors = model.named_parameters() if parameters_only else model.state_dict().items()
    h = hashlib.sha256()
    for name, t in tensors:
        h.update(json.dumps([name, str(t.dtype), list(t.shape), tensor_sha(t)]).encode())
    return h.hexdigest()


@contextlib.contextmanager
def rng_preserved(torch, np, cuda=False, evidence=None):
    py, ng, tc = random.getstate(), np.random.get_state(), torch.get_rng_state().clone()
    cg = torch.cuda.get_rng_state(0).clone() if cuda else None
    try:
        yield
    finally:
        random.setstate(py)
        np.random.set_state(ng)
        torch.set_rng_state(tc)
        if cuda:
            torch.cuda.set_rng_state(cg, 0)
        now = np.random.get_state()
        require(random.getstate() == py and now[0] == ng[0] and np.array_equal(now[1], ng[1])
                and now[2:] == ng[2:] and torch.equal(torch.get_rng_state(), tc), 'RNG restoration')
        require(not cuda or torch.equal(torch.cuda.get_rng_state(0), cg), 'CUDA RNG restoration')
        if evidence is not None:
            evidence['rng_restored'] = True


@contextlib.contextmanager
def no_update(torch, model, evidence):
    before = state_sha(model)
    modules = list(model.modules())
    flags = [m.training for m in modules]
    bns = [m for m in modules if isinstance(m, torch.nn.modules.batchnorm._BatchNorm)]
    tracking = [m.track_running_stats for m in bns]
    model.train()
    for m in bns:
        m.track_running_stats = False
    try:
        yield
    finally:
        for m, value in zip(bns, tracking):
            m.track_running_stats = value
        for m, value in zip(modules, flags):
            m.training = value
        model.zero_grad(set_to_none=True)
        evidence.update(state_before=before, state_after=state_sha(model), bn_modules=len(bns),
                        flags_restored=[m.training for m in modules] == flags,
                        bn_tracking_restored=[m.track_running_stats for m in bns] == tracking)
        require(evidence['state_before'] == evidence['state_after'] and evidence['flags_restored']
                and evidence['bn_tracking_restored'], 'model persistent state changed')


def synthetic(np, torch):
    master = np.random.default_rng(20261024).uniform(-.5, .5, (8, 16384, 3)).astype(np.float32)
    target = np.random.default_rng(20261025).uniform(-.5, .5, (8, 8192, 3)).astype(np.float32)
    return torch.from_numpy(master), torch.from_numpy(target)


def check_backend(chamfer, adapter, provider):
    require(chamfer.chamfer is None, 'compiled Chamfer unexpected; explicitly cdist only')
    require(not adapter.using_fallback(), 'PointNet2 native provider required')
    for name in ('furthest_point_sample', 'gather_operation', 'grouping_operation', 'three_nn',
                 'three_interpolate', 'ball_query'):
        require(getattr(adapter, name) is getattr(provider, name), 'PointNet2 adapter origin: ' + name)


def knn_oracle(torch, np, transformer, keys):
    q = torch.from_numpy(np.random.default_rng(20261026).uniform(-.5, .5, (1, 257, 3)).astype(np.float32))
    q = q.to(keys.device)
    require(not transformer._BCSP_KNN_ENABLED, 'oracle needs fresh candidate flag')
    dense = transformer.knn_point(16, keys, q)  # exact frozen legacy branch
    transformer.enable_bcsp_knn()
    candidate = transformer.knn_point(16, keys, q)
    d = transformer.square_distance(q, keys)
    require(candidate.shape == dense.shape and candidate.dtype == torch.long
            and bool(((candidate >= 0) & (candidate < keys.shape[1])).all()), 'KNN shape/range')
    require(bool((candidate.sort(-1).values[..., 1:] != candidate.sort(-1).values[..., :-1]).all()),
            'KNN duplicate indices')
    a, b = d.gather(2, candidate).sort(-1).values, d.gather(2, dense).sort(-1).values
    require(torch.allclose(a, b, atol=1e-5, rtol=1e-5), 'KNN sorted-distance mismatch')
    require(bool((a <= b[..., -1:] + 1e-5 + b[..., -1:].abs() * 1e-5).all()), 'KNN tie cutoff')
    return {'queries': 257, 'keys': keys.shape[1], 'k': 16, 'chunks': [256, 1],
            'candidate_calls': 1, 'dense_parent_calls': 1, 'distance_comparison_pass': True}


def gradient_evidence(torch, model):
    groups = {'grouper': model.base_model.grouper, 'encoder': model.base_model.encoder,
              'decoder': model.base_model.decoder}
    for p in model.parameters():
        require(p.grad is None or bool(torch.isfinite(p.grad).all()), 'nonfinite gradient')
    counts = {name: sum(p.grad is not None and bool((p.grad != 0).any()) for p in m.parameters())
              for name, m in groups.items()}
    require(all(counts.values()), 'missing active grouper/encoder/decoder gradient')
    return counts


def model_step(torch, model, x, target, counters, evidence, phase=lambda name: None):
    with no_update(torch, model, evidence):
        counters['forward'] += 1
        phase('forward_start')
        ret = model(x)
        require(isinstance(ret, tuple) and len(ret) == 4, 'exact training return tuple')
        require([list(t.shape) for t in ret] == [[8, 256, 3], [8, 0, 3], [8, 0, 3], [8, 8192, 3]],
                'training output shapes')
        require(all(t.dtype == torch.float32 and bool(torch.isfinite(t).all()) for t in ret), 'FP32 finite output')
        counters['loss'] += 1
        phase('loss_start')
        denoise, recon = model.get_loss(ret, target, epoch=0, partial=x)
        require(denoise.numel() == recon.numel() == 1 and float(denoise.detach()) == 0
                and bool(torch.isfinite(recon)) and recon.requires_grad, 'true project loss')
        loss = denoise + recon
        counters['backward'] += 1
        phase('backward_start')
        loss.backward()
        phase('backward_returned')
        evidence.update(loss_denoised=float(denoise.detach()), loss_recon=float(recon.detach()),
                        output_shapes=[list(t.shape) for t in ret],
                        nonzero_gradient_parameters=gradient_evidence(torch, model))


class MonitorQueryFailure(RuntimeError):
    def __init__(self, details):
        self.details = details
        super().__init__('monitor query ' + details['status'] + ': ' + str(details.get('exception_type', '')))


def _diagnostic_bytes(value):
    if value is None:
        value = b''
    if isinstance(value, str):
        value = value.encode('utf-8', errors='replace')
    return {'text': value[:DIAGNOSTIC_BYTES].decode('utf-8', errors='replace'),
            'bytes_total': len(value), 'truncated': len(value) > DIAGNOSTIC_BYTES}


def _smi_once(args, timeout, monitor=None, _popen=None):
    """One query only. Injection is for CPU contracts, never a CLI/backend option."""
    started = time.monotonic_ns()
    details = {'command': list(args), 'timeout_seconds': timeout,
               'reap_timeout_seconds': SMI_REAP_TIMEOUT, 'start_monotonic_ns': started,
               'thread': threading.current_thread().name,
               'phase_at_start': monitor.phase_snapshot() if monitor else 'CPU_contract',
               'child_pid': None, 'returncode': None, 'status': 'STARTING', 'query_attempts': 1}
    if monitor:
        details['query_id'] = monitor.next_query_id()
        monitor.event(dict(details, event='smi_start'))
    out, err, proc = b'', b'', None
    try:
        factory = subprocess.Popen if _popen is None else _popen
        proc = factory(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        details['child_pid'] = proc.pid
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            details.update(status='TIMEOUT', exception_type=type(exc).__name__,
                           returncode_at_deadline=proc.poll())
            out, err = exc.output or b'', exc.stderr or b''
            try:
                if proc.poll() is None:
                    proc.kill()
                    details['child_kill_sent'] = True
                else:
                    details['child_kill_sent'] = False
                out, err = proc.communicate(timeout=SMI_REAP_TIMEOUT)
                details['cleanup_completed'] = True
            except Exception as cleanup:
                details.update(cleanup_completed=False, cleanup_exception_type=type(cleanup).__name__,
                               cleanup_error=str(cleanup)[:DIAGNOSTIC_BYTES])
        else:
            details['status'] = 'OK' if proc.returncode == 0 else 'NONZERO_EXIT'
            if proc.returncode != 0:
                details['exception_type'] = 'ChildNonzeroExit'
    except Exception as exc:
        details.update(status='QUERY_ERROR', exception_type=type(exc).__name__,
                       error=str(exc)[:DIAGNOSTIC_BYTES])
    finally:
        ended = time.monotonic_ns()
        details.update(end_monotonic_ns=ended, elapsed_seconds=(ended - started) / 1e9,
                       phase_at_end=monitor.phase_snapshot() if monitor else 'CPU_contract',
                       stdout=_diagnostic_bytes(out), stderr=_diagnostic_bytes(err))
        if proc is not None:
            details['returncode'] = proc.returncode
        if monitor:
            monitor.event(dict(details, event='smi_result'))
    if details['status'] != 'OK':
        raise MonitorQueryFailure(details)
    try:
        return [r.strip() for r in out.decode('utf-8').splitlines() if r.strip()]
    except UnicodeError as exc:
        details.update(status='OUTPUT_DECODE_ERROR', exception_type=type(exc).__name__)
        if monitor:
            monitor.event(dict(details, event='smi_decode_failure'))
        raise MonitorQueryFailure(details) from exc


def smi(query, compute=False):
    flag = '--query-compute-apps=' if compute else '--query-gpu='
    args = ['/usr/bin/nvidia-smi', '--id=' + os.environ['CUDA_VISIBLE_DEVICES'], flag + query,
            '--format=csv,noheader,nounits']
    return _smi_once(args, SMI_TIMEOUT, _MONITOR)


class Budget:
    def __init__(self, scope, output):
        self.r = scope['resources']
        self.output, self.start = Path(output), time.monotonic()
        self.stop = threading.Event()
        self.peak_rss = self.peak_device = 0
        self.error = None
        contract = scope['monitoring_v2']
        for key, expected in {'query_timeout_seconds': SMI_TIMEOUT,
                              'reap_timeout_seconds': SMI_REAP_TIMEOUT,
                              'poll_wait_seconds': MONITOR_POLL_WAIT,
                              'diagnostic_stream_limit_bytes': DIAGNOSTIC_BYTES,
                              'event_record_limit': MONITOR_EVENT_LIMIT}.items():
            require(contract[key] == expected, 'monitor contract: ' + key)
        require(contract['no_query_retries'] is True and contract['timeout_causes_immediate_worker_stop'] is True,
                'monitor fail-stop contract')
        self._state_lock = threading.Lock()
        self._log_lock = threading.Lock()
        self._phase = 'startup'
        self._queries, self._events = 0, 0
        self.event_path = self.output / 'monitor_events.jsonl'
        with self.event_path.open('x', encoding='utf-8'):
            pass

    def phase_snapshot(self):
        with self._state_lock:
            return self._phase

    def next_query_id(self):
        with self._state_lock:
            self._queries += 1
            return self._queries

    def event(self, value):
        with self._log_lock:
            self._events += 1
            require(self._events <= MONITOR_EVENT_LIMIT, 'monitor event cap')
            with self.event_path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')

    def phase(self, name):
        require(isinstance(name, str) and len(name) <= 128, 'phase name')
        with self._state_lock:
            self._phase = name
        self.event({'event': 'phase', 'phase': name, 'monotonic_ns': time.monotonic_ns()})
        print('PHASE ' + name, flush=True)

    def check_values(self, rss, device_mib, output_bytes):
        self.peak_rss, self.peak_device = max(self.peak_rss, rss), max(self.peak_device, device_mib)
        require(time.monotonic() - self.start <= self.r['total_wall_timeout_seconds'], 'wall budget')
        require(rss <= self.r['process_RSS_monitored_limit_bytes'], 'RSS budget')
        require(device_mib <= self.r['device_memory_stop_MiB'], 'device memory budget')
        require(output_bytes <= self.r['result_output_limit_bytes'], 'output budget')

    def sample(self):
        status = Path('/proc/' + str(os.getpid()) + '/status').read_text(encoding='ascii')
        rss = int(next(x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:'))) * 1024
        size = sum(p.stat().st_size for p in self.output.rglob('*') if p.is_file())
        self.check_values(rss, self.peak_device, size)
        device = int(smi('memory.used')[0])
        self.check_values(rss, device, size)
        require(all(int(pid) == os.getpid() for pid in smi('pid', compute=True)), 'other GPU compute process')

    def watch(self):
        while not self.stop.wait(MONITOR_POLL_WAIT):
            try:
                self.sample()
            except Exception as exc:
                self.error = str(exc)[:4096]
                # Best effort evidence, followed by immediate whole-worker termination.
                try:
                    emit_new(self.output / 'monitor_failure.json',
                             {'error': self.error, 'exception_type': type(exc).__name__, 'pid': os.getpid(),
                              'phase': self.phase_snapshot(), 'monotonic_ns': time.monotonic_ns(),
                              'peak_RSS_sampled': self.peak_rss, 'peak_device_MiB_sampled': self.peak_device,
                              'query_failure': getattr(exc, 'details', None)})
                finally:
                    os.kill(os.getpid(), signal.SIGTERM)
                return


def validate_model(model):
    require(model.num_query == 256 and model.num_points == 8192 and model.factor == 32
            and model.decoder_type == 'fc' and model.denoise_weight == 0
            and model.fine_coverage_weight == 1 and model.fine_local_weight == 0, 'model contract')
    base = model.base_model
    require(base.center_num == [512, 256] and base.encoder_type == 'graph'
            and base.query_selection == 'learned_only' and not base.use_denoise
            and not base.encoder_adapter.enabled and not model.scqr_contract.enabled,
            'backbone/optional module contract')
    for name in ('coarse_geometry_guard_enabled', 'local_rim_guard_enabled', 'moment_trust_enabled',
                 'dense_contact_enabled', 'rim_query_enabled'):
        require(getattr(model, name) is False, 'optional path: ' + name)


def run(request, scope, output, budget):
    budget.phase('identity_source_binding')
    root = Path(scope['isolation']['future_root'])
    records = source_map(scope)
    for rel, record in records.items():
        exact(root / rel, record['sha256'], record['bytes'])
    exact(root / 'base_model.yaml', scope['bindings']['base_config']['sha256'])
    for record in scope['bindings']['provider'] + scope['bindings']['environment_metadata']:
        exact(record['path'], record['sha256'], record['bytes'])
    exact(__file__, request['entry_sha256'])
    identity = scope['identity']
    require(socket.gethostname() == identity['hostname'] and os.getuid() == identity['uid'], 'container identity')
    require(str(Path(sys.executable).resolve()) == identity['python_realpath']
            and sys.version.split()[0] == identity['python_version'], 'interpreter identity')
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, 'required -I -S -B')
    for key, value in scope['environment'].items():
        expected = value.replace('<owned_output>', str(output))
        require(os.environ.get(key) == expected, 'environment: ' + key)
    require(shutil.disk_usage(output).free >= scope['resources']['minimum_free_disk_bytes'], 'free disk')
    observed = smi('uuid,name,driver_version,memory.total,memory.used')
    require(len(observed) == 1, 'one physical GPU')
    uuid, name, driver, total, used = [x.strip() for x in observed[0].split(',')]
    require((uuid, name, driver, int(total)) == (identity['gpu_uuid'], identity['gpu_name'],
            identity['driver_version'], identity['nvidia_smi_memory_total_MiB']), 'physical GPU identity')
    require(int(used) <= scope['resources']['maximum_initial_gpu_used_MiB'] and not smi('pid', True), 'GPU idle gate')
    envroot = Path('/opt/conda/envs/adapointr-mamba')
    site = envroot / 'lib/python3.10/site-packages'
    provider_root = Path(scope['bindings']['provider'][0]['path']).parent.parent
    sys.path[:0] = [str(provider_root), str(site)]
    namespace_packages(root)
    sys.meta_path.insert(0, FiniteProjectImports(root, records))
    # Guard before dependency/model import. No parent project or real data root is allowed.
    temp = output / 'tmp'
    temp.mkdir()
    os.environ['TMPDIR'] = str(temp)
    sys.addaudithook(FilePolicy([root, provider_root, envroot, '/usr/lib',
                               '/proc/' + str(os.getpid()), '/dev/null', '/dev/urandom'], output).audit)
    budget.phase('import:numpy')
    import numpy as np
    budget.phase('import:torch')
    import torch
    budget.phase('import:timm')
    import timm
    budget.phase('import:yaml')
    import yaml
    budget.phase('import:easydict')
    from easydict import EasyDict
    require((torch.__version__, np.__version__, timm.__version__) ==
            (identity['torch_version'], identity['numpy_version'], identity['timm_version']), 'dependency versions')
    budget.phase('cuda:initialization')
    require(torch.cuda.is_available() and torch.cuda.device_count() == 1, 'one visible CUDA device')
    torch.cuda.set_device(0)
    configure_numeric(torch)
    props = torch.cuda.get_device_properties(0)
    require(props.total_memory >= scope['resources']['torch_peak_reserved_limit_bytes'], 'logical GPU capacity')
    budget.phase('import:chamfer_wrapper')
    chamfer = importlib.import_module('extensions.chamfer_dist')
    budget.phase('import:pointnet2_provider')
    pointnet = importlib.import_module('utils.pointnet2_utils')
    provider = importlib.import_module('pointnet2_ops.pointnet2_utils')
    native = importlib.import_module('pointnet2_ops._ext')
    require(Path(provider.__file__).resolve() == Path(scope['bindings']['provider'][1]['path']), 'provider wrapper origin')
    require(Path(native.__file__).resolve() == Path(scope['bindings']['provider'][2]['path']), 'provider binary origin')
    check_backend(chamfer, pointnet, provider)
    budget.phase('import:isolated_model')
    transformer = importlib.import_module('models.Transformer_utils')
    adapter = importlib.import_module('tools.bcsp_adapter')
    model_class = importlib.import_module('models.AdaPoinTr').AdaPoinTr
    config = EasyDict(yaml.safe_load((root / 'base_model.yaml').read_text(encoding='utf-8'))['model'])
    budget.phase('synthetic:input_generation')
    master, target = synthetic(np, torch)
    counters = {'forward': 0, 'loss': 0, 'backward': 0, 'optimizer': 0, 'scheduler': 0,
                'BNCal': 0, 'development': 0, 'checkpoint_write': 0}
    summary = {'status': 'RUNNING', 'backend': 'existing_project_torch_cdist', 'arms': [], 'counters': counters,
               'SMI_physical': observed[0], 'torch_logical': {'name': props.name, 'bytes': props.total_memory},
               'no_exclusive_cgroup_claim': True, 'BN_tracking_disabled_preflight_only': True}
    original_knn = adapter.torch_knn
    try:
        for n in (8192, 16384):
            arm = {'input_points': n, 'knn_calls': []}
            budget.phase('arm_start:' + str(n))
            summary['arms'].append(arm)
            with rng_preserved(torch, np, cuda=True, evidence=arm):
                random.seed(0)
                np.random.seed(0)
                torch.manual_seed(0)
                # flag reset only for the standalone exact legacy oracle, not model execution.
                transformer._BCSP_KNN_ENABLED = False
                arm['oracle'] = knn_oracle(torch, np, transformer, master[:1, :n].contiguous().to('cuda:0'))
                def tracked(k, xyz, query, chunk=256):
                    require(chunk == 256 and xyz.dtype == query.dtype == torch.float32, 'full-model KNN contract')
                    arm['knn_calls'].append({'batch': xyz.shape[0], 'keys': xyz.shape[1], 'queries': query.shape[1],
                                             'k': k, 'chunks': [min(256, query.shape[1] - i)
                                                               for i in range(0, query.shape[1], 256)]})
                    return original_knn(k, xyz, query, chunk=chunk)
                adapter.torch_knn = tracked
                model = model_class(config)
                validate_model(model)
                arm['initial_parameter_sha256'] = state_sha(model, True)
                if len(summary['arms']) == 2:
                    require(arm['initial_parameter_sha256'] == summary['arms'][0]['initial_parameter_sha256'],
                            'fresh model initialization mismatch')
                model.to('cuda:0')
                x, y = master[:, :n].contiguous().to('cuda:0'), target.to('cuda:0')
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats(0)
                arm['baseline_allocated'] = torch.cuda.memory_allocated(0)
                arm['baseline_reserved'] = torch.cuda.memory_reserved(0)
                model_step(torch, model, x, y, counters, arm,
                           phase=lambda name: budget.phase(str(n) + ':' + name))
                torch.cuda.synchronize()
                assert_numeric(torch)
                arm.update(peak_allocated=torch.cuda.max_memory_allocated(0),
                           peak_reserved=torch.cuda.max_memory_reserved(0))
                require(arm['peak_allocated'] <= scope['resources']['torch_peak_allocated_limit_bytes']
                        and arm['peak_reserved'] <= scope['resources']['torch_peak_reserved_limit_bytes'], 'torch peak budget')
                require(any(call['keys'] == n for call in arm['knn_calls']), 'full input key count not observed')
                budget.sample()
                del model, x, y
                gc.collect()
                torch.cuda.empty_cache()
                adapter.torch_knn = original_knn
        require(counters == {'forward': 2, 'loss': 2, 'backward': 2, 'optimizer': 0, 'scheduler': 0,
                             'BNCal': 0, 'development': 0, 'checkpoint_write': 0}, 'exact call counts')
        for name, module in tuple(sys.modules.items()):
            if name.split('.')[0] in PREFIXES and name not in PREFIXES:
                origin = Path(module.__file__).resolve()
                require(root in origin.parents, 'project origin escaped: ' + name)
        summary['status'] = 'PASS'
    except Exception as exc:
        summary.update(status='FAIL_STOP_NO_RETRY', error=repr(exc))
        raise
    finally:
        adapter.torch_knn = original_knn
        summary.update(peak_RSS=budget.peak_rss, peak_device_MiB=budget.peak_device,
                       wall_seconds=time.monotonic() - budget.start)
        emit_new(output / 'summary.json', summary)


def main():
    global _MONITOR
    parser = argparse.ArgumentParser()
    for field in ('request', 'request-sha256', 'authorization', 'runtime', 'scope'):
        parser.add_argument('--' + field, required=True)
    args = parser.parse_args()
    request = authorize(args.request, args.request_sha256, args.authorization, args.runtime)
    scope = read_json(exact(args.scope, SCOPE_SHA))
    output = Path(scope['filesystem']['future_output'])
    claim_output(output)
    budget = Budget(scope, output)
    _MONITOR = budget
    watcher = threading.Thread(target=budget.watch, daemon=True)
    try:
        budget.phase('startup:resource_sample')
        budget.sample()
        watcher.start()
        run(request, scope, output, budget)
        budget.sample()
    except Exception as exc:
        if not (output / 'summary.json').exists():
            emit_new(output / 'startup_failure.json', {'status': 'FAIL_STOP_NO_RETRY', 'error': repr(exc)})
        raise
    finally:
        budget.stop.set()
        if watcher.ident is not None:
            watcher.join(timeout=2 * SMI_TIMEOUT + SMI_REAP_TIMEOUT + 1)
        require(not watcher.is_alive(), 'monitor did not stop')


if __name__ == '__main__':
    main()
