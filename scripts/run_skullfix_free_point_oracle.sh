#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="${CONFIG:-cfgs/SkullFix_models/AdaPoinTr_identity_D_fpspreserve_nodenoise.yaml}"
CKPT="${CKPT:-experiments/AdaPoinTr_identity_D_fpspreserve_nodenoise/SkullFix_models/skullfix_identity_D_fpspreserve_nodenoise/ckpt-best.pth}"
STEPS="${STEPS:-2000}"
LR="${LR:-0.001}"
LOG_EVERY="${LOG_EVERY:-50}"
INIT_POINTS="${INIT_POINTS:-}"
ROOT_OUT="${ROOT_OUT:-logs/skullfix/free_point_oracle}"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$ROOT_OUT/oracle_${STAMP}"
LOG_FILE="$ROOT_OUT/oracle_${STAMP}.log"
mkdir -p "$ROOT_OUT"

if [ ! -f "$CKPT" ]; then
  echo "[error] checkpoint not found: $CKPT"
  exit 1
fi

INIT_ARGS=()
if [ -n "$INIT_POINTS" ]; then
  if [ ! -f "$INIT_POINTS" ]; then
    echo "[error] initial point file not found: $INIT_POINTS"
    exit 1
  fi
  INIT_ARGS=(--init_points "$INIT_POINTS")
fi

python tools/validate_stable_chamfer.py

python tools/run_skullfix_free_point_oracle.py \
  --config "$CONFIG" \
  --ckpt "$CKPT" \
  --steps "$STEPS" \
  --lr "$LR" \
  --log_every "$LOG_EVERY" \
  --out_dir "$OUT_DIR" \
  "${INIT_ARGS[@]}" \
  2>&1 | tee "$LOG_FILE"

echo "[done] $(date)"
echo "[output] $OUT_DIR"
echo "[log] $LOG_FILE"
