#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

GENERATION_ROOT="${MUG500PLUS_D4_M2_ROOT:-$HOME/datasets/MUG500plusD4M2_v1}"
SOURCE_ROOT="${MUG500PLUS_D4_SOURCE100_ROOT:-$HOME/datasets/MUG500plusD4Source100_v1}"
OUTPUT_DIR="${MUG500PLUS_D4_M2_AUDIT_DIR:-logs/mamba_v14_d4_contact_support/d4_m2_generation_audit_v1}"

python -m py_compile \
  tools/audit_mamba_v14_d4_mug500plus_m2_generation.py \
  tools/test_mamba_v14_d4_mug500plus_m2_generation_audit.py

python tools/test_mamba_v14_d4_mug500plus_m2_generation_audit.py

python -u tools/audit_mamba_v14_d4_mug500plus_m2_generation.py \
  --generation_root "$GENERATION_ROOT" \
  --source100_qc_lock_dir \
    "$SOURCE_ROOT/data_locks/mug500plus_d4_source100_qc_lock_v1" \
  --protocol_lock_dir \
    "$SOURCE_ROOT/data_locks/mug500plus_d4_m2_fourfold_protocol_lock_v1" \
  --audit_protocol_json \
    docs/mamba_v14_d4_mug500plus_m2_generation_audit_protocol_v1.json \
  --output_dir "$OUTPUT_DIR"

(
  cd "$OUTPUT_DIR"
  sha256sum -c files.sha256
)

echo "[done] D4 M2 independent generation audit completed"
echo "[locked] training=false selection=false protected=false"
echo "[next] freeze a separate D4 candidate and training protocol"
