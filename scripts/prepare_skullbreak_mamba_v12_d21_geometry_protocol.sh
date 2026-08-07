#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

BASE_PROTOCOL="logs/skullbreak_mamba_v12_development/protocol_v1"
GT_REPLAY="logs/skullbreak_mamba_v12_development/posthoc_round_a_gt_geometry/gt_geometry_summary.json"
ROOT="logs/skullbreak_mamba_v12_d21_geometry"
PROTOCOL_DIR="${ROOT}/protocol_v1"
CONFIG_DIR="cfgs/SkullBreak_models/generated_mamba_v12_d21_geometry_v1"

[[ -f "${BASE_PROTOCOL}/protocol.json" && -f "$GT_REPLAY" ]] || {
  echo "[error] frozen D2 protocol or GT replay summary is missing"
  exit 2
}

python tools/lock_mamba_v12_d21_geometry_protocol.py \
  --base_protocol_dir "$BASE_PROTOCOL" \
  --gt_replay_summary "$GT_REPLAY" \
  --output_dir "$PROTOCOL_DIR"

python tools/lock_mamba_v12_d21_geometry_protocol.py \
  --base_protocol_dir "$BASE_PROTOCOL" \
  --gt_replay_summary "$GT_REPLAY" \
  --output_dir "$PROTOCOL_DIR"

python tools/generate_mamba_v12_d21_geometry_configs.py \
  --base_protocol_dir "$BASE_PROTOCOL" \
  --amendment "${PROTOCOL_DIR}/protocol_amendment.json" \
  --output_dir "$CONFIG_DIR"

python tools/generate_mamba_v12_d21_geometry_configs.py \
  --base_protocol_dir "$BASE_PROTOCOL" \
  --amendment "${PROTOCOL_DIR}/protocol_amendment.json" \
  --output_dir "$CONFIG_DIR"

python tools/test_mamba_v12_d21_geometry_guard.py
python -m py_compile \
  models/AdaPoinTr.py \
  tools/lock_mamba_v12_d21_geometry_protocol.py \
  tools/generate_mamba_v12_d21_geometry_configs.py \
  tools/select_mamba_v12_d21_round_a.py

bash -n \
  scripts/prepare_skullbreak_mamba_v12_d21_geometry_protocol.sh \
  scripts/run_skullbreak_mamba_v12_d21_round_a_fold.sh \
  scripts/run_skullbreak_mamba_v12_d21_round_a.sh \
  scripts/launch_skullbreak_mamba_v12_d21_round_a_tmux.sh

echo "[ok] D2.1 protocol and 16 Q0-Q3 configs are immutable"
echo "[ok] GT is training supervision only; inference remains partial-only"
echo "[locked] original D2 Round B remains forbidden"
echo "[locked] confirmation20, old monitor, and official test remain unused"
