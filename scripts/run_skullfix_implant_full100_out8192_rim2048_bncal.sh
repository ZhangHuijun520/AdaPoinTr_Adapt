#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="cfgs/SkullFix_models/AdaPoinTr_implant_full100_out8192_rim2048_bncal.yaml"
EXP_NAME="skullfix_implant_full100_out8192_rim2048_bncal"
EXP_DIR="experiments/AdaPoinTr_implant_full100_out8192_rim2048_bncal/SkullFix_models/${EXP_NAME}"
LOG_DIR="logs/skullfix_implant_point_count"
STAMP="$(date +%Y%m%d_%H%M%S)"
RESUME="${RESUME:-0}"

mkdir -p "$LOG_DIR"

train_args=(
  --config "$CONFIG"
  --exp_name "$EXP_NAME"
  --num_workers 4
  --val_freq 10
)
if [[ "$RESUME" == "1" ]]; then
  train_args+=(--resume)
fi

python main.py "${train_args[@]}" \
  2>&1 | tee "${LOG_DIR}/${EXP_NAME}_${STAMP}.log"

python tools/recalibrate_skullfix_batchnorm.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last.pth" \
  --output "${EXP_DIR}/ckpt-last-bncal.pth" \
  --batch_size 8 \
  --max_batches 10 \
  --num_workers 4

CONFIG="$CONFIG" \
SPLIT=test \
OUT_DIR="logs/skullfix_implant_point_count/full100_out8192_rim2048_bncal_test" \
SAVE_PREDICTIONS_DIR="logs/skullfix_implant_point_count/full100_out8192_rim2048_predictions_test" \
bash scripts/eval_skullfix_implant.sh "${EXP_DIR}/ckpt-last-bncal.pth"

CONFIG="$CONFIG" \
SPLIT=test \
NUM_SAMPLES=10 \
OUT_DIR="experiments/visualizations/skullfix_implant_full100_out8192_rim2048_bncal_test" \
bash scripts/visualize_skullfix_implant.sh "${EXP_DIR}/ckpt-last-bncal.pth"

echo "[done] $(date)"
