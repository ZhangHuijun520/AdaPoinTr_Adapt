#!/usr/bin/env bash
set -euo pipefail

SESSION="${TMUX_SESSION:-mamba-v12-d21-geometry-round-a}"
POINTR_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ROOT="${POINTR_ROOT}/logs/skullbreak_mamba_v12_d21_geometry"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="${ROOT}/tmux_${STAMP}.log"
mkdir -p "$ROOT"

command -v tmux >/dev/null || { echo "[error] tmux is not installed"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 2
fi

COMMAND="cd '$POINTR_ROOT' && set -o pipefail && bash scripts/run_skullbreak_mamba_v12_d21_round_a.sh 2>&1 | tee '$MASTER_LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] experiment exit status:' \$status; exec bash"
tmux new-session -d -s "$SESSION" "$COMMAND"

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] master log: $MASTER_LOG"
