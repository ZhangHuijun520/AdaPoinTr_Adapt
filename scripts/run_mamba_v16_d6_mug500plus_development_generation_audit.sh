#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

GENERATION_ROOT="${MUG500PLUS_D6_DEVELOPMENT400_ROOT:-$HOME/datasets/MUG500plusD6Development400_v1}"
SOURCE_ROOT="${MUG500PLUS_D6_SOURCE_ROOT:-$HOME/datasets/MUG500plusD6Development100_v1}"
OUTPUT_DIR="${MUG500PLUS_D6_GENERATION_AUDIT_DIR:-logs/mamba_v16_d6_contact_support/development_generation_audit_v1}"

python -m py_compile \
  tools/audit_mamba_v16_d6_mug500plus_development_generation.py \
  tools/test_mamba_v16_d6_mug500plus_development_generation_audit.py

python tools/test_mamba_v16_d6_mug500plus_development_generation_audit.py

python -u tools/audit_mamba_v16_d6_mug500plus_development_generation.py \
  --generation_root "$GENERATION_ROOT" \
  --development100_qc_lock_dir \
    "$SOURCE_ROOT/data_locks/mug500plus_d6_development100_qc_lock_v1" \
  --source125_acquisition_lock_dir \
    "$SOURCE_ROOT/data_locks/mug500plus_d6_source125_acquisition_lock_v1" \
  --protocol_lock_dir \
    "$SOURCE_ROOT/data_locks/mug500plus_d6_development_generation_fourfold_protocol_lock_v1" \
  --audit_protocol_json \
    docs/mamba_v16_d6_mug500plus_development_generation_audit_protocol_v1.json \
  --output_dir "$OUTPUT_DIR"

(
  cd "$OUTPUT_DIR"
  sha256sum -c files.sha256
)

echo "[done] D6 development400 independent generation audit completed"
echo "[locked] calibration=false training=false seed1=false D6B=false selection=false confirmation=false"
echo "[next] freeze a separate D6 gradient-calibration protocol"
