#!/usr/bin/env bash
set -euo pipefail
SESSION="${TMUX_SESSION:-mamba-v12-round-c-confirmation}"
ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="${ROOT}/logs/skullbreak_mamba_v12_development/tmux_round_c_${STAMP}.log"
tmux has-session -t "$SESSION" 2>/dev/null && { echo "[error] session exists"; exit 2; }
COMMAND="cd '$ROOT' && set -o pipefail && bash scripts/run_skullbreak_mamba_v12_round_c.sh 2>&1 | tee '$LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] experiment exit status:' \$status; exec bash"
tmux new-session -d -s "$SESSION" "$COMMAND"
echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] log: $LOG"
