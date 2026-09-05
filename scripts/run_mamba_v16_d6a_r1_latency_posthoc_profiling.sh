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
PREFLIGHT="${D6_R1_LATENCY_PROFILING_PREFLIGHT_DIR:-$LOGS/d6a_r1_latency_posthoc_profiling_execution_preflight_v1}"
RESULT="${D6_R1_LATENCY_PROFILING_RESULT_DIR:-$LOGS/d6a_r1_latency_posthoc_profiling_result_v1}"

cd "$ROOT"
python tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_authorization.py \
  --config_dir "$CONFIGS" \
  --authorization_dir "$AUTH"
(
  cd "$PREFLIGHT"
  sha256sum -c files.sha256
)
python tools/run_mamba_v16_d6a_r1_latency_posthoc_profiling.py \
  --config_dir "$CONFIGS" \
  --authorization_dir "$AUTH" \
  --preflight_dir "$PREFLIGHT" \
  --output_dir "$RESULT"
(
  cd "$RESULT"
  sha256sum -c files.sha256
)
echo "[done] D6-A R1 latency post-hoc profiling completed"
echo "[locked] formal gate unchanged; training=false seed1=false D6B=false sealed=false"
