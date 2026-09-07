#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOG_ROOT="${MAMBA_V16_D6_LOG_ROOT:-$ROOT/logs/mamba_v16_d6_contact_support}"
SESSION="${TMUX_SESSION:-mamba-v16-d6a-r1-s2-artificial-benchmark-v1}"
TMUX_LOG_DIR="$LOG_ROOT/d6a_r1_s2_artificial_performance_benchmark_tmux_v1"
RESULT="${D6_R1_S2_BENCHMARK_RESULT_DIR:-$LOG_ROOT/d6a_r1_s2_artificial_performance_benchmark_result_v1}"

[[ ! -e "$RESULT" ]] || { echo "[error] immutable benchmark result already exists: $RESULT"; exit 1; }
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "[error] tmux session already exists: $SESSION"
  exit 1
fi

mkdir -p "$TMUX_LOG_DIR"
STAMP="$(date -u +%Y%m%d_%H%M%S)"
MASTER_LOG="$TMUX_LOG_DIR/tmux_${STAMP}.log"
COMMAND="cd '$ROOT' && bash scripts/run_mamba_v16_d6a_r1_s2_artificial_performance_benchmark.sh 2>&1 | tee '$MASTER_LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] S2 benchmark exit status:' \$status | tee -a '$MASTER_LOG'; exit \$status"

tmux new-session -d -s "$SESSION" "$COMMAND"
echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] master log: $MASTER_LOG"
echo "[locked] production=false formal_rerun=false training=false seed1=false D6B=false sealed=false"
