"""F0-LQI only: 2 full F/B/loss (eval B1, train-mode B8), zero optimizer or real payloads.

Importing this module uses stdlib only. main requires separate authorization.
CPU tests call the small contract helpers, never main or native CUDA.
"""
import argparse
import ast
import contextlib
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import random
import shlex
import signal
import socket
import sys
import threading
import time


SCIENCE = dict(full_forward=2, full_backward=2, full_loss=2,
               decoder_forward=0, decoder_backward=0, optimizer_steps=0,
               real_data_reads=0, checkpoint_loads=0, input_points=8192,
               output_points=8192, full_batches=[1, 8])
TOLERANCE = dict(atol=1e-6, rtol=1e-5)
LIMITS = dict(wall_seconds=1800, RSS_bytes=8589934592, torch_peak_bytes=21474836480, device_MiB=22528, output_bytes=1073741824, minimum_free_disk_bytes=4294967296)
FIXTURE = dict(input_seed=20261110, target_seed=20261112, distribution="NumPy_default_rng_uniform_minus0.5_plus0.5", shape=[8,8192,3], dtype="float32")


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def clean(path):
    p = Path(path).absolute()
    need(not any(x.is_symlink() for x in (p, *p.parents)), 'linked path: '+str(p))
    need(not {'.ssh', '.aws', '.credentials', '.git'} & set(p.parts)
         and p.name not in ('.env', '.netrc', 'auth.json'), 'secret path')
    return p


def sha(path):
    h = hashlib.sha256()
    with clean(path).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def exact(record):
    p = clean(record['path'])
    need(p.is_file() and p.stat().st_size == record['bytes']
         and sha(p) == record['sha256'], 'binding: '+str(p))
    return p


def emit(path, value):
    with clean(path).open('x', encoding='ascii') as f:
        json.dump(value, f, indent=2, allow_nan=False)


def source_module(name, record):
    need(name not in sys.modules, 'preloaded module: '+name)
    p = exact(record)
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    exec(compile(p.read_bytes(), str(p), 'exec', dont_inherit=True), m.__dict__)
    return m


def authorize(q, digest, auth, auth_digest, runtime):
    need(q['schema'] == 'bcsp-lqi-synthetic-cuda-v1'
         and q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION'
         and q['execution_authorized'] is False, 'pending request')
    need(q['science'] == SCIENCE and q['tolerances'] == TOLERANCE and q['limits'] == LIMITS and q['fixture'] == FIXTURE, 'frozen count/tolerance/resource/fixture')
    need(q['readiness']['identity_verified'] and q['readiness']['inherited_assets_verified'],
         'missing bounded readiness evidence')
    need(set(auth) == {'schema', 'request_sha256', 'explicit_user_authorization', 'user_authorization_text'}
         and auth['schema'] == 'bcsp-lqi-cuda-authorization-v1'
         and auth['request_sha256'] == digest and auth['explicit_user_authorization'] is True
         and bool(auth['user_authorization_text'].strip()), 'separate authorization')
    need(runtime == dict(schema='bcsp-lqi-cuda-runtime-v1', request_sha256=digest,
                         authorization_sha256=auth_digest), 'one-way runtime')
    return q


def counters():
    return dict(full_forward=0, full_backward=0, full_loss=0,
                decoder_forward=0, decoder_backward=0, optimizer_steps=0)


def render_launcher(q, request_sha, authorization_sha, runtime_sha):
    """Render only after authorization; callers must preserve these original UTF-8 bytes."""
    for value in (request_sha, authorization_sha, runtime_sha):
        need(len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'full lowercase hash')
    L = q['launch_contract']; out = PurePosixPath(q['output'])
    command = ['/usr/bin/timeout', '--signal=TERM', '--kill-after=10s',
               str(q['limits']['wall_seconds'])+'s', q['identity']['python_realpath'], '-I', '-S', '-B',
               q['entry']['path'], '--request', L['request_path'], '--request-sha256', request_sha,
               '--authorization', L['authorization_path'], '--authorization-sha256', authorization_sha,
               '--runtime', L['runtime_path'], '--runtime-sha256', runtime_sha]
    env = '\n'.join('export '+k+'='+shlex.quote(v.replace('<owned_output>', str(out)))
                    for k, v in q['environment'].items())
    link_checks = ''.join('[ ! -L '+shlex.quote(str(p))+' ] || exit 121\n'
                          for p in reversed((out, *out.parents)) if str(p) != '/')
    script = ('#!/bin/bash\nset -eu\numask 077\ncd '+shlex.quote(q['project'])+'\n'+link_checks+
            'mkdir -p '+shlex.quote(str(out.parent))+'\nmkdir '+shlex.quote(str(out))+'\n'+env+
            '\nset +e\n'+shlex.join(command)+' >'+shlex.quote(str(out/'launch.log'))+' 2>&1\n'
            'rc=$?\nset -e\nprintf "%s\\n" "$rc" >'+shlex.quote(str(out/'exit_code.txt'))+'\nexit "$rc"\n')
    need(max(len(line.encode()) for line in script.splitlines()) <= 2048, 'launcher line bound')
    return script


