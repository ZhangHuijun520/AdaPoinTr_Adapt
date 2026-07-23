#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="cfgs/SkullFix_models/MambaAdapterV11_implant_full100_out8192_bncal.yaml"
EXP_NAME="skullfix_mamba_adapter_v11_full100_out8192_bncal"
EXP_DIR="experiments/MambaAdapterV11_implant_full100_out8192_bncal/SkullFix_models/${EXP_NAME}"
LOG_DIR="logs/skullfix_mamba_adapter_v11_out8192"
STAMP="$(date +%Y%m%d_%H%M%S)"
RESUME="${RESUME:-0}"
MIN_FREE_GB="${MIN_FREE_GB:-10}"

mkdir -p "$LOG_DIR"

free_kb="$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
required_kb="$((MIN_FREE_GB * 1024 * 1024))"
if (( free_kb < required_kb )); then
  echo "[error] less than ${MIN_FREE_GB} GiB free on $HOME"
  df -h "$HOME"
  exit 1
fi

train_args=(
  --config "$CONFIG"
  --exp_name "$EXP_NAME"
  --num_workers 4
  --val_freq 10
  --seed 0
  --deterministic
)
if [[ "$RESUME" == "1" ]]; then
  train_args+=(--resume)
fi

python main.py "${train_args[@]}" \
  2>&1 | tee "${LOG_DIR}/${EXP_NAME}_${STAMP}.log"

python tools/recalibrate_skullfix_batchnorm.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last.pth" \
  --output "${EXP_DIR}/ckpt-last-bncal.pth" \
  --batch_size 8 \
  --max_batches 10 \
  --num_workers 4

python tools/evaluate_skullfix_implant.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last-bncal.pth" \
  --split test \
  --num_samples 0 \
  --out_dir "logs/skullfix_mamba_adapter_v11_out8192_eval/full100_out8192_bncal_test" \
  --rim_band_mm 2.0 \
  --dataset_label SkullFix \
  --save_predictions_dir "logs/skullfix_mamba_adapter_v11_out8192_eval/full100_out8192_predictions_test"

MPLBACKEND=Agg python tools/visualize_skullfix_implant.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last-bncal.pth" \
  --split test \
  --num_samples 10 \
  --out_dir "experiments/visualizations/skullfix_mamba_adapter_v11_full100_out8192_bncal_test"

echo "[done] $(date)"
