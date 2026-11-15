"""Synthetic CPU interfaces only. Artificial mixer is NOT a native Mamba proof."""
import ast
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from bcsp_mamba_encoder_v1 import lexicographic_order, gather_tokens, BidirectionalSpatialMamba, MambaEncoderBlock
import bcsp_p1_model_factory_v1 as factory

checks = []
def check(name, condition):
    if not condition:
        raise AssertionError(name)
    checks.append(name)

def rejects(name, action):
    try:
        action()
    except (ValueError, RuntimeError):
        checks.append(name)
    else:
        raise AssertionError(name)


class ArtificialAttention(nn.Module):
    def __init__(self, dim, **kwargs):
        super().__init__()
        self.proj = nn.Linear(dim, dim)
    def forward(self, x):
        return self.proj(x)


class ArtificialGraph(nn.Module):
    def __init__(self, dim, **kwargs):
        super().__init__()
        self.proj = nn.Linear(dim, dim)
        self.last_pos = self.last_idx = None
    def forward(self, x, pos, idx=None):
        self.last_pos, self.last_idx = pos.detach().clone(), idx.detach().clone()
        return self.proj(x) + pos[..., :1]


class ArtificialMLP(nn.Module):
    def __init__(self, in_features, hidden_features, act_layer, drop):
        super().__init__()
        self.layers = nn.Sequential(nn.Linear(in_features, hidden_features), act_layer(), nn.Linear(hidden_features, in_features))
    def forward(self, x):
        return self.layers(x)


class ArtificialCausalMixer(nn.Module):
    def __init__(self):
        super().__init__()
        self.in_proj = nn.Linear(384, 384)
        self.dt_proj = nn.Linear(2, 2)
        nn.init.constant_(self.dt_proj.bias, -3.)
        self.dt_proj.bias._no_reinit = True
        self.A_log = nn.Parameter(torch.ones(2, 3))
        self.A_log._no_weight_decay = True
        self.D = nn.Parameter(torch.ones(384))
        self.D._no_weight_decay = True
        self.calls = 0
    def forward(self, x):
        self.calls += 1
        return torch.tanh(self.in_proj(x).cumsum(1) / x.shape[1]) + self.dt_proj.bias.mean()


def legacy_block_type():
    path = ROOT / 'outputs/cranial_scqr_v12_qa_github_publish_20261019/models/AdaPoinTr.py'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == '1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4'
    node = next(n for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n, ast.ClassDef) and n.name == 'SelfAttnBlockApi')
    namespace = dict(nn=nn, torch=torch, Attention=ArtificialAttention, DynamicGraphAttention=ArtificialGraph, Mlp=ArtificialMLP)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['SelfAttnBlockApi']


LegacyBlock = legacy_block_type()

class ArtificialLegacyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.base_model = nn.Module()
        self.base_model.encoder = nn.Module()
        self.base_model.encoder.blocks = nn.Module()
        self.base_model.encoder.blocks.blocks = nn.ModuleList([
            LegacyBlock(384, 6, mlp_ratio=2, block_style='attn-graph' if i == 0 else 'attn', combine_style='concat') for i in range(6)])
        self.base_model.coarse_pred = nn.Linear(384, 3)
        self.decode_head = nn.Linear(3, 3)
        self.apply(self.parent_initialize)
    @staticmethod
    def parent_initialize(module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, std=.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', choices=('CPU_validation_v1', 'CPU_validation_v2'), default='CPU_validation_v1')
    args = parser.parse_args()
    torch.set_num_threads(2)
    output = HERE.parent / args.output
    output.mkdir(exist_ok=False)
    try:
        pos = torch.tensor([[[1., 0, 0], [0, 1, 0], [0, 0, 2], [0, 0, 1], [0, 0, 1]],
                            [[0., 0, 1], [0, 0, 1], [1, 0, 0], [0, 1, 0], [0, 0, 2]]])
        order, inverse = lexicographic_order(pos)
        check('stable xyz ordering with exact ties and batch isolation', order.tolist() == [[3, 4, 2, 1, 0], [0, 1, 4, 3, 2]])
        x = torch.randn(2, 5, 384, requires_grad=True)
        check('sort then inverse restores exact tensor bytes', torch.equal(gather_tokens(gather_tokens(x, order), inverse), x))
        bad = pos.clone();bad[0, 0, 0] = float('nan')
        rejects('nonfinite coordinate rejected', lambda: lexicographic_order(bad))
        mixer = ArtificialCausalMixer();branch = BidirectionalSpatialMamba(mixer)
        result = branch(x, pos)
        check('one shared mixer called exactly twice', mixer.calls == 2 and len(list(branch.children())) == 1)
        result.square().mean().backward()
        check('real CPU autograd reaches features and artificial mixer', x.grad is not None and torch.isfinite(x.grad).all() and mixer.in_proj.weight.grad.abs().sum() > 0)
        with torch.no_grad():
            expected = []
            for i in range(2):
                expected.append(branch(x[i:i+1], pos[i:i+1]))
            check('batched result matches independent per-case calls', torch.allclose(result, torch.cat(expected), atol=1e-6, rtol=1e-6))
        rejects('wrong feature width rejected', lambda: branch(x[..., :383], pos))
        nonfinite = x.detach().clone();nonfinite[0, 0, 0] = float('inf')
        rejects('nonfinite feature rejected', lambda: branch(nonfinite, pos))
        # Exact old block control: inject the original global function, not a new approximation.
        class OriginalGlobal(nn.Module):
            def __init__(self, original):super().__init__();self.original = original
            def forward(self, features, coordinates):return self.original(features)
        for style in ('attn', 'attn-graph'):
            block = LegacyBlock(384, 6, mlp_ratio=2, block_style=style, combine_style='concat').eval()
            adapted = MambaEncoderBlock(block, OriginalGlobal(block.attn)).eval()
            idx = torch.zeros(2, 5, 2, dtype=torch.long)
            with torch.no_grad():old = block(x, pos, idx);new = adapted(x, pos, idx)
            check('parent block exact OFF-path regression: '+style, torch.equal(old, new))
            check('shared residual and FFN module identity: '+style, adapted.norm1 is block.norm1 and adapted.mlp is block.mlp and adapted.norm2 is block.norm2)
            if style == 'attn-graph':
                check('local graph receives original order and KNN indices', adapted.local_attn is block.local_attn and torch.equal(block.local_attn.last_pos, pos) and torch.equal(block.local_attn.last_idx, idx) and adapted.merge_map is block.merge_map)
        rng = torch.get_rng_state().clone()
        t0, te = factory.build_model(ArtificialLegacyModel, 'T0')
        m0, me = factory._build(ArtificialLegacyModel, 'M0', 0, ArtificialCausalMixer, artificial_fixture=True)
        check('factory restores caller CPU RNG', torch.equal(torch.get_rng_state(), rng))
        check('T0 and M0 shared initial state exact', te['common_state'] == me['common_state'])
        check('exact six global replacements; no attention branch left', all(isinstance(b, MambaEncoderBlock) and isinstance(b.attn, BidirectionalSpatialMamba) for b in m0.base_model.encoder.blocks.blocks) and me['replaced_global_branches'] == 6)
        check('only first block retains graph', [b.local_attn is not None for b in m0.base_model.encoder.blocks.blocks] == [True, False, False, False, False, False])
        check('post-parent SSM special bias and flags preserved', all(torch.equal(b.attn.mixer.dt_proj.bias, torch.full((2,), -3.)) and getattr(b.attn.mixer.dt_proj.bias, '_no_reinit', False) for b in m0.base_model.encoder.blocks.blocks))
        check('no attention/adapter fallback labeled as native Mamba', me['artificial_fixture'] and not me['native_attention_retained'] and me['shared_bidirectional_scans_per_forward'] == 12)
        # Save/load synthetic state only, to test names and strict state restoration.
        clone, _ = factory._build(ArtificialLegacyModel, 'M0', 0, ArtificialCausalMixer, artificial_fixture=True)
        clone.load_state_dict(m0.state_dict(), strict=True)
        check('strict synthetic M0 state restore', all(torch.equal(v, clone.state_dict()[n]) for n, v in m0.state_dict().items()))
        rejects('unsupported seed refused', lambda: factory.build_model(ArtificialLegacyModel, 'T0', seed=1))
        # Runtime functions extracted without importing payload loaders or a real training entry.
        runtime_path = HERE / 'bcsp_p1_training_runtime_v1.py'
        tree = ast.parse(runtime_path.read_text(encoding='utf-8'))
        selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('optimizer_groups', 'make_optimizer', 'set_bn_momentum')]
        def require(v, text):
            if not v:raise ValueError(text)
        namespace = dict(torch=torch, require=require)
        exec(compile(ast.Module(body=selected, type_ignores=[]), str(runtime_path), 'exec'), namespace)
        groups, records = namespace['optimizer_groups'](m0)
        check('all six A_log matrices explicitly exempted', len([r for r in records if r['name'].endswith('.A_log') and r['weight_decay'] == 0 and r['reason'] == 'explicit_no_weight_decay']) == 6)
        check('normal matrices retain original decay', all(r['weight_decay'] == .0005 for r in records if r['name'].endswith('in_proj.weight')))
        original_groups = {n: 0. if p.ndim == 1 or n.endswith('.bias') else .0005 for n,p in t0.named_parameters()}
        _, tr = namespace['optimizer_groups'](t0)
        check('T0 decay grouping unchanged exactly', original_groups == {r['name']:r['weight_decay'] for r in tr})
        check('every trainable parameter assigned once', len({id(p) for g in groups for p in g['params']}) == len(list(m0.parameters())) == sum(len(g['params']) for g in groups))
        optimizer = namespace['make_optimizer'](m0)
        check('AdamW inherited numeric defaults', optimizer.defaults['lr'] == .0001 and optimizer.defaults['betas'] == (.9,.999) and optimizer.defaults['eps'] == 1e-8 and optimizer.defaults['amsgrad'] is False)
        # Verify no lifecycle edit beyond one grouping receipt and two alias fields.
        parent_path = ROOT / 'outputs/cranial_bcsp_geov1_20261024/training_closure_v5/bcsp_training_runtime_v5.py'
        assert hashlib.sha256(parent_path.read_bytes()).hexdigest() == '55ad69b0e87f3fc4ecac68a5ebcc4cdd560c4825ff01363ba9868de5875f0847'
        parent = ast.parse(parent_path.read_text(encoding='utf-8'))
        adapted = copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='train_lifecycle'))
        original = next(n for n in parent.body if isinstance(n,ast.FunctionDef) and n.name=='train_lifecycle')
        class StripAliases(ast.NodeTransformer):
            def visit_Expr(self,node):
                if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='emit' and any(isinstance(n,ast.Constant) and n.value=='optimizer_parameter_groups.json' for n in ast.walk(node)):
                    return None
                return self.generic_visit(node)
            def visit_Dict(self,node):
                pairs=[(k,v) for k,v in zip(node.keys,node.values) if not isinstance(k,ast.Constant) or k.value not in ('loss_denoise','loss_reconstruction')]
                node.keys=[k for k,v in pairs];node.values=[v for k,v in pairs];return self.generic_visit(node)
        adapted=StripAliases().visit(adapted)
        check('whole 3900-step lifecycle AST unchanged except receipts/aliases', ast.dump(adapted,include_attributes=False)==ast.dump(original,include_attributes=False))
        for name in ('BCSPDataset','make_order','make_loader','set_bn_momentum','claim_output'):
            first=next(n for n in parent.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==name)
            second=next(n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name==name)
            check('parent data/order/BN/claim unchanged: '+name,ast.dump(first,include_attributes=False)==ast.dump(second,include_attributes=False))
        check('no optimizer updates or real data accessed by this test', True)
        result=dict(status='TARGETED_ARTIFICIAL_CPU_CONTRACTS_PASS',count=len(checks),checks=checks,torch_version=torch.__version__,native_mamba_locally_available=importlib.util.find_spec('mamba_ssm') is not None,
                    actual_native_Mamba_calls=0,full_AdaPoinTr_calls=0,GPU_calls=0,optimizer_steps=0,real_checkpoint_loads=0,real_payload_reads=0,
                    limitation='Artificial mixer + original block AST with artificial Attention/graph/MLP; no claim of actual Mamba, full model or CUDA correctness')
        with (output/'result_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
        print(json.dumps(result))
    except BaseException as exc:
        with (output/'failure_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',passed=checks,error=repr(exc)),f,indent=2)
        raise


if __name__=='__main__':main()
