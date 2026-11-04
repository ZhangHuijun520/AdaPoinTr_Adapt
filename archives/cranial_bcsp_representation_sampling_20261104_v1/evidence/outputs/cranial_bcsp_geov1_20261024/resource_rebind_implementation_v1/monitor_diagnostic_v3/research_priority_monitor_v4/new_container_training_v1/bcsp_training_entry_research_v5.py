"""Dedicated BCSP entry. Main requires future separate request authorization; no prepare CLI."""
import argparse
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import socket
import sys
import time

CONTRACT_SHA = '08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499'


def install_contract():
    # -I excludes the script directory; load only this exact hash-pinned sibling.
    path = Path(__file__).absolute().with_name('bcsp_training_contract_01dt08_v3.py')
    if any(p.is_symlink() for p in (path, *path.parents)) or hashlib.sha256(path.read_bytes()).hexdigest() != CONTRACT_SHA:
        raise RuntimeError('contract bootstrap identity')
    spec = importlib.util.spec_from_file_location('bcsp_training_contract_v1', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for name in ('require', 'exact', 'json_bound', 'no_links', 'sha', 'emit', 'authorize',
                 'verify_qualified_receipt', 'validate_order', 'canonical_sha',
                 'validate_rebind', 'validate_environment', 'validate_live_identity'):
        globals()[name] = getattr(module, name)

PREFLIGHT_SHA = '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'
SCOPE_SHA = 'c6edb9bfcf833d2abf98eb18749d03b49a490579d79475e4823750df6a8311e6'
QC_SHA = '54fcd0018f9a51f04b8408b3842b6d5c4243777979a0e0add31541e04fa3c55b'
FOLD_SHA = 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'
GPU_AUDIT_SHA = 'af3c3053be96a443d203c486ccede4d2bf2f0799ae753294ee946618726cf000'
PREFLIGHT_REQUEST = '7a7a74fcec86bb4fa6c7ab77b74e8d509a26ae75ade73a05d9c8cab183ef2365'
PROJECT = '/home/jovyan/adapointr_work/PoinTr'


def load_bound(name, record):
    path = exact(record)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def payload_paths(root, selected):
    root = no_links(root)
    result = {}
    for record in selected:
        p = no_links(root / record['point_path'])
        require(root in p.parents and p.suffix == '.npz' and p not in result, 'exact distinct NPZ paths')
        result[p] = record['sha256']
    require(len(result) == 315, '315 readable payloads only')
    return result


def make_training_policy(helper, read_roots, output, allowed_payloads):
    """Extend only this task's exact 315 NPZ reads and one final checkpoint write/read."""
    class TrainingPolicy(helper.FilePolicy):
        def check(self, filename, write=False):
            if isinstance(filename, int):
                return
            p = no_links(os.fsdecode(filename))
            require(not ({'.ssh', '.aws', '.credentials', '.git'} & set(p.parts))
                    and p.name not in {'.netrc', '.env'}, 'secret path')
            if p.suffix.lower() == '.npz':
                require(not write and p in allowed_payloads, 'non-allowlisted NPZ access: ' + str(p))
                return
            if p.suffix.lower() in helper.PAYLOAD or p.name.lower().endswith('.nii.gz'):
                require(p == self.output / 'ckpt-last.pth', 'nonfinal checkpoint/payload denied: ' + str(p))
                return
            return super().check(filename, write)
    return TrainingPolicy(read_roots, output)


class TrainingBudget:
    """Per-step monitored contract, not a cgroup or continuous-memory guarantee."""
    def __init__(self, limits, output, torch, helper):
        self.limits, self.output, self.torch, self.helper = limits, Path(output), torch, helper
        self.start, self.records = time.monotonic(), 0
        self.path = self.output / 'resources.jsonl'
        with self.path.open('x', encoding='utf-8'):
            pass
        torch.cuda.reset_peak_memory_stats(0)

    def local(self):
        require(time.monotonic() - self.start <= self.limits['wall_seconds'], 'training wall budget')
        status = Path('/proc/' + str(os.getpid()) + '/status').read_text(encoding='ascii')
        rss = int(next(x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:'))) * 1024
        size = sum(p.stat().st_size for p in self.output.rglob('*') if p.is_file())
        require(rss <= self.limits['RSS_bytes'] and size <= self.limits['output_bytes'],
                'training RSS/output budget')
        require(shutil.disk_usage(self.output).free >= self.limits['minimum_free_disk_bytes'], 'free disk')
        return rss, size

    def sample(self, label, step):
        rss, size = self.local()
        self.torch.cuda.synchronize()
        allocated = self.torch.cuda.max_memory_allocated(0)
        reserved = self.torch.cuda.max_memory_reserved(0)
        used = int(self.helper.smi('memory.used')[0])
        # User-approved research-priority policy: PID telemetry is diagnostic only.
        # SMI PIDs and container PIDs have no established common namespace here.
        pids, pid_query_error = None, None
        try:
            pids = [int(p) for p in self.helper.smi('pid', True)]
        except Exception as exc:
            pid_query_error = repr(exc)[:512]
        own_pid = os.getpid()
        checks = {
            'allocated_within_limit': allocated <= self.limits['torch_peak_bytes'],
            'reserved_within_limit': reserved <= self.limits['torch_peak_bytes'],
            'device_within_limit': used <= self.limits['device_MiB'],
        }
        self.records += 1
        require(self.records <= 3902, 'fixed training resource record cap')
        event = {
            'phase': label, 'committed_step': step, 'RSS': rss, 'output_bytes': size,
            'peak_allocated': allocated, 'peak_reserved': reserved, 'device_MiB': used,
            'compute_PIDs': pids, 'own_PID': own_pid,
            'PID_policy': 'DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE',
            'PID_query_error': pid_query_error,
            'raw_PIDs_match_worker_number': (all(p == own_pid for p in pids) if pids else None),
            'PID_warning': (pid_query_error is not None or not pids
                            or any(p != own_pid for p in pids)),
            'elapsed_seconds': time.monotonic() - self.start,
            'limits': dict(self.limits), 'checks': checks,
            'failed_checks': [key for key, passed in checks.items() if not passed],
            'resource_guard_passed': all(checks.values()),
        }
        # Persist the failed sample before enforcing exactly the original assertion.
        # A logging/fsync failure propagates immediately; it never permits training to continue.
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event, allow_nan=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        require(allocated <= self.limits['torch_peak_bytes'] and reserved <= self.limits['torch_peak_bytes']
                and used <= self.limits['device_MiB'],
                'training GPU memory budget')

    def before_step(self, step):
        self.local()

    def after_step(self, step):
        self.sample('after_step', step)

    def before_final(self):
        self.sample('before_final', 3900)

    def after_final(self):
        self.sample('after_final', 3900)


def verify_timeout(seconds, parent_argv):
    require(parent_argv[:4] == ['/usr/bin/timeout', '--signal=TERM', '--kill-after=5s', str(seconds) + 's'],
            'external timeout parent required')


def main():
    parser = argparse.ArgumentParser()
    for key in ('request', 'request-sha256', 'authorization', 'authorization-sha256', 'runtime', 'runtime-sha256'):
        parser.add_argument('--' + key, required=True)
    args = parser.parse_args()
    def record(path, digest):
        p = no_links(path)
        return {'path': str(p), 'bytes': p.stat().st_size, 'sha256': digest}
    request_record = record(args.request, args.request_sha256)
    q, static = authorize(request_record, record(args.authorization, args.authorization_sha256),
                          record(args.runtime, args.runtime_sha256))
    require(sys.platform == 'linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
            'Linux -I -S -B required')
    require(q['GPU_audit']['sha256'] == GPU_AUDIT_SHA and q['preflight_request_sha256'] == PREFLIGHT_REQUEST
            and q['preflight_scope']['sha256'] == SCOPE_SHA and q['QC']['verification']['sha256'] == QC_SHA
            and q['QC']['fold_binding']['sha256'] == FOLD_SHA,
            'fixed prior evidence; no implicit identity rebind')
    scope = json_bound(q['preflight_scope'])
    rebind = validate_rebind(q['resource_rebind'], q['preflight_scope'], q['GPU_audit'])
    require(q['identity'] == rebind['new_identity'] and q['model_root'] == scope['isolation']['future_root'],
            'explicit rebound identity; unchanged model root')
    identity = q['identity']
    require(socket.gethostname() == identity['hostname'] and os.getuid() == identity['uid']
            and str(Path(sys.executable).resolve()) == identity['python_realpath']
            and sys.version.split()[0] == identity['python_version'], 'current container/Python identity')
    os.chdir(PROJECT)
    require(str(Path.cwd()) == PROJECT, 'project root')
    output = no_links(q['output'])
    require(Path(PROJECT + '/logs') in output.parents, 'owned result root')
    require(set(q['implementation']) == {'entry', 'contract', 'runtime', 'preflight_helper'}, 'four implementation bindings')
    require(Path(q['implementation']['entry']['path']).absolute() == Path(__file__).absolute(), 'entry origin')
    require(q['implementation']['preflight_helper']['sha256'] == PREFLIGHT_SHA, 'unchanged GPU helper')
    for r in q['implementation'].values():
        exact(r)
    require(str(Path(q['implementation']['contract']['path']).absolute()) ==
            str(Path(sys.modules['bcsp_training_contract_v1'].__file__).absolute()), 'contract module origin')
    parent_argv = Path('/proc/' + str(os.getppid()) + '/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    verify_timeout(static['resources']['wall_seconds'], parent_argv)
    marker = json.loads(no_links(q['launch_attempt']).read_text(encoding='utf-8'))
    require(marker.get('request_sha256') == args.request_sha256 and marker.get('status') == 'CLAIMED_BEFORE_TMUX',
            'single-use launcher attempt required')
    selected, fold = verify_qualified_receipt(json_bound(q['QC']['qualified_receipt']), q['QC']['verification'],
                                              q['QC']['manifests'], q['QC']['fold_binding'], q['fold'], q['n_input'])
    plan = validate_order(json_bound(q['order_plan']), fold['train_case_ids'])
    allowed = payload_paths(q['data_root'], selected)
    require(str(no_links(q['data_root'])).startswith('/home/jovyan/')
            and len(Path(q['data_root']).parts) > 3, 'explicit server data root; no Windows translation')
    for p, digest in allowed.items():
        require(p.is_file() and sha(p) == digest, 'approved payload drift: ' + str(p))
    helper = load_bound('bcsp_frozen_gpu_helper', q['implementation']['preflight_helper'])
    root = Path(q['model_root'])
    records = helper.source_map(scope)
    for rel, r in records.items():
        helper.exact(root / rel, r['sha256'], r['bytes'])
    helper.exact(root / 'base_model.yaml', scope['bindings']['base_config']['sha256'])
    for r in scope['bindings']['provider'] + scope['bindings']['environment_metadata']:
        helper.exact(r['path'], r['sha256'], r['bytes'])
    validate_environment(scope, identity, output, os.environ)
    helper._MONITOR = None
    observed = [x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    validate_live_identity(identity, {'hostname': socket.gethostname(), 'gpu_uuid': observed[0],
                                      'driver_version': observed[2]})
    require(observed[:4] == [identity['gpu_uuid'], identity['gpu_name'], identity['driver_version'],
                            str(identity['nvidia_smi_memory_total_MiB'])]
            and int(observed[4]) <= 256 and not helper.smi('pid', True), 'GPU identity/idle gate')
    if output.exists():
        require({p.name for p in output.iterdir()} == {'launch.log'} and not (output / 'launch.log').is_symlink(),
                'fresh launcher-only output')
    else:
        output.mkdir()
    with (output / 'worker.pid').open('x', encoding='ascii') as stream:
        stream.write(str(os.getpid()) + '\n')
    try:
        envroot = Path('/opt/conda/envs/adapointr-mamba')
        provider = Path(scope['bindings']['provider'][0]['path']).parent.parent
        impl = Path(q['implementation']['entry']['path']).parent
        sys.path[:0] = [str(provider), str(envroot / 'lib/python3.10/site-packages')]
        helper.namespace_packages(root)
        sys.meta_path.insert(0, helper.FiniteProjectImports(root, records))
        (output / 'tmp').mkdir()
        require(os.environ.get('TMPDIR') == str(output / 'tmp'), 'owned TMPDIR')
        sys.addaudithook(make_training_policy(helper, [root, impl, envroot, provider, '/usr/lib',
                                                       '/proc/' + str(os.getpid()), '/dev/null', '/dev/urandom'],
                                              output, allowed).audit)
        import numpy as np
        import torch
        import timm
        import yaml
        from easydict import EasyDict
        require((torch.__version__, np.__version__, timm.__version__) ==
                (identity['torch_version'], identity['numpy_version'], identity['timm_version']), 'versions')
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1, 'single CUDA GPU')
        torch.cuda.set_device(0)
        helper.configure_numeric(torch)
        import importlib
        chamfer = importlib.import_module('extensions.chamfer_dist')
        pointnet = importlib.import_module('utils.pointnet2_utils')
        pn = importlib.import_module('pointnet2_ops.pointnet2_utils')
        native = importlib.import_module('pointnet2_ops._ext')
        require(str(Path(pn.__file__).resolve()) == scope['bindings']['provider'][1]['path']
                and str(Path(native.__file__).resolve()) == scope['bindings']['provider'][2]['path'], 'native provider origins')
        helper.check_backend(chamfer, pointnet, pn)
        model_cls = importlib.import_module('models.AdaPoinTr').AdaPoinTr
        transformer = importlib.import_module('models.Transformer_utils')
        require(static['model'] == yaml.safe_load((root / 'base_model.yaml').read_text(encoding='utf-8'))['model'],
                'exact validated model config')
        runtime = load_bound('bcsp_training_runtime_v5', q['implementation']['runtime'])
        # The separately authorized order file is authoritative for both arms.
        # Do not regenerate a platform/version-dependent randperm at GPU launch.
        random.seed(0)
        np.random.seed(0)
        torch.manual_seed(0)
        model = model_cls(EasyDict(static['model']))
        helper.validate_model(model)
        dataset = runtime.BCSPDataset(q['data_root'], selected, fold['train_sources'], q['n_input'])
        budget = TrainingBudget(static['resources'], output, torch, helper)
        return runtime.train_lifecycle(model, lambda e: runtime.make_loader(dataset, plan, e), selected, plan,
                                       output, device='cuda:0', numeric_check=helper.assert_numeric,
                                       resources=budget, knn_enable=transformer.enable_bcsp_knn,
                                       state_fingerprint=helper.state_sha)
    except BaseException as exc:
        if not (output / 'failure.json').exists() and not (output / 'completion.json').exists():
            emit(output / 'startup_failure.json', {'status': 'FAILED_STOP_NO_RETRY', 'error': repr(exc)})
        raise


install_contract()

if __name__ == '__main__':
    main()
