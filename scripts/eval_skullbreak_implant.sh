#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="${CONFIG:-cfgs/SkullBreak_models/AdaPoinTr_implant_small75_bncal.yaml}"
CKPT="${1:?Pass a checkpoint path as the first argument}"
SPLIT="${SPLIT:-test}"
NUM_SAMPLES="${NUM_SAMPLES:-0}"
OUT_DIR="${OUT_DIR:-logs/skullbreak_implant_eval}"
RIM_BAND_MM="${RIM_BAND_MM:-2.0}"
BOOTSTRAP_SAMPLES="${BOOTSTRAP_SAMPLES:-2000}"
CONFIDENCE="${CONFIDENCE:-0.95}"
SAVE_PREDICTIONS_DIR="${SAVE_PREDICTIONS_DIR:-}"

args=(
  --config "$CONFIG"
  --ckpt "$CKPT"
  --split "$SPLIT"
  --num_samples "$NUM_SAMPLES"
  --out_dir "$OUT_DIR"
  --rim_band_mm "$RIM_BAND_MM"
  --bootstrap_samples "$BOOTSTRAP_SAMPLES"
  --confidence "$CONFIDENCE"
  --dataset_label SkullBreak
)

if [[ -n "$SAVE_PREDICTIONS_DIR" ]]; then
  args+=(--save_predictions_dir "$SAVE_PREDICTIONS_DIR")
fi

python tools/evaluate_skullfix_implant.py "${args[@]}"
