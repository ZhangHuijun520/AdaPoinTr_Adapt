"""One artificial CPU contract batch; no main(), native provider or CUDA calls."""
import ast
import copy
import ctypes
import hashlib
import importlib.util
import json
from functools import partial
from pathlib import Path
import random
import sys
import traceback
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE/'artificial_cpu_entry_batch_v1'
sys.path.insert(0, str(HERE))
import bcsp_f0_cuda_admission_v1 as entry


def run():
    import numpy as np
    import torch
    from torch import nn
    torch.set_num_threads(2)
    torch.random.default_generator.manual_seed(321)
    checks = []
    def check(name, ok):
        assert bool(ok), name
        checks.append(name)
    def reject(name, fn):
        try:
            fn()
        except (RuntimeError, ValueError):
            checks.append(name); return
        raise AssertionError('accepted: '+name)
    check('fixed 4 full F/B and 6 decoder F/1B all0step', entry.SCIENCE == dict(
        full_forward=4, full_backward=4, full_loss=4, decoder_forward=6,
        decoder_backward=1, optimizer_steps=0, real_data_reads=0, checkpoint_loads=0,
        input_points=8192, output_points=8192, full_batches=[1, 1, 8, 8]))
    q = dict(schema='bcsp-f0-synthetic-cuda-v1', status='AWAITING_EXPLICIT_USER_AUTHORIZATION',
             execution_authorized=False, science=copy.deepcopy(entry.SCIENCE),
             tolerances=copy.deepcopy(entry.TOLERANCE),
             readiness=dict(identity_verified=True, inherited_assets_verified=True))
    auth = dict(schema='bcsp-f0-cuda-authorization-v1', request_sha256='a'*64,
                explicit_user_authorization=True, user_authorization_text='ARTIFICIAL CPU fixture only')
    runtime = dict(schema='bcsp-f0-cuda-runtime-v1', request_sha256='a'*64, authorization_sha256='b'*64)
    check('actual authorize path', entry.authorize(q, 'a'*64, auth, 'b'*64, runtime) is q)
    for name, field, value in [('count mismatch', 'science', dict(entry.SCIENCE, full_forward=5)),
                                ('missing readiness', 'readiness', dict(identity_verified=False, inherited_assets_verified=True)),
                                ('tolerance drift', 'tolerances', dict(entry.TOLERANCE, atol=1.))]:
        broken = copy.deepcopy(q); broken[field] = value
        reject(name, lambda: entry.authorize(broken, 'a'*64, auth, 'b'*64, runtime))
    reject('reverse receipt binding denied', lambda: entry.authorize(q, 'a'*64, dict(auth, runtime_sha256='c'*64), 'b'*64, runtime))
    reject('authorization hash mismatch', lambda: entry.authorize(q, 'a'*64, auth, 'c'*64, runtime))
    reject('no explicit user authorization', lambda: entry.authorize(q, 'a'*64, dict(auth, explicit_user_authorization=False), 'b'*64, runtime))
    events = []; c = entry.counters()
    for _ in range(4):
        entry.claim(c, 'full_forward', events.append)
    check('attempt recorded before possible operation', len(events) == 4 and events[-1]['counts']['full_forward'] == 4)
    reject('extra full forward rejected', lambda: entry.claim(c, 'full_forward', events.append))
    reject('optimizer step claim rejected', lambda: entry.claim(c, 'optimizer_steps', events.append))
    launchq = dict(project='/home/jovyan/adapointr_work/PoinTr',
        output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_v1',
        launch_contract=dict(request_path='/tmp/request.json', authorization_path='/tmp/authorization.json', runtime_path='/tmp/runtime.json'),
        limits=dict(wall_seconds=1800), identity=dict(python_realpath='/opt/conda/envs/adapointr-mamba/bin/python3.10'),
        entry=dict(path='/tmp/entry.py'), environment=dict(CUBLAS_WORKSPACE_CONFIG=':4096:8'))
    launch = entry.render_launcher(launchq, 'a'*64, 'b'*64, 'c'*64)
    check('POSIX parent and no Windows slash', '\\' not in launch.replace('\\n', '') and 'mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba\n' in launch)
    check('parent created before redirection', launch.index('mkdir -p') < launch.index(' >'))
    check('exclusive output creation and hard timeout', 'mkdir /home/' in launch and '--kill-after=10s 1800s' in launch and 'mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_' not in launch)
    check('exit code preserved', 'rc=$?' in launch and 'exit "$rc"' in launch)
    reject('truncated launch hash denied', lambda: entry.render_launcher(launchq, 'a'*8, 'b'*64, 'c'*64))

    def tensor_sha(t):
        t = t.detach().cpu().contiguous()
        return hashlib.sha256(ctypes.string_at(t.data_ptr(), t.numel()*t.element_size())).hexdigest()
    def state_sha(m, parameters_only=False):
        pairs = m.named_parameters() if parameters_only else m.state_dict().items()
        return hashlib.sha256(repr([(n, tensor_sha(t)) for n, t in pairs]).encode()).hexdigest()
    helper = SimpleNamespace(tensor_sha=tensor_sha, state_sha=state_sha)
    def rng_state(*args):
        return (repr(random.getstate()), repr(np.random.get_state()), tensor_sha(torch.get_rng_state()))
    parent = SimpleNamespace(rng_state=rng_state)
    # A CPU-only API facade; all cuda methods here point to ordinary CPU RNG/no-op functions.
    cuda_fixture = SimpleNamespace(get_rng_state=lambda _: torch.get_rng_state(),
        set_rng_state=lambda s, _: torch.set_rng_state(s), synchronize=lambda: None)
    class Proxy:
        cuda = cuda_fixture
        def __getattr__(self, name):
            return getattr(torch, name)
    proxy = Proxy()
    class Gain(nn.Module):
        def __init__(self):
            super().__init__(); self.weight = nn.Parameter(torch.tensor(.01))
    class FullFixture(nn.Module):
        def __init__(self):
            super().__init__(); b = nn.Module(); self.base_model = b
            b.coarse_pred = nn.Linear(3, 3); self.reduce_map = nn.Linear(3, 3)
            b.encoder = nn.Module(); b.encoder.blocks = nn.Module()
            b.encoder.blocks.blocks = nn.ModuleList()
            for _ in range(6):
                block = nn.Module(); block.attn = nn.Module(); block.attn.mixer = Gain()
                b.encoder.blocks.blocks.append(block)
            b.decoder = nn.Module(); b.decoder.coordinate_pe = nn.Linear(3, 3, bias=False)
            b.decoder.blocks = nn.ModuleList()
            for _ in range(8):
                block = nn.Module(); block.self_ssm = Gain(); block.cond_ssm = Gain()
                b.decoder.blocks.append(block)
            self.bn = nn.BatchNorm1d(3); self.loss_calls = 0; self.forward_calls = 0
        def forward(self, x):
            self.forward_calls += 1
            y = self.bn(x.transpose(1, 2)).mean(-1)
            y = self.reduce_map(self.base_model.coarse_pred(y))+self.base_model.decoder.coordinate_pe(y)
            y = y + sum(p for n, p in self.named_parameters() if n.endswith('.weight') and p.ndim == 0)
            coarse = y[:, None].expand(-1, 256, -1)
            dense = y[:, None].expand(-1, 8192, -1)
            return (coarse, coarse[:, :0], dense[:, :0], dense) if self.training else (coarse, dense)
        def get_loss(self, ret, target, epoch, partial):
            self.loss_calls += 1
            return ret[0].new_zeros(()), (ret[-1]-target).square().mean()+ret[0].square().mean()
    model = FullFixture().eval(); original = state_sha(model)
    x = torch.randn(8, 8192, 3); target = torch.randn_like(x)
    counts = entry.counters(); events = []
    records = entry.full_checks(proxy, np, model, helper, parent, x, target, counts, events.append, lambda *a: None)
    check('full engine actual 4F4loss4B on cheap fixture', model.forward_calls == model.loss_calls == counts['full_forward'] == counts['full_backward'] == 4)
    check('eval/train batch1/8 contract', [r['batch'] for r in records] == [1, 1, 8, 8])
    check('train BN updates logged eval remains unchanged', not records[0]['BN_changed'] and bool(records[2]['BN_changed']))
    check('full engine restored initial state and eval modes', state_sha(model) == original and not any(m.training for m in model.modules()))
    check('full gradient coverage includes all22 artificial mixers', len(records[0]['gradients']['module_norm_sums']) == 25)
    check('full repeat tolerance used without exact gradient equality', records[1]['repeat']['dense']['close'] and records[3]['repeat']['loss']['close'])
    # Construct genuine eight-layer decoder classes from bound mother AST, with declared surrogate mixers.
    source = ROOT/'outputs/cranial_bcsp_fullmamba_20261110/implementation_v1'
    p1 = ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'
    sys.path[:0] = [str(source), str(p1)]
    from bcsp_f0_decoder_v1 import F0Decoder
    snap = ROOT/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/models'
    def knn_point(k, xyz, query):
        return torch.cdist(query, xyz).topk(k, largest=False).indices
    def index_points(points, idx):
        return points[torch.arange(points.shape[0]).view(-1, 1, 1), idx]
    env = dict(torch=torch, nn=nn, partial=partial, knn_point=knn_point,
               index_points=index_points, trunc_normal_=nn.init.trunc_normal_)
    for filename, names in [('Transformer_utils.py', ['Mlp', 'Attention', 'CrossAttention', 'DynamicGraphAttention', 'LayerScale']),
                            ('AdaPoinTr.py', ['CrossAttnBlockApi', 'TransformerDecoder', 'PointTransformerDecoder'])]:
        tree = ast.parse((snap/filename).read_text(encoding='utf-8'))
        nodes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name in names]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, 'exec'), env)
    class Mixer(nn.Module):
        def __init__(self):
            super().__init__(); self.gain = nn.Parameter(torch.rand(384)*.02+.1)
        def forward(self, x):
            return x*self.gain+torch.cumsum(x, 1)*.001
    old = env['PointTransformerDecoder'](embed_dim=384, depth=8, num_heads=6, mlp_ratio=2, k=8,
        self_attn_block_style_list=['attn-graph']+['attn']*7, cross_attn_block_style_list=['attn-graph']+['attn']*7)
    dm = nn.Module(); dm.base_model = nn.Module(); dm.base_model.decoder = F0Decoder(old, Mixer).eval()
    events = []; counts = entry.counters()
    entry.decoder_checks(torch, dm, helper, counts, events.append, lambda *a: None, device='cpu')
    check('real decoder helper six artificial forwards one backward', counts['decoder_forward'] == 6 and counts['decoder_backward'] == 1)
    mechanism = next(e for e in events if e['kind'] == 'PREFIX_MECHANISM')
    check('early prefix boundary fixed and response measured before merge', mechanism['boundary_last_prefix_tokens_unchanged'] == 3 and mechanism['first_layer_conditional_suffix_before_graph'])
    check('three prefix variants exceed frozen noise floor in surrogate', all(v > mechanism['response_threshold'] for v in mechanism['effects'].values()))
    check('decoder batch isolation checked', mechanism['batch_first']['close'])
    check('decoder prefix memory and PE gradients covered', events[-1]['memory_grad_norm'] > 0)
    emit = dict(status='ARTIFICIAL_CPU_ENTRY_BATCH_PASS', checks=checks, check_count=len(checks),
        CUDA_calls=0, native_Mamba=False, actual_Chamfer=False, optimizer_steps=0,
        real_data_reads=0, full_fixture_forward=4, decoder_fixture_forward=6,
        warning='CPU surrogate and cheap loss validate entry logic only; no native admission')
    return emit


if __name__ == '__main__':
    OUT.mkdir(exist_ok=False)
    try:
        result = run()
    except BaseException as exc:
        (OUT/'failure.json').write_text(json.dumps(dict(status='FAIL_STOP_NO_RETRY', error=repr(exc),
                                             traceback=traceback.format_exc()), indent=2), encoding='utf-8')
        raise
    (OUT/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))
