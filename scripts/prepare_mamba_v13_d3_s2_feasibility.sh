#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

S0_COMPLETION="logs/mamba_v13_d3_mug500plus/s0_seed0_completion_v1/s0_seed0_completion_receipt.json"
PARENT_LOCK="${PROTOCOL_LOCK:-$HOME/baseline_archives/mamba_v13_d3_round_a_v1}"
LOCK_DIR="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1"
HOTFIX_DIR="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_hotfix1"

python -m py_compile \
  models/AdaPoinTr.py \
  tools/lock_mamba_v13_d3_s2_feasibility_protocol.py \
  tools/authorize_mamba_v13_d3_s2_feasibility_hotfix1.py \
  tools/run_mamba_v13_d3_s2_feasibility_fold.py \
  tools/freeze_mamba_v13_d3_s2_feasibility.py \
  tools/test_mamba_v13_d3_s2_feasibility_contract.py

bash -n \
  scripts/prepare_mamba_v13_d3_s2_feasibility.sh \
  scripts/run_mamba_v13_d3_s2_feasibility_fold.sh \
  scripts/run_mamba_v13_d3_s2_feasibility.sh \
  scripts/launch_mamba_v13_d3_s2_feasibility_tmux.sh

python tools/test_mamba_v13_d3_s2_feasibility_contract.py
python tools/test_mamba_v13_d3_contact.py

if [[ ! -f "$LOCK_DIR/feasibility_lock_receipt.json" ]]; then
  python tools/lock_mamba_v13_d3_s2_feasibility_protocol.py \
    --s0_completion "$S0_COMPLETION" \
    --parent_protocol_lock "$PARENT_LOCK" \
    --output_dir "$LOCK_DIR"
else
  echo "[locked] preserve existing immutable base feasibility lock"
fi

(cd "$LOCK_DIR" && sha256sum -c files.sha256)

python tools/authorize_mamba_v13_d3_s2_feasibility_hotfix1.py \
  --base_lock_dir "$LOCK_DIR" \
  --output_dir "$HOTFIX_DIR"
python tools/authorize_mamba_v13_d3_s2_feasibility_hotfix1.py \
  --base_lock_dir "$LOCK_DIR" \
  --output_dir "$HOTFIX_DIR"
(cd "$HOTFIX_DIR" && sha256sum -c files.sha256)

echo "[done] S2 feasibility preflight, base lock, and hotfix1 receipt passed"
echo "[authorized] frozen-S0 head-only folds A-D, seed=0"
echo "[locked] S1=false S2_full=false holdout=false selection_started=false"
