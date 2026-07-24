#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CANDIDATE="${1:?Pass O0, O1, O2, or O3}"
case "$CANDIDATE" in
  O0)
    ORDER="xyz"
    CONFIG="cfgs/SkullBreak_models/MambaAdapterV11OrderingO0_xyz_out8192_monitor.yaml"
    EXP_NAME="skullbreak_mamba_v11_ordering_o0_xyz_seed0"
    EVAL_NAME="O0_xyz_monitor"
    ;;
  O1)
    ORDER="identity"
    CONFIG="cfgs/SkullBreak_models/MambaAdapterV11OrderingO1_identity_out8192_monitor.yaml"
    EXP_NAME="skullbreak_mamba_v11_ordering_o1_identity_seed0"
    EVAL_NAME="O1_identity_monitor"
    ;;
  O2)
    ORDER="zyx"
    CONFIG="cfgs/SkullBreak_models/MambaAdapterV11OrderingO2_zyx_out8192_monitor.yaml"
    EXP_NAME="skullbreak_mamba_v11_ordering_o2_zyx_seed0"
    EVAL_NAME="O2_zyx_monitor"
    ;;
  O3)
    ORDER="xzy"
    CONFIG="cfgs/SkullBreak_models/MambaAdapterV11OrderingO3_xzy_out8192_monitor.yaml"
    EXP_NAME="skullbreak_mamba_v11_ordering_o3_xzy_seed0"
    EVAL_NAME="O3_xzy_monitor"
    ;;
  *)
    echo "[error] unsupported candidate: $CANDIDATE"
    exit 2
    ;;
esac

DECISION="logs/skullbreak_mamba_ordering_v11_out8192/ordering_decision_seed0.json"
if [[ -e "$DECISION" || -e "${DECISION}.sha256" ]]; then
  echo "[error] ordering is already frozen; refusing candidate training"
  exit 1
fi

CONFIG_STEM="$(basename "$CONFIG" .yaml)"
EXP_DIR="experiments/${CONFIG_STEM}/SkullBreak_models/${EXP_NAME}"
LOG_DIR="logs/skullbreak_mamba_ordering_v11_out8192"
EVAL_DIR="logs/skullbreak_mamba_ordering_v11_out8192_eval/${EVAL_NAME}"
AUDIT_JSON="${LOG_DIR}/strict_monitor_protocol_audit.json"
STAMP="$(date +%Y%m%d_%H%M%S)"
RESUME="${RESUME:-0}"
MIN_FREE_GB="${MIN_FREE_GB:-5}"

mkdir -p "$LOG_DIR"

python tools/audit_skullbreak_ordering_protocol.py \
  --manifest data/SkullBreakPC_out8192/manifest.jsonl \
  --output "$AUDIT_JSON"

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
  --seed 0
  --deterministic
)
if [[ "$RESUME" == "1" ]]; then
  train_args+=(--resume)
fi

echo "[candidate] id=${CANDIDATE} order=${ORDER}"
echo "[protocol] strict train=520 cases/104 skulls; monitor=50/10"

python main.py "${train_args[@]}" \
  2>&1 | tee "${LOG_DIR}/${EXP_NAME}_${STAMP}.log"

python tools/recalibrate_skullfix_batchnorm.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last.pth" \
  --output "${EXP_DIR}/ckpt-last-bncal.pth" \
  --batch_size 8 \
  --max_batches 65 \
  --num_workers 4 \
  --seed 0

python tools/evaluate_skullfix_implant.py \
  --config "$CONFIG" \
  --ckpt "${EXP_DIR}/ckpt-last-bncal.pth" \
  --split val \
  --num_samples 0 \
  --seed 0 \
  --out_dir "$EVAL_DIR" \
  --rim_band_mm 2.0 \
  --bootstrap_samples 2000 \
  --confidence 0.95 \
  --dataset_label SkullBreak

echo "[done] ${CANDIDATE} monitor-only $(date)"
echo "[locked] no official-test evaluation was run"
