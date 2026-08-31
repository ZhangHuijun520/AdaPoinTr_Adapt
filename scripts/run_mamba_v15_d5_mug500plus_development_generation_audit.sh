#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

GENERATION_ROOT="${MUG500PLUS_D5_DEVELOPMENT400_ROOT:-$HOME/datasets/MUG500plusD5Development400_v1}"
SOURCE_ROOT="${MUG500PLUS_D5_SOURCE_ROOT:-$HOME/datasets/MUG500plusD5Development100_v1}"
OUTPUT_DIR="${MUG500PLUS_D5_GENERATION_AUDIT_DIR:-logs/mamba_v15_d5_contact_support/development_generation_audit_v1}"

python -m py_compile \
  tools/audit_mamba_v15_d5_mug500plus_development_generation.py \
  tools/test_mamba_v15_d5_mug500plus_development_generation_audit.py

python tools/test_mamba_v15_d5_mug500plus_development_generation_audit.py

python -u tools/audit_mamba_v15_d5_mug500plus_development_generation.py \
  --generation_root "$GENERATION_ROOT" \
  --development100_qc_lock_dir \
    "$SOURCE_ROOT/data_locks/mug500plus_d5_development100_qc_lock_v1" \
  --source150_acquisition_lock_dir \
    "$SOURCE_ROOT/data_locks/mug500plus_d5_source150_acquisition_lock_v1" \
  --protocol_lock_dir \
    "$SOURCE_ROOT/data_locks/mug500plus_d5_development400_fourfold_protocol_lock_v1" \
  --audit_protocol_json \
    docs/mamba_v15_d5_mug500plus_development_generation_audit_protocol_v1.json \
  --output_dir "$OUTPUT_DIR"

(
  cd "$OUTPUT_DIR"
  sha256sum -c files.sha256
)

echo "[done] D5 development400 independent generation audit completed"
echo "[locked] model=false training=false selection=false sealed=false"
echo "[next] freeze a separate D5 candidate and training protocol"
