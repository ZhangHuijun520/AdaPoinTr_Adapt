#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="cfgs/SkullFix_models/AdaPoinTr_implant_small_bncal.yaml"
EXP_NAME="skullfix_implant_small_bncal"
EXP_DIR="experiments/AdaPoinTr_implant_small_bncal/SkullFix_models/${EXP_NAME}"
LOG_DIR="logs/skullfix_implant"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$LOG_DIR"

python main.py \
  --config "$CONFIG" \
  --exp_name "$EXP_NAME" \
  --num_workers 2 \
  --val_freq 1 \
  2>&1 | tee "${LOG_DIR}/${EXP_NAME}_${STAMP}.log"

python tools/recalibrate_skullfix_batchnorm.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last.pth" \
  --output "${EXP_DIR}/ckpt-last-bncal.pth" \
  --batch_size 4 \
  --max_batches 4 \
  --num_workers 2

for split in val test; do
  CONFIG="$CONFIG" \
  SPLIT="$split" \
  OUT_DIR="logs/skullfix_implant_eval/small_bncal_${split}" \
  bash scripts/eval_skullfix_implant.sh "${EXP_DIR}/ckpt-last-bncal.pth"
done

echo "[done] $(date)"
