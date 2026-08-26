#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python tools/test_mamba_v13_d3_contact.py
python tools/test_mamba_v13_d3_data_protocol.py
python tools/test_mamba_v13_d3_model_contract.py
python -m py_compile \
  models/AdaPoinTr.py \
  tools/runner.py \
  tools/lock_mamba_v13_d3_data_protocol.py

required=(
  D3_EXTERNAL_MANIFEST
  D3_PROTECTED_FINGERPRINTS
  D3_GENERATOR_SHA256
  D3_SURFACE_FINGERPRINT_ALGORITHM_SHA256
)
missing=()
for name in "${required[@]}"; do
  [[ -n "${!name:-}" ]] || missing+=("$name")
done

if (( ${#missing[@]} > 0 )); then
  echo "[blocked] D3 candidate training has not started"
  echo "[blocked] missing new-data inputs: ${missing[*]}"
  echo "[next] generate and audit the locked healthy125 x four-family M2 manifest"
  exit 2
fi

python tools/lock_mamba_v13_d3_data_protocol.py \
  --manifest "$D3_EXTERNAL_MANIFEST" \
  --protected_fingerprints "$D3_PROTECTED_FINGERPRINTS" \
  --generator_sha256 "$D3_GENERATOR_SHA256" \
  --surface_fingerprint_algorithm_sha256 \
    "$D3_SURFACE_FINGERPRINT_ALGORITHM_SHA256" \
  --expected_skulls 125 \
  --output_dir logs/mamba_v13_d3_contact_support/protocol_v1

echo "[ready] D3 independent-data protocol passed all hard audits"
echo "[locked] candidate configs and training remain a separate frozen step"
