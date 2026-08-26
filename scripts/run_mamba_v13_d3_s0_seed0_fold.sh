#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
cd "$ROOT"

FOLD="${1:?Pass fold A, B, C, or D}"
[[ "$FOLD" =~ ^[A-D]$ ]] || { echo "[error] invalid fold: $FOLD"; exit 2; }

CONFIG_DIR="cfgs/MUG500plus_models/generated_mamba_v13_d3_s0_seed0_v1"
CONFIG="${CONFIG_DIR}/MambaV13D3_S0_fold${FOLD}_seed0.yaml"
AUTH_DIR="logs/mamba_v13_d3_mug500plus/s0_seed0_authorization_v1"
AUTH_RECEIPT="${AUTH_DIR}/s0_seed0_authorization_receipt.json"
SMOKE_DIR="logs/mamba_v13_d3_mug500plus/s0_seed0_smoke_v1"
SMOKE_RECEIPT="${SMOKE_DIR}/s0_seed0_smoke_receipt.json"
DEPLOYMENT_RECEIPT="logs/mamba_v13_d3_mug500plus/data_deployment_v1/asset_deployment_receipt.json"
PROTOCOL_LOCK="${PROTOCOL_LOCK:-$HOME/baseline_archives/mamba_v13_d3_round_a_v1}"
CONFIG_STEM="$(basename "$CONFIG" .yaml)"
CONFIG_PARENT="$(basename "$(dirname "$CONFIG")")"
EXP_NAME="mug500plus_mamba_v13_d3_S0_fold${FOLD}_seed0"
EXP_DIR="experiments/${CONFIG_STEM}/${CONFIG_PARENT}/${EXP_NAME}"
RUN_DIR="logs/mamba_v13_d3_mug500plus/round_a/S0_fold${FOLD}_seed0"
EVAL_DIR="${RUN_DIR}/evaluation"
TRAIN_LOG="${RUN_DIR}/training.log"
RAW_CKPT="${EXP_DIR}/ckpt-last.pth"
BNCAL_CKPT="${EXP_DIR}/ckpt-last-bncal.pth"
EXPECTED_IDS="data/MUG500plusM2SourceSplitV1/fold${FOLD}_dev_case_ids.txt"
MIN_FREE_GB="${MIN_FREE_GB:-8}"

python tools/verify_mamba_v13_d3_s0_runtime_authorization.py \
  --config_dir "$CONFIG_DIR" \
  --receipt "$AUTH_RECEIPT"
python tools/smoke_mamba_v13_d3_s0_seed0.py \
  --config_dir "$CONFIG_DIR" \
  --authorization_receipt "$AUTH_RECEIPT" \
  --deployment_receipt "$DEPLOYMENT_RECEIPT" \
  --output "$SMOKE_RECEIPT" \
  --verify_only

if [[ -f "${RUN_DIR}/run_record.json" ]]; then
  (
    cd "$RUN_DIR"
    sha256sum -c run_record.json.sha256
  )
  echo "[locked] completed S0 run already exists: ${RUN_DIR}/run_record.json"
  exit 0
fi

for required in \
  "$CONFIG" "$AUTH_RECEIPT" "$SMOKE_RECEIPT" "$DEPLOYMENT_RECEIPT" \
  "$EXPECTED_IDS" "$PROTOCOL_LOCK/protocol_lock_receipt.json"; do
  [[ -f "$required" ]] || { echo "[error] required frozen artifact missing: $required"; exit 2; }
done

mkdir -p "$RUN_DIR" "$EVAL_DIR"
free_kb="$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
required_kb="$((MIN_FREE_GB * 1024 * 1024))"
if (( free_kb < required_kb )); then
  echo "[error] less than ${MIN_FREE_GB} GiB free on HOME"
  df -h "$HOME"
  exit 1
fi

