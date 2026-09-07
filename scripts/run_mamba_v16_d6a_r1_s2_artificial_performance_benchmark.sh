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

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

[[ ! -e "$RESULT" ]] || { echo "[error] immutable benchmark result already exists: $RESULT"; exit 1; }

echo "===== Verify authorized benchmark boundary ====="
"$PYTHON" tools/verify_mamba_v16_d6a_r1_s2_artificial_performance_benchmark_authorization.py \
  --config_dir "$CONFIG" \
  --authorization_dir "$AUTH"

echo "===== Run one frozen S0-versus-S2 artificial benchmark ====="
"$PYTHON" tools/run_mamba_v16_d6a_r1_s2_artificial_performance_benchmark.py \
  --config_dir "$CONFIG" \
  --authorization_dir "$AUTH" \
  --preflight_dir "$PREFLIGHT" \
  --output_dir "$RESULT"

echo "===== Verify immutable result files ====="
(
  cd "$RESULT"
  sha256sum -c files.sha256
)

echo "[done] S2 artificial performance benchmark result frozen"
echo "[locked] rerun=false production=false formal_rerun=false training=false seed1=false D6B=false sealed=false"
