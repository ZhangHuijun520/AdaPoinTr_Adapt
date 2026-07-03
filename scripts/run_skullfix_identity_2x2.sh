#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

LOG_DIR="${LOG_DIR:-logs/skullfix/identity_2x2}"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="$LOG_DIR/identity_2x2_${STAMP}.log"
exec > >(tee -a "$MASTER_LOG") 2>&1

A_CKPT="experiments/AdaPoinTr_identity_overfit_controlled/SkullFix_models/skullfix_adapointr_identity_overfit/ckpt-best.pth"
if [ ! -f "$A_CKPT" ]; then
  echo "[error] Existing A checkpoint not found: $A_CKPT"
  echo "Run the original controlled identity overfit before this comparison."
  exit 1
fi

CONFIGS=(
  "cfgs/SkullFix_models/AdaPoinTr_identity_B_nodenoise.yaml"
  "cfgs/SkullFix_models/AdaPoinTr_identity_C_fpspreserve_denoise.yaml"
  "cfgs/SkullFix_models/AdaPoinTr_identity_D_fpspreserve_nodenoise.yaml"
)
EXP_NAMES=(
  "skullfix_identity_B_nodenoise"
  "skullfix_identity_C_fpspreserve_denoise"
  "skullfix_identity_D_fpspreserve_nodenoise"
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

python tools/summarize_skullfix_identity_2x2.py \
  --out_json "$LOG_DIR/identity_2x2_summary.json" \
  --out_csv "$LOG_DIR/identity_2x2_summary.csv"

echo "[done] $(date)"
echo "[summary] $LOG_DIR/identity_2x2_summary.json"
echo "[summary] $LOG_DIR/identity_2x2_summary.csv"
