#!/usr/bin/env bash
set -Euo pipefail

ROOT="/home/jovyan/adapointr_work/PoinTr"
PYTHON="/opt/conda/envs/adapointr-mamba/bin/python"
PROTOCOL="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_intervention_protocol_v1.json"
REQUEST="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_intervention_execution_authorization_request_v1.json"
AUTHORIZATION="$ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_intervention_execution_authorization_receipt_v1.json"
RUNNER="$ROOT/tools/run_cranial_scqr_v11_l4_round_a_intervention.py"
ANALYZER="$ROOT/tools/analyze_cranial_scqr_v11_l4_round_a_intervention.py"
TEST_CONTRACT="$ROOT/tools/test_cranial_scqr_v11_l4_round_a_intervention_contract.py"
PARENT_RUNNER="$ROOT/tools/run_cranial_scqr_v11_l4_round_a_dev_eval.py"
PARENT_ANALYZER="$ROOT/tools/analyze_cranial_scqr_v11_l4_round_a.py"
DATA_ROOT="/home/jovyan/datasets/SkullBreakPC_out8192"
MANIFEST="$DATA_ROOT/manifest.jsonl"
FROZEN_V2="$ROOT/logs/cranial_scqr_v11/l4_round_a_development_evaluation/cranial_scqr_v11_l4_round_a_dev_eval_v2_20260914T054006Z"
FROZEN_V2_METRICS="$FROZEN_V2/per_model_case_metrics.csv"
RUN_ID="cranial_scqr_v11_l4_round_a_intervention_v1_20260914T131311Z"
OUTPUT_PARENT="$ROOT/logs/cranial_scqr_v11/l4_round_a_intervention"
OUTPUT="$OUTPUT_PARENT/$RUN_ID"

PROTOCOL_SHA="3c8b8e8e73b6e258e43bfa67a8a50d37b43fdfe27cdce450715b527acbf6a85a"
REQUEST_SHA="3728cf1c833115b7ec74f42a59165010a1010f8ff64fc8a398b7babfbc0f9a15"
AUTHORIZATION_SHA="f591489d3d4006fef36a8a659a23034b089e58eb9df1286fe277461d8e82f91d"
RUNNER_SHA="57288c1888c3dbb995e60e62e3e159a238af05cd9d6bfe3a198d65b3fe16aedf"
ANALYZER_SHA="180bc58b644d6042b50c6828cbf87df151110ae27f5fac5110a05b0fcdd0b012"
TEST_CONTRACT_SHA="d540beff893e3b549c22971de33b83f4d51b81ccbcb778141496510bfd0432d7"
PARENT_RUNNER_SHA="6be1c38b46270eff278ea7a54805ba0d572e8aef81a103350308072380c38798"
PARENT_ANALYZER_SHA="3a54206a950c5d6825373ca6364d41feacca44bac28e62b505a7d3d35d47985d"
MANIFEST_SHA="f1f8cae47ed7d5529dc2ca244179cedddbc039981cdc0ff24b25a5c81ad30538"
FROZEN_V2_FILES_SHA="a203a4b3a9d9b154f0f22c1e967b407125f26903d22d348f27a7cd415a33df52"
FROZEN_V2_METRICS_SHA="c2e1317715fb037a73ab3e1054c573d0cd3efe4ea57cefb161de2b1d1bdec29e"

