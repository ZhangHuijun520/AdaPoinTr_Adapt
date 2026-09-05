#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
LOCK="${D6_R1_LATENCY_PROFILING_LOCK_DIR:-$LOGS/d6a_r1_latency_bottleneck_posthoc_profiling_protocol_v1}"
CONFIGS="${D6_R1_LATENCY_PROFILING_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_latency_posthoc_profiling_authorized_v1}"
AUTH="${D6_R1_LATENCY_PROFILING_AUTH_DIR:-$LOGS/d6a_r1_latency_posthoc_profiling_execution_authorization_v1}"

cd "$ROOT"
python tools/test_mamba_v16_d6a_r1_latency_posthoc_profiling_execution_contract.py
for pass in 1 2; do
  python tools/authorize_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py \
    --profiling_lock_dir "$LOCK" \
    --config_output_dir "$CONFIGS" \
    --authorization_output_dir "$AUTH"
done
python tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_authorization.py \
  --config_dir "$CONFIGS" \
  --authorization_dir "$AUTH"
(
  cd "$AUTH"
  sha256sum -c files.sha256
  sha256sum -c profiling_execution_authorization_receipt.json.sha256
)
echo "[done] D6-A R1 latency profiling execution authorization frozen"
echo "[locked] execution not started; training=false seed1=false D6B=false sealed=false"
echo "[next] run separate zero-count CUDA authorization preflight"
