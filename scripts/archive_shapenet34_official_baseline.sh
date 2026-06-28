#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives}"
RUN_NAME="${RUN_NAME:-shapenet34_adapointr_official_full_4gpu}"
EXP_DIR="experiments/AdaPoinTr/ShapeNet34_models/$RUN_NAME"
TRAIN_LOG_DIR="logs/shapenet34_official_4gpu"
EVAL_LOG_DIR="logs/shapenet34_official_eval"
VIS_DIR="experiments/visualizations/shapenet34_official_full_4gpu"
STAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_NAME="${RUN_NAME}_${STAMP}"
TMP_ROOT="$(mktemp -d)"
META_DIR="$TMP_ROOT/metadata"
FILE_LIST="$TMP_ROOT/archive_file_list.txt"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

cd "$REPO_ROOT"
mkdir -p "$ARCHIVE_ROOT" "$META_DIR"

required_paths=(
  "$EXP_DIR/ckpt-best.pth"
  "$EXP_DIR/ckpt-last.pth"
  "cfgs/ShapeNet34_models/AdaPoinTr.yaml"
  "cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml"
  "cfgs/dataset_configs/ShapeNet-34.yaml"
  "cfgs/dataset_configs/ShapeNet-Unseen21.yaml"
  "$TRAIN_LOG_DIR"
  "$EVAL_LOG_DIR"
  "$VIS_DIR"
)

for path in "${required_paths[@]}"; do
  if [ ! -e "$path" ]; then
    echo "[error] required baseline artifact is missing: $path" >&2
    exit 1
  fi
done

cat > "$META_DIR/README.txt" <<EOF
AdaPoinTr ShapeNet34 official baseline archive

Created: $(date --iso-8601=seconds)
Repository: $REPO_ROOT
Experiment: $RUN_NAME

Restore procedure:
1. Verify the outer archive with the adjacent .sha256 file.
2. Extract the .tar file into a new empty directory.
3. Run: bash scripts/verify_shapenet34_official_archive.sh .
4. Recreate the ShapeNet55-34 dataset separately; raw data is not archived.
EOF

{
  echo "created=$(date --iso-8601=seconds)"
  echo "hostname=$(hostname)"
  echo "user=$(id -un)"
  echo "repo_root=$REPO_ROOT"
  echo "run_name=$RUN_NAME"
  echo "python=$(command -v python || true)"
  python -V 2>&1 || true
  python - <<'PY' 2>&1 || true
try:
    import torch
    print(f"torch={torch.__version__}")
    print(f"torch_cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()}")
    print(f"cuda_device_count={torch.cuda.device_count()}")
    if torch.cuda.is_available():
        for index in range(torch.cuda.device_count()):
            print(f"cuda_device_{index}={torch.cuda.get_device_name(index)}")
except Exception as exc:
    print(f"torch_probe_failed={exc!r}")
PY
  echo
  echo "---- nvidia-smi ----"
  nvidia-smi 2>&1 || true
  echo
  echo "---- nvcc ----"
  nvcc --version 2>&1 || true
  echo
  echo "---- storage ----"
  df -h "$HOME" 2>&1 || true
} > "$META_DIR/system_info.txt"

python -m pip freeze > "$META_DIR/pip_freeze.txt" 2>&1 || true
conda env export --no-builds > "$META_DIR/conda_environment.yml" 2>&1 || true
conda list --explicit > "$META_DIR/conda_explicit.txt" 2>&1 || true

{
  echo "---- evaluation metrics ----"
  grep -R "\[TEST\] Metrics" "$EVAL_LOG_DIR" -n || true
  echo
  echo "---- evaluation overall rows ----"
  grep -R "Overall" "$EVAL_LOG_DIR" -n || true
  echo
  echo "---- best validation records ----"
  grep -R "\[Validation\].*Metrics" "$EXP_DIR" "$TRAIN_LOG_DIR" -n \
    | sort -t"'" -k2,2gr \
    | head -20 || true
} > "$META_DIR/metrics_summary.txt"

{
  echo "Raw ShapeNet data is not included in this archive."
  echo
  for split in \
    data/ShapeNet55-34/ShapeNet-34/train.txt \
    data/ShapeNet55-34/ShapeNet-34/test.txt \
    data/ShapeNet55-34/ShapeNet-Unseen21/test.txt; do
    if [ -f "$split" ]; then
      wc -l "$split"
    fi
  done
  if [ -d data/ShapeNet55-34/shapenet_pc ]; then
    printf "npy_files "
    find -L data/ShapeNet55-34/shapenet_pc -maxdepth 1 -name '*.npy' | wc -l
  fi
  du -sh data/ShapeNet55-34 2>/dev/null || true
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
  --exclude='./baseline_archives' \
  --exclude='./__pycache__' \
  --exclude='*/__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.so' \
  -czf "$META_DIR/code_snapshot.tar.gz" \
  .

{
  cat <<EOF
$EXP_DIR
cfgs/ShapeNet34_models/AdaPoinTr.yaml
cfgs/ShapeNetUnseen21_models/AdaPoinTr.yaml
cfgs/dataset_configs/ShapeNet-34.yaml
cfgs/dataset_configs/ShapeNet-Unseen21.yaml
$TRAIN_LOG_DIR
$EVAL_LOG_DIR
$VIS_DIR
EOF
  optional_paths=(
    "docs/shapenet34_adapointr_official_full_report_zh.md"
    "docs/shapenet34_official_comparison.md"
    "docs/shapenet34_official_4gpu.md"
    "tools/diagnose_shapenet34_fscore.py"
    "scripts/run_shapenet34_adapointr_official_4gpu.sh"
    "scripts/eval_shapenet34_official_seen_unseen.sh"
    "scripts/eval_shapenet34_adapointr_seen_unseen.sh"
    "scripts/visualize_shapenet34_official.sh"
    "scripts/archive_shapenet34_official_baseline.sh"
    "scripts/verify_shapenet34_official_archive.sh"
  )
  for path in "${optional_paths[@]}"; do
    if [ -e "$path" ]; then
      printf '%s\n' "$path"
    fi
  done
} | awk '!seen[$0]++' > "$FILE_LIST"

while IFS= read -r path; do
  if [ -d "$path" ]; then
    find "$path" -type f -print0
  elif [ -f "$path" ]; then
    printf '%s\0' "$path"
  fi
done < "$FILE_LIST" \
  | sort -zu \
  | xargs -0 sha256sum > "$META_DIR/MANIFEST.sha256"

cp "$FILE_LIST" "$META_DIR/ARCHIVE_PATHS.txt"

ARCHIVE_PATH="$ARCHIVE_ROOT/$ARCHIVE_NAME.tar"
echo "[archive] selected source directories:"
du -sh "$EXP_DIR" "$TRAIN_LOG_DIR" "$EVAL_LOG_DIR" "$VIS_DIR"
echo "[archive] destination filesystem:"
df -h "$ARCHIVE_ROOT"

tar -cf "$ARCHIVE_PATH" \
  -C "$TMP_ROOT" metadata \
  -C "$REPO_ROOT" \
  --files-from "$FILE_LIST"

(cd "$ARCHIVE_ROOT" && sha256sum "$(basename "$ARCHIVE_PATH")" > "$(basename "$ARCHIVE_PATH").sha256")

echo "[ok] archive: $ARCHIVE_PATH"
echo "[ok] checksum: $ARCHIVE_PATH.sha256"
du -h "$ARCHIVE_PATH" "$ARCHIVE_PATH.sha256"
echo
echo "Download both files to persistent storage before deleting the server copy."
