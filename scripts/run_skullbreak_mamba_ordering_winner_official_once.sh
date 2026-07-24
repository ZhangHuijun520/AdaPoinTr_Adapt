#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

DECISION="logs/skullbreak_mamba_ordering_v11_out8192/ordering_decision_seed0.json"
ATTEMPT="logs/skullbreak_mamba_ordering_v11_out8192/official_test_attempt_seed0.json"
RECEIPT="logs/skullbreak_mamba_ordering_v11_out8192/official_test_receipt_seed0.json"
if [[
  -e "$ATTEMPT" || -e "${ATTEMPT}.sha256" ||
  -e "$RECEIPT" || -e "${RECEIPT}.sha256"
]]; then
  echo "[error] official test has already started or completed"
  exit 1
fi

mapfile -t WINNER < <(
  python tools/select_skullbreak_mamba_ordering.py winner \
    --repo_root . \
    --manifest data/SkullBreakPC_out8192/manifest.jsonl \
    --decision "$DECISION"
)

CANDIDATE="${WINNER[0]}"
ORDER="${WINNER[1]}"
CONFIG="${WINNER[2]}"
CKPT="${WINNER[3]}"
CONFIG_STEM="$(basename "$CONFIG" .yaml)"
OUT_DIR="logs/skullbreak_mamba_ordering_v11_out8192_official/${CANDIDATE}_${ORDER}_seed0"
PRED_DIR="logs/skullbreak_mamba_ordering_v11_out8192_official/${CANDIDATE}_${ORDER}_seed0_predictions"
OFFICIAL_CSV="${OUT_DIR}/${CONFIG_STEM}_test_per_sample.csv"
PRED_MANIFEST="${PRED_DIR}/predictions_manifest.jsonl"

echo "[official unlock] candidate=${CANDIDATE} order=${ORDER}"
echo "[policy] this is the single permitted official-test run"

python tools/select_skullbreak_mamba_ordering.py start-official \
  --repo_root . \
  --manifest data/SkullBreakPC_out8192/manifest.jsonl \
  --decision "$DECISION" \
  --attempt "$ATTEMPT" \
  --receipt "$RECEIPT"

python tools/evaluate_skullfix_implant.py \
  --config "$CONFIG" \
  --ckpt "$CKPT" \
  --split test \
  --num_samples 0 \
  --seed 0 \
  --out_dir "$OUT_DIR" \
  --rim_band_mm 2.0 \
  --bootstrap_samples 2000 \
  --confidence 0.95 \
  --dataset_label SkullBreak \
  --save_predictions_dir "$PRED_DIR"

python tools/select_skullbreak_mamba_ordering.py record-official \
  --repo_root . \
  --manifest data/SkullBreakPC_out8192/manifest.jsonl \
  --decision "$DECISION" \
  --attempt "$ATTEMPT" \
  --official_csv "$OFFICIAL_CSV" \
  --predictions_manifest "$PRED_MANIFEST" \
  --receipt "$RECEIPT"

echo "[done] official test consumed for frozen winner"
echo "[locked] do not reopen candidate definitions or selection rules"
