#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

RAW_ROOT="${RAW_ROOT:-$HOME/datasets/SkullFixRaw}"
OUT_ROOT="${OUT_ROOT:-$HOME/datasets/SkullFixPC_out8192}"
SEED="${SEED:-20260708}"
SPLIT="${SPLIT:-0.8,0.1,0.1}"

python tools/prepare_skullfix_pointcloud.py \
  --input_root "$RAW_ROOT" \
  --output_root "$OUT_ROOT" \
  --n_partial 8192 \
  --n_complete 8192 \
  --n_implant 8192 \
  --seed "$SEED" \
  --split "$SPLIT" \
  --normalization_source defective \
  --strict_geometry \
  --overwrite

mkdir -p data
if [[ -e data/SkullFixPC_out8192 && ! -L data/SkullFixPC_out8192 ]]; then
  echo "[error] data/SkullFixPC_out8192 exists and is not a symlink" >&2
  exit 1
fi
ln -sfn "$OUT_ROOT" data/SkullFixPC_out8192
python tools/check_skullfix_pointcloud.py --data_root "$OUT_ROOT"
