#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MECHANISM="${D6_MECHANISM_LOCK_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_slot32_mechanism_protocol_lock_v1}"
ZERO_STEP="${D6_ZERO_STEP_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_synthetic_zero_step_v1}"
FOURFOLD="${D6_FOURFOLD_LOCK_DIR:-$HOME/datasets/MUG500plusD6Development100_v1/data_locks/mug500plus_d6_development_generation_fourfold_protocol_lock_v1}"
AUDIT="${D6_GENERATION_AUDIT_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/development_generation_audit_v1}"
OUT="${D6_CALIBRATION_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_gradient_ratio_calibration_protocol_v1}"

echo "===== D6-A gradient calibration protocol tests ====="
python tools/test_mamba_v16_d6a_gradient_ratio_calibration_protocol.py

echo "===== Freeze non-runnable D6-A calibration protocol ====="
python tools/lock_mamba_v16_d6a_gradient_ratio_calibration_protocol.py \
  --repo_root "$ROOT" \
  --mechanism_lock_dir "$MECHANISM" \
  --zero_step_dir "$ZERO_STEP" \
  --fourfold_lock_dir "$FOURFOLD" \
  --generation_audit_dir "$AUDIT" \
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
    "D6A_R1_gradient_calibration_protocol_frozen_execution_not_authorized"
)
assert receipt["optimizer_steps"] == 0
assert receipt["model_updates"] == 0
assert receipt["dev_cases_accessed"] == 0
assert receipt["calibration_execution_authorized"] is False
assert receipt["separate_calibration_execution_authorization_allowed_next"] is True
assert receipt["runtime_config_materialization_authorized"] is False
assert receipt["seed0_training_authorized"] is False
assert receipt["seed1_training_authorized"] is False
assert receipt["proposal_confirmation_authorized"] is False
assert receipt["D6B_authorized"] is False
assert receipt["selection_started"] is False
assert receipt["protected_or_sealed_data_accessed"] is False
assert list(receipt["folds"]) == ["A", "B", "C", "D"]
for binding in receipt["folds"].values():
    assert binding["train_cases"] == 300
    assert binding["calibration_batches"] == 8
    assert binding["batch_size"] == 8
    assert binding["measured_case_slots"] == 64
    assert binding["calibration_execution_authorized"] is False
print("[ok] D6-A calibration protocol lock semantics verified")
PY

echo "[done] D6-A R1 gradient-ratio calibration protocol frozen"
echo "[authorized-next] separate calibration execution authorization only"
echo "[locked] calibration=false training=false seed1=false D6B=false confirmation=false"
