#!/usr/bin/env bash
set -euo pipefail

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

bash scripts/prepare_skullbreak_mamba_v12_d22_protocol.sh
for fold in A B C D; do
  for candidate in R0 R1 R2; do
    bash scripts/run_skullbreak_mamba_v12_d22_round_a_fold.sh \
      "$candidate" "$fold"
  done
done

python tools/select_mamba_v12_d22_round_a.py \
  --records_root logs/skullbreak_mamba_v12_d22_local_rim/round_a \
  --protocol docs/mamba_v12_d22_local_rim_trust_protocol_v1.json \
  --amendment docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1.json \
  --output logs/skullbreak_mamba_v12_d22_local_rim/round_a_selection.json

echo "[done] D2.2 Round A completed"
echo "[next] obey round_a_selection.json; do not inspect protected splits"
