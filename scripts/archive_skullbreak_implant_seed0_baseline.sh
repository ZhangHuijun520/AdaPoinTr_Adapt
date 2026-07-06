#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives}"
ARCHIVE_NAME="${ARCHIVE_NAME:-skullbreak_adapointr_implant_seed0_v1}"
RUN_NAME="skullbreak_implant_full100_bncal"
EXP_DIR="experiments/AdaPoinTr_implant_full100_bncal/SkullBreak_models/$RUN_NAME"
CKPT="$EXP_DIR/ckpt-last-bncal.pth"
CONFIG="cfgs/SkullBreak_models/AdaPoinTr_implant_full100_bncal.yaml"
DATASET_CONFIG="cfgs/dataset_configs/SkullBreak.yaml"
TRAIN_LOG_DIR="logs/skullbreak_implant"
OFFICIAL_EVAL_DIR="logs/skullbreak_implant_eval/full100_bncal_official_test"
MONITOR_EVAL_DIR="logs/skullbreak_implant_eval/full100_bncal_monitor"
PREDICTION_DIR="logs/skullbreak_implant_eval/full100_predictions_test"
VIS_DIR="experiments/visualizations/skullbreak_implant_full100_bncal_test"
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
  "$DATASET_CONFIG"
  "$OFFICIAL_EVAL_DIR"
  "$PREDICTION_DIR"
  "$VIS_DIR"
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
  echo "[error] no full-baseline training log found below $TRAIN_LOG_DIR" >&2
  exit 1
fi

cat > "$META_DIR/README.txt" <<EOF
AdaPoinTr-Implant SkullBreak seed-0 baseline archive

Created: $(date --iso-8601=seconds)
Repository: $REPO_ROOT
Run: $RUN_NAME
Official protocol: 114 training skulls / 570 cases; 20 test skulls / 100 cases

Included:
- frozen config and relevant implementation/scripts
- BN-calibrated checkpoint and checkpoint metadata
- training log and official-test point/rim evaluation outputs
- per-case prediction NPZ files and prediction manifest
- official-test visualizations
- code snapshot, environment inventory, Git state, and SHA256 manifest

Not included:
- raw or converted SkullBreak datasets
- local Windows voxel evaluation outputs

Keep the local voxel_evaluation directory beside this archive. Restore into an
empty directory, then run scripts/verify_skullbreak_implant_seed0_archive.sh .
EOF

{
  echo "created=$(date --iso-8601=seconds)"
  echo "hostname=$(hostname)"
  echo "user=$(id -un)"
  echo "repo_root=$REPO_ROOT"
  echo "run_name=$RUN_NAME"
  echo "checkpoint=$CKPT"
  echo "checkpoint_sha256=$(sha256sum "$CKPT" | awk '{print $1}')"
  echo "python=$(command -v python || true)"
  python -V 2>&1 || true
  python - <<'PY' 2>&1 || true
try:
    import numpy
    import torch
    print(f"numpy={numpy.__version__}")
    print(f"torch={torch.__version__}")
    print(f"torch_cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()}")
    print(f"cuda_device_count={torch.cuda.device_count()}")
    for index in range(torch.cuda.device_count()):
        print(f"cuda_device_{index}={torch.cuda.get_device_name(index)}")
except Exception as exc:
    print(f"python_probe_failed={exc!r}")
PY
  echo
  echo "---- nvidia-smi ----"
  nvidia-smi 2>&1 || true
  echo
  echo "---- storage ----"
  df -h "$HOME" 2>&1 || true
} > "$META_DIR/system_info.txt"

python -m pip freeze > "$META_DIR/pip_freeze.txt" 2>&1 || true
conda env export --no-builds > "$META_DIR/conda_environment.yml" 2>&1 || true
conda list --explicit > "$META_DIR/conda_explicit.txt" 2>&1 || true

{
  echo "---- official point/rim summary ----"
  find "$OFFICIAL_EVAL_DIR" -maxdepth 1 -name '*summary.json' -print -exec cat {} \;
  echo
  echo "---- checkpoint metadata ----"
  cat "$CKPT.json"
} > "$META_DIR/results_summary.txt"

{
  echo "Raw and converted SkullBreak data are intentionally excluded."
  echo "Expected official split: train=114 skulls/570 cases, test=20 skulls/100 cases."
  if [[ -f data/SkullBreakPC/manifest.jsonl ]]; then
    echo "manifest_records=$(wc -l < data/SkullBreakPC/manifest.jsonl)"
    sha256sum data/SkullBreakPC/manifest.jsonl
  fi
  if [[ -L data/SkullBreakPC ]]; then
    echo "dataset_link=$(readlink data/SkullBreakPC)"
  fi
} > "$META_DIR/dataset_inventory.txt"

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git rev-parse HEAD > "$META_DIR/git_head.txt"
  git status --short > "$META_DIR/git_status.txt"
  git diff --binary HEAD > "$META_DIR/git_worktree.patch"
  git ls-files --others --exclude-standard > "$META_DIR/git_untracked_files.txt"
  git bundle create "$META_DIR/repository.bundle" --all
else
  echo "This server copy is not a Git working tree." > "$META_DIR/git_status.txt"
fi

tar \
  --exclude='./.git' \
  --exclude='./data' \
  --exclude='./experiments' \
  --exclude='./logs' \
  --exclude='./__pycache__' \
  --exclude='*/__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.so' \
  -czf "$META_DIR/code_snapshot.tar.gz" \
  .

cat > "$FILE_LIST" <<EOF
$CKPT
$CKPT.json
$CONFIG
$DATASET_CONFIG
$OFFICIAL_EVAL_DIR
$PREDICTION_DIR
$VIS_DIR
datasets/SkullBreakDataset.py
tools/prepare_skullbreak_pointcloud.py
tools/check_skullbreak_pointcloud.py
tools/test_skullbreak_data_protocol.py
tools/recalibrate_skullfix_batchnorm.py
scripts/run_skullbreak_implant_full100_bncal.sh
scripts/eval_skullbreak_implant.sh
scripts/visualize_skullbreak_implant.sh
scripts/archive_skullbreak_implant_seed0_baseline.sh
scripts/verify_skullbreak_implant_seed0_archive.sh
docs/skullbreak_adapointr_implant_baseline_protocol.md
EOF

if [[ -d "$MONITOR_EVAL_DIR" ]]; then
  echo "$MONITOR_EVAL_DIR" >> "$FILE_LIST"
fi
if [[ -f "$EXP_DIR/config.yaml" ]]; then
  echo "$EXP_DIR/config.yaml" >> "$FILE_LIST"
fi
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
du -sh "$EXP_DIR" "$OFFICIAL_EVAL_DIR" "$PREDICTION_DIR" "$VIS_DIR"
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
echo
echo "Download both files and verify the SHA256 locally before deleting server copies."
