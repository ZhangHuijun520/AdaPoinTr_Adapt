"""Freeze finite local RF implementation inputs and CPU-only static criteria."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import sys
import torch

R = Path(__file__).resolve().parent.parent
O = R / 'outputs/scq_rf_implementation_20261114_v1'


def rec(p):
    p = p.resolve()
    return dict(path=str(p), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def emit(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)


review = json.loads((R / 'outputs/scq_rf_stageA_readonly_20261114_v1/finite_compute_graph_review_v1.json').read_bytes())
for row in review['sources']:
    assert rec(Path(row['path']))['sha256'] == row['sha256']
audit = R / 'outputs/scq_rf_audit_20261114_v1/formal_post_diagnostic_freeze_audit_v1.json'
assert json.loads(audit.read_bytes())['status'] == 'FORMAL_SCQ_RF_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS'
files = [O / n for n in ['bcsp_scq_rf_residual_v1.py', 'bcsp_scq_rf_factory_v1.py', 'test_scq_rf_cpu_v1.py']]
for p in files:
    compile(p.read_bytes(), str(p), 'exec')
    tree = ast.parse(p.read_text(encoding='utf-8'))
    assert not any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr == 'step' for x in ast.walk(tree))
module = ast.parse(files[0].read_text(encoding='utf-8'))
cls = next(x for x in module.body if isinstance(x, ast.ClassDef) and x.name == 'RFResidual')
fw = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == 'forward')
assert [x.arg for x in fw.args.args] == ['self', 'M', 'F', 'z', 'Q1', 'N0']
desc = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == 'describe')
branches = [x for x in ast.walk(desc) if isinstance(x, ast.IfExp)]
assert len(branches) == 1 and ast.unparse(branches[0]) == "N0 if self.variant == 'RF-Static' else self.knn(8, M, Q1)"
spec = importlib.util.spec_from_file_location('rf_init_only', files[0])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rng = torch.random.get_rng_state().clone()
values = m.initialization_values()
assert torch.equal(rng, torch.random.get_rng_state())
raw = b''.join(t.contiguous().numpy().tobytes() for t in values.values())
assert len(raw) == 231171 * 4 and sys.byteorder == 'little'
init_path = O / 'initialization_v1.bin'
with init_path.open('xb') as f: f.write(raw)
emit(O / 'initialization_manifest_v1.json', dict(**rec(init_path), seed=m.SEED, byte_order=sys.byteorder,
     procedure='private CPU Generator; Linear-default-equivalent uniform +/-1/sqrt(1802) W1 then bias; V2/bias exact zero',
     torch_version=torch.__version__, CPU_RNG_unchanged=True,
     layout=[dict(name=k, shape=list(v.shape), sha256=hashlib.sha256(v.numpy().tobytes()).hexdigest()) for k, v in values.items()]))
inherited = [Path(row['path']) for row in review['sources'][:4]]
inherited += [R / 'outputs/cranial_bcsp_scq_implementation_20261113_v1/test_scq_cpu_v1.py',
              R / 'outputs/cranial_bcsp_scq_implementation_20261113_v1/initialization_v1.bin',
              R / 'outputs/cranial_bcsp_scq_implementation_20261113_v1/initialization_manifest_v1.json',
              R / 'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1/bcsp_lqi_factory_v1.py',
              R / 'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_model_factory_v1.py',
              R / 'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_mamba_encoder_v1.py',
              R / 'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/tools/bcsp_adapter.py',
              R / 'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/models/AdaPoinTr.py',
              R / 'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/models/Transformer_utils.py',
              R / 'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/extensions/chamfer_dist/__init__.py',
              R / 'outputs/cranial_bcsp_fullmamba_20261110/implementation_v1/test_f0_cpu_v1.py']
plan = R / 'docs/cranial_bcsp_scq_rf_20261114/Cranial_BCSP_FullMamba_SCQ_RF_下一阶段正式实验计划书_zh_2026-11-14_v2.md'
assert rec(plan)['sha256'] == 'fe041d33cb16d6517ab31820599a8b750c7aee1db10580b3fe913f45618499d2'
emit(O / 'static_review_v1.json', dict(status='RF_STATIC_S0_S1_PASS_NOT_RUNTIME_OR_CUDA',
     frozen_files=[rec(p) for p in dict.fromkeys(files + inherited + [plan, audit, init_path, O / 'initialization_manifest_v1.json'])],
     checks=dict(syntax=True, one_arm_conditional=True, no_optimizer_step=True, exact_no_GT_signature=True,
                 all_inherited_graph_sources_unchanged=True, private_seed_frozen=True),
     criteria=dict(one_retained_CPU_batch=True, on_failure_stop_no_automatic_retry=True,
                   descriptor_reference_atol=2e-6, descriptor_reference_rtol=2e-5,
                   parameter_delta=231171, expected_native_parameters=40827847,
                   no_server=True, no_real_data=True, no_checkpoint=True, no_CUDA=True, no_training=True)))
print(json.dumps(dict(status='STATIC_PASS_INITIALIZATION_FROZEN', bytes=len(raw), SHA256=rec(init_path)['sha256'])))
