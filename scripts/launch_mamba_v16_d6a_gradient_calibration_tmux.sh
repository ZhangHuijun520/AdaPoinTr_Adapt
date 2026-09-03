#!/usr/bin/env bash

set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGROOT="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}/d6a_gradient_calibration_tmux_v1"
SESSION="${TMUX_SESSION:-mamba-v16-d6a-gradient-calibration-v1}"
mkdir -p "$LOGROOT"
LOG="$LOGROOT/tmux_$(date -u +%Y%m%d_%H%M%S).log"
tmux has-session -t "$SESSION" 2>/dev/null && { echo "[error] tmux session exists: $SESSION"; exit 1; }
tmux new-session -d -s "$SESSION" \
  "cd '$ROOT' && bash scripts/run_mamba_v16_d6a_gradient_calibration.sh 2>&1 | tee '$LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] calibration exit status:' \$status | tee -a '$LOG'; exit \$status"
echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] master log: $LOG"
