#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

REPO_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v13_d3_round_a_negative_seed0}"
BASE="${ARCHIVE_NAME:-mamba_v13_d3_round_a_s0_s1_s2_negative_seed0_v1}"
PART_SIZE="${PART_SIZE:-256M}"
OVERWRITE="${OVERWRITE:-0}"
PARENT_LOCK="${PROTOCOL_LOCK:-$HOME/baseline_archives/mamba_v13_d3_round_a_v1}"

LOG_ROOT="logs/mamba_v13_d3_mug500plus"
S0_COMPLETION="$LOG_ROOT/s0_seed0_completion_v1/s0_seed0_completion_receipt.json"
S1_COMPLETION="$LOG_ROOT/s1_seed0_completion_v1/s1_seed0_completion_receipt.json"
S2_NEGATIVE="$LOG_ROOT/s2_head_feasibility_negative_freeze_v1/negative_result_receipt.json"
GATE_DIR="$LOG_ROOT/round_a_seed0_gate_v1"
REPORT="docs/mamba_v13_d3_round_a_s0_s1_s2_complete_negative_result_zh.md"
REPORT_SHA256="65ff436a3e7dc1795807a4b75538a969dafc4d7aae9f68189ff52dd671ccc516"

cd "$REPO_ROOT"
mkdir -p "$ARCHIVE_ROOT"

expected_root="$HOME/baseline_archives/mamba_v13_d3_round_a_negative_seed0"
[[ "$(realpath -m "$ARCHIVE_ROOT")" == "$(realpath -m "$expected_root")" ]] || {
  echo "[error] unexpected archive root: $ARCHIVE_ROOT" >&2
  exit 1
}

required=(
  "$S0_COMPLETION" "$S0_COMPLETION.sha256"
  "$S1_COMPLETION" "$S1_COMPLETION.sha256"
  "$S2_NEGATIVE" "$GATE_DIR/files.sha256" "$REPORT"
  "$PARENT_LOCK/files.sha256"
  "models/AdaPoinTr.py" "datasets/SkullBreakDataset.py"
  "utils/mamba_d3_contact.py"
  "tools/verify_mamba_v13_d3_round_a_negative_archive.py"
  "scripts/verify_mamba_v13_d3_round_a_negative_archive.sh"
)
for path in "${required[@]}"; do
  [[ -e "$path" ]] || { echo "[error] required frozen artifact missing: $path" >&2; exit 1; }
done
[[ "$(sha256sum "$REPORT" | awk '{print $1}')" == "$REPORT_SHA256" ]] || {
  echo "[error] complete negative-result report hash mismatch" >&2
  exit 1
}

python tools/verify_mamba_v13_d3_round_a_seed0.py --result_dir "$GATE_DIR"
python tools/test_mamba_v13_d3_round_a_negative_archive_contract.py

existing=()
shopt -s nullglob
existing+=("$ARCHIVE_ROOT/$BASE".part-*)
shopt -u nullglob
for path in \
  "$ARCHIVE_ROOT/$BASE.parts.sha256" \
  "$ARCHIVE_ROOT/$BASE.tar.sha256" \
  "$ARCHIVE_ROOT/$BASE.bytes" \
  "$ARCHIVE_ROOT/$BASE.parts.count"; do
  [[ -e "$path" ]] && existing+=("$path")
