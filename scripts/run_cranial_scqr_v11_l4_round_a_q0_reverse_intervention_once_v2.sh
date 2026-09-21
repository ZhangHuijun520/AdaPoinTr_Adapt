#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

ROOT=/home/jovyan/adapointr_work/PoinTr
PYTHON=/opt/conda/envs/adapointr-mamba/bin/python
REQUEST="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_q0_reverse_inference_intervention_execution_authorization_request_v2.json"
RECEIPT="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_q0_reverse_inference_intervention_execution_authorization_receipt_v2.json"
PROTOCOL="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_q0_reverse_inference_intervention_protocol_v1.json"
RUNNER="$ROOT/tools/run_cranial_scqr_v11_l4_round_a_q0_reverse_intervention.py"
MANIFEST=/home/jovyan/datasets/SkullBreakPC_out8192/manifest.jsonl
DATA_ROOT=/home/jovyan/datasets/SkullBreakPC_out8192
ROUND_A_CASES="$ROOT/logs/cranial_scqr_v11/l4_round_a_development_evaluation/cranial_scqr_v11_l4_round_a_dev_eval_v2_20260914T054006Z/per_model_case_metrics.csv"
QC_CASES="$ROOT/logs/cranial_scqr_v11/l4_round_a_intervention/cranial_scqr_v11_l4_round_a_intervention_protocol_v2_run1_20260918T132417Z/per_condition_case_metrics.csv"
OUTPUT="$ROOT/logs/cranial_scqr_v11/l4_round_a_q0_reverse_intervention/cranial_scqr_v11_l4_round_a_q0_reverse_intervention_v2_20260919T055847Z"
REQUEST_SHA=505264de56463ecdaa5e931d3a4c7c8ab6d5a8f356e8dd6964a77a31a1281cbe
RECEIPT_SHA=e73b49c9251ad9b956090ce6ecdf57e7352c32cb66ab0d3ccddd90c6d8edb7d8
PROTOCOL_SHA=bf447b2585aa799f00bd0f942033971a567eb2ebc527a6ef3d28664facfd3de0
MANIFEST_SHA=f1f8cae47ed7d5529dc2ca244179cedddbc039981cdc0ff24b25a5c81ad30538
ROUND_A_CASES_SHA=c2e1317715fb037a73ab3e1054c573d0cd3efe4ea57cefb161de2b1d1bdec29e
QC_CASES_SHA=f13969d1d38c7440f7c2128807a7670a849414bc31ea68633790253f77088865
GPU_UUID=GPU-3f28fa66-923a-0815-6594-075e89429bf9

on_exit() {
  local code=$?
  trap - EXIT
  printf '[launcher] exit_code=%s finished_at_utc=%s\n' "$code" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit "$code"
}
trap on_exit EXIT

cd "$ROOT"
printf '[launcher] started_at_utc=%s pid=%s launcher_sha256=%s\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$$" "$(sha256sum "$0" | awk '{print $1}')"
[[ "$(pwd -P)" == "$ROOT" && "$(id -un)" == jovyan ]]
[[ "$(hostname)" == shu-common-25721452-notebook-f3ncns-0 ]]
[[ ! -e "$OUTPUT" && ! -L "$OUTPUT" ]]
[[ "$(readlink -f "$PYTHON")" == /opt/conda/envs/adapointr-mamba/bin/python3.10 ]]

"$PYTHON" - "$REQUEST" "$RECEIPT" "$OUTPUT" <<'PY_BINDINGS'
import hashlib
import json
import sys
from pathlib import Path

root = Path('/home/jovyan/adapointr_work/PoinTr')
request_path, receipt_path, output = map(Path, sys.argv[1:])

def verify(path, sha, size=None):
    path = Path(path)
    if not path.is_absolute():
        path = root / path
    assert path.is_file(), f'missing {path}'
    if size is not None:
        assert path.stat().st_size == size, f'byte drift {path}'
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    assert digest.hexdigest() == sha, f'SHA256 drift {path}'
    return path