def claim(c, key, event):
    need(key != 'optimizer_steps' and c[key] < SCIENCE[key], 'call cap: '+key)
    c[key] += 1
    event(dict(kind='ATTEMPT_BEFORE_CALL', operation=key, counts=dict(c)))


def compare(torch, a, b):
    d = (a.detach()-b.detach()).abs()
    return dict(max_abs=float(d.max()), close=bool(torch.allclose(
        a.detach(), b.detach(), atol=TOLERANCE['atol'], rtol=TOLERANCE['rtol'])))


def gradients(torch, model, prefixes):
    norms = {}
    for n, p in model.named_parameters():
        if p.grad is not None:
            need(bool(torch.isfinite(p.grad).all()), 'nonfinite gradient: '+n)
            norms[n] = float(p.grad.detach().double().norm())
    totals = {prefix: sum(v for n, v in norms.items() if n.startswith(prefix)) for prefix in prefixes}
    need(all(v > 0 for v in totals.values()), 'inactive gradient modules: '+repr(totals))
    return dict(parameter_norms=norms, module_norm_sums=totals)


def full_checks(torch, np, model, helper, parent, x, target, counts, event, sample):
    initial = {n: v.detach().cpu().clone() for n, v in model.state_dict().items()}
    parameter_sha = helper.state_sha(model, parameters_only=True)
    initial_state = helper.state_sha(model)
    rng = (random.getstate(), np.random.get_state(), torch.get_rng_state().clone(),
           torch.cuda.get_rng_state(0).clone())
    initial_rng_record = parent.rng_state(torch, np, helper, True)
    original_modes = [m.training for m in model.modules()]
    bn = [(m, m.momentum) for m in model.modules()
          if isinstance(m, torch.nn.modules.batchnorm._BatchNorm)]
    def restore():
        model.load_state_dict(initial, strict=True)
        model.zero_grad(set_to_none=True)
        random.setstate(rng[0]); np.random.set_state(rng[1])
        torch.set_rng_state(rng[2]); torch.cuda.set_rng_state(rng[3], 0)
        for m, momentum in bn:
            m.momentum = momentum
        for m, training in zip(model.modules(), original_modes):
            m.training = training
    records = []
    try:
        for phase, batch, training in [('eval_1', 1, False), ('train_1', 8, True)]:
            restore(); model.train(training)
            for m, _ in bn:
                need(m.track_running_stats, 'ordinary BN tracking')
                if training:
                    m.momentum = .9
            before_rng = parent.rng_state(torch, np, helper, True)
            sample(phase+':before', counts['full_forward'])
            claim(counts, 'full_forward', event)
            with torch.enable_grad():
                ret = model(x[:batch])
                need(len(ret) == (4 if training else 2), 'original tuple')
                coarse, dense = ret[0], ret[-1]
                need(coarse.shape == (batch, 256, 3) and dense.shape == (batch, 8192, 3)
                     and all(t.dtype == torch.float32 and bool(torch.isfinite(t).all())
                             for t in (coarse, dense)), 'full output shape/FP32/finite')
                loss_ret = ret if training else (coarse, coarse[:, :0], dense[:, :0], dense)
                claim(counts, 'full_loss', event)
                denoise, reconstruction = model.get_loss(loss_ret, target[:batch], epoch=0, partial=x[:batch])
                loss = denoise+reconstruction
                need(float(denoise.detach()) == 0 and loss.ndim == 0
                     and bool(torch.isfinite(loss)) and loss.requires_grad, 'full original loss')
                sample(phase+':before_backward', counts['full_forward'])
                claim(counts, 'full_backward', event)
                loss.backward()
            torch.cuda.synchronize()
            prefixes = ['base_model.coarse_pred.', 'base_model.decoder.coordinate_pe.',
                        'reduce_map.']
            prefixes += ['base_model.encoder.blocks.blocks.'+str(i)+'.attn.mixer.' for i in range(6)]
            prefixes += ['base_model.decoder.blocks.'+str(i)+'.'+s+'.'
                         for i in range(8) for s in ('self_ssm', 'cond_ssm')]
            prefixes += ['base_model.decoder.blocks.'+str(i)+'.norm_v.' for i in range(8)]
            prefixes += ['increase_dim.', 'decode_head.']
            grad = gradients(torch, model, prefixes)
            need(helper.state_sha(model, parameters_only=True) == parameter_sha, 'weight update')
            bn_changes = [n for n, t in model.state_dict().items()
                          if not torch.equal(t.detach().cpu(), initial[n])]
            need(all(n.endswith(('running_mean', 'running_var', 'num_batches_tracked'))
                     for n in bn_changes), 'non-BN state drift')
            need(bool(bn_changes) if training else not bn_changes, 'BN mode contract')
            after_rng = parent.rng_state(torch, np, helper, True)
            need(training or before_rng == after_rng, 'eval RNG drift')
            record = dict(phase=phase, batch=batch, loss=float(loss.detach()),
                          gradients=grad, BN_changed=bn_changes,
                          parameters_unchanged=True, RNG_before=before_rng, RNG_after=after_rng,
                          state_sha256=helper.state_sha(model))
            event(record); records.append(record)
            del ret, coarse, dense, loss_ret, denoise, reconstruction, loss
            restore(); sample(phase+':restored', counts['full_forward'])
    finally:
        restore()
        restored = dict(kind='FULL_RESTORATION', state_restored=helper.state_sha(model) == initial_state,
                        RNG_restored=parent.rng_state(torch, np, helper, True) == initial_rng_record,
                        modes_restored=[m.training for m in model.modules()] == original_modes)
        event(restored); need(all(v for k, v in restored.items() if k != 'kind'), 'restoration')
    return records


