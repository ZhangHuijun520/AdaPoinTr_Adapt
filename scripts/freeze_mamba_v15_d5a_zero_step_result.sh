#!/usr/bin/env bash
set -euo pipefail

export PS1="${PS1-}"
source "$HOME/conda/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV:-adapointr-mamba}"

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="$ROOT/logs/mamba_v15_d5_contact_support"
CANDIDATE="${MAMBA_V15_D5_CANDIDATE_PROTOCOL_LOCK_DIR:-$LOGS/candidate_training_protocol_v1}"
ZERO="${MAMBA_V15_D5A_ZERO_STEP_DIR:-$LOGS/d5a_zero_step_preflight_v1}"
TRANSPORT="${MAMBA_V15_D5A_TRANSPORT_RECEIPT:-$LOGS/d5a_overlay_transport_normalization_v1/overlay_transport_normalization_receipt.json}"
LINEAGE="${MAMBA_V15_D5A_LINEAGE_RECEIPT:-$LOGS/d5a_d4_parent_lineage_hotfix1_v1/d4_parent_lineage_hotfix_receipt.json}"
OUTPUT="${MAMBA_V15_D5A_ZERO_STEP_RESULT_DIR:-$LOGS/d5a_zero_step_result_freeze_v1}"

cd "$ROOT"

python -m py_compile \
  tools/freeze_mamba_v15_d5a_zero_step_result.py \
  tools/test_mamba_v15_d5a_zero_step_result_freeze.py
bash -n scripts/freeze_mamba_v15_d5a_zero_step_result.sh
python tools/test_mamba_v15_d5a_zero_step_result_freeze.py

for pass in 1 2; do
  python tools/freeze_mamba_v15_d5a_zero_step_result.py \
    --candidate_lock_dir "$CANDIDATE" \
    --zero_step_dir "$ZERO" \
    --transport_receipt "$TRANSPORT" \
    --lineage_receipt "$LINEAGE" \
    --output_dir "$OUTPUT"
done

(
  cd "$OUTPUT"
  sha256sum -c files.sha256
)

echo "[done] D5-A V0/V1 zero-step complete result frozen"
echo "[locked] training=false seed1=false D5B=false selection=false sealed=false"
echo "[next] create and restore-verify the separate credential archive"