verify(request_path, '505264de56463ecdaa5e931d3a4c7c8ab6d5a8f356e8dd6964a77a31a1281cbe', 21671)
verify(receipt_path, 'e73b49c9251ad9b956090ce6ecdf57e7352c32cb66ab0d3ccddd90c6d8edb7d8', 3073)
r = json.loads(request_path.read_text(encoding='utf-8'))
a = json.loads(receipt_path.read_text(encoding='utf-8'))
assert r['request_id'] == 'cranial-scqr-v1.1-L4-roundA-I-Q0-reverse-inference-intervention-execution-request-v2'
assert r['status'] == 'PENDING_EXPLICIT_SINGLE_EXECUTION_AUTHORIZATION'
assert r['authorization_effective'] is False and r['execution_authorized'] is False
assert a['status'] == 'AUTHORIZED_Q0_REVERSE_INTERVENTION_V2_ONCE'
assert a['authorization_effective'] is True and a['execution_authorized'] is True and a['authorized_once'] is True
assert a['authorization_request_sha256'] == '505264de56463ecdaa5e931d3a4c7c8ab6d5a8f356e8dd6964a77a31a1281cbe'
assert a['authorization_request'] == str(request_path.relative_to(root))
assert a['protocol_id'] == r['protocol']['id']
assert a['protocol_sha256'] == r['protocol']['sha256']
assert a['output_directory'] == str(output)
assert a['resource_scope']['gpu_uuid'] == r['resource_scope']['gpu_uuid']
assert a['authorized_counts'] == r['future_authorization_receipt_contract']['authorized_counts']
assert a['authorized_checkpoint_order'] == r['requested_once_execution']['checkpoint_order']
assert a['authorized_condition_order'] == r['requested_once_execution']['condition_order_per_case']
assert a['q0_reverse_intervention'] is True and a['qc_checkpoint_rerun'] is False
assert a['training_authorized'] is False and a['bncal_authorized'] is False
assert a['round_b_authorized'] is False and a['automatic_retry_authorized'] is False
assert a['automatic_resume_authorized'] is False and a['subsequent_run_authorized'] is False
assert not any(a['protected_payload_access'].values())

verify(r['superseded_unexecuted_request']['path'], r['superseded_unexecuted_request']['sha256'], r['superseded_unexecuted_request']['bytes'])
for key in ('protocol',):
    entry = r[key]
    verify(entry['path'], entry['sha256'], entry['bytes'])
for key in ('implementation_authorization_request', 'runner', 'analyzer', 'synthetic_contract_test'):
    entry = r['implementation_bindings'][key]
    verify(entry['path'], entry['sha256'], entry['bytes'])
for path, sha in r['implementation_bindings']['read_only_parent_source_sha256'].items():
    verify(path, sha)
verify(r['python_environment']['realpath'], r['python_environment']['binary_sha256'], r['python_environment']['binary_bytes'])
for entry in r['checkpoint_matrix']:
    for path_key, sha_key, bytes_key in (
        ('runtime_config', 'runtime_config_sha256', 'runtime_config_bytes'),
        ('completion_receipt', 'completion_receipt_sha256', 'completion_receipt_bytes'),
        ('bncal_checkpoint', 'bncal_checkpoint_sha256', 'bncal_checkpoint_bytes'),
    ):
        verify(entry[path_key], entry[sha_key], entry[bytes_key])
d = r['data_scope']
verify(d['manifest'], d['manifest_sha256'], d['manifest_bytes'])
fold_a = verify(d['fold_a_allowlist'], d['fold_a_allowlist_sha256'], d['fold_a_allowlist_bytes']).read_text().splitlines()
fold_b = verify(d['fold_b_allowlist'], d['fold_b_allowlist_sha256'], d['fold_b_allowlist_bytes']).read_text().splitlines()
assert len(fold_a) == len(set(fold_a)) == len(fold_b) == len(set(fold_b)) == 105
assert not set(fold_a) & set(fold_b)
for reference in r['frozen_reference_results'].values():
    verify(reference['directory'] + '/files.sha256', reference['files_sha256_sha256'], reference['files_sha256_bytes'])
    for name in ('per_model_case_metrics', 'per_condition_case_metrics'):
        if name in reference:
            verify(reference[name], reference[name + '_sha256'], reference[name + '_bytes'])
for name in ('authorization_receipt', 'launcher', 'master_log'):
    assert (root / r['fixed_execution_paths'][name]).is_file()
assert not output.exists() and not output.is_symlink()
v1 = json.loads((root / r['superseded_unexecuted_request']['path']).read_text(encoding='utf-8'))
for name in ('authorization_receipt', 'launcher', 'master_log', 'formal_output_directory'):
    prior = root / v1['fixed_execution_paths'][name]
    assert not prior.exists() and not prior.is_symlink(), f'v1 path collision {prior}'
print('[prelaunch] frozen file, receipt, count, case and path bindings PASS')
PY_BINDINGS

for directory in \
  "$ROOT/logs/cranial_scqr_v11/l4_round_a_development_evaluation/cranial_scqr_v11_l4_round_a_dev_eval_v2_20260914T054006Z" \
  "$ROOT/logs/cranial_scqr_v11/l4_round_a_intervention/cranial_scqr_v11_l4_round_a_intervention_protocol_v2_run1_20260918T132417Z"; do
  (cd "$directory" && sha256sum -c files.sha256)
