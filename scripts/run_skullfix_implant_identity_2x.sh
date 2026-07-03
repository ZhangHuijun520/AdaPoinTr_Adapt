#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

LOG_DIR="${LOG_DIR:-logs/skullfix_implant}"
NUM_WORKERS="${NUM_WORKERS:-2}"
VAL_FREQ="${VAL_FREQ:-25}"
mkdir -p "$LOG_DIR"

run_one() {
  local config="$1"
  local exp_name="$2"
  local stamp
  local log_file

  stamp="$(date +%Y%m%d_%H%M%S)"
  log_file="$LOG_DIR/${exp_name}_${stamp}.log"

  python main.py \
    --config "$config" \
    --exp_name "$exp_name" \
    --num_workers "$NUM_WORKERS" \
    --val_freq "$VAL_FREQ" \
    2>&1 | tee "$log_file"
}

run_one \
  cfgs/SkullFix_models/AdaPoinTr_implant_identity_learned.yaml \
  skullfix_implant_identity_learned

run_one \
  cfgs/SkullFix_models/AdaPoinTr_implant_identity_fpspreserve.yaml \
  skullfix_implant_identity_fpspreserve
