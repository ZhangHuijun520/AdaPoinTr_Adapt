#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

LOG_DIR="${LOG_DIR:-logs/skullfix/identity_patch_local}"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="$LOG_DIR/identity_patch_local_${STAMP}.log"
exec > >(tee -a "$MASTER_LOG") 2>&1

D_CKPT="experiments/AdaPoinTr_identity_D_fpspreserve_nodenoise/SkullFix_models/skullfix_identity_D_fpspreserve_nodenoise/ckpt-best.pth"
if [ ! -f "$D_CKPT" ]; then
  echo "[error] Existing D checkpoint not found: $D_CKPT"
  exit 1
fi

python tools/validate_patch_local_loss.py

CONFIGS=(
  "cfgs/SkullFix_models/AdaPoinTr_identity_G_local05.yaml"
  "cfgs/SkullFix_models/AdaPoinTr_identity_H_local10.yaml"
)
EXP_NAMES=(
  "skullfix_identity_G_local05"
  "skullfix_identity_H_local10"
)

for index in "${!CONFIGS[@]}"; do
  config="${CONFIGS[$index]}"
  exp_name="${EXP_NAMES[$index]}"
  echo "================================================================"
  echo "[run] config=$config"
  echo "[run] exp_name=$exp_name"
  CONFIG="$config" \
  EXP_NAME="$exp_name" \
  NUM_WORKERS="${NUM_WORKERS:-0}" \
  VAL_FREQ="${VAL_FREQ:-25}" \
    bash scripts/run_skullfix_adapointr_identity_overfit.sh
done

python tools/summarize_skullfix_identity_patch_local.py \
  --out_json "$LOG_DIR/identity_patch_local_summary.json" \
  --out_csv "$LOG_DIR/identity_patch_local_summary.csv"

echo "[done] $(date)"
echo "[summary] $LOG_DIR/identity_patch_local_summary.json"
echo "[summary] $LOG_DIR/identity_patch_local_summary.csv"
