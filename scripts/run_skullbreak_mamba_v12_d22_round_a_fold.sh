#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CANDIDATE="${1:?Pass R0, R1, or R2}"
FOLD="${2:?Pass fold A, B, C, or D}"
[[ "$CANDIDATE" =~ ^R[0-2]$ ]] || { echo "[error] invalid candidate: $CANDIDATE"; exit 2; }
[[ "$FOLD" =~ ^[A-D]$ ]] || { echo "[error] invalid fold: $FOLD"; exit 2; }

ROOT="logs/skullbreak_mamba_v12_d22_local_rim"
CONFIG_DIR="cfgs/SkullBreak_models/generated_mamba_v12_d22_local_rim_v1"
CONFIG="${CONFIG_DIR}/MambaV12D22LocalRim_${CANDIDATE}_fold${FOLD}_seed0.yaml"
CONFIG_STEM="$(basename "$CONFIG" .yaml)"
CONFIG_PARENT="$(basename "$(dirname "$CONFIG")")"
EXP_NAME="skullbreak_mamba_v12_d22_${CANDIDATE}_fold${FOLD}_seed0"
EXP_DIR="experiments/${CONFIG_STEM}/${CONFIG_PARENT}/${EXP_NAME}"
RUN_DIR="${ROOT}/round_a/${CANDIDATE}_fold${FOLD}_seed0"
R0_RUN_DIR="${ROOT}/round_a/R0_fold${FOLD}_seed0"
EVAL_DIR="${RUN_DIR}/evaluation"
INSTRUMENT_DIR="${RUN_DIR}/instrumentation"
RAW_CKPT="${EXP_DIR}/ckpt-last.pth"
BNCAL_CKPT="${EXP_DIR}/ckpt-last-bncal.pth"
TEACHER_CACHE="${ROOT}/teacher_cache/seed0/fold${FOLD}/teacher_cache.json"
MIN_FREE_GB="${MIN_FREE_GB:-8}"

[[ -f "${ROOT}/preflight_receipt.json" && -f "$CONFIG" ]] || {
  echo "[error] run D2.2 prepare/preflight script first"
  exit 2
}
(
  cd "$ROOT"
  sha256sum -c preflight_receipt.json.sha256
)
(
  cd "${ROOT}/gt_rim_cache/fold${FOLD}"
  sha256sum -c files.sha256
)
if [[ "$CANDIDATE" != "R0" && ! -f "${R0_RUN_DIR}/run_record.json" ]]; then
  echo "[error] same-fold R0 must be frozen before $CANDIDATE"
  exit 2
fi
if [[ "$CANDIDATE" == "R2" && ! -f "$TEACHER_CACHE" ]]; then
  echo "[error] same-fold R0 teacher cache is missing"
  exit 2
fi

if [[ -f "${RUN_DIR}/run_record.json" ]]; then
  if [[ "$CANDIDATE" == "R0" && ! -f "$TEACHER_CACHE" ]]; then
    python tools/generate_mamba_v12_d22_teacher_cache.py \
      --config "$CONFIG" --ckpt "$BNCAL_CKPT" --fold "$FOLD" --seed 0 \
      --output "$TEACHER_CACHE" --batch_size 8 --num_workers 4
  fi
  echo "[locked] completed D2.2 run already exists: ${RUN_DIR}/run_record.json"
  exit 0
fi

mkdir -p "$RUN_DIR" "$EVAL_DIR" "$INSTRUMENT_DIR"
free_kb="$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
required_kb="$((MIN_FREE_GB * 1024 * 1024))"
if (( free_kb < required_kb )); then
  echo "[error] less than ${MIN_FREE_GB} GiB free on HOME"
  df -h "$HOME"
  exit 1
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
TRAIN_LOG="${RUN_DIR}/${EXP_NAME}_${STAMP}.log"
echo "[D2.2 Round A] candidate=${CANDIDATE} fold=${FOLD} seed=0"
echo "[locked] development84 only; protected splits forbidden"

if [[ ! -f "$BNCAL_CKPT" ]]; then
  resume_args=()
  if [[ -f "$RAW_CKPT" ]]; then
    checkpoint_epoch="$(python - "$RAW_CKPT" <<'PY'
