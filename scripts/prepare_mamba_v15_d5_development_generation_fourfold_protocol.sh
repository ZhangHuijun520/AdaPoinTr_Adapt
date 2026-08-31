#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${MUG500PLUS_D5_DEVELOPMENT100_QC_LOCK_DIR:?set MUG500PLUS_D5_DEVELOPMENT100_QC_LOCK_DIR}"
: "${MUG500PLUS_D5_SOURCE150_ACQUISITION_LOCK_DIR:?set MUG500PLUS_D5_SOURCE150_ACQUISITION_LOCK_DIR}"
: "${MUG500PLUS_D5_DEVELOPMENT_PROTOCOL_LOCK_DIR:?set MUG500PLUS_D5_DEVELOPMENT_PROTOCOL_LOCK_DIR}"

python -m py_compile \
  tools/generate_mamba_v15_d5_mug500plus_development_cases.py \
  tools/lock_mamba_v15_d5_mug500plus_development_fourfold_protocol.py \
  tools/test_mamba_v15_d5_mug500plus_development_fourfold_protocol.py

python tools/test_mamba_v15_d5_mug500plus_development_fourfold_protocol.py

args=(
  --development100_qc_lock_dir "$MUG500PLUS_D5_DEVELOPMENT100_QC_LOCK_DIR"
  --source150_acquisition_lock_dir "$MUG500PLUS_D5_SOURCE150_ACQUISITION_LOCK_DIR"
  --protocol_json docs/mamba_v15_d5_mug500plus_development_generation_fourfold_protocol_v1.json
  --generator_entry tools/generate_mamba_v15_d5_mug500plus_development_cases.py
  --engine tools/generate_mug500plus_m2_synthetic_defects.py
  --base_protocol docs/mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json
  --test_script tools/test_mamba_v15_d5_mug500plus_development_fourfold_protocol.py
  --out_dir "$MUG500PLUS_D5_DEVELOPMENT_PROTOCOL_LOCK_DIR"
)

python tools/lock_mamba_v15_d5_mug500plus_development_fourfold_protocol.py "${args[@]}"
python tools/lock_mamba_v15_d5_mug500plus_development_fourfold_protocol.py "${args[@]}"

(
  cd "$MUG500PLUS_D5_DEVELOPMENT_PROTOCOL_LOCK_DIR"
  sha256sum -c files.sha256
)

echo "[done] D5 development generation and source-fourfold protocol frozen"
echo "[authorized-next] frozen development400 generation only"
echo "[locked] generation_not_started=true model=false training=false selection=false sealed=false"
