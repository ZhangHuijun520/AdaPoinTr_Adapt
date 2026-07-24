#!/usr/bin/env bash
set -euo pipefail

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

python tools/select_skullbreak_mamba_ordering.py select \
  --repo_root . \
  --manifest data/SkullBreakPC_out8192/manifest.jsonl \
  --decision logs/skullbreak_mamba_ordering_v11_out8192/ordering_decision_seed0.json

echo "[frozen] ordering selection is complete"
echo "[next] inspect the decision JSON, then run the official-test unlock script once"
