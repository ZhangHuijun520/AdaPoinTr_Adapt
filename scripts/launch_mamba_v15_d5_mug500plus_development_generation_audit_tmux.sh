#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

SESSION="${TMUX_SESSION:-mamba-v15-d5-development-generation-audit-v1}"
LOG_ROOT="logs/mamba_v15_d5_contact_support/development_generation_audit_tmux"
mkdir -p "$LOG_ROOT"
MASTER_LOG="$LOG_ROOT/tmux_$(date -u +%Y%m%d_%H%M%S).log"

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 1
fi

tmux new-session -d -s "$SESSION" \
  "bash -lc 'set -o pipefail; export PS1=\"\${PS1-}\"; source \"$HOME/conda/etc/profile.d/conda.sh\"; conda activate adapointr-mamba; cd \"$PWD\"; bash scripts/run_mamba_v15_d5_mug500plus_development_generation_audit.sh 2>&1 | tee \"$MASTER_LOG\"; status=\${PIPESTATUS[0]}; echo \"[tmux] audit exit status: \$status\"; exec bash'"

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] master log: $PWD/$MASTER_LOG"
