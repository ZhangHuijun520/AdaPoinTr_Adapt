#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"

D22_ROOT="logs/skullbreak_mamba_v12_d22_local_rim"
OUTPUT="$D22_ROOT/frozen_negative_result_v1"

python tools/freeze_mamba_v12_d22_negative_result.py \
  --selection "$D22_ROOT/round_a_selection.json" \
  --records_root "$D22_ROOT/round_a" \
  --protocol docs/mamba_v12_d22_local_rim_trust_protocol_v1.json \
  --amendment docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1.json \
  --output_dir "$OUTPUT" \
  --verify_all_inputs

(
  cd "$OUTPUT"
  sha256sum -c files.sha256
  sha256sum -c files.sha256.sha256
)

echo "[done] D2.2 negative result frozen: $OUTPUT"
echo "[locked] positive mechanism signal but safety gate failed"
echo "[locked] winner=None; Round B forbidden"
