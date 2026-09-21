#!/usr/bin/env bash
set -Euo pipefail

ROOT="/home/jovyan/adapointr_work/PoinTr"
PYTHON="/opt/conda/envs/adapointr-mamba/bin/python"
PROTOCOL="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_development_evaluation_protocol_v1.json"
REQUEST="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_development_evaluation_execution_authorization_request_v2.json"
AUTHORIZATION="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_development_evaluation_execution_authorization_receipt_v2.json"
RUNNER="$ROOT/tools/run_cranial_scqr_v11_l4_round_a_dev_eval.py"
ANALYZER="$ROOT/tools/analyze_cranial_scqr_v11_l4_round_a.py"
TEST_CONTRACT="$ROOT/tools/test_cranial_scqr_v11_l4_round_a_dev_eval_contract.py"
DATA_ROOT="/home/jovyan/datasets/SkullBreakPC_out8192"
MANIFEST="$DATA_ROOT/manifest.jsonl"
RUN_ID="cranial_scqr_v11_l4_round_a_dev_eval_v2_20260914T054006Z"
OUTPUT_PARENT="$ROOT/logs/cranial_scqr_v11/l4_round_a_development_evaluation"
OUTPUT="$OUTPUT_PARENT/$RUN_ID"
V1_OUTPUT="$OUTPUT_PARENT/cranial_scqr_v11_l4_round_a_dev_eval_v1_20260914T052540Z"

PROTOCOL_SHA="04077152848c055c76fbc64f4427301af9809e2fda6cd2117d644088bad7e8ae"
REQUEST_SHA="3fea0c5634cf009030d353eb5af8ab281f085008b4ac3b719326f6d1cbb30de0"
AUTHORIZATION_SHA="28444c351f7e564f468e12e5fb8a18c8480d6f0357b86ce0984e76efb8a344c8"
RUNNER_SHA="6be1c38b46270eff278ea7a54805ba0d572e8aef81a103350308072380c38798"
ANALYZER_SHA="3a54206a950c5d6825373ca6364d41feacca44bac28e62b505a7d3d35d47985d"
TEST_CONTRACT_SHA="d20c0f81f8b0bc49f72a90040ccdb52cb65ce475d30da9e7df989c4dc4e3b34b"
MANIFEST_SHA="f1f8cae47ed7d5529dc2ca244179cedddbc039981cdc0ff24b25a5c81ad30538"
V1_FILES_SHA256_SHA="ca4d410d4de167fb5d52c5871580e5b2d9f7a677e1bf5c0435c869776dc2a257"
V1_FAILURE_SHA="69ad8727d38bb578b4de50be32939e65ab22900c1a44a74478972f57af83c7f4"

cd "$ROOT" || exit 10
if [[ -e "$OUTPUT" ]]; then
  echo "[blocked] immutable v2 output already exists: $OUTPUT" >&2
  exit 11
fi
if [[ ! -d "$V1_OUTPUT" ]]; then
  echo "[blocked] v1 failure evidence directory is missing" >&2
  exit 12
fi

echo "$PROTOCOL_SHA  $PROTOCOL" | sha256sum -c - || exit 13
echo "$REQUEST_SHA  $REQUEST" | sha256sum -c - || exit 14
echo "$AUTHORIZATION_SHA  $AUTHORIZATION" | sha256sum -c - || exit 15
echo "$RUNNER_SHA  $RUNNER" | sha256sum -c - || exit 16
echo "$ANALYZER_SHA  $ANALYZER" | sha256sum -c - || exit 17
echo "$TEST_CONTRACT_SHA  $TEST_CONTRACT" | sha256sum -c - || exit 18
echo "$MANIFEST_SHA  $MANIFEST" | sha256sum -c - || exit 19
echo "$V1_FILES_SHA256_SHA  $V1_OUTPUT/files.sha256" | sha256sum -c - || exit 20
echo "$V1_FAILURE_SHA  $V1_OUTPUT/evaluation_failure_receipt.json" | sha256sum -c - || exit 21
(cd "$V1_OUTPUT" && sha256sum -c files.sha256) || exit 22

