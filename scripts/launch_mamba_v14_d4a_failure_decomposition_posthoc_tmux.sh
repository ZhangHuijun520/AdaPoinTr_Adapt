#!/usr/bin/env bash

set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
SESSION="${TMUX_SESSION:-mamba-v14-d4a-failure-decomposition-posthoc}"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="${ROOT}/logs/mamba_v14_d4_contact_support/d4a_failure_decomposition_posthoc_tmux/tmux_${STAMP}.log"

command -v tmux >/dev/null 2>&1 || { echo "[error] tmux unavailable"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 2
fi

cd "$ROOT"
python tools/test_mamba_v14_d4a_failure_decomposition_posthoc.py
mkdir -p "$(dirname "$MASTER_LOG")"

COMMAND="set -o pipefail; \
export POINTR_ROOT='$ROOT'; \
export PYTHONUNBUFFERED=1; \
export TQDM_MININTERVAL=1; \
bash scripts/run_mamba_v14_d4a_failure_decomposition_posthoc.sh \
2>&1 | tee '$MASTER_LOG'; \
status=\${PIPESTATUS[0]}; \
echo '[tmux] post-hoc exit status:' \$status; \
echo '[tmux] master log: $MASTER_LOG'; \
exec bash"

tmux new-session -d -s "$SESSION" -c "$ROOT" "$COMMAND"
tmux set-window-option -t "$SESSION" remain-on-exit on

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] detach: press Ctrl-b, then d"
echo "[tmux] master log: $MASTER_LOG"
