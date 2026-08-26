#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
SESSION="${TMUX_SESSION:-mamba-v13-d3-s1-seed0}"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="${ROOT}/logs/mamba_v13_d3_mug500plus/s1_seed0_tmux/tmux_${STAMP}.log"

command -v tmux >/dev/null 2>&1 || { echo "[error] tmux unavailable"; exit 1; }
[[ -d "$ROOT" ]] || { echo "[error] PoinTr root missing: $ROOT"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  echo "[attach] tmux attach -t $SESSION"
  exit 2
fi

cd "$ROOT"
bash scripts/preflight_mamba_v13_d3_s1_seed0.sh
mkdir -p "$(dirname "$MASTER_LOG")"

COMMAND="set -o pipefail; \
export POINTR_ROOT='$ROOT'; \
export PYTHONUNBUFFERED=1; \
export TQDM_MININTERVAL=1; \
bash scripts/run_mamba_v13_d3_s1_seed0.sh \
2>&1 | tee '$MASTER_LOG'; \
status=\${PIPESTATUS[0]}; \
echo '[tmux] experiment exit status:' \$status; \
echo '[tmux] master log: $MASTER_LOG'; \
exec bash"

tmux new-session -d -s "$SESSION" -c "$ROOT" "$COMMAND"
tmux set-window-option -t "$SESSION" remain-on-exit on

echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] detach: press Ctrl-b, then d"
echo "[tmux] master log: $MASTER_LOG"
