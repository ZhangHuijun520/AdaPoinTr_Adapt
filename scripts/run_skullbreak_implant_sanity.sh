#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="cfgs/SkullBreak_models/AdaPoinTr_implant_sanity.yaml"
EXP_NAME="skullbreak_implant_sanity"
LOG_DIR="logs/skullbreak_implant"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

python main.py \
  --config "$CONFIG" \
  --exp_name "$EXP_NAME" \
  --num_workers 0 \
  --val_freq 1 \
  --seed 0 \
  --deterministic \
  2>&1 | tee "${LOG_DIR}/${EXP_NAME}_${STAMP}.log"

echo "[done] $(date)"
