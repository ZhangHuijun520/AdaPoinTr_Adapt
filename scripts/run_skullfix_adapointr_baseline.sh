#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="${CONFIG:-cfgs/SkullFix_models/AdaPoinTr_baseline.yaml}"
EXP_NAME="${EXP_NAME:-skullfix_adapointr_baseline}"
NUM_WORKERS="${NUM_WORKERS:-4}"
VAL_FREQ="${VAL_FREQ:-10}"
LOG_DIR="${LOG_DIR:-logs/skullfix}"
EXP_DIR="experiments/$(basename "$CONFIG" .yaml)/$(basename "$(dirname "$CONFIG")")/$EXP_NAME"
mkdir -p "$LOG_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${EXP_NAME}_${STAMP}.log"
RESUME_ARGS=()
if [ -f "$EXP_DIR/ckpt-last.pth" ]; then
  RESUME_ARGS+=(--resume)
  echo "[resume] found $EXP_DIR/ckpt-last.pth" | tee "$LOG_FILE"
else
  echo "[resume] no checkpoint found; starting fresh" | tee "$LOG_FILE"
fi

python main.py \
  --config "$CONFIG" \
  --exp_name "$EXP_NAME" \
  --num_workers "$NUM_WORKERS" \
  --val_freq "$VAL_FREQ" \
  "${RESUME_ARGS[@]}" \
  2>&1 | tee -a "$LOG_FILE"
