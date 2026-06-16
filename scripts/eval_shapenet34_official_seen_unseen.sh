#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate adapointr-server
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CKPT="${1:-experiments/AdaPoinTr/ShapeNet34_models/shapenet34_adapointr_official_full_4gpu/ckpt-best.pth}"
RUN_TAG="${RUN_TAG:-shapenet34_adapointr_official_full_4gpu}"
NUM_WORKERS="${NUM_WORKERS:-4}"
LOG_DIR="${LOG_DIR:-logs/shapenet34_official_eval}"

RUN_TAG="$RUN_TAG" NUM_WORKERS="$NUM_WORKERS" LOG_DIR="$LOG_DIR" \
SEEN_CONFIG="cfgs/ShapeNet34_models/AdaPoinTr.yaml" \
UNSEEN_CONFIG="cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml" \
  bash scripts/eval_shapenet34_adapointr_seen_unseen.sh "$CKPT"
