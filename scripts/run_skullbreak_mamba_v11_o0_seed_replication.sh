#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

SEED="${1:?Pass replication seed 1 or 2}"
if [[ "$SEED" != "1" && "$SEED" != "2" ]]; then
  echo "[error] R1 only permits seed 1 or 2, got: $SEED"
  exit 2
fi

CONFIG="cfgs/SkullBreak_models/MambaAdapterV11OrderingO0_xyz_out8192_monitor.yaml"
CONFIG_STEM="$(basename "$CONFIG" .yaml)"
EXP_NAME="skullbreak_mamba_v11_o0_xyz_seed${SEED}_replication"
EXP_DIR="experiments/${CONFIG_STEM}/SkullBreak_models/${EXP_NAME}"
ROOT_LOG="logs/skullbreak_mamba_v11_o0_multiseed"
SEED_LOG="${ROOT_LOG}/seed${SEED}"
EVAL_DIR="${ROOT_LOG}/monitor/seed${SEED}"
INSTRUMENT_DIR="${ROOT_LOG}/instrumentation/seed${SEED}"
PROTOCOL_DIR="${ROOT_LOG}/protocol"
PANEL="${PROTOCOL_DIR}/strict_train_instrumentation_panel.json"
STAMP="$(date +%Y%m%d_%H%M%S)"
RESUME="${RESUME:-0}"
MIN_FREE_GB="${MIN_FREE_GB:-5}"

mkdir -p "$SEED_LOG" "$PROTOCOL_DIR"

python tools/audit_skullbreak_ordering_protocol.py \
  --manifest data/SkullBreakPC_out8192/manifest.jsonl \
  --output "${PROTOCOL_DIR}/strict_monitor_protocol_audit.json"

python tools/select_skullbreak_mamba_instrumentation_panel.py \
  --config "$CONFIG" \
  --output "$PANEL" \
  --num_cases 20 \
  --selection_seed 20260803

python tools/test_mamba_adapter_instrumentation.py

python tools/verify_mamba_instrumentation_zero_perturbation.py \
  --config "$CONFIG" \
  --panel "$PANEL" \
  --output "${PROTOCOL_DIR}/zero_perturbation_before_seed${SEED}.json" \
  --num_cases 2 \
  --seed 20260803

free_kb="$(df -Pk "$HOME" | awk 'NR==2 {print $4}')"
required_kb="$((MIN_FREE_GB * 1024 * 1024))"
if (( free_kb < required_kb )); then
  echo "[error] less than ${MIN_FREE_GB} GiB free on $HOME"
  df -h "$HOME"
  exit 1
fi

train_args=(
  --config "$CONFIG"
  --exp_name "$EXP_NAME"
  --num_workers 4
  --val_freq 10
  --seed "$SEED"
  --deterministic
)
if [[ "$RESUME" == "1" ]]; then
  train_args+=(--resume)
fi

echo "[R1] frozen O0=xyz replication seed=${SEED}"
echo "[protocol] strict train=520/104 monitor=50/10 official-test=forbidden"
echo "[instrumentation] strict-train panel=${PANEL}"

PYTHONUNBUFFERED=1 python main.py "${train_args[@]}" \
  2>&1 | tee "${SEED_LOG}/${EXP_NAME}_${STAMP}.log"

python tools/recalibrate_skullfix_batchnorm.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last.pth" \
  --output "${EXP_DIR}/ckpt-last-bncal.pth" \
  --batch_size 8 \
  --max_batches 65 \
  --num_workers 4 \
  --seed "$SEED"

python tools/evaluate_skullfix_implant.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last-bncal.pth" \
  --split val \
  --num_samples 0 \
  --seed "$SEED" \
  --out_dir "$EVAL_DIR" \
  --rim_band_mm 2.0 \
  --bootstrap_samples 2000 \
  --confidence 0.95 \
  --dataset_label SkullBreak

bash scripts/instrument_skullbreak_mamba_v11_o0_checkpoint.sh \
  "$SEED" \
  "${EXP_DIR}/ckpt-last-bncal.pth" \
  "$INSTRUMENT_DIR"

echo "[done] R1 seed=${SEED} $(date)"
echo "[locked] no official-test evaluation was run"
echo "[locked] do not alter seed 2 after inspecting seed 1"
