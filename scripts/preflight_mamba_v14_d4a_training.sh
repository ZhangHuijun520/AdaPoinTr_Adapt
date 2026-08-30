#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
CONFIG_DIR="${MAMBA_V14_D4A_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v14_d4a_seed0_authorized_v1}"
AUTH_DIR="${MAMBA_V14_D4A_AUTH_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_training_authorization_v1}"
FOURFOLD_LOCK="${MUG500PLUS_D4_M2_FOURFOLD_LOCK_DIR:-$HOME/datasets/MUG500plusD4Source100_v1/data_locks/mug500plus_d4_m2_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D4_GENERATION_AUDIT_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4_m2_generation_audit_v1}"

cd "$ROOT"

python -m py_compile \
  tools/run_mamba_v14_d4a_training_fold.py \
  tools/freeze_mamba_v14_d4a_training.py

bash -n \
  scripts/preflight_mamba_v14_d4a_training.sh \
  scripts/run_mamba_v14_d4a_training_fold.sh \
  scripts/run_mamba_v14_d4a_training.sh \
  scripts/launch_mamba_v14_d4a_training_tmux.sh

python tools/test_mamba_v14_d4a_training_pipeline_contract.py
python tools/verify_mamba_v14_d4a_training_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_dir "$AUTH_DIR"

[[ -d "$FOURFOLD_LOCK" && -s "$FOURFOLD_LOCK/files.sha256" ]]
[[ -d "$AUDIT" && -s "$AUDIT/files.sha256" ]]

(
  cd "$FOURFOLD_LOCK"
  sha256sum -c files.sha256 >/dev/null
)
(
  cd "$AUDIT"
  sha256sum -c files.sha256 >/dev/null
)

for fold in A B C D; do
  [[ -s "$CONFIG_DIR/MambaV14D4A_fold${fold}_seed0.json" ]]
done

echo "[done] D4-A training preflight passed"
echo "[authorized] launch D4-A head-only folds A-D in tmux"
echo "[locked] T0=false T1=false T2=false selection=false protected=false"
