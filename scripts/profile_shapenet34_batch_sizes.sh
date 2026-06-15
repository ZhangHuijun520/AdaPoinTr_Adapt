#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="${CONFIG:-cfgs/ShapeNet34_models/AdaPoinTr_1gpu_5epoch.yaml}"
NUM_WORKERS="${NUM_WORKERS:-4}"
LOG_DIR="${LOG_DIR:-logs/shapenet34_profile}"
mkdir -p "$LOG_DIR"

for bs in "${@:-2 4 8}"; do
  stamp="$(date +%Y%m%d_%H%M%S)"
  log_file="$LOG_DIR/bs${bs}_${stamp}.log"
  echo "[profile] batch_size=$bs config=$CONFIG" | tee "$log_file"
  if python tools/profile_shapenet34_train_step.py \
      --config "$CONFIG" \
      --batch_size "$bs" \
      --num_workers "$NUM_WORKERS" \
      --warmup 2 \
      --iters 5 \
      2>&1 | tee -a "$log_file"; then
    echo "[profile-ok] batch_size=$bs" | tee -a "$log_file"
  else
    echo "[profile-failed] batch_size=$bs" | tee -a "$log_file"
  fi
done
