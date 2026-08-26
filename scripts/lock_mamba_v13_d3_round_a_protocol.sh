#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_LOCK_DIR="${SOURCE_LOCK_DIR:-data/MUG500plusM2SourceSplitV1}"
OUTPUT_DIR="${OUTPUT_DIR:-$HOME/baseline_archives/mamba_v13_d3_round_a_protocol_v1}"

cd "$ROOT"

python -m py_compile \
  datasets/SkullBreakDataset.py \
  tools/runner.py \
  tools/lock_mamba_v13_d3_round_a_protocol.py \
  tools/test_mug500plus_m2_dataset_contract.py \
  tools/test_mamba_v13_d3_round_a_protocol.py

python tools/test_mamba_v13_d3_contact.py
python tools/test_mug500plus_m2_dataset_contract.py
python tools/test_mamba_v13_d3_round_a_protocol.py \
  --source_split_lock_dir "$SOURCE_LOCK_DIR"
python tools/test_mamba_v13_d3_model_contract.py

python tools/lock_mamba_v13_d3_round_a_protocol.py \
  --source_split_lock_dir "$SOURCE_LOCK_DIR" \
  --output_dir "$OUTPUT_DIR"
python tools/lock_mamba_v13_d3_round_a_protocol.py \
  --source_split_lock_dir "$SOURCE_LOCK_DIR" \
  --output_dir "$OUTPUT_DIR"

(
  cd "$OUTPUT_DIR"
  sha256sum -c files.sha256
)

echo "[done] D3 S0/S1/S2 candidate templates and execution protocol frozen"
echo "[locked] training has not been authorized or started"
echo "[locked] locked holdout has not been referenced or accessed"
echo "[next] materialize receipt-bound S0 seed-0 runtime configs"
