#!/usr/bin/env bash
set -euo pipefail

RESTORE_ROOT="${1:-.}"
cd "$RESTORE_ROOT"

required_metadata=(
  "metadata/README.txt"
  "metadata/ARCHIVE_PATHS.txt"
  "metadata/MANIFEST.sha256"
  "metadata/CHECKPOINTS.sha256"
  "metadata/runtime_environment.txt"
  "metadata/skullbreak_out8192_manifest.jsonl"
)

for path in "${required_metadata[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "[error] required archive metadata is missing: $path" >&2
    exit 1
  fi
done

echo "[verify] checking archived payload hashes"
sha256sum -c metadata/MANIFEST.sha256

echo "[verify] checking three canonical checkpoints"
sha256sum -c metadata/CHECKPOINTS.sha256

P1_ROOT="logs/skullbreak_mamba_v11_o0_multiseed/posthoc_full_monitor"
P1_SUMMARY="$P1_ROOT/analysis/posthoc_summary.json"

echo "[verify] checking frozen P1 hash chain"
sha256sum -c "$P1_ROOT/posthoc_tree_sha256.txt.sha256"
sha256sum -c "$P1_ROOT/posthoc_tree_sha256.txt" >/dev/null
echo "[ok] all files in the frozen P1 tree match"

SEED0_METRICS="logs/skullbreak_mamba_ordering_v11_out8192_eval/O0_xyz_monitor/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"
SEED1_METRICS="logs/skullbreak_mamba_v11_o0_multiseed/monitor/seed1/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"
SEED2_METRICS="logs/skullbreak_mamba_v11_o0_multiseed/monitor/seed2/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"

python - "$SEED0_METRICS" "$SEED1_METRICS" "$SEED2_METRICS" "$P1_SUMMARY" <<'PY'
import csv
import json
import math
import sys
from pathlib import Path

case_sets = []
for value in sys.argv[1:4]:
    path = Path(value)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    cases = {row["case_id"] for row in rows}
    if len(rows) != 50 or len(cases) != 50:
        raise SystemExit(f"[error] invalid 50-case monitor CSV: {path}")
    case_sets.append(cases)
if not all(case_sets[0] == cases for cases in case_sets[1:]):
    raise SystemExit("[error] restored seed monitor case sets differ")

summary = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
checks = {
    "posthoc": summary.get("posthoc") is True,
    "selection_allowed": summary.get("selection_allowed") is False,
    "official_test_used": summary.get("official_test_used") is False,
    "threshold": summary.get("catastrophe_threshold_mm") == 50.0,
    "records": summary.get("num_records") == 150,
    "cases": summary.get("num_cases") == 50,
    "catastrophes": summary.get("catastrophes_by_seed") == {"0": 0, "1": 2, "2": 3},
    "tokens_equal": summary.get("token_equality", {}).get("all_equal") is True,
    "coordinate_delta": math.isclose(
        float(summary.get("token_equality", {}).get("maximum_coordinate_delta", math.inf)),
        0.0,
        rel_tol=0.0,
        abs_tol=0.0,
    ),
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("[error] restored P1 semantic checks failed: " + ", ".join(failed))

print("[ok] restored R1/P1 semantic checks passed")
PY

for seed in 0 1 2; do
  case "$seed" in
    0) run_name="skullbreak_mamba_v11_ordering_o0_xyz_seed0" ;;
    1) run_name="skullbreak_mamba_v11_o0_xyz_seed1_replication" ;;
    2) run_name="skullbreak_mamba_v11_o0_xyz_seed2_replication" ;;
  esac
  checkpoint="experiments/MambaAdapterV11OrderingO0_xyz_out8192_monitor/SkullBreak_models/$run_name/ckpt-last-bncal.pth"
  if [[ ! -s "$checkpoint" || ! -f "$checkpoint.json" ]]; then
    echo "[error] restored seed-$seed checkpoint or sidecar is missing" >&2
    exit 1
  fi
done

if find . -path '*official*test*' -print -quit | grep -q .; then
  echo "[warning] a path containing official/test exists in the restore root"
  echo "          Confirm it came from another archive; R1/P1 does not require it."
fi

echo "[ok] R1/P1 archive contents, hashes, and frozen semantics are valid"
echo "[locked] no seed selection, ordering reopening, or official-test feedback"
