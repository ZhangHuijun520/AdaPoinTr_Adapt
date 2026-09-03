#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
PREFLIGHT="${MAMBA_V16_D6A_CALIBRATION_PREFLIGHT_DIR:-$LOGS/d6a_gradient_calibration_execution_preflight_v1}"
FOLD_ROOT="${MAMBA_V16_D6A_CALIBRATION_FOLD_ROOT:-$LOGS/d6a_gradient_calibration_seed0_v1}"
COMPLETION="${MAMBA_V16_D6A_CALIBRATION_COMPLETION_DIR:-$LOGS/d6a_gradient_calibration_completion_v1}"

cd "$ROOT"
(
  cd "$PREFLIGHT"
  sha256sum -c files.sha256
)
for fold in A B C D; do
  bash scripts/run_mamba_v16_d6a_gradient_calibration_fold.sh "$fold"
done
python tools/freeze_mamba_v16_d6a_gradient_calibration.py \
  --fold_root "$FOLD_ROOT" --output_dir "$COMPLETION"
(
  cd "$COMPLETION"
  sha256sum -c files.sha256
)
echo "[done] D6-A R1 gradient calibration folds A-D frozen"
echo "[locked] seed0 training was not started; seed1=false confirmation=false D6B=false sealed=false"