echo "[D3 Round A] candidate=S0 fold=${FOLD} seed=0"
echo "[authorized] S0 only; development fold only"
echo "[locked] S1=false S2=false holdout=false selection_started=false"

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
      echo "[resume] checkpoint epoch=${checkpoint_epoch}; resume training"
      resume_args+=(--resume)
    else
      echo "[resume] epoch-100 raw checkpoint exists; skip training"
    fi
  fi

  if [[ ! -f "$RAW_CKPT" || "${#resume_args[@]}" -gt 0 ]]; then
    PYTHONUNBUFFERED=1 TQDM_MININTERVAL="${TQDM_MININTERVAL:-1}" \
      python main.py \
        --config "$CONFIG" \
        --exp_name "$EXP_NAME" \
        --num_workers 4 \
        --val_freq 10 \
        --seed 0 \
        --deterministic \
        "${resume_args[@]}" \
        2>&1 | tee -a "$TRAIN_LOG"
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
    --config "$CONFIG" \
    --ckpt "$RAW_CKPT" \
    --output "$BNCAL_CKPT" \
    --batch_size 8 \
    --max_batches 100000 \
    --num_workers 4 \
    --seed 0
else
  echo "[resume] BNCal checkpoint exists; skip training and recalibration"
fi

[[ -s "$TRAIN_LOG" ]] || {
  echo "[error] training log is missing: $TRAIN_LOG"
  exit 1
}
[[ -f "${BNCAL_CKPT}.json" ]] || {
  echo "[error] BNCal report is missing: ${BNCAL_CKPT}.json"
  exit 1
}

python tools/evaluate_skullfix_implant.py \
  --config "$CONFIG" \
  --ckpt "$BNCAL_CKPT" \
  --split val \
  --num_samples 0 \
  --seed 0 \
  --out_dir "$EVAL_DIR" \
  --rim_band_mm 2.0 \
  --bootstrap_samples 2000 \
  --confidence 0.95 \
  --dataset_label MUG500plusM2 \
  --include_coarse_rim_metrics

python tools/benchmark_mamba_v12_efficiency.py \
  --config "$CONFIG" \
  --ckpt "$BNCAL_CKPT" \
  --split val \
  --warmup 10 \
  --repeats 50 \
  --output "${RUN_DIR}/efficiency.json"

METRICS_CSV="$(find "$EVAL_DIR" -maxdepth 1 -type f -name '*_per_sample.csv' -print -quit)"
METRICS_SUMMARY="$(find "$EVAL_DIR" -maxdepth 1 -type f -name '*_summary.json' -print -quit)"
[[ -n "$METRICS_CSV" && -n "$METRICS_SUMMARY" ]] || {
  echo "[error] D3 evaluation outputs not found"
  exit 1
}

python tools/write_mamba_v13_d3_run_record.py \
  --candidate S0 \
  --fold "$FOLD" \
  --seed 0 \
  --config "$CONFIG" \
  --checkpoint "$BNCAL_CKPT" \
  --metrics_csv "$METRICS_CSV" \
  --metrics_summary "$METRICS_SUMMARY" \
  --efficiency "${RUN_DIR}/efficiency.json" \
  --training_log "$TRAIN_LOG" \
  --authorization_receipt "$AUTH_RECEIPT" \
  --smoke_receipt "$SMOKE_RECEIPT" \
  --expected_case_ids "$EXPECTED_IDS" \
  --extra_artifact "deployment_receipt=${DEPLOYMENT_RECEIPT}" \
  --extra_artifact "protocol_lock_receipt=${PROTOCOL_LOCK}/protocol_lock_receipt.json" \
  --extra_artifact "bncal_report=${BNCAL_CKPT}.json" \
  --output "${RUN_DIR}/run_record.json"

find "$EXP_DIR" -maxdepth 1 -type f -name 'ckpt*.pth' \
  ! -name 'ckpt-last-bncal.pth' -delete

echo "[done] D3 S0 fold=${FOLD} seed=0 $(date -u --iso-8601=seconds)"
echo "[retained] $BNCAL_CKPT"
echo "[locked] no holdout access and no model selection"
