#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1
export TQDM_MININTERVAL="${TQDM_MININTERVAL:-1}"

D22_ROOT="logs/skullbreak_mamba_v12_d22_local_rim"
NEGATIVE_DIR="$D22_ROOT/frozen_negative_result_v1"
POSTHOC_ROOT="$D22_ROOT/posthoc_contact_support_v1"
REPLAY_DIR="$POSTHOC_ROOT/replay"
ANALYSIS_DIR="$POSTHOC_ROOT/analysis"
BASE_PROTOCOL="logs/skullbreak_mamba_v12_development/protocol_v1"

python tools/test_mamba_v12_d22_negative_freeze.py
python tools/test_mamba_v12_d22_contact_support_posthoc.py
bash scripts/freeze_skullbreak_mamba_v12_d22_negative_result.sh

mkdir -p "$REPLAY_DIR" "$ANALYSIS_DIR"
python tools/replay_mamba_v12_d22_contact_support.py \
  --records_root "$D22_ROOT/round_a" \
  --negative_receipt "$NEGATIVE_DIR/negative_result_receipt.json" \
  --posthoc_protocol docs/mamba_v12_d22_contact_support_posthoc_v1.json \
  --development_case_ids "$BASE_PROTOCOL/development84_case_ids.txt" \
  --confirmation_case_ids "$BASE_PROTOCOL/confirmation20_case_ids.txt" \
  --output_dir "$REPLAY_DIR" \
  --device "${DEVICE:-cuda:0}"

python tools/analyze_mamba_v12_d22_contact_support_posthoc.py \
  --per_case "$REPLAY_DIR/contact_support_per_case.csv" \
  --replay_summary "$REPLAY_DIR/contact_support_replay_summary.json" \
  --negative_receipt "$NEGATIVE_DIR/negative_result_receipt.json" \
  --output_dir "$ANALYSIS_DIR"

find "$POSTHOC_ROOT" -type f \
  ! -name posthoc_tree_sha256.txt \
  ! -name posthoc_tree_sha256.txt.sha256 \
  -print0 | sort -z | xargs -0 sha256sum \
  > "$POSTHOC_ROOT/posthoc_tree_sha256.txt"
sha256sum "$POSTHOC_ROOT/posthoc_tree_sha256.txt" \
  > "$POSTHOC_ROOT/posthoc_tree_sha256.txt.sha256"
sha256sum -c "$POSTHOC_ROOT/posthoc_tree_sha256.txt.sha256"

echo "[done] D2.2 post-hoc contact-support replay and analysis"
echo "[report] $ANALYSIS_DIR/contact_support_posthoc_report_zh.md"
echo "[locked] selection unchanged; Round B remains forbidden"
echo "[locked] confirmation20, old monitor, and official test were not accessed"
