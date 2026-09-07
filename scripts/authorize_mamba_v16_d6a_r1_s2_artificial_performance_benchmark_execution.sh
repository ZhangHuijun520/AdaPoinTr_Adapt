#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
LOG_ROOT="$ROOT/logs/mamba_v16_d6_contact_support"
LOCK="${D6_R1_S2_BENCHMARK_LOCK_DIR:-$LOG_ROOT/d6a_r1_s2_artificial_performance_benchmark_protocol_v1}"
S2_RESULT="${D6_R1_S2_ZERO_STEP_RESULT_DIR:-$LOG_ROOT/d6a_r1_s2_certified_fast_path_artificial_zero_step_v1}"
CONFIG="${D6_R1_S2_BENCHMARK_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_authorized_v1}"
AUTH="${D6_R1_S2_BENCHMARK_AUTH_DIR:-$LOG_ROOT/d6a_r1_s2_artificial_performance_benchmark_execution_authorization_v1}"
PYTHON="${D6_R1_S2_BENCHMARK_PYTHON:-/opt/conda/envs/adapointr-mamba/bin/python}"
[[ -x "$PYTHON" ]] || PYTHON="$(command -v python)"

echo "===== S2 artificial benchmark execution contract tests ====="
"$PYTHON" tools/test_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_execution_contract.py

echo "===== Issue frozen S2 artificial benchmark execution authorization ====="
"$PYTHON" tools/authorize_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_execution.py \
  --protocol_lock_dir "$LOCK" \
  --s2_result_dir "$S2_RESULT" \
  --config_output_dir "$CONFIG" \
  --authorization_output_dir "$AUTH"

echo "===== Verify authorization and runtime config ====="
"$PYTHON" tools/verify_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_authorization.py \
  --config_dir "$CONFIG" \
  --authorization_dir "$AUTH"
(
  cd "$AUTH"
  sha256sum -c files.sha256
)

echo "[done] S2 artificial benchmark execution authorization frozen"
echo "[next] separate zero-count CUDA authorization preflight"
echo "[locked] execution not started; production=false formal_rerun=false training=false D6=false"
