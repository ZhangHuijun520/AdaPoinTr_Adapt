#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

ROOT="logs/skullbreak_mamba_v12_d21_geometry"
RECORDS="${ROOT}/round_a"
AUDIT="${ROOT}/round_a_top2_gate_failure.json"
POSTHOC="${ROOT}/posthoc_paired_geometry"
LABELS="${POSTHOC}/labels/round_a_case_labels.csv"
REPLAY="${POSTHOC}/gt_replay/gt_geometry_per_case.csv"

[[ -f "$AUDIT" ]] || { echo "[error] frozen D2.1 gate audit missing"; exit 2; }

python tools/prepare_mamba_v12_d21_posthoc_labels.py \
  --records_root "$RECORDS" \
  --gate_audit "$AUDIT" \
  --output_dir "${POSTHOC}/labels"

python tools/replay_mamba_v12_round_a_gt_geometry.py \
  --records_root "$RECORDS" \
  --case_labels "$LABELS" \
  --gate_audit "$AUDIT" \
  --output_dir "${POSTHOC}/gt_replay" \
  --device cuda:0 \
  --rim_band_mm 2.0

python tools/analyze_mamba_v12_d21_paired_geometry.py \
  --case_labels "$LABELS" \
  --gt_geometry "$REPLAY" \
  --gate_audit "$AUDIT" \
  --output_dir "${POSTHOC}/analysis"

echo "[done] D2.1 post-hoc paired geometry replay"
echo "[report] ${POSTHOC}/analysis/paired_posthoc_report_zh.md"
echo "[locked] Round B remains forbidden; no protected split was accessed"
