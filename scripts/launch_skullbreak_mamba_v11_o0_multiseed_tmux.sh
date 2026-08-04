#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
SESSION="${TMUX_SESSION:-mamba-v11-o0-multiseed-r1}"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="${ROOT}/logs/skullbreak_mamba_v11_o0_multiseed/tmux_${STAMP}.log"

if ! command -v tmux >/dev/null 2>&1; then
  echo "[error] tmux is not installed"
  exit 1
fi
if [[ ! -d "$ROOT" ]]; then
  echo "[error] PoinTr root does not exist: $ROOT"
  exit 1
fi
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 1
fi

mkdir -p "$(dirname "$MASTER_LOG")"

COMMAND="set -o pipefail; \
export POINTR_ROOT='$ROOT'; \
export PYTHONUNBUFFERED=1; \
export TQDM_MININTERVAL=1; \
bash scripts/run_skullbreak_mamba_v11_o0_seed1_seed2.sh \
2>&1 | tee '$MASTER_LOG'; \
status=\${PIPESTATUS[0]}; \
echo '[tmux] experiment exit status:' \$status; \
echo '[tmux] master log: $MASTER_LOG'; \
exec bash"

tmux new-session -d -s "$SESSION" -c "$ROOT" "$COMMAND"
tmux set-window-option -t "$SESSION" remain-on-exit on

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] log: $MASTER_LOG"
echo "[progress] main/evaluation/instrumentation all use tqdm progress bars"
