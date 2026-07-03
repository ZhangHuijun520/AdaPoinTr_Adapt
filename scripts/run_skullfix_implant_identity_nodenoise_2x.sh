#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p logs/skullfix_implant

run_identity() {
  local name="$1"
  local config="$2"
  local stamp
  stamp="$(date +%Y%m%d_%H%M%S)"

  echo "[run] ${name}"
  python main.py \
    --config "${config}" \
    --exp_name "${name}" \
    --num_workers 0 \
    --val_freq 25 \
    2>&1 | tee "logs/skullfix_implant/${name}_${stamp}.log"
}

run_identity \
  skullfix_implant_identity_learned_nodenoise \
  cfgs/SkullFix_models/AdaPoinTr_implant_identity_learned_nodenoise.yaml

run_identity \
  skullfix_implant_identity_fpsonly_nodenoise \
  cfgs/SkullFix_models/AdaPoinTr_implant_identity_fpsonly_nodenoise.yaml

echo "[done] $(date)"
