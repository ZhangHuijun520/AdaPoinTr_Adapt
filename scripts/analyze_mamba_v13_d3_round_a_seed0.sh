#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

S0="logs/mamba_v13_d3_mug500plus/s0_seed0_completion_v1/s0_seed0_completion_receipt.json"
S1="logs/mamba_v13_d3_mug500plus/s1_seed0_completion_v1/s1_seed0_completion_receipt.json"
S2="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_negative_freeze_v1"
OUTPUT="logs/mamba_v13_d3_mug500plus/round_a_seed0_gate_v1"

python tools/test_mamba_v13_d3_round_a_gate_contract.py
python tools/test_mamba_v13_d3_round_a_gate_e2e.py

python tools/analyze_mamba_v13_d3_round_a_seed0.py \
  --s0_completion "$S0" \
  --s1_completion "$S1" \
  --s2_negative_dir "$S2" \
  --output_dir "$OUTPUT"

python tools/verify_mamba_v13_d3_round_a_seed0.py \
  --result_dir "$OUTPUT"

(
  cd "$OUTPUT"
  sha256sum -c files.sha256.sha256
  sha256sum -c files.sha256
)

echo "[done] D3 Round-A seed-0 gate analysis frozen"
echo "[negative] no experimental candidate advances to seed-1"
echo "[locked] holdout=false official_test=false rule_revision=false"
