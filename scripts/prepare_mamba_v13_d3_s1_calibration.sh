#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

PARENT_LOCK="${PROTOCOL_LOCK:-$HOME/baseline_archives/mamba_v13_d3_round_a_v1}"
S0_COMPLETION="logs/mamba_v13_d3_mug500plus/s0_seed0_completion_v1/s0_seed0_completion_receipt.json"
S2_BASE_LOCK="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1"
S2_NEGATIVE="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_negative_freeze_v1"
AUTH_DIR="logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_authorization_v1"
HOTFIX_DIR="logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_tensor_hash_hotfix1"
RUNS_ROOT="logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_v1"
FAILED_MASTER_LOG="${FAILED_MASTER_LOG:-logs/mamba_v13_d3_mug500plus/s1_gradient_calibration_tmux/tmux_20260826_080510.log}"

python -m py_compile \
  tools/authorize_mamba_v13_d3_s1_calibration.py \
  tools/authorize_mamba_v13_d3_s1_calibration_hotfix1.py \
  tools/run_mamba_v13_d3_s1_calibration_fold.py \
  tools/freeze_mamba_v13_d3_s1_calibration.py \
  tools/test_mamba_v13_d3_s1_calibration_contract.py

bash -n \
  scripts/prepare_mamba_v13_d3_s1_calibration.sh \
  scripts/run_mamba_v13_d3_s1_calibration_fold.sh \
  scripts/run_mamba_v13_d3_s1_calibration.sh \
  scripts/launch_mamba_v13_d3_s1_calibration_tmux.sh

python tools/test_mamba_v13_d3_s1_calibration_contract.py

[[ -f "$AUTH_DIR/s1_calibration_authorization_receipt.json" ]] || {
  echo "[error] the original S1 calibration authorization is missing"
  echo "[locked] the hotfix must not regenerate or replace base authorization"
  exit 1
}
[[ -f "$FAILED_MASTER_LOG" ]] || {
  echo "[error] failed master log is missing: $FAILED_MASTER_LOG"
  exit 1
}

(cd "$AUTH_DIR" && sha256sum -c files.sha256)

python tools/authorize_mamba_v13_d3_s1_calibration_hotfix1.py \
  --base_authorization_dir "$AUTH_DIR" \
  --failed_master_log "$FAILED_MASTER_LOG" \
  --runs_root "$RUNS_ROOT" \
  --output_dir "$HOTFIX_DIR"

# A second pass proves that hotfix rendering is deterministic and immutable.
python tools/authorize_mamba_v13_d3_s1_calibration_hotfix1.py \
  --base_authorization_dir "$AUTH_DIR" \
  --failed_master_log "$FAILED_MASTER_LOG" \
  --runs_root "$RUNS_ROOT" \
  --output_dir "$HOTFIX_DIR"

(cd "$HOTFIX_DIR" && sha256sum -c files.sha256)

echo "[done] S1 calibration preflight and bounded tensor-hash hotfix passed"
echo "[preserved] original authorization and failed master log remain hash-bound"
echo "[authorized] S1 seed-0 folds A-D gradient measurement only"
echo "[locked] optimizer_steps=0 dev=false holdout=false S2=false training=false"