QC_A_CONFIG="$ROOT/cfgs/SkullBreak_models/cranial_scqr_v11_l4_round_a_authorized_v1/CranialSCQRV11_QC_foldA_seed0.yaml"
QC_B_CONFIG="$ROOT/cfgs/SkullBreak_models/cranial_scqr_v11_l4_round_a_authorized_v1/CranialSCQRV11_QC_foldB_seed0.yaml"
QC_A_RECEIPT="$ROOT/logs/cranial_scqr_v11/l4_round_a/cranial_scqr_v11_QC_foldA_seed0_v1_20260912T160825Z/run_completion_receipt.json"
QC_B_RECEIPT="$ROOT/logs/cranial_scqr_v11/l4_round_a/cranial_scqr_v11_QC_foldB_seed0_v1_20260914T031939Z/run_completion_receipt.json"
QC_A_CHECKPOINT="$ROOT/experiments/CranialSCQRV11_QC_foldA_seed0/cranial_scqr_v11_l4_round_a_authorized_v1/cranial_scqr_v11_QC_foldA_seed0_v1_20260912T160825Z/ckpt-last-bncal.pth"
QC_B_CHECKPOINT="$ROOT/experiments/CranialSCQRV11_QC_foldB_seed0/cranial_scqr_v11_l4_round_a_authorized_v1/cranial_scqr_v11_QC_foldB_seed0_v1_20260914T031939Z/ckpt-last-bncal.pth"
FOLD_A_ALLOWLIST="$ROOT/logs/skullbreak_mamba_v12_development/protocol_v1/foldA_dev_case_ids.txt"
FOLD_B_ALLOWLIST="$ROOT/logs/skullbreak_mamba_v12_development/protocol_v1/foldB_dev_case_ids.txt"

check_sha() {
  local expected="$1"
  local path="$2"
  printf '%s  %s\n' "$expected" "$path" | sha256sum -c -
}

cd "$ROOT" || exit 10
if [[ -e "$OUTPUT" ]]; then
  echo "[blocked] immutable output already exists: $OUTPUT" >&2
  exit 11
fi

check_sha "$PROTOCOL_SHA" "$PROTOCOL" || exit 12
check_sha "$REQUEST_SHA" "$REQUEST" || exit 13
check_sha "$AUTHORIZATION_SHA" "$AUTHORIZATION" || exit 14
check_sha "$RUNNER_SHA" "$RUNNER" || exit 15
check_sha "$ANALYZER_SHA" "$ANALYZER" || exit 16
check_sha "$TEST_CONTRACT_SHA" "$TEST_CONTRACT" || exit 17
check_sha "$PARENT_RUNNER_SHA" "$PARENT_RUNNER" || exit 18
check_sha "$PARENT_ANALYZER_SHA" "$PARENT_ANALYZER" || exit 19
check_sha "$MANIFEST_SHA" "$MANIFEST" || exit 20
check_sha "$FROZEN_V2_FILES_SHA" "$FROZEN_V2/files.sha256" || exit 21
check_sha "$FROZEN_V2_METRICS_SHA" "$FROZEN_V2_METRICS" || exit 22
(cd "$FROZEN_V2" && sha256sum -c files.sha256) || exit 23
check_sha "b2b7c296e17ee0516393337704caa637b87b0002a4fe589545b8b80c94bc56f7" "$QC_A_CONFIG" || exit 24
check_sha "89b0c118e29110b9450d1e398c0d8598beaa123fd73b0f7a316c9ed331636df9" "$QC_B_CONFIG" || exit 25
check_sha "45e9ea07fdd8c0980bde2e6dea3afde1818d3a9bb77be68c5ce1890c7a1e4eed" "$QC_A_RECEIPT" || exit 26
check_sha "d58142682ae30628bc08992377d30628a0634cc98355676da8938f8db27b18af" "$QC_B_RECEIPT" || exit 27
check_sha "b73e1090ce7aa2e81f2707ad63243a29108eca2f35f7e27ff8e7a9c755235358" "$QC_A_CHECKPOINT" || exit 28
check_sha "9069f456abaa66e61c3315a85f3e865becd2889b97475bf8469de9bacbfdee3b" "$QC_B_CHECKPOINT" || exit 29
check_sha "83ec25f96831c7b5620fa94a2d255605668697bd3fa11ee5c6aab9f92c5dcd01" "$FOLD_A_ALLOWLIST" || exit 30
check_sha "803a313cdba850a3a277b3a253f4fc106b0bba0eb8289b12f59c38fa95175b1b" "$FOLD_B_ALLOWLIST" || exit 31

