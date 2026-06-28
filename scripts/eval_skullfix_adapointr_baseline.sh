#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="${CONFIG:-cfgs/SkullFix_models/AdaPoinTr_baseline.yaml}"
EXP_NAME="${EXP_NAME:-skullfix_adapointr_baseline_eval}"
CKPT="${1:-experiments/AdaPoinTr_baseline/SkullFix_models/skullfix_adapointr_baseline/ckpt-best.pth}"
NUM_WORKERS="${NUM_WORKERS:-4}"
LOG_DIR="${LOG_DIR:-logs/skullfix}"
mkdir -p "$LOG_DIR"

if [ ! -f "$CKPT" ]; then
  echo "[error] checkpoint not found: $CKPT" >&2
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${EXP_NAME}_${STAMP}.log"

python main.py \
  --test \
  --config "$CONFIG" \
  --ckpts "$CKPT" \
  --exp_name "$EXP_NAME" \
  --num_workers "$NUM_WORKERS" \
  2>&1 | tee "$LOG_FILE"
