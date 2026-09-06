#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOG_ROOT="$ROOT/logs/mamba_v16_d6_contact_support"
PARENT="${D6_R1_S2_PARENT_LOCK_DIR:-$LOG_ROOT/d6a_r1_exact_assignment_optimization_feasibility_protocol_v1}"
RESTORE="${D6_R1_S2_PARENT_RESTORE_DIR:-$LOG_ROOT/d6a_r1_s1_parent_lock_lf_restore_v1}"
AUTH="${D6_R1_S2_S1_AUTH_DIR:-$LOG_ROOT/d6a_r1_s1_exact_assignment_zero_step_authorization_v1}"
CONFIG="${D6_R1_S2_S1_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_s1_exact_assignment_zero_step_authorized_v1}"
RESULT="${D6_R1_S2_S1_RESULT_DIR:-$LOG_ROOT/d6a_r1_s1_exact_assignment_artificial_zero_step_v1}"
OUT="${D6_R1_S2_PROTOCOL_LOCK_DIR:-$LOG_ROOT/d6a_r1_s2_certified_fast_path_feasibility_protocol_v1}"

echo "===== D6-A R1 S2 certified fast-path protocol tests ====="
python tools/test_mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_protocol.py

echo "===== Freeze non-runnable S2 feasibility protocol ====="
python tools/lock_mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_protocol.py \
  --repo_root "$ROOT" \
  --canonical_parent_dir "$PARENT" \
  --restoration_dir "$RESTORE" \
  --authorization_dir "$AUTH" \
  --config_dir "$CONFIG" \
  --result_dir "$RESULT" \
  --out_dir "$OUT"

echo "===== Verify immutable S2 protocol lock ====="
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
    "D6A_R1_S2_certified_fast_path_feasibility_protocol_frozen_non_runnable"
)
assert receipt["S1_result_status"] == (
    "D6A_R1_S1_exact_assignment_artificial_zero_step_equivalence_failed"
)
assert receipt["equivalence_cases"] == 168
assert receipt["equivalence_required"] == (
    "168/168_for_slot_selected_hard_and_objective"
)
assert receipt["certified_fast_path_cases_minimum"] == 96
assert receipt["edge_exclusion_solves_per_candidate_case"] == 32
assert receipt["S2_implementation_runs"] == 0
assert receipt["timing_calls"] == 0
assert receipt["warmup_runs"] == 0
assert receipt["timed_runs"] == 0
assert receipt["optimizer_steps"] == 0
assert receipt["model_updates"] == 0
assert receipt["D6_cases_accessed"] == 0
assert receipt["protocol_lock_authorized"] is True
for key in (
    "S2_shadow_implementation_authorized",
    "S2_artificial_zero_step_authorized",
    "S2_artificial_performance_benchmark_authorized",
    "S1_rerun_authorized",
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
print("[ok] D6-A R1 S2 non-runnable protocol semantics verified")
PY

echo "[done] D6-A R1 S2 certified fast-path feasibility protocol frozen"
echo "[authorized-next] separate S2 shadow implementation and 168-case artificial zero-step only"
echo "[locked] timing=false benchmark=false production=false training=false seed1=false D6B=false sealed=false"
