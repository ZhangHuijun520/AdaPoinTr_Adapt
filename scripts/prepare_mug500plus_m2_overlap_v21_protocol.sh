#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${MUG500PLUS_OVERLAP_V2_DIR:?set MUG500PLUS_OVERLAP_V2_DIR to the frozen v2 audit directory}"

MUG500PLUS_OVERLAP_V21_PROTOCOL_DIR="${MUG500PLUS_OVERLAP_V21_PROTOCOL_DIR:-logs/mamba_v13_d3_mug500plus/protocol_overlap_v21}"
PROTOCOL_JSON="docs/mamba_v13_d3_mug500plus_phase_m2_overlap_audit_protocol_v21.json"
PROVENANCE_JSON="docs/mug500plus_skullbreak_skullfix_source_provenance_v1.json"

python -m py_compile \
  tools/lock_mug500plus_m2_overlap_v21_protocol.py \
  tools/test_mug500plus_m2_overlap_v21_protocol.py

python tools/test_mug500plus_m2_overlap_v21_protocol.py

python tools/lock_mug500plus_m2_overlap_v21_protocol.py \
  --v2_audit_dir "$MUG500PLUS_OVERLAP_V2_DIR" \
  --protocol_json "$PROTOCOL_JSON" \
  --provenance_json "$PROVENANCE_JSON" \
  --output_dir "$MUG500PLUS_OVERLAP_V21_PROTOCOL_DIR"

python tools/lock_mug500plus_m2_overlap_v21_protocol.py \
  --v2_audit_dir "$MUG500PLUS_OVERLAP_V2_DIR" \
  --protocol_json "$PROTOCOL_JSON" \
  --provenance_json "$PROVENANCE_JSON" \
  --output_dir "$MUG500PLUS_OVERLAP_V21_PROTOCOL_DIR"

echo "[ready] source-stratified + provenance v2.1 protocol is immutable"
echo "[locked] adjudication has not started"
echo "[locked] 100/25 data lock and D3 training remain disabled"
