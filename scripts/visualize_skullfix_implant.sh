#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
export MPLBACKEND="${MPLBACKEND:-Agg}"

CONFIG="${CONFIG:-cfgs/SkullFix_models/AdaPoinTr_implant_small.yaml}"
CKPT="${1:-experiments/AdaPoinTr_implant_small/SkullFix_models/skullfix_implant_small/ckpt-best.pth}"
SPLIT="${SPLIT:-test}"
NUM_SAMPLES="${NUM_SAMPLES:-4}"
OUT_DIR="${OUT_DIR:-experiments/visualizations/skullfix_implant_small}"

python tools/visualize_skullfix_implant.py \
  --config "$CONFIG" \
  --ckpt "$CKPT" \
  --split "$SPLIT" \
  --num_samples "$NUM_SAMPLES" \
  --out_dir "$OUT_DIR"
