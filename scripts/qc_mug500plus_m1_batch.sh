#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

: "${MUG500_STL_ROOT:?Set MUG500_STL_ROOT to the extracted A-series clear-STL root}"
: "${MUG500_EXPECTED_CASES:?Set MUG500_EXPECTED_CASES to a frozen batch expected-case list}"
: "${MUG500_QC_OUTPUT:?Set MUG500_QC_OUTPUT to a new batch-specific output directory}"

python tools/qc_mug500plus_clear_stl.py \
  --stl_root "$MUG500_STL_ROOT" \
  --expected_cases "$MUG500_EXPECTED_CASES" \
  --out_dir "$MUG500_QC_OUTPUT"

(
  cd "$MUG500_QC_OUTPUT"
  sha256sum -c files.sha256
)

echo "[done] MUG500+ M1 geometry-only QC"
echo "[locked] no model metric or B-series payload was accessed"
