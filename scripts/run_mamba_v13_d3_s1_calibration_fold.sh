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

AUTH_DIR="logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_authorization_v1"
HOTFIX_DIR="logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_tensor_hash_hotfix1"
OUTPUT="logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_v1/fold${FOLD}_seed0"

python tools/run_mamba_v13_d3_s1_calibration_fold.py \
  --fold "$FOLD" \
  --authorization_dir "$AUTH_DIR" \
  --hotfix_dir "$HOTFIX_DIR" \
  --output_dir "$OUTPUT" \
  --num_workers "${NUM_WORKERS:-4}"

(cd "$OUTPUT" && sha256sum -c files.sha256)
echo "[done] S1 training-only gradient calibration fold=${FOLD}"
echo "[locked] no optimizer step, dev evaluation, holdout access, or training"
