#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives}"
ARCHIVE_NAME="${ARCHIVE_NAME:-skullfix_adapointr_implant_out8192_ablation_seed20260628_v1}"
RUN_NAME="skullfix_implant_full100_out8192_bncal"
EXP_DIR="experiments/AdaPoinTr_implant_full100_out8192_bncal/SkullFix_models/$RUN_NAME"
CKPT="$EXP_DIR/ckpt-last-bncal.pth"
CONFIG="cfgs/SkullFix_models/AdaPoinTr_implant_full100_out8192_bncal.yaml"
TRAIN_LOG_DIR="logs/skullfix_implant_point_count"
POINT_EVAL_DIR="logs/skullfix_implant_point_count/full100_out8192_bncal_test"
PREDICTION_DIR="logs/skullfix_implant_point_count/full100_out8192_predictions_test"
VIS_DIR="experiments/visualizations/skullfix_implant_full100_out8192_bncal_test"
TMP_ROOT="$(mktemp -d)"
META_DIR="$TMP_ROOT/metadata"
FILE_LIST="$TMP_ROOT/archive_paths.txt"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

cd "$REPO_ROOT"
mkdir -p "$ARCHIVE_ROOT" "$META_DIR"

required_paths=(
  "$CKPT"
  "$CKPT.json"
  "$CONFIG"
  "$POINT_EVAL_DIR"
  "$PREDICTION_DIR"
  "$VIS_DIR"
  "docs/rim_local_and_output_point_count_ablation_zh.md"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    echo "[error] required artifact is missing: $path" >&2
    exit 1
  fi
done

shopt -s nullglob
train_logs=("$TRAIN_LOG_DIR/${RUN_NAME}_"*.log)
shopt -u nullglob
if (( ${#train_logs[@]} == 0 )); then
  echo "[error] no out8192 training log found below $TRAIN_LOG_DIR" >&2
  exit 1
fi

cat > "$META_DIR/README.txt" <<EOF
AdaPoinTr-Implant SkullFix 8192-output point-count ablation archive

Created: $(date --iso-8601=seconds)
Repository: $REPO_ROOT
Run: $RUN_NAME
Protocol: input=8192 defective skull points, output=8192 implant points
Split: SkullFix seed-0 compatible split generated with seed 20260628

Included:
- config and BN-calibrated checkpoint
- training log
- point/rim evaluation outputs and per-case prediction NPZ files
- visualizations
- point-count ablation analysis document
- metadata and SHA256 manifest

Not included:
- raw SkullFix NRRD data
- local Windows voxel evaluation outputs
EOF

{
  echo "created=$(date --iso-8601=seconds)"
  echo "run_name=$RUN_NAME"
  echo "checkpoint=$CKPT"
  echo "checkpoint_sha256=$(sha256sum "$CKPT" | awk '{print $1}')"
  python -V 2>&1 || true
  python - <<'PY' 2>&1 || true
try:
    import numpy
    import torch
    print(f"numpy={numpy.__version__}")
    print(f"torch={torch.__version__}")
    print(f"cuda_available={torch.cuda.is_available()}")
except Exception as exc:
    print(f"python_probe_failed={exc!r}")
PY
  df -h "$HOME" 2>&1 || true
} > "$META_DIR/system_info.txt"

{
  echo "---- point/rim summary ----"
  find "$POINT_EVAL_DIR" -maxdepth 1 -name '*summary.json' -print -exec cat {} \;
  echo
  echo "---- checkpoint metadata ----"
  cat "$CKPT.json"
} > "$META_DIR/results_summary.txt"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git rev-parse HEAD > "$META_DIR/git_head.txt"
  git status --short > "$META_DIR/git_status.txt"
  git diff --binary HEAD > "$META_DIR/git_worktree.patch"
fi

cat > "$FILE_LIST" <<EOF
$CKPT
$CKPT.json
$CONFIG
$POINT_EVAL_DIR
$PREDICTION_DIR
$VIS_DIR
docs/rim_local_and_output_point_count_ablation_zh.md
tools/evaluate_skullfix_gt_sampling_upper_bound.py
tools/prepare_skullfix_pointcloud.py
tools/check_skullfix_pointcloud.py
scripts/run_skullfix_gt_sampling_upper_bound.sh
scripts/prepare_skullfix_pc_out8192.sh
scripts/run_skullfix_implant_full100_out8192_bncal.sh
scripts/archive_skullfix_implant_out8192_ablation.sh
EOF
printf '%s\n' "${train_logs[@]}" >> "$FILE_LIST"
awk '!seen[$0]++' "$FILE_LIST" > "$FILE_LIST.tmp"
mv "$FILE_LIST.tmp" "$FILE_LIST"

while IFS= read -r path; do
  if [[ -d "$path" ]]; then
    find "$path" -type f -print0
  elif [[ -f "$path" ]]; then
    printf '%s\0' "$path"
  fi
done < "$FILE_LIST" \
  | sort -zu \
  | xargs -0 sha256sum > "$META_DIR/MANIFEST.sha256"

cp "$FILE_LIST" "$META_DIR/ARCHIVE_PATHS.txt"

ARCHIVE_PATH="$ARCHIVE_ROOT/$ARCHIVE_NAME.tar"
echo "[archive] selected artifacts:"
du -sh "$EXP_DIR" "$POINT_EVAL_DIR" "$PREDICTION_DIR" "$VIS_DIR"
echo "[archive] destination filesystem:"
df -h "$ARCHIVE_ROOT"

tar -cf "$ARCHIVE_PATH" \
  -C "$TMP_ROOT" metadata \
  -C "$REPO_ROOT" \
  --files-from "$FILE_LIST"

(
  cd "$ARCHIVE_ROOT"
  sha256sum "$(basename "$ARCHIVE_PATH")" > "$(basename "$ARCHIVE_PATH").sha256"
)

echo "[ok] archive: $ARCHIVE_PATH"
echo "[ok] checksum: $ARCHIVE_PATH.sha256"
ls -lh "$ARCHIVE_PATH" "$ARCHIVE_PATH.sha256"
