#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v12_d22_negative_seed0}"
ARCHIVE_NAME="${ARCHIVE_NAME:-skullbreak_mamba_v12_d22_negative_contact_support_seed0_v1}"
CONDA_ENV="${CONDA_ENV:-adapointr-mamba}"
OVERWRITE="${OVERWRITE:-0}"
CREATE_PARTS="${CREATE_PARTS:-1}"
PART_SIZE_MB="${PART_SIZE_MB:-256}"
RESERVE_GB="${RESERVE_GB:-2}"

D22_ROOT="logs/skullbreak_mamba_v12_d22_local_rim"
BASE_PROTOCOL_ROOT="logs/skullbreak_mamba_v12_development/protocol_v1"
CONFIG_DIR="cfgs/SkullBreak_models/generated_mamba_v12_d22_local_rim_v1"
DATASET_CONFIG="cfgs/dataset_configs/SkullBreak.yaml"
DATASET_MANIFEST="data/SkullBreakPC_out8192/manifest.jsonl"

ARCHIVE_PATH="$ARCHIVE_ROOT/$ARCHIVE_NAME.tar"
ARCHIVE_SHA="$ARCHIVE_PATH.sha256"
ARCHIVE_BYTES="$ARCHIVE_ROOT/$ARCHIVE_NAME.bytes"
PART_PREFIX="$ARCHIVE_ROOT/$ARCHIVE_NAME.part-"
PARTS_SHA="$ARCHIVE_ROOT/$ARCHIVE_NAME.parts.sha256"

cd "$REPO_ROOT"
mkdir -p "$ARCHIVE_ROOT"

if ! [[ "$PART_SIZE_MB" =~ ^[1-9][0-9]*$ ]]; then
  echo "[error] PART_SIZE_MB must be a positive integer" >&2
  exit 2
fi

