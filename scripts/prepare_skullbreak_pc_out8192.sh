#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

TRAINING_ROOT="${TRAINING_ROOT:-$HOME/datasets/SkullBreak/raw/train}"
EVALUATION_ROOT="${EVALUATION_ROOT:-$HOME/datasets/SkullBreak/raw/test}"
OUT_ROOT="${OUT_ROOT:-$HOME/datasets/SkullBreakPC_out8192}"
SEED="${SEED:-20260703}"
GATE_SPLIT="${GATE_SPLIT:-0.8,0.1,0.1}"
MONITOR_SKULLS="${MONITOR_SKULLS:-10}"
WORKERS="${WORKERS:-1}"

python tools/prepare_skullbreak_pointcloud.py \
  --training_root "$TRAINING_ROOT" \
  --evaluation_root "$EVALUATION_ROOT" \
  --output_root "$OUT_ROOT" \
  --n_partial 8192 \
  --n_complete 8192 \
  --n_implant 8192 \
  --seed "$SEED" \
  --gate_split "$GATE_SPLIT" \
  --monitor_skulls "$MONITOR_SKULLS" \
  --strict_geometry \
  --workers "$WORKERS" \
  --overwrite

mkdir -p data
if [[ -e data/SkullBreakPC_out8192 && ! -L data/SkullBreakPC_out8192 ]]; then
  echo "[error] data/SkullBreakPC_out8192 exists and is not a symlink" >&2
  exit 1
fi
ln -sfn "$OUT_ROOT" data/SkullBreakPC_out8192
python tools/check_skullbreak_pointcloud.py \
  --data_root "$OUT_ROOT" \
  --expected_train_skulls 114 \
  --expected_test_skulls 20 \
  --verify_checksums