done

GPU_COUNT="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | sed '/^[[:space:]]*$/d' | wc -l)"
GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | sed -n '1p')"
GPU_CURRENT_UUID="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | sed -n '1p')"
GPU_FREE_MIB="$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | sed -n '1p' | tr -d ' ')"
GPU_PROCESSES="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | sed '/^[[:space:]]*$/d')"
DISK_FREE_KIB="$(df -Pk /home/jovyan | awk 'NR==2 {print $4}')"
[[ "$GPU_COUNT" == 1 && "$GPU_NAME" == 'NVIDIA GeForce RTX 4090 D' && "$GPU_CURRENT_UUID" == "$GPU_UUID" ]]
[[ "$GPU_FREE_MIB" -ge 22000 && -z "$GPU_PROCESSES" ]]
[[ "$DISK_FREE_KIB" -ge 8388608 ]]
[[ ! -e "$OUTPUT" && ! -L "$OUTPUT" ]]
printf '[prelaunch] gpu_uuid=%s free_mib=%s disk_free_kib=%s PASS\n' "$GPU_CURRENT_UUID" "$GPU_FREE_MIB" "$DISK_FREE_KIB"

CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -u "$RUNNER" \
  --protocol "$PROTOCOL" --protocol-sha256 "$PROTOCOL_SHA" \
  --execution-authorization "$RECEIPT" --execution-authorization-sha256 "$RECEIPT_SHA" \
  --manifest "$MANIFEST" --manifest-sha256 "$MANIFEST_SHA" --data-root "$DATA_ROOT" \
  --frozen-round-a-case-metrics "$ROUND_A_CASES" --frozen-round-a-case-metrics-sha256 "$ROUND_A_CASES_SHA" \
  --frozen-qc-case-metrics "$QC_CASES" --frozen-qc-case-metrics-sha256 "$QC_CASES_SHA" \
  --output-dir "$OUTPUT" --device cuda:0

"$PYTHON" - "$OUTPUT" <<'PY_VERIFY_OUTPUT'
import csv
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
required = (
    'invocation.json', 'per_condition_case_metrics.csv', 'per_condition_source_metrics.csv',
    'reverse_intervention_diagnostics.csv', 'factorial_paired_deltas.csv',
    'factorial_summary.json', 'weight_state_classification_receipt.json',
    'reverse_intervention_execution_receipt.json', 'formal_result_report_zh.md',
    'environment.json', 'files.sha256',
)
for name in required:
    assert (out / name).is_file() and (out / name).stat().st_size > 0, name
with (out / 'per_condition_case_metrics.csv').open(newline='', encoding='utf-8') as stream:
    rows = list(csv.DictReader(stream))
assert len(rows) == 420
assert {row['condition'] for row in rows} == {'native_q0', 'q0_beta1'}
with (out / 'reverse_intervention_diagnostics.csv').open(newline='', encoding='utf-8') as stream:
    assert len(list(csv.DictReader(stream))) == 420
execution = json.loads((out / 'reverse_intervention_execution_receipt.json').read_text(encoding='utf-8'))
classification = json.loads((out / 'weight_state_classification_receipt.json').read_text(encoding='utf-8'))
assert execution['status'] == 'PASS' and execution['model_state_hashes_unchanged'] is True
counts = execution['counters']
assert counts['checkpoint_loads'] == 2 and counts['npz_open_events'] == 210
assert counts['model_case_forward_calls'] == 420
assert counts['member_partial'] == counts['member_implant'] == counts['member_gt'] == 210
assert counts['temporary_beta_assignments'] == counts['temporary_beta_restorations'] == 210
for name in ('qc_checkpoint_loads', 'qc_model_forwards', 'optimizer_constructions', 'optimizer_steps', 'model_parameter_updates', 'persistent_net_buffer_updates'):
    assert counts[name] == 0, name
assert execution['round_b_authorized'] is False and execution['automatic_next_run'] is False
controls = classification['execution_controls']
assert controls['status'] == 'PASS'
assert controls['native_q0_reproduction_pass'] is True
assert controls['coarse_condition_invariance_pass'] is True
assert controls['frozen_qc_cells_reused_without_checkpoint_load'] is True
assert classification['round_b_authorized'] is False and classification['automatic_next_run'] is False
print('[verify] 420 rows, counts, immutable model state and scientific gates PASS')
print('[verify] overall_classification=' + classification['overall_classification'])
PY_VERIFY_OUTPUT

(cd "$OUTPUT" && sha256sum -c files.sha256)
printf '[launcher] formal Q0 reverse intervention PASS; no subsequent run authorized\n'
