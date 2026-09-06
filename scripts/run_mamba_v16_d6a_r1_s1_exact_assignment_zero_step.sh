#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CONFIG="${D6_R1_S1_ZERO_STEP_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_s1_exact_assignment_zero_step_authorized_v1}"
AUTH="${D6_R1_S1_ZERO_STEP_AUTH_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_s1_exact_assignment_zero_step_authorization_v1}"
OUT="${D6_R1_S1_ZERO_STEP_RESULT_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_s1_exact_assignment_artificial_zero_step_v1}"

echo "===== Reverify S1 zero-step authorization ====="
(
  cd "$AUTH"
  sha256sum -c files.sha256
)

echo "===== Run one authorized 168-case artificial CUDA zero-step ====="
python tools/preflight_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py \
  --config_dir "$CONFIG" \
  --authorization_dir "$AUTH" \
  --output_dir "$OUT"

echo "===== Verify immutable S1 zero-step result ====="
(
  cd "$OUT"
  sha256sum -c files.sha256
)

python - "$OUT/s1_artificial_zero_step_receipt.json" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["status"] in {
    "D6A_R1_S1_exact_assignment_artificial_zero_step_passed",
    "D6A_R1_S1_exact_assignment_artificial_zero_step_equivalence_failed",
}
assert receipt["cases"] == 168
assert receipt["families"] == 7
assert receipt["S0_assignments"] == 168
assert receipt["S1_assignments"] == 168
assert receipt["state_unchanged"] is True
assert receipt["performance_timing_calls"] == 0
assert receipt["warmup_runs"] == 0
assert receipt["timed_runs"] == 0
assert receipt["torch_profiler_traces"] == 0
assert receipt["formal_gate_evaluated"] is False
assert receipt["optimizer_steps"] == 0
assert receipt["model_updates"] == 0
assert receipt["D6_cases_accessed"] == 0
for key in (
    "S1_artificial_performance_benchmark_authorized",
    "S2_implementation_authorized",
    "R1_production_implementation_change_authorized",
    "formal_efficiency_rerun_authorized",
    "seed0_training_authorized",
    "seed1_training_authorized",
    "D6B_authorized",
    "protected_or_sealed_data_accessed",
):
    assert receipt[key] is False
print("[ok] S1 168-case artificial zero-step frozen semantics verified")
print("status:", receipt["status"])
print("slot mapping:", receipt["slot_to_candidate_exact"], "/ 168")
print("selected set:", receipt["sorted_selected_indices_exact"], "/ 168")
print("objective:", receipt["adjusted_objective_exact"], "/ 168")
if receipt["all_equivalence_gates_passed"]:
    assert receipt["slot_to_candidate_exact"] == 168
    assert receipt["hard_assignment_exact"] == 168
else:
    assert receipt["slot_to_candidate_exact"] < 168
    assert receipt["S1_artificial_performance_benchmark_authorized"] is False
PY

echo "[done] D6-A R1 S1 artificial equivalence zero-step completed"
echo "[next] follow the frozen receipt; benchmark only if every equivalence gate passed"
echo "[locked] benchmark=false production=false formal_rerun=false training=false D6B=false sealed=false"
