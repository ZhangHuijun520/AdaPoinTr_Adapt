#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

LOCK="${D6_CANDIDATE_TRAINING_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_candidate_training_efficiency_protocol_v1}"
OUT="${D6_EFFICIENCY_ZERO_STEP_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_efficiency_implementation_zero_step_v1}"

echo "===== D6-A efficiency implementation tests ====="
python tools/test_mamba_v16_d6a_efficiency_implementation.py

echo "===== D6-A artificial full-inference zero-step ====="
python tools/preflight_mamba_v16_d6a_efficiency_implementation_zero_step.py \
  --protocol_lock_dir "$LOCK" \
  --out_dir "$OUT"

echo "===== Verify immutable zero-step output ====="
(
  cd "$OUT"
  sha256sum -c files.sha256
)

echo "[done] D6-A efficiency implementation artificial zero-step completed"
echo "[locked] formal_efficiency=false training=false seed1=false D6B=false"
