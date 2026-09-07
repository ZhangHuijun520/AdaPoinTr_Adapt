#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_ROOT="$ROOT/logs/mamba_v16_d6_contact_support"
PARENT="${D6_R1_S2_BENCHMARK_PARENT_LOCK_DIR:-$LOG_ROOT/d6a_r1_s2_certified_fast_path_feasibility_protocol_v1}"
RESULT="${D6_R1_S2_BENCHMARK_RESULT_DIR:-$LOG_ROOT/d6a_r1_s2_certified_fast_path_artificial_zero_step_v1}"
OUT="${D6_R1_S2_BENCHMARK_PROTOCOL_LOCK_DIR:-$LOG_ROOT/d6a_r1_s2_artificial_performance_benchmark_protocol_v1}"
PYTHON="${D6_R1_S2_BENCHMARK_PYTHON:-/opt/conda/envs/adapointr-mamba/bin/python}"

if [[ ! -x "$PYTHON" ]]; then
  PYTHON="$(command -v python)"
fi

echo "===== D6-A R1 S2 artificial benchmark protocol tests ====="
"$PYTHON" tools/test_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_protocol.py

echo "===== Freeze non-runnable S2 artificial benchmark protocol ====="
"$PYTHON" tools/lock_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_protocol.py \
  --parent_lock_dir "$PARENT" \
  --result_dir "$RESULT" \
  --out_dir "$OUT"

echo "===== Verify immutable S2 benchmark protocol lock ====="
(
  cd "$OUT"
  sha256sum -c files.sha256
)

"$PYTHON" - "$OUT/protocol_lock_receipt.json" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["status"] == (
    "D6A_R1_S2_artificial_performance_benchmark_protocol_frozen_non_runnable"
)
assert receipt["correctness_replay_cases"] == 168
assert receipt["expected_certified_fast_path_cases"] == 96
assert receipt["expected_fallback_s0_cases"] == 72
assert receipt["warmup_calls_planned"] == 28
assert receipt["measurement_blocks_planned"] == 3
assert receipt["timed_calls_per_candidate_planned"] == 504
assert receipt["timed_observation_rows_planned"] == 1008
assert receipt["warmup_calls_executed"] == 0
assert receipt["timed_calls_executed"] == 0
assert receipt["torch_profiler_traces"] == 0
assert receipt["optimizer_steps"] == receipt["model_updates"] == 0
assert receipt["D6_cases_accessed"] == 0
assert receipt["protocol_lock_authorized"] is True
for key in (
    "S2_artificial_performance_benchmark_execution_authorized",
    "S2_implementation_change_authorized",
    "R1_production_implementation_change_authorized",
    "formal_efficiency_rerun_authorized",
    "seed0_training_authorized",
    "seed1_training_authorized",
    "proposal_confirmation_authorized",
    "D6B_authorized",
    "candidate_selection_authorized",
    "protected_or_sealed_data_accessed",
):
    assert receipt[key] is False
print("[ok] D6-A R1 S2 non-runnable artificial benchmark protocol verified")
PY

echo "[done] D6-A R1 S2 artificial performance benchmark protocol frozen"
echo "[authorized-next] separate S2 artificial performance benchmark execution authorization only"
echo "[locked] benchmark=false production=false formal_rerun=false training=false seed1=false D6B=false sealed=false"