GPU_COUNT="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | wc -l)"
GPU_NAME="$(nvidia-smi --query-gpu=name --format=csv,noheader | sed -n '1p')"
GPU_UUID="$(nvidia-smi --query-gpu=uuid --format=csv,noheader | sed -n '1p')"
read -r GPU_USED GPU_TOTAL < <(
  nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits \
    | tr -d ',' | awk 'NR==1 {print $1, $2}'
)
GPU_FREE="$((GPU_TOTAL - GPU_USED))"
GPU_PROCESSES="$(
  nvidia-smi --query-compute-apps=pid --format=csv,noheader,nounits 2>/dev/null \
    | sed '/^[[:space:]]*$/d'
)"
DISK_FREE_KIB="$(df -Pk /home/jovyan | awk 'NR==2 {print $4}')"
if [[ "$GPU_COUNT" -ne 1 || "$GPU_NAME" != "NVIDIA GeForce RTX 4090 D" || "$GPU_UUID" != "GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed" ]]; then
  echo "[blocked] GPU identity mismatch: count=$GPU_COUNT name=$GPU_NAME uuid=$GPU_UUID" >&2
  exit 32
fi
if [[ "$GPU_FREE" -lt 22000 || -n "$GPU_PROCESSES" ]]; then
  echo "[blocked] GPU occupancy gate failed: free_mib=$GPU_FREE processes=${GPU_PROCESSES:-none}" >&2
  exit 33
fi
if [[ "$DISK_FREE_KIB" -lt 8388608 ]]; then
  echo "[blocked] disk gate failed: free_kib=$DISK_FREE_KIB" >&2
  exit 34
fi

mkdir -p "$OUTPUT_PARENT"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TEMP_CONSOLE="$(mktemp "/tmp/${RUN_ID}.XXXXXX.console.log")"

monitor_resources() {
  local runner_pid="$1"
  while [[ ! -d "$OUTPUT" ]]; do
    if ! kill -0 "$runner_pid" 2>/dev/null; then
      return
    fi
    sleep 0.2
  done
  printf 'timestamp_utc\tmemory_used_mib\tutilization_gpu_percent\ttemperature_c\n' > "$OUTPUT/resource_monitor.tsv"
  while kill -0 "$runner_pid" 2>/dev/null; do
    nvidia-smi --query-gpu=timestamp,memory.used,utilization.gpu,temperature.gpu \
      --format=csv,noheader,nounits \
      | awk -F', ' '{printf "%s\t%s\t%s\t%s\n",$1,$2,$3,$4}' \
      >> "$OUTPUT/resource_monitor.tsv"
    sleep 1
  done
}

set +e
CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 \
  timeout --signal=TERM --kill-after=30s 14400s \
  "$PYTHON" -u "$RUNNER" \
    --protocol "$PROTOCOL" \
    --protocol-sha256 "$PROTOCOL_SHA" \
    --execution-authorization "$AUTHORIZATION" \
    --execution-authorization-sha256 "$AUTHORIZATION_SHA" \
    --manifest "$MANIFEST" \
    --manifest-sha256 "$MANIFEST_SHA" \
    --data-root "$DATA_ROOT" \
    --frozen-v2-case-metrics "$FROZEN_V2_METRICS" \
    --frozen-v2-case-metrics-sha256 "$FROZEN_V2_METRICS_SHA" \
    --output-dir "$OUTPUT" \
    --device cuda:0 \
    > "$TEMP_CONSOLE" 2>&1 &
RUNNER_PID="$!"
monitor_resources "$RUNNER_PID" &
MONITOR_PID="$!"
wait "$RUNNER_PID"
RUNNER_STATUS="$?"
wait "$MONITOR_PID"
set -e

if [[ ! -d "$OUTPUT" ]]; then
  mkdir "$OUTPUT"
fi
if [[ -e "$OUTPUT/console.log" ]]; then
  echo "[blocked] unexpected console.log collision" >&2
  exit 35
