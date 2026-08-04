#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CONFIG="cfgs/SkullBreak_models/MambaAdapterV11OrderingO0_xyz_out8192_monitor.yaml"
ROOT="logs/skullbreak_mamba_v11_o0_multiseed/posthoc_full_monitor"
PANEL="${ROOT}/protocol/full_monitor_panel.json"
ANALYSIS="${ROOT}/analysis"

SEED0_CKPT="experiments/MambaAdapterV11OrderingO0_xyz_out8192_monitor/SkullBreak_models/skullbreak_mamba_v11_ordering_o0_xyz_seed0/ckpt-last-bncal.pth"
SEED1_CKPT="experiments/MambaAdapterV11OrderingO0_xyz_out8192_monitor/SkullBreak_models/skullbreak_mamba_v11_o0_xyz_seed1_replication/ckpt-last-bncal.pth"
SEED2_CKPT="experiments/MambaAdapterV11OrderingO0_xyz_out8192_monitor/SkullBreak_models/skullbreak_mamba_v11_o0_xyz_seed2_replication/ckpt-last-bncal.pth"

SEED0_METRICS="logs/skullbreak_mamba_ordering_v11_out8192_eval/O0_xyz_monitor/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"
SEED1_METRICS="logs/skullbreak_mamba_v11_o0_multiseed/monitor/seed1/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"
SEED2_METRICS="logs/skullbreak_mamba_v11_o0_multiseed/monitor/seed2/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"

mkdir -p "${ROOT}/protocol"

for required in \
  "$SEED0_CKPT" "$SEED1_CKPT" "$SEED2_CKPT" \
  "$SEED0_METRICS" "$SEED1_METRICS" "$SEED2_METRICS"; do
  if [[ ! -f "$required" ]]; then
    echo "[error] required frozen artifact is missing: $required"
    exit 1
  fi
done

python tools/lock_skullbreak_mamba_posthoc_monitor_panel.py \
  --config "$CONFIG" \
  --output "$PANEL"

declare -A CKPTS=(
  [0]="$SEED0_CKPT"
  [1]="$SEED1_CKPT"
  [2]="$SEED2_CKPT"
)

for seed in 0 1 2; do
  echo "[post-hoc] instrumenting complete monitor seed=${seed}"
  python tools/instrument_mamba_adapter_tokens.py \
    --config "$CONFIG" \
    --ckpt "${CKPTS[$seed]}" \
    --panel "$PANEL" \
    --out_dir "${ROOT}/instrumentation/seed${seed}" \
    --seed "$seed" \
    --allow_nontrain
done

python tools/analyze_skullbreak_mamba_multiseed_posthoc.py \
  --metrics "0=${SEED0_METRICS}" \
  --metrics "1=${SEED1_METRICS}" \
  --metrics "2=${SEED2_METRICS}" \
  --instrumentation "0=${ROOT}/instrumentation/seed0" \
  --instrumentation "1=${ROOT}/instrumentation/seed1" \
  --instrumentation "2=${ROOT}/instrumentation/seed2" \
  --panel "$PANEL" \
  --out_dir "$ANALYSIS" \
  --catastrophe_threshold_mm 50.0

echo "[done] declared post-hoc full-monitor diagnosis"
echo "[report] ${ANALYSIS}/posthoc_report_zh.md"
echo "[locked] no official-test evaluation was run"
echo "[locked] results cannot select seed, ordering, or model"
