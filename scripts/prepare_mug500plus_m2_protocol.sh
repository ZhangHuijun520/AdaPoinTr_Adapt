#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${MUG500PLUS_DATA_LOCK_DIR:?set MUG500PLUS_DATA_LOCK_DIR to the healthy125 data lock}"
: "${MUG500PLUS_SOURCE_ROOT:?set MUG500PLUS_SOURCE_ROOT to the healthy125 clear-STL root}"

MUG500PLUS_M2_PROTOCOL_DIR="${MUG500PLUS_M2_PROTOCOL_DIR:-logs/mamba_v13_d3_mug500plus/protocol_m2_v1}"
PROTOCOL_JSON="docs/mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json"

python -m py_compile \
  tools/generate_mug500plus_m2_synthetic_defects.py \
  tools/lock_mug500plus_m2_protocol.py \
  tools/test_mug500plus_m2_synthetic_defects.py

python tools/test_mug500plus_m2_synthetic_defects.py

python tools/lock_mug500plus_m2_protocol.py \
  --data_lock_dir "$MUG500PLUS_DATA_LOCK_DIR" \
  --source_root "$MUG500PLUS_SOURCE_ROOT" \
  --protocol_json "$PROTOCOL_JSON" \
  --output_dir "$MUG500PLUS_M2_PROTOCOL_DIR"

python tools/generate_mug500plus_m2_synthetic_defects.py \
  --data_lock_dir "$MUG500PLUS_DATA_LOCK_DIR" \
  --source_root "$MUG500PLUS_SOURCE_ROOT" \
  --protocol_json "$PROTOCOL_JSON" \
  --out_dir "${MUG500PLUS_M2_OUTPUT_DIR:-logs/mamba_v13_d3_mug500plus/m2_not_generated}" \
  --preflight_only

python tools/lock_mug500plus_m2_protocol.py \
  --data_lock_dir "$MUG500PLUS_DATA_LOCK_DIR" \
  --source_root "$MUG500PLUS_SOURCE_ROOT" \
  --protocol_json "$PROTOCOL_JSON" \
  --output_dir "$MUG500PLUS_M2_PROTOCOL_DIR"

echo "[ready] M2 protocol is immutable and healthy125 preflight passed"
echo "[locked] no synthetic case was generated"
echo "[locked] D3 training and MUG500+ protected validation remain inaccessible"
