#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

REPO_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v13_d3_s2_feasibility_negative_seed0}"
ARCHIVE_NAME="${ARCHIVE_NAME:-mamba_v13_d3_s2_head_feasibility_negative_seed0_v1}"
PARENT_LOCK="${PROTOCOL_LOCK:-$HOME/baseline_archives/mamba_v13_d3_round_a_v1}"
OVERWRITE="${OVERWRITE:-0}"

RUNS="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_v1"
COMPLETION="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_completion_v1/s2_head_feasibility_completion_receipt.json"
BASE_LOCK="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_protocol_v1"
HOTFIX="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_hotfix1"
S0_COMPLETION="logs/mamba_v13_d3_mug500plus/s0_seed0_completion_v1/s0_seed0_completion_receipt.json"
FREEZE="logs/mamba_v13_d3_mug500plus/s2_head_feasibility_negative_freeze_v1"
REPORT="docs/mamba_v13_d3_s2_head_feasibility_negative_result_zh.md"

ARCHIVE="$ARCHIVE_ROOT/$ARCHIVE_NAME.tar"
ARCHIVE_SHA="$ARCHIVE.sha256"
ARCHIVE_BYTES="$ARCHIVE_ROOT/$ARCHIVE_NAME.bytes"

cd "$REPO_ROOT"
mkdir -p "$ARCHIVE_ROOT"
if [[ -e "$ARCHIVE" || -e "$ARCHIVE_SHA" || -e "$ARCHIVE_BYTES" ]]; then
  if [[ "$OVERWRITE" != "1" ]]; then
    echo "[error] archive output already exists below $ARCHIVE_ROOT" >&2
    exit 1
  fi
  rm -f -- "$ARCHIVE" "$ARCHIVE_SHA" "$ARCHIVE_BYTES"
fi

required=(
  "$RUNS"
  "$COMPLETION"
  "$COMPLETION.sha256"
  "$BASE_LOCK"
  "$HOTFIX"
  "$S0_COMPLETION"
  "$S0_COMPLETION.sha256"
  "$REPORT"
  "$PARENT_LOCK/files.sha256"
  "models/AdaPoinTr.py"
  "utils/mamba_d3_contact.py"
  "tools/freeze_mamba_v13_d3_s2_feasibility_negative.py"
  "tools/verify_mamba_v13_d3_s2_feasibility_archive.py"
  "scripts/archive_mamba_v13_d3_s2_feasibility_negative.sh"
  "scripts/verify_mamba_v13_d3_s2_feasibility_archive.sh"
)
for path in "${required[@]}"; do
  [[ -e "$path" ]] || { echo "[error] required artifact missing: $path" >&2; exit 1; }
done

python tools/freeze_mamba_v13_d3_s2_feasibility_negative.py \
  --runs_root "$RUNS" \
  --completion "$COMPLETION" \
  --base_lock_dir "$BASE_LOCK" \
  --hotfix_dir "$HOTFIX" \
  --s0_completion "$S0_COMPLETION" \
  --report "$REPORT" \
  --output_dir "$FREEZE"
(cd "$FREEZE" && sha256sum -c files.sha256)

tmp_root="$(mktemp -d)"
metadata="$tmp_root/metadata"
paths="$tmp_root/archive_paths.txt"
restore="$tmp_root/restore"
mkdir -p "$metadata" "$restore"
cleanup() { rm -rf -- "$tmp_root"; }
trap cleanup EXIT

cp -a "$PARENT_LOCK" "$metadata/parent_round_a_protocol_lock"
(cd "$metadata/parent_round_a_protocol_lock" && sha256sum -c files.sha256)

cat > "$metadata/README.txt" <<EOF
Mamba v1.3 D3 S2 head-only feasibility frozen negative result

Created: $(date --iso-8601=seconds)
Seed: 0
Folds: A, B, C, D
Development cases: 400
Case hits: 392
Missed cases: 8
Hard gate: failed because every fold was required to reach 100/100
S2 weight calibration authorized: false
S2 full training authorized: false
S1 weight calibration authorized by this archive: false
Holdout accessed: false
Selection started: false

This compact archive contains four head-only checkpoints, all per-case results,
base and hotfix locks, completion and negative-result receipts, the Chinese
report, relevant source, runtime metadata, and the parent Round-A protocol lock.
The four large S0 checkpoints and all raw/derived datasets are intentionally
excluded. Their SHA256 values and frozen run-record lineage remain recorded.

Feasibility checkpoints are audit-only and must not initialize full S2.
EOF

{
  echo "archived_utc=$(date -u --iso-8601=seconds)"
  echo "hostname=$(hostname)"
  echo "user=$(id -un)"
  echo "repo_root=$REPO_ROOT"
  echo "archive=$ARCHIVE_NAME.tar"
  echo "protocol=mamba-v13-d3-s2-head-only-feasibility-execution-amendment-v1"
  echo "result=failed_preregistered_hard_gate"
  echo "fold_hits=A98,B96,C98,D100"
  echo "pooled_hits=392/400"
  echo "s2_calibration_authorized=false"
  echo "s2_full_training_authorized=false"
  echo "s1_calibration_authorized=false"
  echo "holdout_accessed=false"
  echo "selection_started=false"
  echo "kernel=$(uname -a 2>&1)"
  echo "nvcc=$(nvcc --version 2>/dev/null | tail -1 || true)"
  echo
  echo "===== GPU ====="
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>&1 || true
  echo
  echo "===== CPU ====="
  lscpu 2>&1 || true
  echo
  echo "===== STORAGE ====="
  df -h "$HOME" 2>&1 || true
} > "$metadata/runtime_environment.txt"

