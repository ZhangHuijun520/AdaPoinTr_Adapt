#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MECHANISM_LOCK="${MAMBA_V16_D6A_MECHANISM_LOCK_DIR:-$REPO_ROOT/logs/mamba_v16_d6_contact_support/d6a_slot32_mechanism_protocol_lock_v1}"
OUT_DIR="${MAMBA_V16_D6A_ZERO_STEP_OUT_DIR:-$REPO_ROOT/logs/mamba_v16_d6_contact_support/d6a_synthetic_zero_step_v1}"

echo "===== D6-A implementation tests ====="
python tools/test_mamba_v16_d6a_slot_allocator.py

echo "===== D6-A artificial CUDA zero-step ====="
python tools/preflight_mamba_v16_d6a_synthetic_zero_step.py \
  --mechanism_lock_dir "$MECHANISM_LOCK" \
  --out_dir "$OUT_DIR"

echo "===== Verify immutable zero-step output ====="
(
  cd "$OUT_DIR"
  sha256sum -c files.sha256
)

python - "$OUT_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
receipt = json.loads((root / "zero_step_preflight_receipt.json").read_text())

assert receipt["status"] == "D6A_R0_R1_artificial_CUDA_zero_step_passed"
assert receipt["artificial_cases"] == 4
assert receipt["forward_passes"] == 8
assert receipt["backward_passes"] == 8
assert receipt["optimizer_constructed"] is False
assert receipt["optimizer_steps"] == 0
assert receipt["model_updates"] == 0
assert receipt["state_hash_before"] == receipt["state_hash_after"]
assert receipt["R1_trainable_parameters"] <= 100000
assert receipt["D6_cases_accessed"] == 0
assert receipt["D6_geometry_accessed"] is False
assert receipt["training_authorized"] is False
assert receipt["proposal_confirmation_authorized"] is False
assert receipt["protected_or_sealed_data_accessed"] is False

print("status:", receipt["status"])
print("scipy:", receipt["scipy_version"])
print("cuda:", receipt["cuda_device_name"])
print("R1 parameters:", receipt["R1_trainable_parameters"])
print("[ok] D6-A artificial zero-step frozen semantics verified")
PY

echo "[done] D6-A artificial CUDA zero-step passed"
echo "[locked] D6=0 generation=false calibration=false training=false sealed=false"
