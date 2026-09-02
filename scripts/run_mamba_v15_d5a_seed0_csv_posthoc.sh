#!/usr/bin/env bash

set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V15_D5_LOG_ROOT:-$ROOT/logs/mamba_v15_d5_contact_support}"
COMPLETION="${MAMBA_V15_D5A_SEED0_COMPLETION_DIR:-$LOGS/d5a_seed0_training_completion_v1}"
OUTPUT="${MAMBA_V15_D5A_SEED0_CSV_POSTHOC_DIR:-$LOGS/d5a_seed0_csv_posthoc_v1}"

cd "$ROOT"

python -m py_compile \
  tools/analyze_mamba_v15_d5a_seed0_csv_posthoc.py \
  tools/test_mamba_v15_d5a_seed0_csv_posthoc.py

python tools/test_mamba_v15_d5a_seed0_csv_posthoc.py

python -u tools/analyze_mamba_v15_d5a_seed0_csv_posthoc.py \
  --completion_dir "$COMPLETION" \
  --output_dir "$OUTPUT"

(
  cd "$OUTPUT"
  sha256sum -c files.sha256
)

echo "[done] D5-A seed-0 CSV-only post-hoc completed"
echo "[locked] original 368/400 top-32 gate unchanged"
echo "[locked] seed1=false confirmation=false D5B=false selection=false sealed=false"
