#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
export MPLBACKEND="${MPLBACKEND:-Agg}"

CONFIG="${CONFIG:-cfgs/SkullFix_models/AdaPoinTr_baseline.yaml}"
CKPT="${1:-experiments/AdaPoinTr_baseline/SkullFix_models/skullfix_adapointr_baseline/ckpt-best.pth}"
OUT_DIR="${OUT_DIR:-experiments/visualizations/skullfix_adapointr_baseline}"
NUM_SAMPLES="${NUM_SAMPLES:-8}"

python tools/visualize_skullfix_completion.py \
  --config "$CONFIG" \
  --ckpt "$CKPT" \
  --num_samples "$NUM_SAMPLES" \
  --out_dir "$OUT_DIR"
