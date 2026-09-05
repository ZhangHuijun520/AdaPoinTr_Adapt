#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
CONFIGS="${D6_R1_LATENCY_PROFILING_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_latency_posthoc_profiling_authorized_v1}"
AUTH="${D6_R1_LATENCY_PROFILING_AUTH_DIR:-$LOGS/d6a_r1_latency_posthoc_profiling_execution_authorization_v1}"
OUTPUT="${D6_R1_LATENCY_PROFILING_PREFLIGHT_DIR:-$LOGS/d6a_r1_latency_posthoc_profiling_execution_preflight_v1}"

cd "$ROOT"
python -m py_compile \
  utils/mamba_d6a_r1_latency_profiler.py \
  tools/authorize_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py \
  tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_authorization.py \
  tools/preflight_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py \
  tools/run_mamba_v16_d6a_r1_latency_posthoc_profiling.py
python tools/test_mamba_v16_d6a_r1_latency_posthoc_profiling_execution_contract.py
python tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_authorization.py \
  --config_dir "$CONFIGS" \
  --authorization_dir "$AUTH"
python tools/preflight_mamba_v16_d6a_r1_latency_posthoc_profiling_execution.py \
  --config_dir "$CONFIGS" \
  --authorization_dir "$AUTH" \
  --output_dir "$OUTPUT"
(
  cd "$OUTPUT"
  sha256sum -c files.sha256
)
echo "[done] D6-A R1 profiling zero-count authorization preflight passed"
echo "[authorized-next] separate tmux launch of R1 profiling only"
echo "[locked] profiling not started by preflight; training=false seed1=false D6B=false sealed=false"
