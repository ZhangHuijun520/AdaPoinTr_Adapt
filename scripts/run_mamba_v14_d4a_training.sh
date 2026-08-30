#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
AUTH_DIR="${MAMBA_V14_D4A_AUTH_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_training_authorization_v1}"
FOLD_ROOT="${MAMBA_V14_D4A_FOLD_ROOT:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_head_only_seed0_v1}"
COMPLETION="${MAMBA_V14_D4A_COMPLETION_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_training_completion_v1}"

cd "$ROOT"
bash scripts/preflight_mamba_v14_d4a_training.sh

for fold in A B C D; do
  bash scripts/run_mamba_v14_d4a_training_fold.sh "$fold"
done

python tools/freeze_mamba_v14_d4a_training.py \
  --fold_root "$FOLD_ROOT" \
  --authorization_dir "$AUTH_DIR" \
  --output_dir "$COMPLETION"

(
  cd "$COMPLETION"
  sha256sum -c files.sha256
)

echo "[done] D4-A seed-0 folds A-D trained and frozen"
echo "[locked] no automatic T0/T1/T2 training or candidate selection"
echo "[next] inspect the D4-A all-case completion receipt"
