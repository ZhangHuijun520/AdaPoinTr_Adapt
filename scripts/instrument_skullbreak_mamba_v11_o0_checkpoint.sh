#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

SEED="${1:?Pass checkpoint seed, for example 0, 1, or 2}"
CKPT="${2:?Pass checkpoint path}"
OUT_DIR="${3:-logs/skullbreak_mamba_v11_o0_multiseed/instrumentation/seed${SEED}}"
CONFIG="cfgs/SkullBreak_models/MambaAdapterV11OrderingO0_xyz_out8192_monitor.yaml"
PROTOCOL_DIR="logs/skullbreak_mamba_v11_o0_multiseed/protocol"
PANEL="${PROTOCOL_DIR}/strict_train_instrumentation_panel.json"

mkdir -p "$PROTOCOL_DIR"

python tools/select_skullbreak_mamba_instrumentation_panel.py \
  --config "$CONFIG" \
  --output "$PANEL" \
  --num_cases 20 \
  --selection_seed 20260803

python tools/instrument_mamba_adapter_tokens.py \
  --config "$CONFIG" \
  --ckpt "$CKPT" \
  --panel "$PANEL" \
  --out_dir "$OUT_DIR" \
  --seed "$SEED"

echo "[done] observation-only instrumentation seed=${SEED}"
echo "[output] ${OUT_DIR}"