def main():
    parser = argparse.ArgumentParser()
    for key in ('request', 'request-sha256', 'authorization', 'authorization-sha256', 'runtime', 'runtime-sha256'):
        parser.add_argument('--'+key, required=True)
    args = vars(parser.parse_args())
    def record(key):
        p = clean(args[key]); return dict(path=str(p), bytes=p.stat().st_size, sha256=args[key+'_sha256'])
    qr, ar, rr = (record(k) for k in ('request', 'authorization', 'runtime'))
    q = authorize(json.loads(exact(qr).read_bytes()), qr['sha256'],
                  json.loads(exact(ar).read_bytes()), ar['sha256'], json.loads(exact(rr).read_bytes()))
    need(sys.platform == 'linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         'isolated Linux no-site no-bytecode')
    I = q['identity']; root = clean(q['model_root']); out = clean(q['output'])
    parent_cmd = Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    need(parent_cmd[:4] == ['/usr/bin/timeout','--signal=TERM','--kill-after=10s','1800s'], 'external timeout')
    marker = json.loads(clean(q['launch_contract']['launch_attempt_path']).read_bytes())
    need(marker == dict(status='CLAIMED_BEFORE_TMUX', request_sha256=qr['sha256']), 'single attempt marker')
    need(socket.gethostname() == I['hostname'] and os.getuid() == I['uid']
         and str(Path(sys.executable).resolve()) == I['python_realpath']
         and sys.version.split()[0] == I['python_version'], 'current identity')
    need(Path.cwd().resolve() == Path(q['project']), 'project cwd')
    need(out.parent == Path(q['project'])/'logs/cranial_bcsp_fullmamba', 'output parent')
    for key, value in q['environment'].items():
        need(os.environ.get(key) == value.replace('<owned_output>', str(out)), 'environment: '+key)
    exact(q['entry']); p3=json.loads(exact(q['P3']).read_bytes())
    need(p3['status']=='LQI_CUDA_ENTRY_LOCAL_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'] and p3['decoder_sha256']==q['implementation']['lqi_decoder']['sha256'] and p3['factory_sha256']==q['implementation']['lqi_factory']['sha256'], 'final implementation P3')
    for r in q['dependencies'] + list(q['implementation'].values()):
        exact(r)
    helper = source_module('f0_frozen_preflight_helper', q['helper'])
    parent = source_module('f0_frozen_prediction_helpers', q['parent_helper'])
    utc_module = source_module('f0_exact_utc', q['timezone_implementation'])
    need(q['timezone_resource'] == utc_module.UTC_RESOURCE, 'exact UTC contract')
    scope = json.loads(exact(q['preflight_scope']).read_bytes())
    static = json.loads(exact(q['static_config']).read_bytes())
    records = helper.source_map(scope)
    for rel, r in records.items():
        helper.exact(root/rel, r['sha256'], r['bytes'])
    helper.exact(root/'base_model.yaml', scope['bindings']['base_config']['sha256'])
    for r in scope['bindings']['provider'] + scope['bindings']['environment_metadata']:
        helper.exact(r['path'], r['sha256'], r['bytes'])
    values = [v.strip() for v in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    need(values[:4] == [I['gpu_uuid'], I['gpu_name'], I['driver_version'], str(I['nvidia_smi_memory_total_MiB'])]
         and int(values[4]) <= 256, 'current idle device')
    helper.claim_output(out)
    for name in ('tmp', 'cache', 'mplconfig', 'triton_cache', 'hf_cache'):
        (out/name).mkdir(exist_ok=False)
    journal = out/'events.jsonl'; journal.open('x').close()
    def event(value):
        with journal.open('a', encoding='ascii') as f:
            f.write(json.dumps(value, allow_nan=False)+'\n'); f.flush(); os.fsync(f.fileno())
    counts = counters(); stop = threading.Event(); watcher = None
    utc = utc_module.ExactUTCReader(q['timezone_resource'])
    guard = parent.ExactSourceReads(dict(encoder=q['implementation']['encoder'], factory=q['implementation']['factory'], f0_decoder=q['implementation']['lqi_decoder'], f0_factory=q['implementation']['lqi_factory']))
    try:
        envroot = Path('/opt/conda/envs/adapointr-mamba')
        provider = Path(scope['bindings']['provider'][0]['path']).parent.parent
        sys.path[:0] = [str(Path(__file__).parent), str(provider), str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root); sys.meta_path.insert(0, helper.FiniteProjectImports(root, records))
        # Compile all four new/parent modules from exact bytes; no neighboring pyc is consulted.
        policy = parent.make_policy(helper, [root, envroot, provider, Path(__file__).parent,
                    '/usr/lib', '/proc/'+str(os.getpid()), '/dev/null', '/dev/urandom'], out,
                    [], [], [], utc, guard)
        sys.addaudithook(policy.audit)
        import numpy as np
        import torch
        import timm
        import yaml
        import importlib
        from easydict import EasyDict
        need((torch.__version__, np.__version__, timm.__version__) ==
             (I['torch_version'], I['numpy_version'], I['timm_version']), 'versions')
        need(torch.cuda.is_available() and torch.cuda.device_count() == 1, 'one CUDA device')
        torch.cuda.set_device(0); helper.configure_numeric(torch)
        need(torch.version.cuda == I['torch_cuda_version'], 'torch CUDA version')
        ch = importlib.import_module('extensions.chamfer_dist')
        pn = importlib.import_module('utils.pointnet2_utils')
        pm = importlib.import_module('pointnet2_ops.pointnet2_utils')
        ext = importlib.import_module('pointnet2_ops._ext')
        helper.check_backend(ch, pn, pm)
        need(str(Path(pm.__file__).resolve()) == scope['bindings']['provider'][1]['path']
             and str(Path(ext.__file__).resolve()) == scope['bindings']['provider'][2]['path'], 'provider origin')
        transformer = importlib.import_module('models.Transformer_utils')
        cls = importlib.import_module('models.AdaPoinTr').AdaPoinTr
        need(static['model'] == yaml.safe_load((root/'base_model.yaml').read_text())['model'], 'frozen model config')
        transformer.enable_bcsp_knn()
        source_module('bcsp_mamba_encoder_v1', q['implementation']['encoder'])
        source_module('bcsp_p1_model_factory_v1', q['implementation']['factory'])
        source_module('bcsp_lqi_decoder_v1', q['implementation']['lqi_decoder'])
        factory = source_module('bcsp_lqi_factory_v1', q['implementation']['lqi_factory'])
        lock = threading.Lock()
        budget = parent.Budget(q, out, torch, helper)
        def sample(label, count):
            with lock:
                helper.assert_numeric(torch); budget.sample(label, count)
        def watch():
            while not stop.wait(2.):
                try:
                    sample('MONITOR', counts['full_forward'])
                except BaseException as exc:
                    try:
                        emit(out/'monitor_failure.json', dict(error=repr(exc), counts=dict(counts)))
                    finally:
                        os.kill(os.getpid(), signal.SIGTERM)
                    return
        watcher = threading.Thread(target=watch, daemon=True); watcher.start()
        sample('before_construction', 0)
        model, construction = factory.build_model(lambda: cls(EasyDict(static['model'])), seed=0)
        need(not construction['artificial_fixture'] and construction['version']=='F0-LQI-implementation-v1' and construction['variant']=='F0-LQI-v1' and construction['conditional_sequence']=='query_aligned_local_memory_interleaving' and construction['additional_learned_parameters']==0, 'native LQI model only'); helper.validate_model(model)
        need(sum(p.numel() for p in model.parameters())==39903169, 'same39903169 model parameters')
        names = ['mamba_ssm', 'mamba_ssm.modules.mamba_simple', 'mamba_ssm.ops.selective_scan_interface',
                 'causal_conv1d', 'causal_conv1d.causal_conv1d_interface', 'selective_scan_cuda', 'causal_conv1d_cuda']
        mods = [importlib.import_module(n) for n in names]
        origins = [str(Path(m.__file__).resolve()) for m in mods]
        need(set(origins) <= {r['path'] for r in q['dependencies']} and mods[0].__version__ == '2.3.1', 'native origins')
        emit(out/'construction.json', dict(factory=construction, native_origins=origins,
                                          torch_logical_capacity=torch.cuda.get_device_properties(0).total_memory))
        model.eval().to('cuda:0'); torch.cuda.reset_peak_memory_stats(0)
        master = np.random.default_rng(20261110).uniform(-.5, .5, (8, 8192, 3)).astype(np.float32)
        target = np.random.default_rng(20261112).uniform(-.5, .5, (8, 8192, 3)).astype(np.float32)
        x = torch.from_numpy(master).to('cuda:0'); target = torch.from_numpy(target).to('cuda:0')
        random.seed(0); np.random.seed(0); torch.manual_seed(0)
        # Scope-limited dynamic audit: block actual dispatched attention ops; record other suspicious ops.
        from torch.utils._python_dispatch import TorchDispatchMode
        dispatched = {}
        class NoAttention(TorchDispatchMode):
            def __torch_dispatch__(self, func, types, args=(), kwargs=None):
                name = str(func)
                need(not any(s in name.lower() for s in ('scaled_dot_product', 'flash_attention',
                          'efficient_attention', 'native_multi_head_attention')), 'attention op: '+name)
                if 'softmax' in name.lower() or 'einsum' in name.lower():
                    dispatched[name] = dispatched.get(name, 0)+1
                return func(*args, **(kwargs or {}))
        ssm_calls = {}; hooks = []
        def ssm_hook(name):
            def hook(module, args):
                need(args[0].shape[1] in (256, 512), 'native token length')
                ssm_calls[name] = ssm_calls.get(name, 0)+1
            return hook
        for name, module in model.named_modules():
            if type(module).__module__ == 'mamba_ssm.modules.mamba_simple':
                hooks.append(module.register_forward_pre_hook(ssm_hook(name)))
        try:
            with NoAttention():
                full_checks(torch, np, model, helper, parent, x, target, counts, event, sample)
        finally:
            for hook in hooks:
                hook.remove()
        need(counts == {k: SCIENCE[k] for k in counts}, 'exact final counts')
        need(sum(ssm_calls.values()) == 72 and len(ssm_calls) == 22 and all(v == (2 if '.cond_ssm' in n else 4) for n,v in ssm_calls.items()), 'actual native call counts')
        sample('complete', counts['full_forward']); stop.set(); watcher.join(15.)
        need(not watcher.is_alive(), 'monitor did not stop')
        emit(out/'completion.json', dict(status='LQI_NATIVE_CUDA_COMPLETE_PENDING_FORMAL_FREEZE_AUDIT',
             request_sha256=qr['sha256'], counts=counts, native_SSM_calls=ssm_calls,
             dispatch_observations=dispatched, attention_registered=factory.no_attention_inventory(model),
             dynamic_audit_limit='Known dispatched attention ops + bound module source; opaque extension internals not semantically inspected',
             finite_gradient_nondeterminism_disclosed=True, real_data_reads=0, checkpoint_loads=0,
             optimizer_constructed=False, training_admission=False, BNCal=False))
        files = [p for p in out.iterdir() if p.is_file() and p.name not in ('launch.log', 'worker.pid')]
        emit(out/'payload_manifest.json', [dict(name=p.name, bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(files)])
    except BaseException as exc:
        stop.set()
        if watcher is not None:
            watcher.join(15.)
        emit(out/'failure.json', dict(status='FAILED_STOP_NO_RETRY', error=repr(exc), counts=counts))
        raise
    finally:
        guard.close(); utc.close()


if __name__ == '__main__':
    main()
