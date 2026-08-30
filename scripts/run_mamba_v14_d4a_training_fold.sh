#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
FOLD="${1:?Pass fold A, B, C, or D}"
[[ "$FOLD" =~ ^[A-D]$ ]] || { echo "[error] invalid fold: $FOLD"; exit 2; }

CONFIG_DIR="${MAMBA_V14_D4A_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v14_d4a_seed0_authorized_v1}"
AUTH_DIR="${MAMBA_V14_D4A_AUTH_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_training_authorization_v1}"
FOURFOLD_LOCK="${MUG500PLUS_D4_M2_FOURFOLD_LOCK_DIR:-$HOME/datasets/MUG500plusD4Source100_v1/data_locks/mug500plus_d4_m2_fourfold_protocol_lock_v1}"
AUDIT="${MUG500PLUS_D4_GENERATION_AUDIT_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4_m2_generation_audit_v1}"
OUTPUT_ROOT="${MAMBA_V14_D4A_FOLD_ROOT:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_head_only_seed0_v1}"

cd "$ROOT"

echo "[D4-A] fold=${FOLD} seed=0 epochs=50 head-only"
echo "[locked] dev opens only after 1900 optimizer steps"

python -u tools/run_mamba_v14_d4a_training_fold.py \
  --fold "$FOLD" \
  --config "$CONFIG_DIR/MambaV14D4A_fold${FOLD}_seed0.json" \
  --authorization_dir "$AUTH_DIR" \
  --fourfold_lock_dir "$FOURFOLD_LOCK" \
  --generation_audit_dir "$AUDIT" \
  --output_dir "$OUTPUT_ROOT/fold${FOLD}_seed0"

echo "[done] D4-A fold=${FOLD} seed=0 $(date -u --iso-8601=seconds)"
echo "[locked] T0=false T1=false T2=false selection=false protected=false"
