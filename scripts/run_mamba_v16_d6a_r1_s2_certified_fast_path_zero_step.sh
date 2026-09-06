#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CONFIG="${D6_R1_S2_ZERO_STEP_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_authorized_v1}"
AUTH="${D6_R1_S2_ZERO_STEP_AUTH_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_zero_step_authorization_v1}"
OUT="${D6_R1_S2_ZERO_STEP_RESULT_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_artificial_zero_step_v1}"

echo "===== Reverify S2 zero-step authorization ====="
(
  cd "$AUTH"
  sha256sum -c files.sha256
)

echo "===== Run one authorized 168-case artificial CUDA zero-step ====="
python tools/preflight_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py \
  --config_dir "$CONFIG" \
  --authorization_dir "$AUTH" \
  --output_dir "$OUT"

echo "===== Verify immutable S2 zero-step result ====="
(
  cd "$OUT"
  sha256sum -c files.sha256
)

python - "$OUT/s2_artificial_zero_step_receipt.json" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["status"] in {
    "D6A_R1_S2_certified_fast_path_artificial_zero_step_passed",
    "D6A_R1_S2_certified_fast_path_artificial_zero_step_equivalence_failed",
    "D6A_R1_S2_certified_fast_path_artificial_zero_step_routing_gate_failed",
}
assert receipt["cases"] == receipt["S0_assignments"] == receipt["S2_assignments"] == 168
assert receipt["state_unchanged"] is True
assert receipt["performance_timing_calls"] == 0
assert receipt["warmup_runs"] == receipt["timed_runs"] == receipt["torch_profiler_traces"] == 0
assert receipt["optimizer_steps"] == receipt["model_updates"] == receipt["D6_cases_accessed"] == 0
for key in (
    "S2_artificial_performance_benchmark_authorized",
    "R1_production_implementation_change_authorized",
    "formal_efficiency_rerun_authorized",
    "seed0_training_authorized",
    "seed1_training_authorized",
    "D6B_authorized",
    "protected_or_sealed_data_accessed",
):
    assert receipt[key] is False
if receipt["status"].endswith("_passed"):
    assert receipt["all_gates_passed"] is True
    assert receipt["slot_to_candidate_exact"] == 168
    assert receipt["hard_assignment_exact"] == 168
    assert receipt["adjusted_objective_exact"] == 168
    assert receipt["certified_fast_path_cases"] >= 96
else:
    assert receipt["all_gates_passed"] is False
print("[ok] S2 168-case artificial zero-step frozen semantics verified")
print("status:", receipt["status"])
print("slot/selected/hard/objective:", receipt["slot_to_candidate_exact"], receipt["sorted_selected_indices_exact"], receipt["hard_assignment_exact"], receipt["adjusted_objective_exact"])
print("fast/fallback:", receipt["certified_fast_path_cases"], receipt["fallback_s0_cases"])
PY

echo "[done] D6-A R1 S2 artificial equivalence/routing zero-step completed"
echo "[next] benchmark requires a separate authorization and every frozen gate to pass"
echo "[locked] benchmark=false production=false formal_rerun=false training=false D6B=false sealed=false"
