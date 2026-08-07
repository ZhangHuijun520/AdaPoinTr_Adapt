#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
SESSION="${TMUX_SESSION:-mamba-v12-round-a-gt-replay}"
LOG_DIR="$ROOT/logs/skullbreak_mamba_v12_development/posthoc_round_a_gt_geometry"
STAMP="$(date +%Y%m%d_%H%M%S)"
MASTER_LOG="$LOG_DIR/tmux_${STAMP}.log"
mkdir -p "$LOG_DIR"

tmux has-session -t "$SESSION" 2>/dev/null && {
  echo "[error] tmux session already exists: $SESSION"
  exit 2
}

COMMAND="cd '$ROOT' && source /opt/conda/etc/profile.d/conda.sh && conda activate adapointr-mamba && python tools/replay_mamba_v12_round_a_gt_geometry.py --records_root logs/skullbreak_mamba_v12_development/round_a --case_labels logs/skullbreak_mamba_v12_development/posthoc_round_a_failure/round_a_case_labels.csv --gate_audit logs/skullbreak_mamba_v12_development/selection/round_a_top2_gate_failure.json --output_dir logs/skullbreak_mamba_v12_development/posthoc_round_a_gt_geometry 2>&1 | tee '$MASTER_LOG'; status=\${PIPESTATUS[0]}; echo '[tmux] GT replay exit status:' \$status; exit \$status"

tmux new-session -d -s "$SESSION" "bash -lc \"$COMMAND\""
echo "[tmux] started: $SESSION"
echo "[tmux] attach: tmux attach -t $SESSION"
echo "[tmux] master log: $MASTER_LOG"
