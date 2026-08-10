#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
SESSION="${TMUX_SESSION:-mamba-v12-d22-contact-support-posthoc}"
LOG_DIR="$ROOT/logs/skullbreak_mamba_v12_d22_local_rim/posthoc_contact_support_v1_tmux"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="$LOG_DIR/tmux_${STAMP}.log"

command -v tmux >/dev/null 2>&1 || {
  echo "[error] tmux is not installed or not on PATH"
  exit 1
}
[[ -d "$ROOT" ]] || {
  echo "[error] PoinTr root does not exist: $ROOT"
  exit 1
}
tmux has-session -t "$SESSION" 2>/dev/null && {
  echo "[error] tmux session already exists: $SESSION"
  echo "[attach] tmux attach -t $SESSION"
  exit 2
}

mkdir -p "$LOG_DIR"
COMMAND="set -o pipefail; \
export POINTR_ROOT='$ROOT'; \
export PYTHONUNBUFFERED=1; \
export TQDM_MININTERVAL=1; \
bash scripts/run_skullbreak_mamba_v12_d22_contact_support_posthoc.sh \
2>&1 | tee '$MASTER_LOG'; \
status=\${PIPESTATUS[0]}; \
echo '[tmux] post-hoc exit status:' \$status; \
echo '[tmux] master log: $MASTER_LOG'; \
exec bash"

tmux new-session -d -s "$SESSION" -c "$ROOT" "$COMMAND"
tmux set-window-option -t "$SESSION" remain-on-exit on

echo "[started] tmux session: $SESSION"
echo "[log] $MASTER_LOG"
echo "[attach] tmux attach -t $SESSION"
echo "[detach] press Ctrl-b, then d"
echo "[status] tmux capture-pane -pt $SESSION | tail -60"
