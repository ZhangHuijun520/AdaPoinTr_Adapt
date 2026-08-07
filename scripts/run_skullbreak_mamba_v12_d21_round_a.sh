#!/usr/bin/env bash
set -euo pipefail

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

bash scripts/prepare_skullbreak_mamba_v12_d21_geometry_protocol.sh

for candidate in Q0 Q1 Q2 Q3; do
  for fold in A B C D; do
    bash scripts/run_skullbreak_mamba_v12_d21_round_a_fold.sh \
      "$candidate" "$fold"
  done
done

python tools/select_mamba_v12_d21_round_a.py \
  --records_root logs/skullbreak_mamba_v12_d21_geometry/round_a \
  --protocol logs/skullbreak_mamba_v12_d21_geometry/protocol_v1/protocol_amendment.json \
  --output logs/skullbreak_mamba_v12_d21_geometry/round_a_top2.json

echo "[done] D2.1 Round A completed"
echo "[next] inspect the frozen receipt before implementing Round B"
