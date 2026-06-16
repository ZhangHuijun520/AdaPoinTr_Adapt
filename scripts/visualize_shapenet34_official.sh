#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

export MPLBACKEND="${MPLBACKEND:-Agg}"

CKPT="${1:-experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth}"
OUT_ROOT="${OUT_ROOT:-experiments/visualizations/shapenet34_official_full_4gpu}"
NUM_SAMPLES="${NUM_SAMPLES:-8}"

if [ ! -f "$CKPT" ]; then
  echo "[error] checkpoint not found: $CKPT" >&2
  exit 1
fi

python tools/visualize_shapenet34_completion.py \
  --config cfgs/ShapeNet34_models/AdaPoinTr.yaml \
  --ckpt "$CKPT" \
  --split seen \
  --mode hard \
  --num_samples "$NUM_SAMPLES" \
  --out_dir "$OUT_ROOT/seen_hard"

python tools/visualize_shapenet34_completion.py \
  --config cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml \
  --ckpt "$CKPT" \
  --split unseen \
  --mode hard \
  --num_samples "$NUM_SAMPLES" \
  --out_dir "$OUT_ROOT/unseen_hard"
