#!/usr/bin/env bash
set -uo pipefail

if [[ "$#" -ne 5 ]]; then
  echo "usage: $0 PROTOCOL OUTPUT_DIR LAUNCH_LOG PID_FILE EXIT_FILE" >&2
  exit 64
fi

readonly PROJECT_ROOT="/home/jovyan/adapointr_work/PoinTr"
readonly PYTHON_BIN="/opt/conda/envs/adapointr-mamba/bin/python"
readonly RUNNER="${PROJECT_ROOT}/tools/run_cranial_scqr_v11_l3_benchmark.py"
readonly PROTOCOL="$1"
readonly OUTPUT_DIR="$2"
readonly LAUNCH_LOG="$3"
readonly PID_FILE="$4"
readonly EXIT_FILE="$5"

if [[ -e "${OUTPUT_DIR}" || -e "${LAUNCH_LOG}" || -e "${PID_FILE}" || -e "${EXIT_FILE}" ]]; then
  echo "refusing to reuse an L3 output or sidecar path" >&2
  exit 73
fi

printf '%s\n' "$$" > "${PID_FILE}"
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export PYTHONDONTWRITEBYTECODE=1

"${PYTHON_BIN}" -B "${RUNNER}" \
  --protocol "${PROTOCOL}" \
  --output-dir "${OUTPUT_DIR}" \
  > "${LAUNCH_LOG}" 2>&1
status=$?
printf '%s\n' "${status}" > "${EXIT_FILE}"
exit "${status}"