fi
mv "$TEMP_CONSOLE" "$OUTPUT/console.log"
printf '[launcher] runner_status=%s\n' "$RUNNER_STATUS" >> "$OUTPUT/console.log"
if [[ ! -e "$OUTPUT/resource_monitor.tsv" ]]; then
  printf 'timestamp_utc\tmemory_used_mib\tutilization_gpu_percent\ttemperature_c\n' > "$OUTPUT/resource_monitor.tsv"
fi
printf '%s\n' "$STARTED_AT" > "$OUTPUT/started_at_utc.txt"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUTPUT/finished_at_utc.txt"

FINAL_STATUS="$RUNNER_STATUS"
PEAK_USED_MIB="$(
  awk -F '\t' 'NR>1 && $2+0>max {max=$2+0} END {print max+0}' \
    "$OUTPUT/resource_monitor.tsv"
)"
if [[ "$FINAL_STATUS" -eq 0 && "$PEAK_USED_MIB" -gt 20480 ]]; then
  echo "[failed] observed GPU memory used exceeded 20480 MiB: $PEAK_USED_MIB" >> "$OUTPUT/console.log"
  FINAL_STATUS=36
fi

LAUNCHER_SHA="$(sha256sum "$0" | awk '{print $1}')"
if [[ "$FINAL_STATUS" -eq 0 ]]; then
  set +e
  "$PYTHON" - "$OUTPUT" "$PEAK_USED_MIB" "$GPU_USED" "$GPU_TOTAL" "$DISK_FREE_KIB" "$LAUNCHER_SHA" <<'PY'
import csv
import json
import platform
import socket
import sys
from pathlib import Path

out = Path(sys.argv[1])
peak, launch_used, total, disk = map(int, sys.argv[2:6])
launcher_sha = sys.argv[6]
required = (
    "invocation.json",
    "per_condition_case_metrics.csv",
    "per_condition_source_metrics.csv",
    "intervention_mechanism_diagnostics.csv",
    "paired_intervention_deltas.csv",
    "intervention_summary.json",
    "mechanism_classification_receipt.json",
    "intervention_execution_receipt.json",
    "console.log",
    "resource_monitor.tsv",
    "started_at_utc.txt",
    "finished_at_utc.txt",
)
for name in required:
    assert (out / name).is_file() and (out / name).stat().st_size > 0, name

def rows(name):
    with (out / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))

assert len(rows("per_condition_case_metrics.csv")) == 840
assert len(rows("per_condition_source_metrics.csv")) == 168
assert len(rows("intervention_mechanism_diagnostics.csv")) == 840
assert len(rows("paired_intervention_deltas.csv")) == 168
execution = json.loads((out / "intervention_execution_receipt.json").read_text())
classification = json.loads((out / "mechanism_classification_receipt.json").read_text())
summary = json.loads((out / "intervention_summary.json").read_text())
counts = execution["counters"]
assert execution["status"] == "PASS"
assert execution["model_state_hashes_unchanged"] is True
assert counts["checkpoint_loads"] == 2
assert counts["npz_open_events"] == 210
assert counts["member_partial"] == counts["member_implant"] == counts["member_gt"] == 210
assert counts["model_case_forward_calls"] == 840
assert counts["probability_hooks_registered"] == counts["probability_hooks_removed"] == 630
assert counts["optimizer_constructions"] == counts["optimizer_steps"] == 0
assert counts["model_parameter_updates"] == counts["model_buffer_updates"] == 0
assert execution["round_b_authorized"] is False
assert execution["automatic_next_run"] is False
assert classification["execution_controls"]["status"] == "PASS"
assert classification["execution_controls"]["native_reproduction_pass"] is True
assert classification["execution_controls"]["case_mean_probability_equals_bias_zero_pass"] is True
assert classification["execution_controls"]["coarse_condition_invariance_pass"] is True
assert classification["round_b_authorized"] is False
assert classification["automatic_next_run"] is False
assert classification["automatic_beta_tuning"] is False

