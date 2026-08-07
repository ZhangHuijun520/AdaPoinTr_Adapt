#!/usr/bin/env bash
set -euo pipefail

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

bash scripts/prepare_skullbreak_mamba_v12_development_protocol.sh

for candidate in C0 C1 C2 C3; do
  for fold in A B C D; do
    bash scripts/run_skullbreak_mamba_v12_round_a_fold.sh \
      "$candidate" "$fold" 0
  done
done

python tools/select_mamba_v12_round.py \
  --records_root logs/skullbreak_mamba_v12_development/round_a \
  --protocol logs/skullbreak_mamba_v12_development/protocol_v1/protocol.json \
  --round A \
  --output logs/skullbreak_mamba_v12_development/selection/round_a_top2.json

echo "[done] all 16 Round-A trainings and preregistered selection completed"
echo "[next] inspect only the frozen top-two receipt, then generate Round B"
