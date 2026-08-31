#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

SOURCE_ROOT="${MUG500PLUS_D5_SOURCE_ROOT:-$HOME/datasets/MUG500plusD5Development100_v1}"
OUTPUT_FINAL="${MUG500PLUS_D5_DEVELOPMENT400_ROOT:-$HOME/datasets/MUG500plusD5Development400_v1}"
OUTPUT_WORKING="${OUTPUT_FINAL}.generating"
WORKERS="${MUG500PLUS_D5_GENERATION_WORKERS:-1}"

DEVELOPMENT_LOCK="$SOURCE_ROOT/data_locks/mug500plus_d5_development100_qc_lock_v1"
ACQUISITION_LOCK="$SOURCE_ROOT/data_locks/mug500plus_d5_source150_acquisition_lock_v1"
PROTOCOL_LOCK="$SOURCE_ROOT/data_locks/mug500plus_d5_development400_fourfold_protocol_lock_v1"
DEVELOPMENT_STL="$SOURCE_ROOT/raw_v20/clear_stl/d5_source150_v1/development"

for path in "$DEVELOPMENT_LOCK" "$ACQUISITION_LOCK" "$PROTOCOL_LOCK" "$DEVELOPMENT_STL"; do
  [[ -e "$path" ]] || { echo "[error] missing deployment path: $path"; exit 1; }
done
[[ ! -e "$OUTPUT_FINAL" ]] || { echo "[error] final output already exists: $OUTPUT_FINAL"; exit 1; }
[[ ! -e "$OUTPUT_WORKING" ]] || { echo "[error] working output requires inspection: $OUTPUT_WORKING"; exit 1; }

python -m py_compile \
  tools/generate_mamba_v15_d5_mug500plus_development_cases.py \
  tools/lock_mamba_v15_d5_mug500plus_development_fourfold_protocol.py

echo "[preflight] verify frozen D5 development100 assets and protocol"
python -u tools/generate_mamba_v15_d5_mug500plus_development_cases.py \
  --development100_qc_lock_dir "$DEVELOPMENT_LOCK" \
  --source150_acquisition_lock_dir "$ACQUISITION_LOCK" \
  --protocol_lock_dir "$PROTOCOL_LOCK" \
  --development_source_root "$DEVELOPMENT_STL" \
  --out_dir "$OUTPUT_WORKING" \
  --d5_protocol_json \
    docs/mamba_v15_d5_mug500plus_development_generation_fourfold_protocol_v1.json \
  --base_protocol_json \
    docs/mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json \
  --num_workers "$WORKERS" \
  --preflight_only

echo "[start] frozen D5 development400 generation"
python -u tools/generate_mamba_v15_d5_mug500plus_development_cases.py \
  --development100_qc_lock_dir "$DEVELOPMENT_LOCK" \
  --source150_acquisition_lock_dir "$ACQUISITION_LOCK" \
  --protocol_lock_dir "$PROTOCOL_LOCK" \
  --development_source_root "$DEVELOPMENT_STL" \
  --out_dir "$OUTPUT_WORKING" \
  --d5_protocol_json \
    docs/mamba_v15_d5_mug500plus_development_generation_fourfold_protocol_v1.json \
  --base_protocol_json \
    docs/mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json \
  --num_workers "$WORKERS"

(
  cd "$OUTPUT_WORKING"
  sha256sum -c files.sha256
)
[[ "$(find "$OUTPUT_WORKING/cases" -maxdepth 1 -type f -name '*.npz' | wc -l)" -eq 400 ]]

mv "$OUTPUT_WORKING" "$OUTPUT_FINAL"
echo "[done] D5 development400 frozen generation completed"
echo "[output] $OUTPUT_FINAL"
echo "[locked] model=false training=false selection=false sealed=false pending_audit=true"
echo "[next] run the separate D5 generation audit"
