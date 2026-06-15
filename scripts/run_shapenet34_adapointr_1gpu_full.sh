#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="${CONFIG:-cfgs/ShapeNet34_models/AdaPoinTr_1gpu_full.yaml}"
EXP_NAME="${EXP_NAME:-shapenet34_adapointr_1gpu_full}"
NUM_WORKERS="${NUM_WORKERS:-4}"
VAL_FREQ="${VAL_FREQ:-10}"
LOG_DIR="${LOG_DIR:-logs/shapenet34_full}"
mkdir -p "$LOG_DIR"

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${EXP_NAME}_${STAMP}.log"

echo "[start] $(date)" | tee "$LOG_FILE"
echo "[root] $(pwd)" | tee -a "$LOG_FILE"
echo "[config] $CONFIG" | tee -a "$LOG_FILE"
echo "[exp] $EXP_NAME" | tee -a "$LOG_FILE"
echo "[env] $CONDA_DEFAULT_ENV" | tee -a "$LOG_FILE"
nvidia-smi 2>&1 | tee -a "$LOG_FILE" || true

python main.py \
  --config "$CONFIG" \
  --exp_name "$EXP_NAME" \
  --num_workers "$NUM_WORKERS" \
  --val_freq "$VAL_FREQ" \
  2>&1 | tee -a "$LOG_FILE"

echo "[done] $(date)" | tee -a "$LOG_FILE"
