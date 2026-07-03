#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

LOG_DIR="${LOG_DIR:-logs/skullfix/identity_directional}"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="$LOG_DIR/identity_directional_${STAMP}.log"
exec > >(tee -a "$MASTER_LOG") 2>&1

D_CKPT="experiments/AdaPoinTr_identity_D_fpspreserve_nodenoise/SkullFix_models/skullfix_identity_D_fpspreserve_nodenoise/ckpt-best.pth"
if [ ! -f "$D_CKPT" ]; then
  echo "[error] Existing D checkpoint not found: $D_CKPT"
  exit 1
fi

python tools/validate_directional_chamfer.py

CONFIGS=(
  "cfgs/SkullFix_models/AdaPoinTr_identity_E_coverage2.yaml"
  "cfgs/SkullFix_models/AdaPoinTr_identity_F_coverage4.yaml"
)
EXP_NAMES=(
  "skullfix_identity_E_coverage2"
  "skullfix_identity_F_coverage4"
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

python tools/summarize_skullfix_identity_directional.py \
  --out_json "$LOG_DIR/identity_directional_summary.json" \
  --out_csv "$LOG_DIR/identity_directional_summary.csv"

echo "[done] $(date)"
echo "[summary] $LOG_DIR/identity_directional_summary.json"
echo "[summary] $LOG_DIR/identity_directional_summary.csv"
