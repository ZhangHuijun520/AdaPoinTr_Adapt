#!/usr/bin/env bash
set -uo pipefail

REPO_ROOT="/home/jovyan/adapointr_work/PoinTr"
REQUEST="$REPO_ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_intervention_negative_control_numeric_diagnostic_execution_authorization_request_v3.json"
PROTOCOL="$REPO_ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_intervention_negative_control_numeric_diagnostic_protocol_v1.json"
RECEIPT="$REPO_ROOT/docs/cranial_scqr_v1_research_2026_09_10/l4_round_a_intervention_negative_control_numeric_diagnostic_execution_authorization_receipt_v3.json"
RUNNER="$REPO_ROOT/tools/run_cranial_scqr_v11_l4_round_a_i_negative_control_numeric_diagnostic.py"
PYTHON_BIN="/opt/conda/envs/adapointr-mamba/bin/python"
PYTHON_REAL="/opt/conda/envs/adapointr-mamba/bin/python3.10"
EASYDICT_FILE="/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/easydict/__init__.py"
MANIFEST="/home/jovyan/datasets/SkullBreakPC_out8192/manifest.jsonl"
DATA_ROOT="/home/jovyan/datasets/SkullBreakPC_out8192"
MASTER_LOG="$REPO_ROOT/logs/cranial_scqr_v11/l4_round_a_intervention_negative_control_numeric_diagnostic/tmux_v3/cranial_scqr_v11_l4_round_a_i_negative_control_numeric_diagnostic_v3_20260915T060436Z.log"
OUTPUT_DIR="$REPO_ROOT/logs/cranial_scqr_v11/l4_round_a_intervention_negative_control_numeric_diagnostic/cranial_scqr_v11_l4_round_a_i_negative_control_numeric_diagnostic_v3_20260915T060436Z"
EXPECTED_GPU_UUID="GPU-6833d44f-1430-f95a-371b-15b67088153c"
EXPECTED_GPU_NAME="NVIDIA GeForce RTX 4090 D"

sha_of() {
  sha256sum "$1" | awk '{print $1}'
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "$value"
}

fail_before_log() {
  printf 'LAUNCHER_FAIL_CLOSED %s\n' "$1" >&2
  exit 1
}

[[ "$(sha_of "$REQUEST")" == "9f1ac60aa6d820d0a011e8c05e02891d9568819a271a0fc89b28de727e0fb6eb" ]] || fail_before_log "request SHA mismatch"
[[ "$(sha_of "$PROTOCOL")" == "10e7c777974f27fd92e55115942660910d18a21230a5699d244b9b3fffc2806f" ]] || fail_before_log "protocol SHA mismatch"
[[ "$(sha_of "$RECEIPT")" == "51350afee70dae3f8dfd33af432bfda07a572b5f4830373a4266d4d51dc1041e" ]] || fail_before_log "receipt SHA mismatch"
[[ "$(sha_of "$RUNNER")" == "a125013e9aa8d6ba03f7108b7ae1218f0be6f63fad16a64b8326cc5d0dcbae20" ]] || fail_before_log "runner SHA mismatch"
[[ "$(readlink -f "$PYTHON_BIN")" == "$PYTHON_REAL" ]] || fail_before_log "Python realpath mismatch"
[[ "$(sha_of "$PYTHON_REAL")" == "01b4275dc374dcae51d245bda004daad6d7882d3f5de7f9852567bb7ab83180d" ]] || fail_before_log "Python binary SHA mismatch"
[[ "$(sha_of "$EASYDICT_FILE")" == "7d561cb13a5f3d12d8b9fdf5fce82e7a15ec42f3bf1361574c7310d83614513a" ]] || fail_before_log "easydict SHA mismatch"
(cd "$REPO_ROOT" && CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" -c "import easydict") || fail_before_log "bound Python easydict import failed"
[[ "$(sha_of "$MANIFEST")" == "f1f8cae47ed7d5529dc2ca244179cedddbc039981cdc0ff24b25a5c81ad30538" ]] || fail_before_log "manifest SHA mismatch"
[[ ! -e "$OUTPUT_DIR" ]] || fail_before_log "output directory already exists"
[[ ! -e "$MASTER_LOG" ]] || fail_before_log "single-use master log already exists"

mapfile -t gpu_rows < <(nvidia-smi --query-gpu=uuid,name,memory.free --format=csv,noheader,nounits)
[[ "${#gpu_rows[@]}" -eq 1 ]] || fail_before_log "expected exactly one visible GPU"
IFS=',' read -r gpu_uuid gpu_name gpu_free_mib <<< "${gpu_rows[0]}"
gpu_uuid="$(trim "$gpu_uuid")"
gpu_name="$(trim "$gpu_name")"
gpu_free_mib="$(trim "$gpu_free_mib")"
[[ "$gpu_uuid" == "$EXPECTED_GPU_UUID" ]] || fail_before_log "GPU UUID mismatch"
[[ "$gpu_name" == "$EXPECTED_GPU_NAME" ]] || fail_before_log "GPU model mismatch"
[[ "$gpu_free_mib" =~ ^[0-9]+$ && "$gpu_free_mib" -ge 22000 ]] || fail_before_log "insufficient free GPU memory"
disk_free_kib="$(df -Pk "$REPO_ROOT" | awk 'NR==2 {print $4}')"
[[ "$disk_free_kib" =~ ^[0-9]+$ && "$disk_free_kib" -ge 8388608 ]] || fail_before_log "insufficient free disk"

mkdir -p "$(dirname "$MASTER_LOG")" "$(dirname "$OUTPUT_DIR")"
( set -o noclobber; : > "$MASTER_LOG" ) || fail_before_log "single-use master log claim failed"
exec >> "$MASTER_LOG" 2>&1

printf 'LAUNCHER_START_UTC %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'GPU_UUID %s\n' "$gpu_uuid"
printf 'GPU_NAME %s\n' "$gpu_name"
printf 'GPU_FREE_MIB %s\n' "$gpu_free_mib"
printf 'DISK_FREE_KIB %s\n' "$disk_free_kib"

cd "$REPO_ROOT" || exit 1
set +e
CUDA_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 "$PYTHON_BIN" -u "$RUNNER" \
  --protocol "$PROTOCOL" \
  --protocol-sha256 "10e7c777974f27fd92e55115942660910d18a21230a5699d244b9b3fffc2806f" \
  --execution-authorization "$RECEIPT" \
  --execution-authorization-sha256 "51350afee70dae3f8dfd33af432bfda07a572b5f4830373a4266d4d51dc1041e" \
  --manifest "$MANIFEST" \
  --manifest-sha256 "f1f8cae47ed7d5529dc2ca244179cedddbc039981cdc0ff24b25a5c81ad30538" \
  --data-root "$DATA_ROOT" \
  --output-dir "$OUTPUT_DIR" \
  --device cuda:0
exit_code=$?
set -e

printf 'RUNNER_EXIT_CODE %s\n' "$exit_code"
printf 'LAUNCHER_FINISH_UTC %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
exit "$exit_code"
