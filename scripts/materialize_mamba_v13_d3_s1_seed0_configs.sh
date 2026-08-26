#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
PROTOCOL_LOCK="${PROTOCOL_LOCK:-$HOME/baseline_archives/mamba_v13_d3_round_a_v1}"
COMPLETION="${S1_CALIBRATION_COMPLETION:-$ROOT/logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_completion_v1/s1_gradient_calibration_completion_receipt.json}"
CONFIG_DIR="${S1_MATERIALIZED_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v13_d3_s1_seed0_materialized_v1}"
RECEIPT_DIR="${S1_MATERIALIZATION_RECEIPT_DIR:-$ROOT/logs/mamba_v13_d3_mug500plus/s1_seed0_materialization_v1}"

cd "$ROOT"

python -m py_compile \
  tools/materialize_mamba_v13_d3_s1_seed0_runtime_configs.py \
  tools/verify_mamba_v13_d3_s1_seed0_materialization.py \
  tools/test_mamba_v13_d3_s1_materialization_contract.py

python tools/test_mamba_v13_d3_s1_materialization_contract.py

for pass in 1 2; do
  python tools/materialize_mamba_v13_d3_s1_seed0_runtime_configs.py \
    --protocol_lock_dir "$PROTOCOL_LOCK" \
    --completion_receipt "$COMPLETION" \
    --config_output_dir "$CONFIG_DIR" \
    --receipt_output_dir "$RECEIPT_DIR"
done

python tools/verify_mamba_v13_d3_s1_seed0_materialization.py \
  --config_dir "$CONFIG_DIR" \
  --receipt_dir "$RECEIPT_DIR"

(
  cd "$RECEIPT_DIR"
  sha256sum -c files.sha256
  sha256sum -c s1_seed0_materialization_receipt.json.sha256
)

echo "[done] S1 seed-0 fold configs materialized and frozen"
echo "[locked] training=false S2=false holdout=false selection=false"
echo "[next] training authorization remains separate and has not been issued"
