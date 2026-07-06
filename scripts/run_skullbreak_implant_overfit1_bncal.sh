#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="cfgs/SkullBreak_models/AdaPoinTr_implant_overfit1_bncal.yaml"
EXP_NAME="skullbreak_implant_overfit1_bncal"
EXP_DIR="experiments/AdaPoinTr_implant_overfit1_bncal/SkullBreak_models/${EXP_NAME}"
LOG_DIR="logs/skullbreak_implant"
STAMP="$(date +%Y%m%d_%H%M%S)"
RESUME="${RESUME:-0}"
mkdir -p "$LOG_DIR"

train_args=(
  --config "$CONFIG"
  --exp_name "$EXP_NAME"
  --num_workers 0
  --val_freq 25
  --seed 0
  --deterministic
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
  --max_batches 1 \
  --num_workers 0

CONFIG="$CONFIG" \
SPLIT=test \
OUT_DIR="logs/skullbreak_implant_eval/overfit1_bncal" \
bash scripts/eval_skullbreak_implant.sh "${EXP_DIR}/ckpt-last-bncal.pth"

CONFIG="$CONFIG" \
SPLIT=test \
NUM_SAMPLES=1 \
OUT_DIR="experiments/visualizations/skullbreak_implant_overfit1_bncal" \
bash scripts/visualize_skullbreak_implant.sh \
  "${EXP_DIR}/ckpt-last-bncal.pth"

echo "[done] $(date)"
