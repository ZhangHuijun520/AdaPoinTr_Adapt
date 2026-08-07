#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

ROOT="logs/skullbreak_mamba_v12_development"
PROTOCOL_DIR="${ROOT}/protocol_v1"
PREFLIGHT_DIR="${ROOT}/preflight"
CONFIG_DIR="cfgs/SkullBreak_models/generated_mamba_v12_dev_v1"
mkdir -p "$ROOT" "$PREFLIGHT_DIR"

# Revision 2 migration: early overlays wrote derived verification files into
# the immutable protocol directory. Move only those two known files out before
# checking protocol byte identity; reject any conflicting destination.
for name in \
  full_instrumentation_zero_perturbation.json \
  full_instrumentation_zero_perturbation.json.sha256; do
  source_path="${PROTOCOL_DIR}/${name}"
  destination_path="${PREFLIGHT_DIR}/${name}"
  if [[ -f "$source_path" ]]; then
    if [[ -f "$destination_path" ]]; then
      if cmp -s -- "$source_path" "$destination_path"; then
        rm -f -- "$source_path"
      else
        echo "[error] conflicting preflight migration target: $destination_path"
        exit 1
      fi
    else
      mv -- "$source_path" "$destination_path"
    fi
    echo "[migrated] protocol-derived artifact -> $destination_path"
  fi
done

python tools/test_mamba_v12_development_protocol.py
python tools/test_mamba_v12_config_generation.py
python tools/test_mamba_v12_candidate_mechanisms.py

python tools/lock_skullbreak_mamba_v12_development_protocol.py \
  --manifest data/SkullBreakPC_out8192/manifest.jsonl \
  --output_dir "$PROTOCOL_DIR"

(
  cd "$PROTOCOL_DIR"
  sha256sum -c files.sha256
)

python tools/generate_skullbreak_mamba_v12_dev_configs.py \
  --protocol_dir "$PROTOCOL_DIR" \
  --output_dir "$CONFIG_DIR"

python tools/verify_mamba_full_instrumentation_zero_perturbation.py \
  --config "${CONFIG_DIR}/MambaV12Dev_C0_foldA_seed0.yaml" \
  --split val \
  --num_cases 2 \
  --output "${PREFLIGHT_DIR}/full_instrumentation_zero_perturbation.json"

echo "[ready] immutable D2 development protocol and 16 Round-A configs"
echo "[locked] old monitor and official test are absent"
