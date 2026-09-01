#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
CANDIDATE="${1:?Pass candidate V0 or V1}"
FOLD="${2:?Pass fold A, B, C, or D}"
[[ "$CANDIDATE" =~ ^V[01]$ ]] || { echo "[error] invalid candidate: $CANDIDATE"; exit 2; }
[[ "$FOLD" =~ ^[A-D]$ ]] || { echo "[error] invalid fold: $FOLD"; exit 2; }

LOCKS="${MUG500PLUS_D5_DATA_LOCK_ROOT:-$HOME/datasets/MUG500plusD5Development100_v1/data_locks}"
LOGS="${MAMBA_V15_D5_LOG_ROOT:-$ROOT/logs/mamba_v15_d5_contact_support}"
CONFIG_DIR="${MAMBA_V15_D5A_SEED0_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v15_d5a_seed0_authorized_v1}"
AUTH_DIR="${MAMBA_V15_D5A_SEED0_AUTH_DIR:-$LOGS/d5a_seed0_training_authorization_v1}"
FOURFOLD="${MUG500PLUS_D5_FOURFOLD_LOCK_DIR:-$LOCKS/mug500plus_d5_development400_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D5_GENERATION_AUDIT_DIR:-$LOGS/development_generation_audit_v1}"
OUTPUT_ROOT="${MAMBA_V15_D5A_SEED0_FOLD_ROOT:-$LOGS/d5a_seed0_head_only_v1}"

cd "$ROOT"

echo "[D5-A] candidate=${CANDIDATE} fold=${FOLD} seed=0 epochs=50 head-only"
echo "[locked] dev opens only after 1900 optimizer steps"

python -u tools/run_mamba_v15_d5a_seed0_training_fold.py \
  --candidate "$CANDIDATE" \
  --fold "$FOLD" \
  --config "$CONFIG_DIR/MambaV15D5A_${CANDIDATE}_fold${FOLD}_seed0.json" \
  --authorization_dir "$AUTH_DIR" \
  --fourfold_lock_dir "$FOURFOLD" \
  --generation_audit_dir "$AUDIT" \
  --output_dir "$OUTPUT_ROOT/${CANDIDATE}_fold${FOLD}_seed0"

echo "[done] D5-A ${CANDIDATE}/fold${FOLD} seed=0 $(date -u --iso-8601=seconds)"
echo "[locked] seed1=false confirmation=false D5B=false selection=false sealed=false"
