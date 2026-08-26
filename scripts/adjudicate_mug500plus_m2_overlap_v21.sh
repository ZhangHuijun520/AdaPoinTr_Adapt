#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${MUG500PLUS_OVERLAP_V2_DIR:?set MUG500PLUS_OVERLAP_V2_DIR to the frozen v2 audit directory}"

MUG500PLUS_OVERLAP_V21_PROTOCOL_DIR="${MUG500PLUS_OVERLAP_V21_PROTOCOL_DIR:-$(dirname "$MUG500PLUS_OVERLAP_V2_DIR")/protocol_overlap_v21}"
MUG500PLUS_OVERLAP_V21_ADJUDICATION_DIR="${MUG500PLUS_OVERLAP_V21_ADJUDICATION_DIR:-$(dirname "$MUG500PLUS_OVERLAP_V2_DIR")/protected_overlap_adjudication_v21}"

python -m py_compile \
  tools/adjudicate_mug500plus_m2_overlap_v21.py \
  tools/test_mug500plus_m2_overlap_v21_adjudicator.py

python tools/test_mug500plus_m2_overlap_v21_adjudicator.py

python tools/adjudicate_mug500plus_m2_overlap_v21.py \
  --v2_audit_dir "$MUG500PLUS_OVERLAP_V2_DIR" \
  --protocol_lock_dir "$MUG500PLUS_OVERLAP_V21_PROTOCOL_DIR" \
  --output_dir "$MUG500PLUS_OVERLAP_V21_ADJUDICATION_DIR"

python tools/adjudicate_mug500plus_m2_overlap_v21.py \
  --v2_audit_dir "$MUG500PLUS_OVERLAP_V2_DIR" \
  --protocol_lock_dir "$MUG500PLUS_OVERLAP_V21_PROTOCOL_DIR" \
  --output_dir "$MUG500PLUS_OVERLAP_V21_ADJUDICATION_DIR"

echo "[done] frozen-table-only v2.1 adjudication completed"
echo "[locked] inspect the receipt before creating the separate 100/25 data lock"
echo "[locked] D3 training was not started"