conda list -n "${CONDA_ENV:-adapointr-mamba}" > "$metadata/conda_list.txt"
python -m pip freeze > "$metadata/pip_freeze.txt"
python - <<'PY' > "$metadata/python_runtime.txt"
import importlib.metadata
import sys
import torch
print("python=" + sys.version.replace("\n", " "))
print("python_executable=" + sys.executable)
print("torch=" + torch.__version__)
print("torch_cuda=" + str(torch.version.cuda))
print("cuda_available=" + str(torch.cuda.is_available()))
print("cudnn=" + str(torch.backends.cudnn.version()))
if torch.cuda.is_available():
    print("gpu=" + torch.cuda.get_device_name(0))
for package in ("mamba-ssm", "causal-conv1d", "triton"):
    try:
        print(package + "=" + importlib.metadata.version(package))
    except importlib.metadata.PackageNotFoundError:
        print(package + "=missing")
PY

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git rev-parse HEAD > "$metadata/git_head.txt"
  git describe --tags --always --dirty > "$metadata/git_describe.txt"
  git status --short > "$metadata/git_status.txt"
  git diff --binary > "$metadata/git_worktree.patch"
  git diff --binary --cached > "$metadata/git_index.patch"
else
  cat > "$metadata/git_status.txt" <<'EOF'
Git metadata is unavailable on this experiment server deployment.
Selected source files are independently covered by MANIFEST.sha256.
EOF
fi

cat > "$paths" <<EOF
$RUNS
$(dirname "$COMPLETION")
$BASE_LOCK
$HOTFIX
$(dirname "$S0_COMPLETION")
$FREEZE
logs/mamba_v13_d3_mug500plus/s2_head_feasibility_tmux
cfgs/MUG500plus_models/generated_mamba_v13_d3_s0_seed0_v1
models/AdaPoinTr.py
datasets/SkullBreakDataset.py
utils/mamba_d3_contact.py
docs/mamba_v13_d3_s2_head_only_feasibility_execution_amendment_v1.json
docs/mamba_v13_d3_s2_head_only_feasibility_execution_amendment_zh.md
docs/mamba_v13_d3_s2_head_only_feasibility_hotfix1_20260825.json
$REPORT
tools/authorize_mamba_v13_d3_s2_feasibility_hotfix1.py
tools/freeze_mamba_v13_d3_s2_feasibility.py
tools/freeze_mamba_v13_d3_s2_feasibility_negative.py
tools/lock_mamba_v13_d3_s2_feasibility_protocol.py
tools/run_mamba_v13_d3_s2_feasibility_fold.py
tools/test_mamba_v13_d3_s2_feasibility_contract.py
tools/verify_mamba_v13_d3_s2_feasibility_archive.py
scripts/archive_mamba_v13_d3_s2_feasibility_negative.sh
scripts/launch_mamba_v13_d3_s2_feasibility_tmux.sh
scripts/prepare_mamba_v13_d3_s2_feasibility.sh
scripts/run_mamba_v13_d3_s2_feasibility.sh
scripts/run_mamba_v13_d3_s2_feasibility_fold.sh
scripts/verify_mamba_v13_d3_s2_feasibility_archive.sh
EOF

for fold in A B C D; do
  echo "logs/mamba_v13_d3_mug500plus/round_a/S0_fold${fold}_seed0/run_record.json" >> "$paths"
  echo "logs/mamba_v13_d3_mug500plus/round_a/S0_fold${fold}_seed0/run_record.json.sha256" >> "$paths"
done
awk 'NF && !seen[$0]++' "$paths" > "$paths.tmp"
mv "$paths.tmp" "$paths"

while IFS= read -r path; do
  [[ -e "$path" ]] || { echo "[error] selected archive path missing: $path" >&2; exit 1; }
  if [[ -d "$path" ]]; then
    find "$path" -type f -print0
  else
    printf '%s\0' "$path"
  fi
done < "$paths" | LC_ALL=C sort -zu | xargs -0 sha256sum > "$metadata/MANIFEST.sha256"

find "$RUNS" -type f -name 'head_only_checkpoint.pth' -print0 \
  | LC_ALL=C sort -z | xargs -0 sha256sum > "$metadata/HEAD_CHECKPOINTS.sha256"
[[ "$(wc -l < "$metadata/HEAD_CHECKPOINTS.sha256")" -eq 4 ]] || {
  echo "[error] expected exactly four head checkpoints" >&2
  exit 1
}
cp "$paths" "$metadata/ARCHIVE_PATHS.txt"
sha256sum -c "$metadata/MANIFEST.sha256" >/dev/null
sha256sum -c "$metadata/HEAD_CHECKPOINTS.sha256" >/dev/null

echo "[archive] creating compact uncompressed tar"
tar -cf "$ARCHIVE" -C "$tmp_root" metadata -C "$REPO_ROOT" --files-from "$paths"
tar -tf "$ARCHIVE" >/dev/null
(
  cd "$ARCHIVE_ROOT"
  sha256sum "$ARCHIVE_NAME.tar" > "$ARCHIVE_NAME.tar.sha256"
  sha256sum -c "$ARCHIVE_NAME.tar.sha256"
  stat -c '%s  %n' "$ARCHIVE_NAME.tar" > "$ARCHIVE_NAME.bytes"
)

echo "[verify] restoring compact archive into a temporary directory"
tar -xf "$ARCHIVE" -C "$restore"
python "$restore/tools/verify_mamba_v13_d3_s2_feasibility_archive.py" --root "$restore"

echo "[ok] S2 feasibility negative archive created and restore-verified"
echo "[archive] $ARCHIVE"
echo "[checksum] $ARCHIVE_SHA"
echo "[bytes] $ARCHIVE_BYTES"
echo "[next] download the tar, tar.sha256, and bytes file"
ls -lh "$ARCHIVE_ROOT"
