#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FOURFOLD="${D6_FOURFOLD_LOCK_DIR:-$HOME/datasets/MUG500plusD6Development100_v1/data_locks/mug500plus_d6_development_generation_fourfold_protocol_lock_v1}"
AUDIT="${D6_GENERATION_AUDIT_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/development_generation_audit_v1}"
CALIBRATION="${D6_CALIBRATION_COMPLETION_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_gradient_calibration_completion_v1}"
WEIGHTED="${D6_WEIGHTED_ZERO_STEP_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_calibrated_weighted_zero_step_v1}"
OUT="${D6_CANDIDATE_TRAINING_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_candidate_training_efficiency_protocol_v1}"

echo "===== D6-A candidate/training/efficiency protocol tests ====="
python tools/test_mamba_v16_d6a_candidate_training_efficiency_protocol.py

echo "===== Freeze non-runnable protocol lock ====="
python tools/lock_mamba_v16_d6a_candidate_training_efficiency_protocol.py \
  --repo_root "$ROOT" \
  --fourfold_lock_dir "$FOURFOLD" \
  --generation_audit_dir "$AUDIT" \
  --calibration_completion_dir "$CALIBRATION" \
  --weighted_zero_step_dir "$WEIGHTED" \
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
assert receipt["status"] == "D6A_candidate_training_efficiency_protocol_frozen_non_runnable"
assert receipt["planned_training_runs"] == 8
assert receipt["planned_optimizer_steps_maximum"] == 15200
assert receipt["optimizer_steps"] == 0
assert receipt["model_updates"] == 0
assert receipt["development_cases_accessed"] == 0
assert len(receipt["bindings"]) == 8
assert receipt["efficiency_implementation_and_artificial_zero_step_authorized_next"] is True
for key in (
    "efficiency_execution_authorized",
    "runtime_training_configs_authorized",
    "seed0_training_authorized",
    "seed1_training_authorized",
    "proposal_confirmation_authorized",
    "D6B_authorized",
    "candidate_selection_authorized",
    "protected_or_sealed_data_accessed",
):
    assert receipt[key] is False
print("[ok] D6-A candidate/training/efficiency lock semantics verified")
PY

echo "[done] D6-A candidate/training/efficiency protocol frozen"
echo "[authorized-next] efficiency implementation and artificial zero-step only"
echo "[locked] efficiency_execution=false training=false seed1=false D6B=false confirmation=false"
