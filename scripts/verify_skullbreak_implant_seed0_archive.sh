#!/usr/bin/env bash
set -euo pipefail

RESTORE_ROOT="${1:-.}"
cd "$RESTORE_ROOT"

if [[ ! -f metadata/MANIFEST.sha256 ]]; then
  echo "[error] metadata/MANIFEST.sha256 was not found" >&2
  echo "Extract the archive into an empty directory, then run this script there." >&2
  exit 1
fi

echo "[verify] checking archived files"
sha256sum --check metadata/MANIFEST.sha256

required_paths=(
  "cfgs/SkullBreak_models/AdaPoinTr_implant_full100_bncal.yaml"
  "cfgs/dataset_configs/SkullBreak.yaml"
  "experiments/AdaPoinTr_implant_full100_bncal/SkullBreak_models/skullbreak_implant_full100_bncal/ckpt-last-bncal.pth"
  "logs/skullbreak_implant_eval/full100_bncal_official_test"
  "logs/skullbreak_implant_eval/full100_predictions_test/predictions_manifest.jsonl"
  "experiments/visualizations/skullbreak_implant_full100_bncal_test"
  "metadata/code_snapshot.tar.gz"
  "metadata/results_summary.txt"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "[error] required restored path is missing: $path" >&2
    exit 1
  fi
done

prediction_count="$(
  find logs/skullbreak_implant_eval/full100_predictions_test \
    -maxdepth 1 -name '*.npz' | wc -l
)"
visual_count="$(
  find experiments/visualizations/skullbreak_implant_full100_bncal_test \
    -mindepth 1 -maxdepth 1 -type d | wc -l
)"

if [[ "$prediction_count" -ne 100 ]]; then
  echo "[error] expected 100 prediction NPZ files, found $prediction_count" >&2
  exit 1
fi
if [[ "$visual_count" -lt 15 ]]; then
  echo "[error] expected at least 15 visualization directories, found $visual_count" >&2
  exit 1
fi

echo "[ok] archive contents and checksums are valid"
echo "[info] predictions=$prediction_count visualizations=$visual_count"
echo "[info] raw SkullBreak data and local voxel evaluation are external to this archive"
