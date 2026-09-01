#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOCKS="${MUG500PLUS_D5_DATA_LOCK_ROOT:-$HOME/datasets/MUG500plusD5Development100_v1/data_locks}"
LOGS="${MAMBA_V15_D5_LOG_ROOT:-$ROOT/logs/mamba_v15_d5_contact_support}"
CONFIG_DIR="${MAMBA_V15_D5A_SEED0_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v15_d5a_seed0_authorized_v1}"
AUTH_DIR="${MAMBA_V15_D5A_SEED0_AUTH_DIR:-$LOGS/d5a_seed0_training_authorization_v1}"
FOURFOLD="${MUG500PLUS_D5_FOURFOLD_LOCK_DIR:-$LOCKS/mug500plus_d5_development400_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D5_GENERATION_AUDIT_DIR:-$LOGS/development_generation_audit_v1}"

cd "$ROOT"

python -m py_compile \
  tools/run_mamba_v15_d5a_seed0_training_fold.py \
  tools/freeze_mamba_v15_d5a_seed0_training.py

bash -n \
  scripts/preflight_mamba_v15_d5a_seed0_training.sh \
  scripts/run_mamba_v15_d5a_seed0_training_fold.sh \
  scripts/run_mamba_v15_d5a_seed0_training.sh \
  scripts/launch_mamba_v15_d5a_seed0_training_tmux.sh

python tools/test_mamba_v15_d5a_seed0_training_pipeline_contract.py
python tools/verify_mamba_v15_d5a_seed0_training_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_dir "$AUTH_DIR"

(
  cd "$FOURFOLD"
  sha256sum -c files.sha256 >/dev/null
)
(
  cd "$AUDIT"
  sha256sum -c files.sha256 >/dev/null
)

for candidate in V0 V1; do
  for fold in A B C D; do
    [[ -s "$CONFIG_DIR/MambaV15D5A_${candidate}_fold${fold}_seed0.json" ]]
  done
done

echo "[done] D5-A V0/V1 seed-0 training preflight passed"
echo "[authorized] future tmux launch may run V0 A-D then V1 A-D"
echo "[locked] this preflight used optimizer_steps=0 training=false dev=false"
echo "[locked] seed1=false confirmation=false D5B=false selection=false sealed=false"
