#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OUTPUT_DIR="${MUG500_INVENTORY_DIR:-logs/mamba_v13_d3_mug500plus/inventory_figshare_v20}"
ARTICLE_JSON="${MUG500_ARTICLE_JSON:-}"
FILES_JSON="${MUG500_FILES_JSON:-}"

python -m py_compile \
  tools/inventory_mug500plus_figshare.py \
  tools/test_mug500plus_inventory.py

python tools/test_mug500plus_inventory.py

args=(
  --article_id 9616319
  --version 20
  --out_dir "$OUTPUT_DIR"
)

if [[ -n "$ARTICLE_JSON" ]]; then
  args+=(--article_json "$ARTICLE_JSON")
fi

if [[ -n "$FILES_JSON" ]]; then
  args+=(--files_json "$FILES_JSON")
fi

python tools/inventory_mug500plus_figshare.py "${args[@]}"

(
  cd "$OUTPUT_DIR"
  sha256sum -c files.sha256
)

echo "[done] MUG500+ Phase M0 official metadata inventory"
echo "[output] $OUTPUT_DIR"
echo "[locked] no archive payload was downloaded"
echo "[locked] do not admit A-series skulls before QC and duplicate audit"
echo "[locked] B-series craniotomy cases remain external-validation-only"