GPU_COUNT="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | wc -l)"
GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | sed -n '1p')"
GPU_UUID="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | sed -n '1p')"
read -r GPU_USED GPU_TOTAL < <(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | tr -d ',' | awk 'NR==1 {print $1, $2}')
GPU_FREE="$((GPU_TOTAL - GPU_USED))"
GPU_PROCESSES="$(nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null | sed '/^[[:space:]]*$/d')"
DISK_FREE_KIB="$(df -Pk /home/jovyan | awk 'NR==2 {print $4}')"
if [[ "$GPU_COUNT" -ne 1 || "$GPU_NAME" != "NVIDIA GeForce RTX 4090 D" || "$GPU_UUID" != "GPU-2f32f6fb-ea5d-730a-4ea2-2f6063e31065" ]]; then
  echo "[blocked] GPU identity mismatch: count=$GPU_COUNT name=$GPU_NAME uuid=$GPU_UUID" >&2
  exit 23
fi
if [[ "$GPU_FREE" -lt 22000 || -n "$GPU_PROCESSES" ]]; then
  echo "[blocked] GPU occupancy gate failed: free_mib=$GPU_FREE processes=${GPU_PROCESSES:-none}" >&2
  exit 24
fi
if [[ "$DISK_FREE_KIB" -lt 8388608 ]]; then
  echo "[blocked] disk gate failed: free_kib=$DISK_FREE_KIB" >&2
  exit 25
fi

mkdir -p "$OUTPUT_PARENT" || exit 26
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

wait_for_output_and_tee() {
  while [[ ! -d "$OUTPUT" ]]; do sleep 0.1; done
  tee "$OUTPUT/console.log"
}

monitor_resources() {
  while [[ ! -d "$OUTPUT" ]]; do sleep 0.1; done
  printf 'timestamp_utc\tmemory_used_mib\tutilization_gpu_percent\ttemperature_c\n' > "$OUTPUT/resource_monitor.tsv"
  while kill -0 "$1" 2>/dev/null; do
    nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader,nounits \
      | awk -F', ' '{printf "%s\t%s\t%s\t%s\n",$1,$2,$3,$4}' >> "$OUTPUT/resource_monitor.tsv"
    sleep 1
  done
}

set +e
CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 timeout --signal=TERM --kill-after=30s 14400s \
  "$PYTHON" -u "$RUNNER" \
    --protocol "$PROTOCOL" \
    --protocol-sha256 "$PROTOCOL_SHA" \
    --execution-authorization "$AUTHORIZATION" \
    --execution-authorization-sha256 "$AUTHORIZATION_SHA" \
    --manifest "$MANIFEST" \
    --manifest-sha256 "$MANIFEST_SHA" \
    --data-root "$DATA_ROOT" \
    --output-dir "$OUTPUT" \
    --device cuda:0 \
    > >(wait_for_output_and_tee) 2>&1 &
RUNNER_PID="$!"
monitor_resources "$RUNNER_PID" &
MONITOR_PID="$!"
wait "$RUNNER_PID"
RUNNER_STATUS="$?"
if [[ ! -d "$OUTPUT" ]]; then
  mkdir "$OUTPUT"
fi
wait "$MONITOR_PID"
wait
set -e

printf '%s\n' "$STARTED_AT" > "$OUTPUT/started_at_utc.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUTPUT/finished_at_utc.txt"

FINAL_STATUS="$RUNNER_STATUS"
PEAK_USED_MIB="$(awk 'NR>1 && $2+0>max {max=$2+0} END {print max+0}' "$OUTPUT/resource_monitor.tsv")"
if [[ "$FINAL_STATUS" -eq 0 && "$PEAK_USED_MIB" -gt 20480 ]]; then
  echo "[failed] observed GPU memory used exceeded 20 GiB: $PEAK_USED_MIB MiB" | tee -a "$OUTPUT/console.log"
  FINAL_STATUS=31
fi

if [[ "$FINAL_STATUS" -eq 0 ]]; then
  set +e
  "$PYTHON" - "$OUTPUT" "$PEAK_USED_MIB" "$GPU_USED" "$GPU_TOTAL" "$DISK_FREE_KIB" <<'PY'
import csv, json, platform, socket, sys
from pathlib import Path

out=Path(sys.argv[1])
peak, launch_used, total, disk=map(int,sys.argv[2:])
required=(
    'per_model_case_metrics.csv','per_model_source_metrics.csv',
    'mechanism_diagnostics.csv','fold_and_combined_summary.json',
    'paired_deltas.csv','round_a_gate_receipt.json',
    'evaluation_execution_receipt.json','console.log','resource_monitor.tsv',
    'started_at_utc.txt','finished_at_utc.txt',
)
for name in required:
    assert (out/name).is_file() and (out/name).stat().st_size>0, name
def rows(name):
    with (out/name).open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))