shopt -s nullglob
existing_parts=("$PART_PREFIX"*)
shopt -u nullglob
if [[ -e "$ARCHIVE_PATH" || -e "$ARCHIVE_SHA" || \
      -e "$ARCHIVE_BYTES" || -e "$PARTS_SHA" || \
      ${#existing_parts[@]} -gt 0 ]]; then
  if [[ "$OVERWRITE" != "1" ]]; then
    echo "[error] archive outputs already exist below $ARCHIVE_ROOT" >&2
    echo "        Set OVERWRITE=1 only after confirming replacement is intended." >&2
    exit 1
  fi
  rm -f -- "$ARCHIVE_PATH" "$ARCHIVE_SHA" "$ARCHIVE_BYTES" \
    "$PARTS_SHA" "${existing_parts[@]}"
fi

required_paths=(
  "$D22_ROOT/round_a_selection.json"
  "$D22_ROOT/round_a_selection.json.sha256"
  "$D22_ROOT/frozen_negative_result_v1"
  "$D22_ROOT/posthoc_contact_support_v1"
  "$D22_ROOT/preflight_receipt.json"
  "$BASE_PROTOCOL_ROOT"
  "$CONFIG_DIR"
  "$DATASET_CONFIG"
  "$DATASET_MANIFEST"
  "docs/mamba_v12_d22_local_rim_trust_protocol_v1.json"
  "docs/mamba_v12_d22_local_rim_trust_preregistered_protocol_zh.md"
  "docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1.json"
  "docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1_zh.md"
  "docs/mamba_v12_d22_contact_support_posthoc_v1.json"
  "docs/mamba_v12_d22_contact_support_posthoc_protocol_zh.md"
  "docs/mamba_v12_d22_local_rim_trust_complete_negative_result_contact_support_posthoc_report_zh.md"
  "tools/verify_mamba_v12_d22_archive_payload.py"
  "scripts/verify_skullbreak_mamba_v12_d22_archive.sh"
)

missing_paths=()
for path in "${required_paths[@]}"; do
  [[ -e "$path" ]] || missing_paths+=("$path")
done
if (( ${#missing_paths[@]} > 0 )); then
  echo "[error] required D2.2 artifacts are missing:" >&2
  printf '  - %s\n' "${missing_paths[@]}" >&2
  exit 1
fi

tmp_root="$(mktemp -d)"
metadata_dir="$tmp_root/metadata"
checkpoint_list="$tmp_root/checkpoints.txt"
archive_paths="$tmp_root/archive_paths.txt"
mkdir -p "$metadata_dir"
cleanup() {
  rm -rf -- "$tmp_root"
}
trap cleanup EXIT

echo "[verify] D2.2 frozen receipts, 12 run records, and post-hoc tree"
python tools/verify_mamba_v12_d22_archive_payload.py \
  --root . --write_checkpoint_list "$checkpoint_list"

mapfile -t checkpoints < "$checkpoint_list"
if (( ${#checkpoints[@]} != 12 )); then
  echo "[error] expected 12 checkpoint paths, found ${#checkpoints[@]}" >&2
  exit 1
fi

checkpoint_sidecars=()
for checkpoint in "${checkpoints[@]}"; do
  [[ -s "$checkpoint" ]] || {
    echo "[error] checkpoint is missing or empty: $checkpoint" >&2
    exit 1
  }
  [[ -s "$checkpoint.json" ]] || {
    echo "[error] BNCal sidecar is missing or empty: $checkpoint.json" >&2
    exit 1
  }
  checkpoint_sidecars+=("$checkpoint.json")
done

cat > "$metadata_dir/README.txt" <<EOF
SkullBreak Mamba v1.2 D2.2 frozen negative result and contact-support post-hoc

Created: $(date --iso-8601=seconds)
Protocol: mamba-v12-d22-local-rim-trust-v1
Candidates: R0, R1, R2
Folds: A, B, C, D
Seed: 0
Canonical checkpoints: 12 BN-calibrated ckpt-last-bncal.pth files
Round-A result: winner=None; Round B forbidden
Post-hoc: observation-only and selection-inert contact-support replay
Protected splits: confirmation20, old monitor, and official test were not used

This archive contains the 12 canonical BNCal checkpoints and JSON sidecars,
the complete D2.2 log/evidence tree, immutable negative-result receipts,
1260-row contact-support replay and analysis, locked protocol/config files,
relevant source code, and runtime metadata. Raw datasets are excluded.

The post-hoc evidence must not be used to select R1/R2, relax the nonfinite
gate, alter the 2 mm primary contact definition, or reopen Round B.
EOF

cp "$DATASET_MANIFEST" "$metadata_dir/skullbreak_out8192_manifest.jsonl"

{
  echo "archived_utc=$(date -u --iso-8601=seconds)"
  echo "hostname=$(hostname)"
  echo "user=$(id -un)"
  echo "repo_root=$REPO_ROOT"
  echo "archive_name=$ARCHIVE_NAME.tar"
  echo "conda_environment=$CONDA_ENV"
  echo "protocol=mamba-v12-d22-local-rim-trust-v1"
  echo "candidate_matrix=R0,R1,R2 x folds A,B,C,D x seed0"
  echo "bncal_checkpoints=12"
  echo "winner=None"
  echo "round_b_allowed=false"
  echo "posthoc_selection_inert=true"
  echo "confirmation20_used=false"
  echo "old_monitor_used=false"
  echo "official_test_used=false"
  echo "kernel=$(uname -a 2>&1)"
  echo "nvcc=$(nvcc --version 2>/dev/null | tail -1 || true)"
  echo
  echo "===== GPU ====="
  nvidia-smi --query-gpu=name,driver_version,memory.total \
    --format=csv,noheader 2>&1 || true
  echo
  echo "===== CPU ====="
  lscpu 2>&1 || true
  echo
  echo "===== STORAGE ====="
  df -h "$HOME" 2>&1 || true
} > "$metadata_dir/runtime_environment.txt"

if command -v conda >/dev/null 2>&1; then
  conda list -n "$CONDA_ENV" > "$metadata_dir/conda_list.txt"
  conda run -n "$CONDA_ENV" python -m pip freeze \
    > "$metadata_dir/pip_freeze.txt"
  conda run -n "$CONDA_ENV" python -c '
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
' > "$metadata_dir/python_runtime.txt"
else
  echo "[error] conda is required to capture the frozen runtime" >&2
  exit 1
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git rev-parse HEAD > "$metadata_dir/git_head.txt"
  git describe --tags --always --dirty > "$metadata_dir/git_describe.txt"
  git status --short > "$metadata_dir/git_status.txt"
  git diff --binary > "$metadata_dir/git_worktree.patch"
  git diff --binary --cached > "$metadata_dir/git_index.patch"
else
  cat > "$metadata_dir/git_status.txt" <<'EOF'
Git metadata is unavailable on this experiment server deployment.
Source files and protocols are independently covered by MANIFEST.sha256.
EOF
fi

sha256sum "${checkpoints[@]}" > "$metadata_dir/CHECKPOINTS.sha256"

cat > "$archive_paths" <<EOF
$D22_ROOT
$BASE_PROTOCOL_ROOT
$CONFIG_DIR
$DATASET_CONFIG
datasets/SkullBreakDataset.py
models/AdaPoinTr.py
tools/analyze_mamba_v12_d22_contact_support_posthoc.py
tools/benchmark_mamba_v12_efficiency.py
tools/evaluate_skullfix_implant.py
tools/freeze_mamba_v12_d22_negative_result.py
tools/generate_mamba_v12_d22_configs.py
tools/generate_mamba_v12_d22_teacher_cache.py
tools/instrument_mamba_full_pipeline.py
tools/prepare_mamba_v12_d22_gt_rim_cache.py
tools/recalibrate_skullfix_batchnorm.py
tools/replay_mamba_v12_d22_contact_support.py
tools/select_mamba_v12_d22_round_a.py
tools/test_mamba_v12_d22_config_generation.py
tools/test_mamba_v12_d22_contact_support_posthoc.py
tools/test_mamba_v12_d22_negative_freeze.py
tools/test_mamba_v12_d22_rim_proxy.py
tools/test_mamba_v12_d22_selection.py
tools/verify_mamba_v12_d22_archive_payload.py
tools/verify_mamba_v12_d22_r0_zero_perturbation.py
tools/write_mamba_v12_run_record.py
tools/runner.py
utils/mamba_d22_contact_support.py
utils/mamba_d22_geometry.py
scripts/archive_skullbreak_mamba_v12_d22_negative_posthoc.sh
scripts/freeze_skullbreak_mamba_v12_d22_negative_result.sh
scripts/launch_skullbreak_mamba_v12_d22_contact_support_posthoc_tmux.sh
scripts/launch_skullbreak_mamba_v12_d22_round_a_tmux.sh
scripts/prepare_skullbreak_mamba_v12_d22_protocol.sh
scripts/run_skullbreak_mamba_v12_d22_contact_support_posthoc.sh
scripts/run_skullbreak_mamba_v12_d22_round_a.sh
scripts/run_skullbreak_mamba_v12_d22_round_a_fold.sh
scripts/verify_skullbreak_mamba_v12_d22_archive.sh
docs/mamba_v12_d22_contact_support_posthoc_protocol_zh.md
docs/mamba_v12_d22_contact_support_posthoc_v1.json
docs/mamba_v12_d22_local_rim_trust_complete_negative_result_contact_support_posthoc_report_zh.md
docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1.json
docs/mamba_v12_d22_local_rim_trust_implementation_amendment_v1_zh.md
docs/mamba_v12_d22_local_rim_trust_preregistered_protocol_zh.md
docs/mamba_v12_d22_local_rim_trust_protocol_v1.json
EOF

printf '%s\n' "${checkpoints[@]}" >> "$archive_paths"
printf '%s\n' "${checkpoint_sidecars[@]}" >> "$archive_paths"

for checkpoint in "${checkpoints[@]}"; do
  run_config="$(dirname "$checkpoint")/config.yaml"
  [[ -f "$run_config" ]] && echo "$run_config" >> "$archive_paths"
done

awk 'NF && !seen[$0]++' "$archive_paths" > "$archive_paths.tmp"
mv "$archive_paths.tmp" "$archive_paths"

while IFS= read -r path; do
  if [[ ! -e "$path" ]]; then
    echo "[error] selected archive path is missing: $path" >&2
    exit 1
  fi
  if [[ -d "$path" ]]; then
    find "$path" -type f -print0
  else
    printf '%s\0' "$path"
  fi
done < "$archive_paths" \
  | LC_ALL=C sort -zu \
  | xargs -0 sha256sum > "$metadata_dir/MANIFEST.sha256"

cp "$archive_paths" "$metadata_dir/ARCHIVE_PATHS.txt"

echo "[verify] selected payload before archive creation"
sha256sum -c "$metadata_dir/MANIFEST.sha256" >/dev/null

payload_bytes="$(
  awk '{sub(/^[0-9a-f]+[[:space:]]+\*?/, ""); print}' \
    "$metadata_dir/MANIFEST.sha256" \
  | tr '\n' '\0' \
  | xargs -0 stat -c '%s' \
  | awk '{total += $1} END {printf "%.0f", total}'
)"
archive_copies=1
[[ "$CREATE_PARTS" == "1" ]] && archive_copies=2
required_bytes="$((payload_bytes * archive_copies + RESERVE_GB * 1024 * 1024 * 1024))"
available_bytes="$(df -PB1 "$ARCHIVE_ROOT" | awk 'NR==2 {print $4}')"
echo "[space] selected payload bytes: $payload_bytes"
echo "[space] required free bytes:    $required_bytes"
echo "[space] available free bytes:   $available_bytes"
if (( available_bytes < required_bytes )); then
  echo "[error] insufficient free space for tar plus requested parts" >&2
  echo "        Set CREATE_PARTS=0 only if a single tar is sufficient." >&2
  df -h "$ARCHIVE_ROOT"
  exit 1
fi

echo "[archive] creating uncompressed tar for robust resumable transfer"
tar -cf "$ARCHIVE_PATH" \
  -C "$tmp_root" metadata \
  -C "$REPO_ROOT" --files-from "$archive_paths"

tar -tf "$ARCHIVE_PATH" >/dev/null
(
  cd "$ARCHIVE_ROOT"
  sha256sum "$ARCHIVE_NAME.tar" > "$ARCHIVE_NAME.tar.sha256"
  sha256sum -c "$ARCHIVE_NAME.tar.sha256"
  stat -c '%s  %n' "$ARCHIVE_NAME.tar" > "$ARCHIVE_NAME.bytes"
)

if [[ "$CREATE_PARTS" == "1" ]]; then
  echo "[archive] splitting into ${PART_SIZE_MB} MiB download parts"
  split -b "${PART_SIZE_MB}M" -d -a 3 \
    "$ARCHIVE_PATH" "$PART_PREFIX"
  (
    cd "$ARCHIVE_ROOT"
    sha256sum "$ARCHIVE_NAME".part-* > "$ARCHIVE_NAME.parts.sha256"
    sha256sum -c "$ARCHIVE_NAME.parts.sha256"
  )
fi

echo "[ok] D2.2 archive created and verified"
echo "[archive] $ARCHIVE_PATH"
echo "[checksum] $ARCHIVE_SHA"
echo "[bytes] $ARCHIVE_BYTES"
if [[ "$CREATE_PARTS" == "1" ]]; then
  echo "[parts] $PARTS_SHA"
  echo "[next] download *.part-* plus *.parts.sha256, *.tar.sha256, and *.bytes"
else
  echo "[next] download the tar, tar.sha256, and bytes file"
fi
ls -lh "$ARCHIVE_ROOT"
