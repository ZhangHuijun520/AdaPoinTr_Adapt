#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${MUG500PLUS_M1_DATA_LOCK_DIR:?set MUG500PLUS_M1_DATA_LOCK_DIR}"
: "${MUG500PLUS_M2_AUDIT_DIR:?set MUG500PLUS_M2_AUDIT_DIR}"
: "${MUG500PLUS_OVERLAP_V21_ADJUDICATION_DIR:?set MUG500PLUS_OVERLAP_V21_ADJUDICATION_DIR}"
: "${MUG500PLUS_M2_SOURCE_SPLIT_LOCK_DIR:?set MUG500PLUS_M2_SOURCE_SPLIT_LOCK_DIR}"

python -m py_compile \
  tools/lock_mug500plus_m2_source_split_v1.py \
  tools/test_mug500plus_m2_source_split_v1.py

python tools/test_mug500plus_m2_source_split_v1.py

args=(
  --m1_data_lock_dir "$MUG500PLUS_M1_DATA_LOCK_DIR"
  --m2_audit_dir "$MUG500PLUS_M2_AUDIT_DIR"
  --v21_adjudication_dir "$MUG500PLUS_OVERLAP_V21_ADJUDICATION_DIR"
  --output_dir "$MUG500PLUS_M2_SOURCE_SPLIT_LOCK_DIR"
  --protocol_json docs/mamba_v13_d3_mug500plus_m2_source_split_100_25_protocol_v1.json
)

python tools/lock_mug500plus_m2_source_split_v1.py "${args[@]}"
python tools/lock_mug500plus_m2_source_split_v1.py "${args[@]}"

echo "[done] immutable MUG500+ M2 100/25 source-skull data lock"
echo "[locked] holdout inference, metrics, and visual review were not consumed"
echo "[locked] D3 training remains a separate preregistered step"
