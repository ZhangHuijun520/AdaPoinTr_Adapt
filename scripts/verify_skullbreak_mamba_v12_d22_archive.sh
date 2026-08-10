#!/usr/bin/env bash
set -euo pipefail

RESTORE_ROOT="${1:-.}"
cd "$RESTORE_ROOT"

required_metadata=(
  "metadata/README.txt"
  "metadata/ARCHIVE_PATHS.txt"
  "metadata/MANIFEST.sha256"
  "metadata/CHECKPOINTS.sha256"
  "metadata/runtime_environment.txt"
  "metadata/python_runtime.txt"
  "metadata/pip_freeze.txt"
  "metadata/conda_list.txt"
  "metadata/skullbreak_out8192_manifest.jsonl"
)

for path in "${required_metadata[@]}"; do
  if [[ ! -s "$path" ]]; then
    echo "[error] required archive metadata is missing or empty: $path" >&2
    exit 1
  fi
done

echo "[verify] selected payload SHA256"
sha256sum -c metadata/MANIFEST.sha256

echo "[verify] 12 canonical BNCal checkpoints"
sha256sum -c metadata/CHECKPOINTS.sha256

echo "[verify] D2.2 frozen semantics and post-hoc integrity"
python tools/verify_mamba_v12_d22_archive_payload.py --root .

echo "[ok] D2.2 archive contents, hashes, and frozen semantics are valid"
echo "[locked] winner=None; Round B remains forbidden"
echo "[locked] confirmation20, old monitor, and official test remain unused"
