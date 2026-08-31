#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_LOCK_ROOT="${MUG500PLUS_D5_DATA_LOCK_ROOT:-$HOME/datasets/MUG500plusD5Development100_v1/data_locks}"
QC_LOCK="${MUG500PLUS_D5_DEVELOPMENT100_QC_LOCK_DIR:-$DATA_LOCK_ROOT/mug500plus_d5_development100_qc_lock_v1}"
FOURFOLD_LOCK="${MUG500PLUS_D5_DEVELOPMENT400_FOURFOLD_LOCK_DIR:-$DATA_LOCK_ROOT/mug500plus_d5_development400_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D5_GENERATION_AUDIT_DIR:-$ROOT/logs/mamba_v15_d5_contact_support/development_generation_audit_v1}"
OUTPUT="${MAMBA_V15_D5_CANDIDATE_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v15_d5_contact_support/candidate_training_protocol_v1}"
TEST="$ROOT/tools/test_mamba_v15_d5_candidate_training_protocol.py"

cd "$ROOT"
python -u "$TEST"
python -u tools/lock_mamba_v15_d5_candidate_training_protocol.py \
  --development100_qc_lock_dir "$QC_LOCK" \
  --fourfold_lock_dir "$FOURFOLD_LOCK" \
  --generation_audit_dir "$AUDIT" \
  --output_dir "$OUTPUT" \
  --test_script "$TEST"
python -u tools/lock_mamba_v15_d5_candidate_training_protocol.py \
  --development100_qc_lock_dir "$QC_LOCK" \
  --fourfold_lock_dir "$FOURFOLD_LOCK" \
  --generation_audit_dir "$AUDIT" \
  --output_dir "$OUTPUT" \
  --test_script "$TEST"

(
  cd "$OUTPUT"
  sha256sum -c files.sha256
)

echo "[done] D5 candidate/training preregistration frozen"
echo "[authorized-next] V0/V1 implementation and zero-step preflight only"
echo "[locked] training=false selection=false sealed=false D5B=false"