done
if (( ${#existing[@]} > 0 )); then
  if [[ "$OVERWRITE" != "1" ]]; then
    echo "[error] archive outputs already exist; set OVERWRITE=1 only after inspection" >&2
    exit 1
  fi
  rm -f -- "${existing[@]}"
fi

tmp_root="$(mktemp -d)"
metadata="$tmp_root/metadata"
selected="$tmp_root/selected_files.txt"
restore="$tmp_root/restore"
mkdir -p "$metadata" "$restore"
cleanup() {
  case "$tmp_root" in
    /tmp/tmp.*) rm -rf -- "$tmp_root" ;;
    *) echo "[warning] refusing to remove unexpected temporary path: $tmp_root" >&2 ;;
  esac
}
trap cleanup EXIT

cp -a "$PARENT_LOCK" "$metadata/parent_round_a_protocol_lock"
(cd "$metadata/parent_round_a_protocol_lock" && sha256sum -c files.sha256 >/dev/null)

cat > "$metadata/README.txt" <<EOF
Mamba v1.3 D3 Round-A S0/S1/S2 frozen negative result

Created: $(date --iso-8601=seconds)
Seed: 0
Development cases: 400
S0 disasters/dense-zero/coarse-zero: 248/33/135
S1 disasters/dense-zero/coarse-zero: 233/25/122
S1 passed all Round-A gates: false
S2 full-training eligible: false
Seed-1 authorized: false
Locked holdout accessed: false
Official test accessed: false
Candidate or gate revision authorized: false

This is a split-only archive. The server intentionally does not retain a full tar.
Download all part files plus parts.sha256, tar.sha256, bytes, and parts.count;
verify every part, concatenate in manifest/name order, then verify the rebuilt tar.
EOF

cat > "$metadata/PROTECTED_SPLITS.txt" <<'EOF'
seed1_authorized=false
holdout_accessed=false
holdout_authorized=false
official_test_accessed=false
candidate_or_rule_revision_authorized=false
skullbreak_confirmation20_accessed=false
old_monitor_accessed=false
skullfix_selection_accessed=false
EOF

{
  echo "archived_utc=$(date -u --iso-8601=seconds)"
  echo "hostname=$(hostname)"
  echo "user=$(id -un)"
  echo "repo_root=$REPO_ROOT"
  echo "archive_name=$BASE.tar"
  echo "part_size=$PART_SIZE"
  echo "full_tar_retained_on_server=false"
  echo "python=$(python --version 2>&1)"
  echo "nvcc=$(nvcc --version 2>/dev/null | tail -1 || true)"
  echo "kernel=$(uname -a 2>&1)"
  echo
  echo "===== GPU ====="
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>&1 || true
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
Git metadata is unavailable on this experiment-server source deployment.
Selected source and result files are independently covered by MANIFEST.sha256.
EOF
fi

{
  find "$LOG_ROOT" -type f -print
  find cfgs/MUG500plus_models -maxdepth 2 -type f -print
  find data/MUG500plusM2SourceSplitV1 -maxdepth 2 -type f -print 2>/dev/null || true
  find docs -maxdepth 1 -type f \( -name 'mamba_v13_d3*' -o -name 'mug500plus_skullbreak_skullfix_source_provenance_v1.json' \) -print
  find tools -maxdepth 1 -type f -name '*mamba_v13_d3*' -print
  find scripts -maxdepth 1 -type f -name '*mamba_v13_d3*' -print
  printf '%s\n' \
    main.py models/AdaPoinTr.py datasets/SkullBreakDataset.py \
    utils/mamba_d3_contact.py tools/runner.py tools/builder.py \
    tools/evaluate_skullfix_implant.py tools/benchmark_mamba_v12_efficiency.py \
    tools/recalibrate_skullfix_batchnorm.py
  python - "$S0_COMPLETION" "$S1_COMPLETION" <<'PY'
import json
import sys
from pathlib import Path
for completion_name in sys.argv[1:]:
    completion = json.loads(Path(completion_name).read_text())
    for fold in "ABCD":
        record = json.loads(Path(completion["run_records"][fold]["path"]).read_text())
        for name in ("checkpoint", "bncal_report"):
            print(record["artifacts"][name]["path"])
PY
} | awk 'NF && !seen[$0]++' | LC_ALL=C sort > "$selected"

while IFS= read -r path; do
  [[ -f "$path" ]] || { echo "[error] selected archive file missing: $path" >&2; exit 1; }
done < "$selected"

checkpoint_count="$(grep -c '/ckpt-last-bncal.pth$' "$selected")"
[[ "$checkpoint_count" -eq 8 ]] || {
  echo "[error] expected exactly eight BNCal checkpoints, found $checkpoint_count" >&2
  exit 1
}

cp "$selected" "$metadata/ARCHIVE_PATHS.txt"
xargs -d '\n' sha256sum < "$selected" > "$metadata/MANIFEST.sha256"
grep '/ckpt-last-bncal.pth  *$\|/ckpt-last-bncal.pth$' "$metadata/MANIFEST.sha256" \
  > "$metadata/BNCal_CHECKPOINTS.sha256" || true
[[ "$(wc -l < "$metadata/BNCal_CHECKPOINTS.sha256")" -eq 8 ]] || {
  echo "[error] BNCal checkpoint hash manifest is incomplete" >&2
  exit 1
}
sha256sum "$REPORT" > "$metadata/REPORT.sha256"
sha256sum -c "$metadata/MANIFEST.sha256" >/dev/null
sha256sum -c "$metadata/BNCal_CHECKPOINTS.sha256" >/dev/null

(cd "$tmp_root" && find metadata -type f ! -name 'METADATA.sha256' -print0 \
  | LC_ALL=C sort -z | xargs -0 sha256sum > metadata/METADATA.sha256)

selected_bytes="$(while IFS= read -r path; do stat -c '%s' "$path"; done < "$selected" \
  | awk '{sum += $1} END {printf "%.0f", sum}')"
free_bytes="$(( $(df -Pk "$HOME" | awk 'NR==2 {print $4}') * 1024 ))"
required_bytes="$(( selected_bytes + 1024 * 1024 * 1024 ))"
echo "[space] selected_bytes=$selected_bytes free_bytes=$free_bytes required_bytes=$required_bytes"
(( free_bytes >= required_bytes )) || {
  echo "[error] insufficient space for split-only archive plus 1 GiB margin" >&2
  exit 1
}

echo "[archive] streaming tar directly into $PART_SIZE parts"
tar -cf - -C "$tmp_root" metadata -C "$REPO_ROOT" --files-from "$selected" \
  | split -b "$PART_SIZE" -d -a 3 - "$ARCHIVE_ROOT/$BASE.part-"

shopt -s nullglob
parts=("$ARCHIVE_ROOT/$BASE".part-*)
shopt -u nullglob
(( ${#parts[@]} > 0 )) || { echo "[error] no archive parts were created" >&2; exit 1; }

(
  cd "$ARCHIVE_ROOT"
  sha256sum "$BASE".part-* > "$BASE.parts.sha256"
  sha256sum -c "$BASE.parts.sha256"
  stream_hash="$(cat "$BASE".part-* | sha256sum | awk '{print $1}')"
  printf '%s  %s\n' "$stream_hash" "$BASE.tar" > "$BASE.tar.sha256"
  total_bytes="$(stat -c '%s' "$BASE".part-* | awk '{sum += $1} END {printf "%.0f", sum}')"
  printf '%s  %s\n' "$total_bytes" "$BASE.tar" > "$BASE.bytes"
  printf '%s\n' "${#parts[@]}" > "$BASE.parts.count"
)

echo "[verify] listing and restoring the concatenated tar stream"
cat "${parts[@]}" | tar -tf - >/dev/null
cat "${parts[@]}" | tar -xf - -C "$restore"
python "$restore/tools/verify_mamba_v13_d3_round_a_negative_archive.py" --root "$restore"

echo "[ok] D3 Round-A split archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[note] no full tar is retained on the server"
echo "[next] download all parts plus four manifest/metadata files"
ls -lh "$ARCHIVE_ROOT"
