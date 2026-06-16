#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="${CONFIG:-cfgs/ShapeNet34_models/AdaPoinTr.yaml}"
EXP_NAME="${EXP_NAME:-shapenet34_adapointr_official_full_4gpu}"
NPROC_PER_NODE="${NPROC_PER_NODE:-4}"
NUM_WORKERS="${NUM_WORKERS:-4}"
VAL_FREQ="${VAL_FREQ:-10}"
LOG_DIR="${LOG_DIR:-logs/shapenet34_official_4gpu}"
mkdir -p "$LOG_DIR"

EXP_DIR="experiments/$(basename "$CONFIG" .yaml)/$(basename "$(dirname "$CONFIG")")/$EXP_NAME"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${EXP_NAME}_${STAMP}.log"
RESUME_ARGS=()

if [ -f "$EXP_DIR/ckpt-last.pth" ]; then
  RESUME_ARGS+=(--resume)
  echo "[resume] found $EXP_DIR/ckpt-last.pth" | tee "$LOG_FILE"
else
  echo "[resume] no checkpoint found; starting fresh" | tee "$LOG_FILE"
fi

echo "[start] $(date)" | tee -a "$LOG_FILE"
echo "[root] $(pwd)" | tee -a "$LOG_FILE"
echo "[config] $CONFIG" | tee -a "$LOG_FILE"
echo "[exp] $EXP_NAME" | tee -a "$LOG_FILE"
echo "[gpus] $NPROC_PER_NODE" | tee -a "$LOG_FILE"
echo "[env] $CONDA_DEFAULT_ENV" | tee -a "$LOG_FILE"
nvidia-smi 2>&1 | tee -a "$LOG_FILE" || true

torchrun \
  --standalone \
  --nproc_per_node="$NPROC_PER_NODE" \
  main.py \
  --launcher pytorch \
  --config "$CONFIG" \
  --exp_name "$EXP_NAME" \
  --num_workers "$NUM_WORKERS" \
  --val_freq "$VAL_FREQ" \
  "${RESUME_ARGS[@]}" \
  2>&1 | tee -a "$LOG_FILE"

echo "[done] $(date)" | tee -a "$LOG_FILE"
