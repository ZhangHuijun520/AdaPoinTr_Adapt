#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CKPT="${1:-experiments/AdaPoinTr_1gpu_full/ShapeNet34_models/shapenet34_adapointr_1gpu_full/ckpt-best.pth}"
NUM_WORKERS="${NUM_WORKERS:-4}"
LOG_DIR="${LOG_DIR:-logs/shapenet34_eval}"
RUN_TAG="${RUN_TAG:-shapenet34_adapointr_1gpu_full}"
SEEN_CONFIG="${SEEN_CONFIG:-cfgs/ShapeNet34_models/AdaPoinTr_1gpu_full.yaml}"
UNSEEN_CONFIG="${UNSEEN_CONFIG:-cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml}"
mkdir -p "$LOG_DIR"

if [ ! -f "$CKPT" ]; then
  echo "[error] checkpoint not found: $CKPT" >&2
  exit 1
fi

run_eval() {
  local split="$1"
  local config="$2"
  local mode="$3"
  local stamp
  stamp="$(date +%Y%m%d_%H%M%S)"
  local exp_name="${RUN_TAG}_${split}"
  local log_file="$LOG_DIR/${exp_name}_${mode}_${stamp}.log"

  echo "[eval] split=$split mode=$mode ckpt=$CKPT" | tee "$log_file"
  python main.py \
    --test \
    --config "$config" \
    --ckpts "$CKPT" \
    --exp_name "$exp_name" \
    --mode "$mode" \
    --num_workers "$NUM_WORKERS" \
    2>&1 | tee -a "$log_file"
}

for mode in easy median hard; do
  run_eval seen "$SEEN_CONFIG" "$mode"
done

for mode in easy median hard; do
  run_eval unseen "$UNSEEN_CONFIG" "$mode"
done
