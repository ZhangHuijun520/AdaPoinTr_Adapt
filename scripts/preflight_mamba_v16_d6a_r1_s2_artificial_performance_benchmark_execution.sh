#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
LOG_ROOT="$ROOT/logs/mamba_v16_d6_contact_support"
CONFIG="${D6_R1_S2_BENCHMARK_CONFIG_DIR:-$ROOT/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_authorized_v1}"
AUTH="${D6_R1_S2_BENCHMARK_AUTH_DIR:-$LOG_ROOT/d6a_r1_s2_artificial_performance_benchmark_execution_authorization_v1}"
PREFLIGHT="${D6_R1_S2_BENCHMARK_PREFLIGHT_DIR:-$LOG_ROOT/d6a_r1_s2_artificial_performance_benchmark_execution_preflight_v1}"
RESULT="${D6_R1_S2_BENCHMARK_RESULT_DIR:-$LOG_ROOT/d6a_r1_s2_artificial_performance_benchmark_result_v1}"
PYTHON="${D6_R1_S2_BENCHMARK_PYTHON:-/opt/conda/envs/adapointr-mamba/bin/python}"
[[ -x "$PYTHON" ]] || PYTHON="$(command -v python)"

[[ ! -e "$RESULT" ]] || { echo "[error] benchmark result already exists: $RESULT"; exit 1; }

echo "===== Reverify frozen authorization ====="
"$PYTHON" tools/verify_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_authorization.py \
  --config_dir "$CONFIG" \
  --authorization_dir "$AUTH"

echo "===== Run zero-count CUDA authorization preflight ====="
"$PYTHON" tools/preflight_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_execution.py \
  --config_dir "$CONFIG" \
  --authorization_dir "$AUTH" \
  --output_dir "$PREFLIGHT"
(
  cd "$PREFLIGHT"
  sha256sum -c files.sha256
)

echo "[done] S2 artificial benchmark zero-count CUDA preflight passed"
echo "[next] separate tmux launch of one authorized benchmark"
echo "[locked] warmup=0 timed=0 production=false formal_rerun=false training=false D6=false"
