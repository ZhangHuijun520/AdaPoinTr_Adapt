#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
AUTH="${MAMBA_V14_D4A_AUTH_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_training_authorization_v1}"
FOLD_ROOT="${MAMBA_V14_D4A_FOLD_ROOT:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_head_only_seed0_v1}"
COMPLETION="${MAMBA_V14_D4A_COMPLETION_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_training_completion_v1}"
AUDIT="${MUG500PLUS_D4_GENERATION_AUDIT_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4_m2_generation_audit_v1}"
OUTPUT="${MAMBA_V14_D4A_POSTHOC_DIR:-$ROOT/logs/mamba_v14_d4_contact_support/d4a_failure_decomposition_posthoc_v1}"

cd "$ROOT"

python -m py_compile \
  tools/run_mamba_v14_d4a_failure_decomposition_posthoc.py \
  tools/test_mamba_v14_d4a_failure_decomposition_posthoc.py

python tools/test_mamba_v14_d4a_failure_decomposition_posthoc.py

python -u tools/run_mamba_v14_d4a_failure_decomposition_posthoc.py \
  --fold_root "$FOLD_ROOT" \
  --authorization_dir "$AUTH" \
  --completion_dir "$COMPLETION" \
  --generation_audit_dir "$AUDIT" \
  --output_dir "$OUTPUT"

(
  cd "$OUTPUT"
  sha256sum -c files.sha256
)

echo "[done] D4-A post-hoc failure decomposition completed"
echo "[locked] original 332/400 gate unchanged; T0/T1/T2 remain forbidden"
echo "[locked] selection=false protected=false model_updates=0"
