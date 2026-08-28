#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
SESSION="${TMUX_SESSION:-mamba-v14-pd3-s2-decomposition}"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
LOG_DIR="$ROOT/logs/mamba_v14_d4_contact_support/pd3_s2_failure_decomposition_tmux"
MASTER_LOG="$LOG_DIR/tmux_${STAMP}.log"
mkdir -p "$LOG_DIR"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 1
fi

tmux new-session -d -s "$SESSION" \
  "cd '$ROOT' && bash scripts/run_mamba_v14_pd3_s2_failure_decomposition.sh 2>&1 | tee '$MASTER_LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] replay exit status:' \$status | tee -a '$MASTER_LOG'; exit \$status"

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] master log: $MASTER_LOG"
