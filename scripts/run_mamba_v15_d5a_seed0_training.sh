#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V15_D5_LOG_ROOT:-$ROOT/logs/mamba_v15_d5_contact_support}"
AUTH_DIR="${MAMBA_V15_D5A_SEED0_AUTH_DIR:-$LOGS/d5a_seed0_training_authorization_v1}"
FOLD_ROOT="${MAMBA_V15_D5A_SEED0_FOLD_ROOT:-$LOGS/d5a_seed0_head_only_v1}"
COMPLETION="${MAMBA_V15_D5A_SEED0_COMPLETION_DIR:-$LOGS/d5a_seed0_training_completion_v1}"

cd "$ROOT"
bash scripts/preflight_mamba_v15_d5a_seed0_training.sh

for candidate in V0 V1; do
  for fold in A B C D; do
    bash scripts/run_mamba_v15_d5a_seed0_training_fold.sh "$candidate" "$fold"
  done
done

python tools/freeze_mamba_v15_d5a_seed0_training.py \
  --fold_root "$FOLD_ROOT" \
  --authorization_dir "$AUTH_DIR" \
  --output_dir "$COMPLETION"

(
  cd "$COMPLETION"
  sha256sum -c files.sha256
)

echo "[done] D5-A V0/V1 seed-0 folds A-D trained and frozen"
echo "[locked] no automatic seed-1, confirmation, D5-B, or candidate selection"
echo "[next] inspect the D5-A seed-0 all-case completion receipt"
