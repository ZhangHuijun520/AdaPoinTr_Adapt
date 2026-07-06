#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="cfgs/SkullBreak_models/AdaPoinTr_implant_small75_bncal.yaml"
EXP_NAME="skullbreak_implant_small75_bncal"
EXP_DIR="experiments/AdaPoinTr_implant_small75_bncal/SkullBreak_models/${EXP_NAME}"
LOG_DIR="logs/skullbreak_implant"
STAMP="$(date +%Y%m%d_%H%M%S)"
RESUME="${RESUME:-0}"
mkdir -p "$LOG_DIR"

train_args=(
  --config "$CONFIG"
  --exp_name "$EXP_NAME"
  --num_workers 4
  --val_freq 5
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
  --batch_size 4 \
  --max_batches 10 \
  --num_workers 4

for split in val test; do
  CONFIG="$CONFIG" \
  SPLIT="$split" \
  OUT_DIR="logs/skullbreak_implant_eval/small75_bncal_${split}" \
  bash scripts/eval_skullbreak_implant.sh \
    "${EXP_DIR}/ckpt-last-bncal.pth"
done

CONFIG="$CONFIG" \
SPLIT=test \
NUM_SAMPLES=10 \
OUT_DIR="experiments/visualizations/skullbreak_implant_small75_bncal" \
bash scripts/visualize_skullbreak_implant.sh \
  "${EXP_DIR}/ckpt-last-bncal.pth"

echo "[done] $(date)"
