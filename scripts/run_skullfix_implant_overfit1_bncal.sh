#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="cfgs/SkullFix_models/AdaPoinTr_implant_overfit1_bncal.yaml"
EXP_NAME="skullfix_implant_overfit1_bncal"
EXP_DIR="experiments/AdaPoinTr_implant_overfit1_bncal/SkullFix_models/${EXP_NAME}"
LOG_DIR="logs/skullfix_implant"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$LOG_DIR"

python main.py \
  --config "$CONFIG" \
  --exp_name "$EXP_NAME" \
  --num_workers 0 \
  --val_freq 25 \
  2>&1 | tee "${LOG_DIR}/${EXP_NAME}_${STAMP}.log"

python tools/recalibrate_skullfix_batchnorm.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last.pth" \
  --output "${EXP_DIR}/ckpt-last-bncal.pth" \
  --batch_size 8 \
  --max_batches 1

CONFIG="$CONFIG" \
SPLIT=test \
OUT_DIR="logs/skullfix_implant_eval/overfit1_bncal" \
bash scripts/eval_skullfix_implant.sh "${EXP_DIR}/ckpt-last-bncal.pth"

echo "[done] $(date)"
