#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

python tools/run_mamba_v14_pd3_s2_failure_decomposition.py \
  --protocol docs/mamba_v14_d4_contact_support_representation_protocol_v1.json \
  --lock_dir logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1 \
  --hotfix_dir logs/mamba_v13_d3_mug500plus/s2_head_feasibility_hotfix1 \
  --negative_freeze logs/mamba_v13_d3_mug500plus/s2_head_feasibility_negative_freeze_v1 \
  --runs_root logs/mamba_v13_d3_mug500plus/s2_head_feasibility_v1 \
  --output_dir logs/mamba_v14_d4_contact_support/pd3_s2_failure_decomposition_v1 \
  --num_workers "${NUM_WORKERS:-4}"

echo "[done] P-D3 S2 selection-inert replay $(date -u --iso-8601=seconds)"
echo "[locked] D3 winner=null; D4 selection=false; protected splits untouched"
