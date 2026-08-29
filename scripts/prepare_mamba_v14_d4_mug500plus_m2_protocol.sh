#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${MUG500PLUS_D4_SOURCE100_QC_LOCK_DIR:?set MUG500PLUS_D4_SOURCE100_QC_LOCK_DIR}"
: "${MUG500PLUS_D4_M2_PROTOCOL_LOCK_DIR:?set MUG500PLUS_D4_M2_PROTOCOL_LOCK_DIR}"

python -m py_compile \
  tools/generate_mamba_v14_d4_mug500plus_m2.py \
  tools/lock_mamba_v14_d4_mug500plus_m2_fourfold_protocol.py \
  tools/test_mamba_v14_d4_mug500plus_m2_fourfold_protocol.py

python tools/test_mamba_v14_d4_mug500plus_m2_fourfold_protocol.py

args=(
  --source100_qc_lock_dir "$MUG500PLUS_D4_SOURCE100_QC_LOCK_DIR"
  --protocol_json docs/mamba_v14_d4_mug500plus_m2_fourfold_protocol_v1.json
  --generator_entry tools/generate_mamba_v14_d4_mug500plus_m2.py
  --engine tools/generate_mug500plus_m2_synthetic_defects.py
  --base_protocol docs/mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json
  --test_script tools/test_mamba_v14_d4_mug500plus_m2_fourfold_protocol.py
  --out_dir "$MUG500PLUS_D4_M2_PROTOCOL_LOCK_DIR"
)

python tools/lock_mamba_v14_d4_mug500plus_m2_fourfold_protocol.py "${args[@]}"
python tools/lock_mamba_v14_d4_mug500plus_m2_fourfold_protocol.py "${args[@]}"

(
  cd "$MUG500PLUS_D4_M2_PROTOCOL_LOCK_DIR"
  sha256sum -c files.sha256
)

echo "[done] D4 M2 generation and source-fourfold protocol frozen"
echo "[authorized-next] frozen D4 M2 generation only"
echo "[locked] generation_not_started=true training=false selection=false protected=false"