import sys
import torch
print(int(torch.load(sys.argv[1], map_location="cpu").get("epoch", -1)))
PY
)"
    if (( checkpoint_epoch < 100 )); then
      resume_args+=(--resume)
    fi
  fi
  if [[ ! -f "$RAW_CKPT" || "${#resume_args[@]}" -gt 0 ]]; then
    PYTHONUNBUFFERED=1 python main.py \
      --config "$CONFIG" --exp_name "$EXP_NAME" \
      --num_workers 4 --val_freq 10 --seed 0 --deterministic \
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
    --config "$CONFIG" --ckpt "$RAW_CKPT" --output "$BNCAL_CKPT" \
    --batch_size 8 --max_batches 40 --num_workers 4 --seed 0
else
  echo "[resume] BNCal checkpoint exists; skip training"
fi

TRAIN_LOG="$(find "$RUN_DIR" -maxdepth 1 -type f -name "${EXP_NAME}_*.log" -print | sort | tail -n 1)"
[[ -n "$TRAIN_LOG" && -f "$TRAIN_LOG" ]] || {
  echo "[error] completed training log not found in $RUN_DIR"
  exit 1
}

if [[ "$CANDIDATE" == "R0" ]]; then
  python tools/generate_mamba_v12_d22_teacher_cache.py \
    --config "$CONFIG" --ckpt "$BNCAL_CKPT" --fold "$FOLD" --seed 0 \
    --output "$TEACHER_CACHE" --batch_size 8 --num_workers 4
  python tools/generate_mamba_v12_d22_teacher_cache.py \
    --config "$CONFIG" --ckpt "$BNCAL_CKPT" --fold "$FOLD" --seed 0 \
    --output "$TEACHER_CACHE" --batch_size 8 --num_workers 4
fi

python tools/evaluate_skullfix_implant.py \
  --config "$CONFIG" --ckpt "$BNCAL_CKPT" --split val \
  --num_samples 0 --seed 0 --out_dir "$EVAL_DIR" \
  --rim_band_mm 2.0 --bootstrap_samples 2000 --confidence 0.95 \
  --dataset_label SkullBreak --include_coarse_rim_metrics

python tools/instrument_mamba_full_pipeline.py \
  --config "$CONFIG" --ckpt "$BNCAL_CKPT" --split val \
  --out_dir "$INSTRUMENT_DIR" --seed 0

python tools/benchmark_mamba_v12_efficiency.py \
  --config "$CONFIG" --ckpt "$BNCAL_CKPT" --split val \
  --warmup 10 --repeats 50 --output "${RUN_DIR}/efficiency.json"

METRICS_CSV="$(find "$EVAL_DIR" -maxdepth 1 -type f -name '*_per_sample.csv' -print -quit)"
METRICS_SUMMARY="$(find "$EVAL_DIR" -maxdepth 1 -type f -name '*_summary.json' -print -quit)"
extra_artifacts=(
  --extra_artifact "preflight_receipt=${ROOT}/preflight_receipt.json"
  --extra_artifact "protocol=docs/mamba_v12_d22_local_rim_trust_protocol_v1.json"
  --extra_artifact "implementation_amendment=docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1.json"
)
if [[ "$CANDIDATE" != "R0" ]]; then
  extra_artifacts+=(
    --extra_artifact "gt_rim_manifest=${ROOT}/gt_rim_cache/fold${FOLD}/gt_rim_manifest.jsonl"
    --extra_artifact "gt_rim_hashes=${ROOT}/gt_rim_cache/fold${FOLD}/files.sha256"
  )
fi
if [[ "$CANDIDATE" == "R0" || "$CANDIDATE" == "R2" ]]; then
  extra_artifacts+=(
    --extra_artifact "teacher_cache=${TEACHER_CACHE}"
    --extra_artifact "teacher_cache_hash=${TEACHER_CACHE}.sha256"
  )
fi
python tools/write_mamba_v12_run_record.py \
  --candidate "$CANDIDATE" --fold "$FOLD" --seed 0 \
  --config "$CONFIG" --checkpoint "$BNCAL_CKPT" \
  --metrics_csv "$METRICS_CSV" --metrics_summary "$METRICS_SUMMARY" \
  --efficiency "${RUN_DIR}/efficiency.json" --training_log "$TRAIN_LOG" \
  "${extra_artifacts[@]}" \
  --output "${RUN_DIR}/run_record.json"

rm -f -- "$RAW_CKPT"
echo "[done] D2.2 Round A ${CANDIDATE} fold=${FOLD} seed=0 $(date)"
echo "[locked] result immutable; protected splits were not run"
