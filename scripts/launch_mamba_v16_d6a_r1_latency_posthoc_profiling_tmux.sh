#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
SESSION="${TMUX_SESSION:-mamba-v16-d6a-r1-latency-posthoc-profiling-v1}"
TMUX_LOG_DIR="$LOGS/d6a_r1_latency_posthoc_profiling_tmux_v1"
RESULT="${D6_R1_LATENCY_PROFILING_RESULT_DIR:-$LOGS/d6a_r1_latency_posthoc_profiling_result_v1}"

[[ ! -e "$RESULT" ]] || {
  echo "[error] immutable profiling result already exists: $RESULT"
  exit 1
}
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 1
fi

mkdir -p "$TMUX_LOG_DIR"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
MASTER_LOG="$TMUX_LOG_DIR/tmux_${STAMP}.log"
COMMAND="cd '$ROOT' && bash scripts/run_mamba_v16_d6a_r1_latency_posthoc_profiling.sh 2>&1 | tee '$MASTER_LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] profiling exit status:' \$status | tee -a '$MASTER_LOG'; exit \$status"

tmux new-session -d -s "$SESSION" "$COMMAND"
echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] master log: $MASTER_LOG"
echo "[locked] training=false seed1=false confirmation=false D6B=false sealed=false"