assert len(rows('per_model_case_metrics.csv'))==840
assert len(rows('per_model_source_metrics.csv'))==168
assert len(rows('mechanism_diagnostics.csv'))==840
assert len(rows('paired_deltas.csv'))==168
execution=json.loads((out/'evaluation_execution_receipt.json').read_text(encoding='utf-8'))
gate=json.loads((out/'round_a_gate_receipt.json').read_text(encoding='utf-8'))
counts=execution['counters']
assert execution['status']=='PASS'
assert execution['model_state_hashes_unchanged'] is True
assert counts['checkpoint_loads']==8
assert counts['npz_open_events']==840
assert counts['member_partial']==counts['member_implant']==counts['member_gt']==840
assert counts['model_case_forward_calls']==840
assert counts['optimizer_constructions']==counts['optimizer_steps']==0
assert counts['model_parameter_updates']==counts['model_buffer_updates']==0
assert execution['round_b_authorized'] is False
assert execution['automatic_next_run'] is False
assert gate['round_b_authorized'] is False
assert gate['automatic_next_run'] is False
environment={
    'status':'PASS','attempt':'v2_replacement_after_import_hotfix1',
    'host':socket.gethostname(),'platform':platform.platform(),'python':sys.version,
    'gpu_name':'NVIDIA GeForce RTX 4090 D',
    'gpu_uuid':'GPU-2f32f6fb-ea5d-730a-4ea2-2f6063e31065',
    'gpu_memory_used_mib_at_launch':launch_used,'gpu_memory_total_mib':total,
    'observed_peak_gpu_memory_used_mib':peak,'disk_free_kib_at_launch':disk,
}
(out/'environment.json').write_text(json.dumps(environment,indent=2,sort_keys=True)+'\n',encoding='utf-8')
summary=json.loads((out/'fold_and_combined_summary.json').read_text(encoding='utf-8'))
primary='rim_gt_rim_to_pred_p95_mm'
qcb0=summary['comparisons']['QC_minus_B0'][primary]
qcq0=summary['comparisons']['QC_minus_Q0'][primary]
report=f'''# Cranial-SCQR v1.1 L4 Round A development v2 正式评估报告\n\n- 执行状态：PASS\n- 执行类型：import hotfix1 后的单次替代执行\n- Round A 门控分类：{gate['classification']}\n- QC-B0 RimCover-P95 delta（Fold A）：{qcb0['A']:.6f} mm\n- QC-B0 RimCover-P95 delta（Fold B）：{qcb0['B']:.6f} mm\n- QC-B0 RimCover-P95 delta（Combined）：{qcb0['combined']:.6f} mm\n- QC-Q0 RimCover-P95 delta（Combined）：{qcq0['combined']:.6f} mm\n- checkpoint loads：8\n- model-case forwards：840\n- NPZ opens：840\n- optimizer steps / parameter updates / buffer updates：0 / 0 / 0\n- Round B authorized：false\n- automatic next run：false\n\n本报告仅为 development84 Round A 探索性门控结果，不构成 confirmation、official test、Round B 或后续实验授权。v1 失败证据保持独立且不可变。\n'''
(out/'formal_result_report_zh.md').write_text(report,encoding='utf-8')
validation={
    'status':'PASS','attempt':'v2_replacement_after_import_hotfix1',
    'required_output_files_present':True,
    'case_rows':840,'source_rows':168,'diagnostic_rows':840,'paired_delta_rows':168,
    'observed_peak_gpu_memory_used_mib':peak,'maximum_allowed_gpu_memory_mib':20480,
    'v1_failure_evidence_preserved':True,
    'round_b_authorized':False,'automatic_next_run':False,
}
(out/'launcher_validation_receipt.json').write_text(json.dumps(validation,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('[verified] v2 counts, state immutability, outputs, resources, v1 preservation, and non-authorization locks')
PY
  VALIDATION_STATUS="$?"
  set -e
  if [[ "$VALIDATION_STATUS" -ne 0 ]]; then
    FINAL_STATUS=32
  fi
fi

printf '%s\n' "$FINAL_STATUS" > "$OUTPUT/exit_code"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUTPUT/finished_at_utc.txt"
(cd "$OUTPUT" && find . -maxdepth 1 -type f ! -name files.sha256 -print0 | sort -z | xargs -0 sha256sum > files.sha256)
(cd "$OUTPUT" && sha256sum -c files.sha256)
echo "[done] final_status=$FINAL_STATUS output=$OUTPUT"
exit "$FINAL_STATUS"
