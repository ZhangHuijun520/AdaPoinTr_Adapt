#!/usr/bin/env bash
set -euo pipefail
cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

ROOT="logs/skullbreak_mamba_v12_development"
ROUND_A="${ROOT}/selection/round_a_top2.json"
[[ -f "$ROUND_A" && -f "${ROUND_A}.sha256" ]] || {
  echo "[error] frozen Round-A selection is missing"
  exit 2
}

python tools/generate_skullbreak_mamba_v12_followup_configs.py \
  --round B --protocol_dir "${ROOT}/protocol_v1" \
  --selection "$ROUND_A" \
  --output_dir cfgs/SkullBreak_models/generated_mamba_v12_dev_round_b

mapfile -t candidates < <(python -c \
  'import json; print("\n".join(json.load(open("logs/skullbreak_mamba_v12_development/selection/round_a_top2.json"))["selected"]))')
[[ "${#candidates[@]}" -eq 2 ]] || { echo "[error] expected two candidates"; exit 2; }

for candidate in "${candidates[@]}"; do
  for fold in A B C D; do
    bash scripts/run_skullbreak_mamba_v12_round_b_fold.sh "$candidate" "$fold"
  done
done

python tools/select_mamba_v12_round.py \
  --records_root "$ROOT" \
  --protocol "${ROOT}/protocol_v1/protocol.json" \
  --round B --round_a_selection "$ROUND_A" \
  --output "${ROOT}/selection/round_b_winner.json"

echo "[done] Round B seed-1 replication and winner freeze"
echo "[next] Round C trains the frozen winner on development84"
