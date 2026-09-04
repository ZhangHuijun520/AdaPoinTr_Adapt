#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

FORMAL_RESULT="${D6_FORMAL_EFFICIENCY_RESULT_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_formal_efficiency_result_v1}"
OUT="${D6_R1_LATENCY_PROFILING_PROTOCOL_LOCK_DIR:-$ROOT/logs/mamba_v16_d6_contact_support/d6a_r1_latency_bottleneck_posthoc_profiling_protocol_v1}"

echo "===== D6-A R1 latency post-hoc profiling protocol tests ====="
python tools/test_mamba_v16_d6a_r1_latency_bottleneck_posthoc_profiling_protocol.py

echo "===== Freeze non-runnable R1 profiling protocol ====="
python tools/lock_mamba_v16_d6a_r1_latency_bottleneck_posthoc_profiling_protocol.py \
  --repo_root "$ROOT" \
  --formal_result_dir "$FORMAL_RESULT" \
  --out_dir "$OUT"

echo "===== Verify immutable protocol lock ====="
(
  cd "$OUT"
  sha256sum -c files.sha256
)

python - "$OUT/protocol_lock_receipt.json" <<'PY'
import json
import sys
from pathlib import Path

receipt = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert receipt["status"] == "D6A_R1_latency_posthoc_profiling_protocol_frozen_non_runnable"
assert receipt["formal_result_status"] == "D6A_formal_efficiency_gate_failed"
assert receipt["frozen_R1_latency_ms_median"] == 292.5087884068489
assert receipt["formal_gate_changed"] is False
assert receipt["formal_gate_rerun"] is False
assert receipt["profiling_runs"] == 0
assert receipt["optimizer_steps"] == 0
assert receipt["model_updates"] == 0
assert receipt["D6_cases_accessed"] == 0
assert receipt["protocol_lock_authorized"] is True
for key in (
    "posthoc_profiling_execution_authorized",
    "formal_efficiency_rerun_authorized",
    "R1_implementation_change_authorized",
    "R2_implementation_authorized",
    "seed0_training_authorized",
    "seed1_training_authorized",
    "proposal_confirmation_authorized",
    "D6B_authorized",
    "candidate_selection_authorized",
    "protected_or_sealed_data_accessed",
):
    assert receipt[key] is False
print("[ok] D6-A R1 profiling protocol lock semantics verified")
PY

echo "[done] D6-A R1 latency post-hoc profiling protocol frozen"
echo "[authorized-next] separate profiling execution authorization only"
echo "[locked] profiling=false training=false seed1=false D6B=false confirmation=false"
