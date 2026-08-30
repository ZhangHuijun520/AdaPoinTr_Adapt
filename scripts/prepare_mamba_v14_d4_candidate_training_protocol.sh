#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${MUG500PLUS_D4_M2_FOURFOLD_LOCK_DIR:?set MUG500PLUS_D4_M2_FOURFOLD_LOCK_DIR}"
: "${MUG500PLUS_D4_GENERATION_AUDIT_DIR:?set MUG500PLUS_D4_GENERATION_AUDIT_DIR}"
: "${MAMBA_V14_D4_CANDIDATE_PROTOCOL_LOCK_DIR:?set MAMBA_V14_D4_CANDIDATE_PROTOCOL_LOCK_DIR}"

python -m py_compile \
  tools/lock_mamba_v14_d4_candidate_training_protocol.py \
  tools/test_mamba_v14_d4_candidate_training_protocol.py

python tools/test_mamba_v14_d4_candidate_training_protocol.py

args=(
  --fourfold_lock_dir "$MUG500PLUS_D4_M2_FOURFOLD_LOCK_DIR"
  --generation_audit_dir "$MUG500PLUS_D4_GENERATION_AUDIT_DIR"
  --output_dir "$MAMBA_V14_D4_CANDIDATE_PROTOCOL_LOCK_DIR"
  --protocol docs/mamba_v14_d4_candidate_training_protocol_v1.json
  --test_script tools/test_mamba_v14_d4_candidate_training_protocol.py
)

python tools/lock_mamba_v14_d4_candidate_training_protocol.py "${args[@]}"
python tools/lock_mamba_v14_d4_candidate_training_protocol.py "${args[@]}"

(
  cd "$MAMBA_V14_D4_CANDIDATE_PROTOCOL_LOCK_DIR"
  sha256sum -c files.sha256
)

echo "[done] D4-A and T0/T1/T2 definitions, budgets, folds, and gates frozen"
echo "[authorized-next] implementation and zero-step preflight only"
echo "[locked] D4A=false training=false selection=false protected=false"
