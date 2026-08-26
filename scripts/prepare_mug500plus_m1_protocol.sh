#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FILES_JSON="${MUG500_FILES_JSON:-$HOME/mug500plus_files_v20.json}"
OUTPUT_DIR="${MUG500_M1_PROTOCOL_DIR:-logs/mamba_v13_d3_mug500plus/protocol_m1_v1}"
EXPECTED_SHA256="f475490611f5d17536bbf76a0f7db0693a668fd3e87e8502ec395db6b461a078"

[[ -f "$FILES_JSON" ]] || {
  echo "[error] missing official Figshare files snapshot: $FILES_JSON"
  exit 1
}

python -m py_compile \
  tools/plan_mug500plus_m1_acquisition.py \
  tools/qc_mug500plus_clear_stl.py \
  tools/test_mug500plus_m1_acquisition.py \
  tools/test_mug500plus_m1_qc.py

python tools/test_mug500plus_m1_acquisition.py
python tools/test_mug500plus_m1_qc.py

python tools/plan_mug500plus_m1_acquisition.py \
  --files_json "$FILES_JSON" \
  --files_json_sha256 "$EXPECTED_SHA256" \
  --out_dir "$OUTPUT_DIR" \
  --batch_target_skulls 40 \
  --minimum_qc_pass_skulls 125

(
  cd "$OUTPUT_DIR"
  sha256sum -c files.sha256
)

echo "[done] MUG500+ M1 acquisition and QC protocol is frozen"
echo "[output] $OUTPUT_DIR"
echo "[next] download only batch_001_downloads.csv on the local D drive"
echo "[locked] no payload was downloaded and D3 training remains disabled"
echo "[locked] craniotomy/B-series data remains external-validation-only"
