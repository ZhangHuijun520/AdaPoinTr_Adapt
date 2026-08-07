#!/usr/bin/env bash
set -euo pipefail

SESSION="${TMUX_SESSION:-mamba-v12-d21-posthoc-paired}"
ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${ROOT}/logs/skullbreak_mamba_v12_d21_geometry/posthoc_paired_geometry"
MASTER_LOG="${LOG_DIR}/tmux_${STAMP}.log"

command -v tmux >/dev/null || { echo "[error] tmux is not installed"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 2
fi
mkdir -p "$LOG_DIR"

COMMAND="cd '$ROOT' && set -o pipefail && bash scripts/run_mamba_v12_d21_posthoc_paired_replay.sh 2>&1 | tee '$MASTER_LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] post-hoc exit status:' \$status; exec bash"
tmux new-session -d -s "$SESSION" "$COMMAND"

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] master log: $MASTER_LOG"
