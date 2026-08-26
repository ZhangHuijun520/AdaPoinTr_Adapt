#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

FOLD="${1:?Pass fold A, B, C, or D}"
[[ "$FOLD" =~ ^[A-D]$ ]] || { echo "[error] invalid fold: $FOLD"; exit 2; }

LOCK_DIR="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1"
HOTFIX_DIR="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_hotfix1"
OUTPUT="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_v1/fold${FOLD}_seed0"

echo "[D3 feasibility] candidate=S2-head-only fold=${FOLD} seed=0"
echo "[locked] S0 encoder eval/frozen; one dev evaluation after epoch 50"

python tools/run_mamba_v13_d3_s2_feasibility_fold.py \
  --fold "$FOLD" \
  --lock_dir "$LOCK_DIR" \
  --hotfix_dir "$HOTFIX_DIR" \
  --output_dir "$OUTPUT" \
  --num_workers "${NUM_WORKERS:-4}"

echo "[done] S2 head-only feasibility fold=${FOLD} $(date -u --iso-8601=seconds)"
echo "[locked] no holdout access and no selection"
