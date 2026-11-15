"""Read-only source and saved-failure review; no imports of candidate or torch."""
from pathlib import Path
import ast
import hashlib
import json

R = Path(__file__).resolve().parent.parent
O = R / 'outputs/scq_rf_implementation_20261114_v1'


def record(p):
    return dict(path=str(p.resolve()), bytes=p.stat().st_size,
                sha256=hashlib.sha256(p.read_bytes()).hexdigest())


static = json.loads((O / 'static_review_v1.json').read_bytes())
for row in static['frozen_files']:
    assert record(Path(row['path']))['sha256'] == row['sha256']
failure = json.loads((O / 'cpu_batch_v1/failure_v1.json').read_bytes())
assert len(failure['checks']) == 46
assert failure['error'] == "AssertionError('original complete loss reaches Q2 and both full heads')"
assert not (O / 'cpu_batch_v1/result_v1.json').exists()
test_path = O / 'test_scq_rf_cpu_v1.py'
tree = ast.parse(test_path.read_text(encoding='utf-8'))
calls = [ast.unparse(x) for x in ast.walk(tree) if isinstance(x, ast.Call)]
assert any('m.base_model.scq.W2.bias.copy_' in c for c in calls)
assert not any('scq.W2.weight.copy_' in c for c in calls)
assert any('rf.V2.weight.copy_' in c for c in calls)
init = json.loads((R / 'outputs/cranial_bcsp_scq_implementation_20261113_v1/initialization_manifest_v1.json').read_bytes())
assert init['head_procedure'].endswith('W2/b2 zero')
production = [O / 'bcsp_scq_rf_residual_v1.py', O / 'bcsp_scq_rf_factory_v1.py']
for p in production:
    compile(p.read_bytes(), str(p), 'exec')
result = dict(status='LOCAL_RF_IMPLEMENTATION_P3_NOT_PASSED_CPU_FAILURE_STOP',
              static_review=record(O / 'static_review_v1.json'), failure=record(O / 'cpu_batch_v1/failure_v1.json'),
              candidate_sources=[record(p) for p in production], test_source=record(test_path),
              initialization=record(O / 'initialization_v1.bin'),
              checks=dict(all_frozen_sources_unchanged=True, static_syntax_pass=True,
                          saved46_completed_CPU_checks=True, failed_assertion_preserved=True,
                          no_pass_receipt_present=True, no_automatic_retry=True),
              CPU_success=False, completed_checks=46,
              source_level_explanation='Fixture changes first SCQ W2.bias but leaves W2.weight zero. For delta0=W2*GELU(W1*h)+b2, dL/dW1 contains W2 and must be zero. The full-loss assertion incorrectly requires all original first-head parameters to have nonzero gradients. No per-tensor runtime gradient diagnostics were saved, so other conjuncts are not independently certified.',
              uncompleted=['Correct artificial nonzero first-head diagnostic fixture and add per-tensor gradient evidence; requires a separately authorized versioned CPU batch.',
                           'Post-backward no-step/BN-restoration check was not reached. The process exited; this artificial instance is not reused.',
                           'Native SSM no-decay grouping needs an exact inherited-policy artificial marker check; current batch retained supplied parent groups but used a synthetic partition.',
                           'Actual native parameter total40827847, CUDA batch8 full loss/backward and resource evidence remain for separate CUDA admission.',
                           'Training entry/request not prepared or authorized.'],
              recommendation='Only correct the CPU diagnostic fixture, preserve candidate implementation and frozen initialization, version the test/output, add specific gradient and inherited no-decay checks, and run one separately authorized artificial CPU batch before new P3.',
              CUDA=False, server_operations=0, training=0, new_execution_request=False)
with (O / 'P3_gap_review_v1.json').open('x', encoding='utf-8') as f:
    json.dump(result, f, indent=2, allow_nan=False)
print(json.dumps(dict(status=result['status'], completed_checks=46, retry=False)))
