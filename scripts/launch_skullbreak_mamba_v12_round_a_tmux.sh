#!/usr/bin/env bash
set -euo pipefail

SESSION="${TMUX_SESSION:-mamba-v12-round-a-seed0}"
ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${ROOT}/logs/skullbreak_mamba_v12_development"
MASTER_LOG="${LOG_DIR}/tmux_round_a_${STAMP}.log"

command -v tmux >/dev/null || { echo "[error] tmux is not installed"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 2
fi
mkdir -p "$LOG_DIR"

COMMAND="cd '$ROOT' && set -o pipefail && bash scripts/run_skullbreak_mamba_v12_round_a.sh 2>&1 | tee '$MASTER_LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] experiment exit status:' \$status; exec bash"
tmux new-session -d -s "$SESSION" "$COMMAND"

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] log: $MASTER_LOG"
