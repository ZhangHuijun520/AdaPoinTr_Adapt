#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOME_ROOT="$(cd "$HOME" && pwd)"
cd "$ROOT"

BASE="mamba_v16_d6a_efficiency_implementation_zero_step_v1"
ARCHIVE_ROOT="${D6_EFFICIENCY_ZERO_STEP_ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v16_d6a_efficiency_zero_step_v1}"
WORKING="${ARCHIVE_ROOT}.working"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"

[[ ! -e "$ARCHIVE_ROOT" ]] || { echo "[error] archive root exists: $ARCHIVE_ROOT"; exit 1; }
[[ ! -e "$WORKING" ]] || { echo "[error] archive working path exists: $WORKING"; exit 1; }

LOCK="logs/mamba_v16_d6_contact_support/d6a_candidate_training_efficiency_protocol_v1"
ZERO="logs/mamba_v16_d6_contact_support/d6a_efficiency_implementation_zero_step_v1"
PARENT_FIX="logs/mamba_v16_d6_contact_support/d6a_candidate_training_parent_normalization_v1"
LOCK_FIX="logs/mamba_v16_d6_contact_support/d6a_candidate_protocol_lock_lf_repair_v1"
OVERLAY_FIX="logs/mamba_v16_d6_contact_support/d6a_efficiency_zero_step_overlay_normalization_v1"

for directory in "$LOCK" "$ZERO" "$PARENT_FIX" "$LOCK_FIX" "$OVERLAY_FIX"; do
  [[ -d "$directory" ]] || { echo "[error] missing frozen directory: $directory"; exit 1; }
done

(
  cd "$LOCK"
  sha256sum -c files.sha256
)
(
  cd "$ZERO"
  sha256sum -c files.sha256
)

mkdir -p "$WORKING/payload"

PATHS=(
  "adapointr_work/PoinTr/docs/mamba_v16_d6a_candidate_training_efficiency_preregistered_protocol_zh.md"
  "adapointr_work/PoinTr/docs/mamba_v16_d6a_candidate_training_efficiency_protocol_v1.json"
  "adapointr_work/PoinTr/docs/mamba_v16_d6a_efficiency_implementation_zero_step_preregistered_protocol_zh.md"
  "adapointr_work/PoinTr/docs/mamba_v16_d6a_efficiency_implementation_zero_step_protocol_v1.json"
  "adapointr_work/PoinTr/docs/mamba_v16_d6a_efficiency_zero_step_import_hotfix1_v1.json"
  "adapointr_work/PoinTr/docs/mamba_v16_d6a_efficiency_implementation_zero_step_complete_result_zh.md"
  "adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_calibration_weighted_zero_step_complete_result_zh.md"
  "adapointr_work/PoinTr/scripts/prepare_mamba_v16_d6a_candidate_training_efficiency_protocol.sh"
  "adapointr_work/PoinTr/scripts/run_mamba_v16_d6a_efficiency_implementation_zero_step.sh"
  "adapointr_work/PoinTr/scripts/archive_mamba_v16_d6a_efficiency_zero_step.sh"
  "adapointr_work/PoinTr/tools/lock_mamba_v16_d6a_candidate_training_efficiency_protocol.py"
  "adapointr_work/PoinTr/tools/test_mamba_v16_d6a_candidate_training_efficiency_protocol.py"
  "adapointr_work/PoinTr/tools/preflight_mamba_v16_d6a_efficiency_implementation_zero_step.py"
  "adapointr_work/PoinTr/tools/test_mamba_v16_d6a_efficiency_implementation.py"
  "adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_efficiency_zero_step_archive.py"
  "adapointr_work/PoinTr/utils/mamba_d5a_proposal.py"
  "adapointr_work/PoinTr/utils/mamba_d6a_slot_allocator.py"
  "adapointr_work/PoinTr/utils/mamba_d6a_efficiency.py"
  "adapointr_work/PoinTr/$LOCK"
  "adapointr_work/PoinTr/$ZERO"
  "adapointr_work/PoinTr/$PARENT_FIX"
  "adapointr_work/PoinTr/$LOCK_FIX"
  "adapointr_work/PoinTr/$OVERLAY_FIX"
)

for relative in "${PATHS[@]}"; do
  [[ -e "$HOME_ROOT/$relative" ]] || { echo "[error] missing payload: $relative"; exit 1; }
done

tar -cf - -C "$HOME_ROOT" "${PATHS[@]}" | tar -xf - -C "$WORKING/payload"

(
  cd "$WORKING/payload"
  find adapointr_work -type f -print0 | sort -z | xargs -0 sha256sum > payload_manifest.sha256
)

python tools/verify_mamba_v16_d6a_efficiency_zero_step_archive.py \
  --restore_root "$WORKING/payload"

mkdir -p "$ARCHIVE_ROOT"
tar -czf "$ARCHIVE" -C "$WORKING/payload" .

sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
stat -c '%s' "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.bytes"
tar -tzf "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.tar_contents.txt"

RESTORE="$WORKING/restore"
mkdir -p "$RESTORE"
tar -xzf "$ARCHIVE" -C "$RESTORE"
python "$RESTORE/adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_efficiency_zero_step_archive.py" \
  --restore_root "$RESTORE"

rm -rf -- "$WORKING"

echo "[ok] D6-A efficiency zero-step archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[excluded] NPZ, STL, checkpoints and sealed data"
ls -lh "$ARCHIVE_ROOT"
