#!/usr/bin/env bash
set -euo pipefail

RESTORE_ROOT="${1:-.}"

cd "$RESTORE_ROOT"

if [ ! -f metadata/MANIFEST.sha256 ]; then
  echo "[error] metadata/MANIFEST.sha256 was not found." >&2
  echo "Extract the baseline archive first, then run this script from its root." >&2
  exit 1
fi

echo "[verify] checking archived experiment files"
sha256sum --check metadata/MANIFEST.sha256

required_paths=(
  "experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth"
  "experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-last.pth"
  "cfgs/ShapeNet34_models/AdaPoinTr.yaml"
  "cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml"
  "logs/shapenet34_official_4gpu"
  "logs/shapenet34_official_eval"
  "experiments/visualizations/shapenet34_official_full_4gpu"
  "metadata/code_snapshot.tar.gz"
)

for path in "${required_paths[@]}"; do
  if [ ! -e "$path" ]; then
    echo "[error] required restored path is missing: $path" >&2
    exit 1
  fi
done

echo "[ok] baseline archive contents and checksums are valid"
echo "[info] raw ShapeNet55-34 data is intentionally not included"
