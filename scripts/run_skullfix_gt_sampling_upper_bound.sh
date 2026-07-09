#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

MANIFEST="${MANIFEST:-data/SkullFixPC/manifest.jsonl}"
DATA_ROOT="${DATA_ROOT:-data/SkullFixPC}"
RAW_ROOT="${RAW_ROOT:-$HOME/datasets/SkullFixRaw}"
SPLIT="${SPLIT:-test}"
COUNTS="${COUNTS:-1024,2048,4096,8192,16384}"
MAX_SAMPLES="${MAX_SAMPLES:-0}"
SPLAT_RADIUS_MM="${SPLAT_RADIUS_MM:-1.0}"
OUT_DIR="${OUT_DIR:-logs/skullfix_implant_point_count/gt_sampling_upper_bound}"

python tools/evaluate_skullfix_gt_sampling_upper_bound.py \
  --manifest "$MANIFEST" \
  --data_root "$DATA_ROOT" \
  --raw_root "$RAW_ROOT" \
  --split "$SPLIT" \
  --counts "$COUNTS" \
  --max_samples "$MAX_SAMPLES" \
  --splat_radius_mm "$SPLAT_RADIUS_MM" \
  --out_dir "$OUT_DIR"
