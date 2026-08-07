#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u
cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CANDIDATE="${1:?Pass frozen Round-A candidate}"
FOLD="${2:?Pass fold A-D}"
[[ "$CANDIDATE" =~ ^C[0-3]$ && "$FOLD" =~ ^[A-D]$ ]] || exit 2

ROOT="logs/skullbreak_mamba_v12_development"
CONFIG="cfgs/SkullBreak_models/generated_mamba_v12_dev_round_b/MambaV12Dev_${CANDIDATE}_fold${FOLD}_seed1.yaml"
CONFIG_STEM="$(basename "$CONFIG" .yaml)"
CONFIG_PARENT="$(basename "$(dirname "$CONFIG")")"
EXP_NAME="skullbreak_mamba_v12_${CANDIDATE}_fold${FOLD}_seed1"
EXP_DIR="experiments/${CONFIG_STEM}/${CONFIG_PARENT}/${EXP_NAME}"
RUN_DIR="${ROOT}/round_b/${CANDIDATE}_fold${FOLD}_seed1"
EVAL_DIR="${RUN_DIR}/evaluation"
INSTRUMENT_DIR="${RUN_DIR}/instrumentation"
STAMP="$(date +%Y%m%d_%H%M%S)"
TRAIN_LOG="${RUN_DIR}/${EXP_NAME}_${STAMP}.log"
RAW_CKPT="${EXP_DIR}/ckpt-last.pth"
BNCAL_CKPT="${EXP_DIR}/ckpt-last-bncal.pth"

[[ -f "$CONFIG" ]] || { echo "[error] locked Round-B config missing"; exit 2; }
[[ ! -e "${RUN_DIR}/run_record.json" ]] || {
  echo "[locked] completed run already exists: ${RUN_DIR}/run_record.json"
  exit 0
}
mkdir -p "$RUN_DIR" "$EVAL_DIR" "$INSTRUMENT_DIR"

echo "[Round B] frozen candidate=${CANDIDATE} fold=${FOLD} seed=1"
echo "[locked] definitions unchanged; old monitor and official test forbidden"
if [[ ! -f "$BNCAL_CKPT" ]]; then
  resume_args=()
  if [[ -f "$RAW_CKPT" ]]; then
    checkpoint_epoch="$(python - "$RAW_CKPT" <<'PY'
import sys
import torch
print(int(torch.load(sys.argv[1], map_location="cpu").get("epoch", -1)))
PY
)"
    if (( checkpoint_epoch >= 100 )); then
      echo "[resume] epoch-100 raw checkpoint exists; skip training"
    else
      echo "[resume] checkpoint epoch=${checkpoint_epoch}; resume training"
      resume_args+=(--resume)
    fi
  fi
  if [[ ! -f "$RAW_CKPT" || "${#resume_args[@]}" -gt 0 ]]; then
    PYTHONUNBUFFERED=1 python main.py \
      --config "$CONFIG" --exp_name "$EXP_NAME" \
      --num_workers 4 --val_freq 10 --seed 1 --deterministic \
      "${resume_args[@]}" 2>&1 | tee "$TRAIN_LOG"
  fi
  final_epoch="$(python - "$RAW_CKPT" <<'PY'
import sys
import torch
print(int(torch.load(sys.argv[1], map_location="cpu").get("epoch", -1)))
PY
)"
  [[ "$final_epoch" == "100" ]] || {
    echo "[error] expected epoch-100 checkpoint, found epoch=${final_epoch}"
    exit 1
  }

  python tools/recalibrate_skullfix_batchnorm.py \
    --config "$CONFIG" --ckpt "$RAW_CKPT" \
    --output "$BNCAL_CKPT" \
    --batch_size 8 --max_batches 40 --num_workers 4 --seed 1
else
  echo "[resume] BN-calibrated checkpoint exists; skip training and BNCal"
fi

TRAIN_LOG="$(find "$RUN_DIR" -maxdepth 1 -type f \
  -name "${EXP_NAME}_*.log" -print | sort | tail -n 1)"
[[ -n "$TRAIN_LOG" && -f "$TRAIN_LOG" ]] || {
  echo "[error] completed training log not found in $RUN_DIR"
  exit 1
}

python tools/evaluate_skullfix_implant.py \
  --config "$CONFIG" --ckpt "$BNCAL_CKPT" \
  --split val --num_samples 0 --seed 1 --out_dir "$EVAL_DIR" \
  --rim_band_mm 2.0 --bootstrap_samples 2000 --confidence 0.95 \
  --dataset_label SkullBreak

python tools/instrument_mamba_full_pipeline.py \
  --config "$CONFIG" --ckpt "$BNCAL_CKPT" \
  --split val --out_dir "$INSTRUMENT_DIR" --seed 1

python tools/benchmark_mamba_v12_efficiency.py \
  --config "$CONFIG" --ckpt "$BNCAL_CKPT" \
  --split val --warmup 10 --repeats 50 \
  --output "${RUN_DIR}/efficiency.json"

METRICS_CSV="$(find "$EVAL_DIR" -maxdepth 1 -type f -name '*_per_sample.csv' -print -quit)"
METRICS_SUMMARY="$(find "$EVAL_DIR" -maxdepth 1 -type f -name '*_summary.json' -print -quit)"
python tools/write_mamba_v12_run_record.py \
  --candidate "$CANDIDATE" --fold "$FOLD" --seed 1 \
  --config "$CONFIG" --checkpoint "$BNCAL_CKPT" \
  --metrics_csv "$METRICS_CSV" --metrics_summary "$METRICS_SUMMARY" \
  --efficiency "${RUN_DIR}/efficiency.json" --training_log "$TRAIN_LOG" \
  --output "${RUN_DIR}/run_record.json"

rm -f -- "$RAW_CKPT"
echo "[done] Round B ${CANDIDATE} fold=${FOLD} seed=1"
