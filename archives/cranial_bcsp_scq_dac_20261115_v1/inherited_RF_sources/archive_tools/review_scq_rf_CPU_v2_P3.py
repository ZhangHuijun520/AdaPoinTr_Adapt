"""Inspect saved CPU v2 outputs and frozen source identities; never run the model."""
from pathlib import Path
import hashlib
import json
import math

R = Path(__file__).resolve().parent.parent
O = R / 'outputs/scq_rf_implementation_20261114_v1'
B = O / 'cpu_batch_v2'
E = O / 'CPU_validation_authorized_execution_v2'


def rec(p):
    return dict(path=str(p.resolve()), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())


scope_path = O / 'CPU_validation_scope_v2.json'
assert rec(scope_path)['sha256'] == 'd512ffbb57622357a14e32c96befbe5b17337d01ca7d3ffa8ecb538b0d49c5f2'
scope = json.loads(scope_path.read_bytes())
static = json.loads(Path(scope['static_review']['path']).read_bytes())
for row in static['frozen_files'] + static['preserved_artifacts'] + [scope['test'], scope['static_review']]:
    assert rec(Path(row['path'])) == row
exit_result = json.loads((E / 'process_exit_v2.json').read_bytes())
assert exit_result['returncode'] == 0 and exit_result['scope_sha256'] == rec(scope_path)['sha256']
assert not (E / 'launch_failure_v2.json').exists() and not (B / 'failure_v2.json').exists()
result = json.loads((B / 'result_v2.json').read_bytes())
assert result['status'] == 'RF_ARTIFICIAL_CPU_CONTRACT_PASS'
assert result['count'] == len(result['checks']) == len(set(result['checks'])) == 59
assert result['optimizer_steps'] == 0 and not any(result[k] for k in ('CUDA', 'real_data', 'real_checkpoint'))
assert result['initialization_sha256'] == 'a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e'
events = [json.loads(line) for line in (B / 'gradient_evidence_v2.jsonl').read_text(encoding='utf-8').splitlines()]
assert [e['stage'] for e in events] == result['gradient_events'] == ['RF_zero_output_initial', 'RF_nonzero_diagnostic', 'original_full8192_loss_nonzero_both_heads']
zero, active, full = [{r['name']: r for r in e['tensors']} for e in events]
for event in events:
    for row in event['tensors']:
        assert row['present'] and row['finite']
        assert all(math.isfinite(row[k]) for k in ('L1', 'L2', 'max_abs'))
assert zero['V1.weight']['nonzero_elements'] == zero['V1.bias']['nonzero_elements'] == 0
assert zero['V2.weight']['nonzero_elements'] > 0 and zero['V2.bias']['nonzero_elements'] > 0
assert len(active) == 8 and all(row['nonzero_elements'] > 0 for row in active.values())
assert len(full) == 9 and all(row['nonzero_elements'] > 0 for row in full.values())
marker = json.loads((B / 'inherited_no_decay_evidence_v2.json').read_bytes())
runtime = R / 'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/bcsp_p1_training_runtime_v1.py'
assert marker['source_sha256'] == rec(runtime)['sha256']
rows = {r['name']: r for r in marker['rows']}
assert rows['flagged']['reason'] == 'explicit_no_weight_decay' and rows['flagged']['weight_decay'] == 0
assert rows['vector']['weight_decay'] == rows['bias_holder.bias']['weight_decay'] == 0
assert rows['matrix']['weight_decay'] == .0005 and 'frozen' not in rows
shared = json.loads((B / 'shared_optimizer_policy_evidence_v2.json').read_bytes())
assert next(r for r in shared['rows'] if r['name'] == shared['marked_artificial_parameter'])['reason'] == 'explicit_no_weight_decay'
assert (E / 'stderr_v2.bin').stat().st_size == 0
assert json.loads((E / 'stdout_v2.bin').read_bytes())['status'] == result['status']
files = sorted(p for p in B.iterdir() if p.is_file())
assert {p.name for p in files} == {'gradient_evidence_v2.jsonl', 'inherited_no_decay_evidence_v2.json', 'shared_optimizer_policy_evidence_v2.json', 'result_v2.json'}
p3 = dict(status='LOCAL_RF_IMPLEMENTATION_P3_PASS_ARTIFICIAL_CPU_ONLY', CPU_checks=59,
          scope=rec(scope_path), test=rec(Path(scope['test']['path'])), static_review=rec(Path(scope['static_review']['path'])),
          artifacts=[rec(p) for p in files], execution_evidence=[rec(p) for p in sorted(E.iterdir()) if p.is_file()],
          candidate_sources=static['preserved_artifacts'][:2], initialization=static['preserved_artifacts'][2:4],
          checks=dict(all_original_and_candidate_sources_unchanged=True, one_authorized_process_exit0=True,
                      all59_artificial_CPU_checks_pass=True, independent_saved_gradient_review_pass=True,
                      exact_inherited_no_decay_regression_pass=True, nine_full_loss_gradients_finite_nonzero=True,
                      original_failure_preserved=True, no_retry=True, no_CUDA=True, no_server_operations=True,
                      no_training_or_optimizer_step=True),
          full_loss_gradient_summary=full, seconds=result['seconds'], limitations=result['limitations'],
          remaining=['Separate formal read-only post-test freeze audit if requested; this is the authorized saved-output P3 review.',
                     'Prepare a dedicated RF CUDA short entry and pending execution request: 5forward/4full loss/4backward/0optimizer step; no automatic execution.',
                     'Native Mamba/PointNet2, full batch8 loss/backward, native total40827847 and resources remain unverified.',
                     'No scientific benefit or reliability conclusion; no training request authorized.'],
          CUDA_execution_request_created=False, training_request_created=False)
with (O / 'P3_implementation_v2.json').open('x', encoding='utf-8') as f:
    json.dump(p3, f, indent=2, allow_nan=False)
print(json.dumps(dict(status=p3['status'], checks=59, seconds=result['seconds'],
                     full_loss_gradient_L1={k: v['L1'] for k, v in full.items()})))