environment = {
    "status": "PASS",
    "host": socket.gethostname(),
    "platform": platform.platform(),
    "python": sys.version,
    "gpu_name": "NVIDIA GeForce RTX 4090 D",
    "gpu_uuid": "GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed",
    "gpu_memory_used_mib_at_launch": launch_used,
    "gpu_memory_total_mib": total,
    "observed_peak_gpu_memory_used_mib": peak,
    "disk_free_kib_at_launch": disk,
    "launcher_sha256": launcher_sha,
}
(out / "environment.json").write_text(
    json.dumps(environment, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)

primary = "rim_gt_rim_to_pred_p95_mm"
bias = summary["comparisons"]["bias_zero_minus_native_qc"][primary]
permutation = summary["comparisons"]["fixed_permutation_minus_native_qc"][primary]
training = summary["comparisons"]["bias_zero_minus_frozen_Q0"][primary]
report = f"""# Cranial-SCQR v1.1 Round A-I 正式机制干预报告

- 执行状态：PASS
- 机制分类：{classification['mechanism_classification']}
- 训练路径分类：{classification['training_path_classification']}
- bias_zero - native_qc（Fold A）：{bias['A']:.6f} mm
- bias_zero - native_qc（Fold B）：{bias['B']:.6f} mm
- bias_zero - native_qc（Combined）：{bias['combined']:.6f} mm
- fixed_permutation - native_qc（Combined）：{permutation['combined']:.6f} mm
- bias_zero - frozen_Q0（Combined）：{training['combined']:.6f} mm
- checkpoint loads / NPZ opens / forwards：2 / 210 / 840
- optimizer steps / parameter updates / buffer updates：0 / 0 / 0
- observed peak GPU memory：{peak} MiB
- Round B authorized：false
- automatic next run：false

本结果仅用于 development84 Round A-I 机制诊断，不构成 confirmation、official test、beta 调参、Round B 或后续实验授权。
"""
(out / "formal_intervention_report_zh.md").write_text(report, encoding="utf-8")
validation = {
    "status": "PASS",
    "required_output_files_present": True,
    "case_rows": 840,
    "source_rows": 168,
    "diagnostic_rows": 840,
    "paired_delta_rows": 168,
    "native_reproduction_pass": True,
    "negative_control_equivalence_pass": True,
    "coarse_condition_invariance_pass": True,
    "model_state_unchanged": True,
    "observed_peak_gpu_memory_used_mib": peak,
    "maximum_allowed_gpu_memory_mib": 20480,
    "frozen_v2_evidence_preserved": True,
    "round_b_authorized": False,
    "automatic_next_run": False,
}
(out / "launcher_validation_receipt.json").write_text(
    json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
)
print("[verified] Round A-I counts, controls, state, outputs, resources and non-authorization locks")
PY
  VALIDATION_STATUS="$?"
  set -e
  if [[ "$VALIDATION_STATUS" -ne 0 ]]; then
    FINAL_STATUS=37
  fi
fi

if [[ "$FINAL_STATUS" -ne 0 ]]; then
  "$PYTHON" - "$OUTPUT" "$FINAL_STATUS" "$RUNNER_STATUS" "$PEAK_USED_MIB" <<'PY'
import json
import sys
from pathlib import Path

out = Path(sys.argv[1])
receipt = {
    "status": "FAILED_STOPPED_NO_RETRY",
    "final_status": int(sys.argv[2]),
    "runner_status": int(sys.argv[3]),
    "observed_peak_gpu_memory_used_mib": int(sys.argv[4]),
    "round_b_authorized": False,
    "automatic_retry": False,
    "automatic_next_run": False,
}
path = out / "launcher_failure_receipt.json"
if not path.exists():
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
fi

printf '%s\n' "$FINAL_STATUS" > "$OUTPUT/exit_code"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUTPUT/finished_at_utc.txt"
(
  cd "$OUTPUT"
  find . -maxdepth 1 -type f ! -name files.sha256 -print0 \
    | sort -z | xargs -0 sha256sum > files.sha256
  sha256sum -c files.sha256
)
echo "[done] final_status=$FINAL_STATUS output=$OUTPUT"
exit "$FINAL_STATUS"
