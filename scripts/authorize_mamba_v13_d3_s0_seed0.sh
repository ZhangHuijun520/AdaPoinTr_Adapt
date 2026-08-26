#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROTOCOL_LOCK="${PROTOCOL_LOCK:-$HOME/baseline_archives/mamba_v13_d3_round_a_v1}"
DEPLOYMENT_RECEIPT="${DEPLOYMENT_RECEIPT:-$ROOT/logs/mamba_v13_d3_mug500plus/data_deployment_v1/asset_deployment_receipt.json}"
CONFIG_DIR="${CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v13_d3_s0_seed0_v1}"
AUTH_DIR="${AUTH_DIR:-$ROOT/logs/mamba_v13_d3_mug500plus/s0_seed0_authorization_v1}"

cd "$ROOT"

python -m py_compile \
  tools/materialize_mamba_v13_d3_s0_seed0_runtime_configs.py \
  tools/verify_mamba_v13_d3_s0_runtime_authorization.py

python tools/materialize_mamba_v13_d3_s0_seed0_runtime_configs.py \
  --protocol_lock_dir "$PROTOCOL_LOCK" \
  --deployment_receipt "$DEPLOYMENT_RECEIPT" \
  --config_output_dir "$CONFIG_DIR" \
  --authorization_output_dir "$AUTH_DIR"

python tools/materialize_mamba_v13_d3_s0_seed0_runtime_configs.py \
  --protocol_lock_dir "$PROTOCOL_LOCK" \
  --deployment_receipt "$DEPLOYMENT_RECEIPT" \
  --config_output_dir "$CONFIG_DIR" \
  --authorization_output_dir "$AUTH_DIR"

python tools/verify_mamba_v13_d3_s0_runtime_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --receipt "$AUTH_DIR/s0_seed0_authorization_receipt.json"

(
  cd "$AUTH_DIR"
  sha256sum -c s0_seed0_authorization_receipt.json.sha256
)

echo "[done] S0 seed-0 runtime configs authorized and frozen"
echo "[authorized] S0 folds A-D only"
echo "[locked] S1=false S2=false holdout=false selection_started=false"
echo "[next] launch S0 fold training in tmux after a dataset/config smoke test"
