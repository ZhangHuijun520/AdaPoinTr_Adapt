#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
export MPLBACKEND="${MPLBACKEND:-Agg}"

CONFIG="${CONFIG:-cfgs/SkullBreak_models/AdaPoinTr_implant_small75_bncal.yaml}"
CKPT="${1:?Pass a checkpoint path as the first argument}"
SPLIT="${SPLIT:-test}"
NUM_SAMPLES="${NUM_SAMPLES:-10}"
OUT_DIR="${OUT_DIR:-experiments/visualizations/skullbreak_implant}"

python tools/visualize_skullfix_implant.py \
  --config "$CONFIG" \
  --ckpt "$CKPT" \
  --split "$SPLIT" \
  --num_samples "$NUM_SAMPLES" \
  --out_dir "$OUT_DIR"
