#!/usr/bin/env bash
set -euo pipefail

HOME_ROOT="$HOME"
REPO="$HOME_ROOT/adapointr_work/PoinTr"
LOGS="$REPO/logs/mamba_v16_d6_contact_support"
FREEZE="$LOGS/d6a_r1_latency_posthoc_profiling_result_freeze_v1"
ARCHIVE_ROOT="${D6_R1_PROFILING_ARCHIVE_ROOT:-$HOME_ROOT/baseline_archives/mamba_v16_d6a_r1_latency_posthoc_profiling_result_v1}"
EXPECTED_ROOT="$HOME_ROOT/baseline_archives/mamba_v16_d6a_r1_latency_posthoc_profiling_result_v1"
BASE="mamba_v16_d6a_r1_latency_posthoc_profiling_result_v1"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"

[[ "$(realpath -m "$ARCHIVE_ROOT")" == "$(realpath -m "$EXPECTED_ROOT")" ]] || {
  echo "[error] unexpected archive root: $ARCHIVE_ROOT"
  exit 1
}
[[ ! -e "$ARCHIVE_ROOT" ]] || { echo "[error] archive root already exists: $ARCHIVE_ROOT"; exit 1; }

WORKING="${ARCHIVE_ROOT}.working"
[[ ! -e "$WORKING" ]] || { echo "[error] archive working path already exists: $WORKING"; exit 1; }
mkdir -p "$WORKING/payload"
cleanup() { rm -rf -- "$WORKING"; }
trap cleanup EXIT

echo "===== Verify frozen result inventory ====="
[[ "$(sha256sum "$FREEZE/artifact_inventory.tsv" | awk '{print $1}')" == \
  "698551249e7983fb98a42ad7fd7bc146b229c612013dded274d6a97e3d6d4c1f" ]]
[[ "$(sha256sum "$FREEZE/profiling_result_freeze_receipt.json" | awk '{print $1}')" == \
  "4156c7a0fb75c7d4f4108bf2d3e14b9483a415ba21e8c56ff2b11c8a66f02501" ]]
(cd "$FREEZE" && sha256sum -c files.sha256)

PATHS=(
  adapointr_work/PoinTr/docs/mamba_v16_d6a_r1_latency_posthoc_profiling_complete_result_zh.md
  adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_archive.py
  adapointr_work/PoinTr/tools/test_mamba_v16_d6a_r1_latency_bottleneck_posthoc_profiling_protocol.py
  adapointr_work/PoinTr/tools/test_mamba_v16_d6a_r1_latency_posthoc_profiling_execution_contract.py
  adapointr_work/PoinTr/scripts/archive_mamba_v16_d6a_r1_latency_posthoc_profiling.sh
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_latency_posthoc_profiling_result_freeze_v1/files.sha256
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_latency_posthoc_profiling_result_freeze_v1/artifact_inventory.tsv
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_latency_posthoc_profiling_result_freeze_v1/profiling_result_freeze_receipt.json
)

while IFS=$'\t' read -r _sha _bytes relative; do
  [[ -n "$relative" && "$relative" != /* && "$relative" != *".."* ]] || {
    echo "[error] unsafe inventory path: $relative"
    exit 1
  }
  PATHS+=("adapointr_work/PoinTr/$relative")
done < "$FREEZE/artifact_inventory.tsv"

cd "$HOME_ROOT"
for path in "${PATHS[@]}"; do
  [[ -f "$path" ]] || { echo "[error] missing archive input: $HOME_ROOT/$path"; exit 1; }
done

echo "===== Stage and verify payload ====="
tar -cf - "${PATHS[@]}" | tar -xf - -C "$WORKING/payload"
(
  cd "$WORKING/payload"
  find adapointr_work -type f -print0 | sort -z | xargs -0 sha256sum > payload_manifest.sha256
)
python "$REPO/tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_archive.py" \
  --restore_root "$WORKING/payload"

echo "===== Create and restore-verify archive ====="
mkdir -p "$ARCHIVE_ROOT"
tar -czf "$ARCHIVE" -C "$WORKING/payload" .
tar -tzf "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.tar_contents.txt"
stat -c '%s' "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.bytes"
(cd "$ARCHIVE_ROOT" && sha256sum "$BASE.tar.gz" > "$BASE.tar.gz.sha256")

mkdir -p "$WORKING/restore"
tar -xzf "$ARCHIVE" -C "$WORKING/restore"
python "$WORKING/restore/adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_r1_latency_posthoc_profiling_archive.py" \
  --restore_root "$WORKING/restore"
(cd "$ARCHIVE_ROOT" && sha256sum -c "$BASE.tar.gz.sha256")

echo "[ok] D6-A R1 latency profiling archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[excluded] checkpoints, NPZ, STL and sealed data"
echo "[locked] optimization=false training=false seed1=false D6B=false sealed=false"
ls -lh "$ARCHIVE_ROOT"
