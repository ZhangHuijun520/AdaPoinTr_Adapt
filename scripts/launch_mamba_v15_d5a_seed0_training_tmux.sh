#!/usr/bin/env bash

set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
SESSION="${TMUX_SESSION:-mamba-v15-d5a-v0-v1-seed0}"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="${ROOT}/logs/mamba_v15_d5_contact_support/d5a_seed0_training_tmux/tmux_${STAMP}.log"

command -v tmux >/dev/null 2>&1 || { echo "[error] tmux unavailable"; exit 1; }
[[ -d "$ROOT" ]] || { echo "[error] PoinTr root missing: $ROOT"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  echo "[attach] tmux attach -t $SESSION"
  exit 2
fi

cd "$ROOT"
bash scripts/preflight_mamba_v15_d5a_seed0_training.sh
mkdir -p "$(dirname "$MASTER_LOG")"

COMMAND="set -o pipefail; \
export POINTR_ROOT='$ROOT'; \
export PYTHONUNBUFFERED=1; \
export TQDM_MININTERVAL=1; \
bash scripts/run_mamba_v15_d5a_seed0_training.sh \
2>&1 | tee '$MASTER_LOG'; \
status=\${PIPESTATUS[0]}; \
echo '[tmux] D5-A seed-0 exit status:' \$status; \
echo '[tmux] master log: $MASTER_LOG'; \
exec bash"

tmux new-session -d -s "$SESSION" -c "$ROOT" "$COMMAND"
tmux set-window-option -t "$SESSION" remain-on-exit on

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] detach: press Ctrl-b, then d"
echo "[tmux] master log: $MASTER_LOG"
