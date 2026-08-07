#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u
cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

ROOT="logs/skullbreak_mamba_v12_development"
ROUND_B="${ROOT}/selection/round_b_winner.json"
CONFIG_DIR="cfgs/SkullBreak_models/generated_mamba_v12_dev_round_c"
[[ -f "$ROUND_B" && -f "${ROUND_B}.sha256" ]] || {
  echo "[error] frozen Round-B winner is missing"
  exit 2
}
WINNER="$(python -c 'import json; print(json.load(open("logs/skullbreak_mamba_v12_development/selection/round_b_winner.json"))["selected"][0])')"

python tools/generate_skullbreak_mamba_v12_followup_configs.py \
  --round C --protocol_dir "${ROOT}/protocol_v1" \
  --selection "$ROUND_B" --output_dir "$CONFIG_DIR"

for seed in 0 1 2; do
  CONFIG="${CONFIG_DIR}/MambaV12Winner_${WINNER}_dev84_seed${seed}.yaml"
  CONFIG_STEM="$(basename "$CONFIG" .yaml)"
  CONFIG_PARENT="$(basename "$(dirname "$CONFIG")")"
  EXP_NAME="skullbreak_mamba_v12_winner_${WINNER}_dev84_seed${seed}"
  EXP_DIR="experiments/${CONFIG_STEM}/${CONFIG_PARENT}/${EXP_NAME}"
  RUN_DIR="${ROOT}/round_c/dev84_seed${seed}"
  RAW_CKPT="${EXP_DIR}/ckpt-last.pth"
  BNCAL_CKPT="${EXP_DIR}/ckpt-last-bncal.pth"
  mkdir -p "$RUN_DIR"
  if [[ ! -f "$BNCAL_CKPT" ]]; then
    LOG="${RUN_DIR}/${EXP_NAME}_$(date +%Y%m%d_%H%M%S).log"
    resume_args=()
    if [[ -f "$RAW_CKPT" ]]; then
      checkpoint_epoch="$(python - "$RAW_CKPT" <<'PY'
import sys
import torch
print(int(torch.load(sys.argv[1], map_location="cpu").get("epoch", -1)))
PY
)"
      if (( checkpoint_epoch >= 100 )); then
        echo "[resume] seed=${seed} epoch-100 raw checkpoint exists; skip training"
      else
        echo "[resume] seed=${seed} checkpoint epoch=${checkpoint_epoch}; resume training"
        resume_args+=(--resume)
      fi
    fi
    if [[ ! -f "$RAW_CKPT" || "${#resume_args[@]}" -gt 0 ]]; then
      PYTHONUNBUFFERED=1 python main.py \
        --config "$CONFIG" --exp_name "$EXP_NAME" \
        --num_workers 4 --val_freq 10 --seed "$seed" --deterministic \
        "${resume_args[@]}" 2>&1 | tee "$LOG"
    fi
    final_epoch="$(python - "$RAW_CKPT" <<'PY'
import sys
import torch
print(int(torch.load(sys.argv[1], map_location="cpu").get("epoch", -1)))
PY
)"
    [[ "$final_epoch" == "100" ]] || {
      echo "[error] seed=${seed} expected epoch-100 checkpoint, found epoch=${final_epoch}"
      exit 1
    }
    python tools/recalibrate_skullfix_batchnorm.py \
      --config "$CONFIG" --ckpt "$RAW_CKPT" \
      --output "$BNCAL_CKPT" \
      --batch_size 8 --max_batches 53 --num_workers 4 --seed "$seed"
    rm -f -- "$RAW_CKPT"
  else
    echo "[resume] seed=${seed} BN-calibrated checkpoint exists; skip training and BNCal"
  fi
done

echo "[locked] all three dev84 trainings completed before confirmation access"
for seed in 0 1 2; do
  TRAIN_CONFIG="${CONFIG_DIR}/MambaV12Winner_${WINNER}_dev84_seed${seed}.yaml"
  CONFIRM_CONFIG="${CONFIG_DIR}/MambaV12Winner_${WINNER}_confirmation20_seed${seed}.yaml"
  CONFIG_STEM="$(basename "$TRAIN_CONFIG" .yaml)"
  CONFIG_PARENT="$(basename "$(dirname "$TRAIN_CONFIG")")"
  EXP_NAME="skullbreak_mamba_v12_winner_${WINNER}_dev84_seed${seed}"
  CKPT="experiments/${CONFIG_STEM}/${CONFIG_PARENT}/${EXP_NAME}/ckpt-last-bncal.pth"
  OUT="${ROOT}/round_c/confirmation20_seed${seed}"
  mkdir -p "$OUT"
  python tools/evaluate_skullfix_implant.py \
    --config "$CONFIRM_CONFIG" --ckpt "$CKPT" \
    --split val --num_samples 0 --seed "$seed" --out_dir "$OUT" \
    --rim_band_mm 2.0 --bootstrap_samples 2000 --confidence 0.95 \
    --dataset_label SkullBreak
  python tools/instrument_mamba_full_pipeline.py \
    --config "$CONFIRM_CONFIG" --ckpt "$CKPT" --split val \
    --out_dir "${OUT}/instrumentation" --seed "$seed"
done

python - <<'PY'
import hashlib, json
from pathlib import Path
root = Path("logs/skullbreak_mamba_v12_development")
receipt = {
    "receipt_version": "mamba-v12-confirmation-one-shot-v1",
    "winner_selection_sha256": hashlib.sha256((root / "selection/round_b_winner.json").read_bytes()).hexdigest(),
    "seeds": [0, 1, 2],
    "confirmation_consumed_once": True,
    "old_monitor_used": False,
    "official_test_used": False,
    "locked_no_return": True,
}
path = root / "round_c/confirmation_receipt.json"
path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
digest = hashlib.sha256(path.read_bytes()).hexdigest()
Path(str(path) + ".sha256").write_text(f"{digest}  {path.name}\n")
print(f"[saved] {path}")
PY

echo "[done] one-shot locked confirmation completed"
echo "[locked] do not revise candidates, winner, or rules from confirmation results"
