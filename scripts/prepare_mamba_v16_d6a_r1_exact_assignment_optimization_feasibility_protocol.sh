#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROFILING_RESULT="${D6_R1_PROFILING_RESULT_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_latency_posthoc_profiling_result_v1}"
PROFILING_FREEZE="${D6_R1_PROFILING_FREEZE_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_latency_posthoc_profiling_result_freeze_v1}"
OUT="${D6_R1_OPTIMIZATION_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_exact_assignment_optimization_feasibility_protocol_v1}"

echo "===== D6-A R1 exact-assignment optimization protocol tests ====="
python tools/test_mamba_v16_d6a_r1_exact_assignment_optimization_feasibility_protocol.py

echo "===== Freeze non-runnable optimization feasibility protocol ====="
python tools/lock_mamba_v16_d6a_r1_exact_assignment_optimization_feasibility_protocol.py \
  --repo_root "$ROOT" \
  --profiling_result_dir "$PROFILING_RESULT" \
  --profiling_freeze_dir "$PROFILING_FREEZE" \
  --out_dir "$OUT"

echo "===== Verify immutable protocol lock ====="
(
  cd "$OUT"
  sha256sum -c files.sha256
)

python - "$OUT/protocol_lock_receipt.json" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["status"] == (
    "D6A_R1_exact_assignment_optimization_feasibility_protocol_frozen_non_runnable"
)
assert receipt["equivalence_cases"] == 168
assert receipt["S1_row_top_k"] == 32
assert receipt["S1_cutoff_ties_included"] is True
assert receipt["S1_full_D2H_retained"] is True
assert receipt["formal_latency_ratio_maximum"] == 1.15
assert receipt["implied_R1_latency_ms_maximum"] == 0.4575819242745637
assert receipt["optimization_runs"] == 0
assert receipt["formal_reruns"] == 0
assert receipt["optimizer_steps"] == 0
assert receipt["model_updates"] == 0
assert receipt["D6_cases_accessed"] == 0
assert receipt["protocol_lock_authorized"] is True
for key in (
    "S1_implementation_authorized",
    "S1_zero_step_authorized",
    "S1_benchmark_authorized",
    "S2_implementation_authorized",
    "S2_benchmark_authorized",
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
print("[ok] D6-A R1 optimization feasibility protocol lock semantics verified")
PY

echo "[done] D6-A R1 exact-assignment optimization feasibility protocol frozen"
echo "[authorized-next] separate S1 implementation and artificial zero-step only"
echo "[locked] optimization=false formal_rerun=false training=false seed1=false D6B=false sealed=false"
