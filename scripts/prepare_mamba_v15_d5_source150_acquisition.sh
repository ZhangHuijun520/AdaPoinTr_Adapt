#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"
cd "$REPO_ROOT"

: "${MUG500PLUS_METADATA_DIR:?set MUG500PLUS_METADATA_DIR}"
: "${MUG500PLUS_D3_SOURCE125_LOCK_DIR:?set MUG500PLUS_D3_SOURCE125_LOCK_DIR}"
: "${MUG500PLUS_D3_SPLIT_LOCK_DIR:?set MUG500PLUS_D3_SPLIT_LOCK_DIR}"
: "${MUG500PLUS_D4_SOURCE100_LOCK_DIR:?set MUG500PLUS_D4_SOURCE100_LOCK_DIR}"
: "${MUG500PLUS_D5_SOURCE150_LOCK_DIR:?set MUG500PLUS_D5_SOURCE150_LOCK_DIR}"

ARTICLE_JSON="$MUG500PLUS_METADATA_DIR/mug500plus_article_v20.json"
FILES_JSON="$MUG500PLUS_METADATA_DIR/mug500plus_files_v20.json"

python tools/test_mamba_v15_d5_source150_acquisition.py

python tools/lock_mamba_v15_d5_source150_acquisition.py \
  --article_json "$ARTICLE_JSON" \
  --files_json "$FILES_JSON" \
  --d3_lock_dir "$MUG500PLUS_D3_SOURCE125_LOCK_DIR" \
  --d3_split_lock_dir "$MUG500PLUS_D3_SPLIT_LOCK_DIR" \
  --d4_lock_dir "$MUG500PLUS_D4_SOURCE100_LOCK_DIR" \
  --out_dir "$MUG500PLUS_D5_SOURCE150_LOCK_DIR"

(
  cd "$MUG500PLUS_D5_SOURCE150_LOCK_DIR"
  sha256sum -c files.sha256
)

python - "$MUG500PLUS_D5_SOURCE150_LOCK_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
receipt = json.loads(
    (root / "source_acquisition_lock_receipt.json").read_text(encoding="utf-8")
)
audit = json.loads((root / "source_overlap_audit.json").read_text(encoding="utf-8"))

assert receipt["status"] == "source150_three_partition_acquisition_locked"
assert receipt["counts"]["selected_sources"] == 150
assert receipt["counts"]["development_sources"] == 100
assert receipt["counts"]["proposal_confirmation_sources"] == 25
assert receipt["counts"]["completion_holdout_sources"] == 25
assert receipt["source_overlap"] == 0
assert receipt["proposal_confirmation_extraction_authorized"] is False
assert receipt["completion_holdout_extraction_authorized"] is False
assert receipt["D5_synthetic_generation_authorized"] is False
assert receipt["D5A_model_implementation_authorized"] is False
assert receipt["D5A_training_authorized"] is False
assert receipt["D5B_training_authorized"] is False

assert audit["selected_prior_overlap"] == 0
assert audit["development_confirmation_overlap"] == 0
assert audit["development_completion_holdout_overlap"] == 0
assert audit["confirmation_completion_holdout_overlap"] == 0
assert audit["craniotomy_or_B_series_selected"] is False

print("[ok] D5 source150 lock and three-partition semantics verified")
print("[sealed] proposal-confirmation25 and completion-holdout25")
print("[locked] generation=false implementation=false training=false")
PY

echo "[done] D5 source150 metadata-only acquisition lock frozen"
echo "[next] download/QC development only; sealed ZIPs may be archived but not extracted"
