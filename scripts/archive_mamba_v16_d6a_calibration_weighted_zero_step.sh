#!/usr/bin/env bash
set -euo pipefail

HOME_ROOT="${HOME}"
REPO="$HOME_ROOT/adapointr_work/PoinTr"
ARCHIVE_ROOT="${D6_CALIBRATION_ARCHIVE_ROOT:-$HOME_ROOT/baseline_archives/mamba_v16_d6a_calibration_weighted_zero_step_v1}"
BASE="mamba_v16_d6a_calibration_weighted_zero_step_v1"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"

[[ "$(realpath -m "$ARCHIVE_ROOT")" == "$(realpath -m "$HOME_ROOT/baseline_archives/mamba_v16_d6a_calibration_weighted_zero_step_v1")" ]] || {
  echo "[error] unexpected archive root: $ARCHIVE_ROOT"
  exit 1
}

mkdir -p "$ARCHIVE_ROOT"
for suffix in tar.gz tar.gz.sha256 bytes tar_contents.txt; do
  [[ ! -e "$ARCHIVE_ROOT/$BASE.$suffix" ]] || {
    echo "[error] archive output already exists: $ARCHIVE_ROOT/$BASE.$suffix"
    exit 1
  }
done

STAGE="$(mktemp -d "$ARCHIVE_ROOT/.stage.XXXXXX")"
RESTORE="$(mktemp -d "$ARCHIVE_ROOT/.restore.XXXXXX")"
cleanup() {
  rm -rf -- "$STAGE" "$RESTORE"
}
trap cleanup EXIT

PATHS=(
  adapointr_work/PoinTr/docs/mamba_v16_d6a_slot32_mechanism_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_synthetic_zero_step_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_scipy_compatibility_amendment_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_slot32_implementation_zero_step_complete_result_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_ratio_calibration_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_ratio_calibration_preregistered_protocol_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_calibration_execution_authorization_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_calibration_execution_authorization_preregistered_protocol_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_calibration_execution_import_hotfix1_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_calibration_complete_result_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_calibrated_weighted_zero_step_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_calibrated_weighted_zero_step_preregistered_protocol_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_calibration_weighted_zero_step_complete_result_zh.md
  adapointr_work/PoinTr/utils/mamba_d4a_proposal.py
  adapointr_work/PoinTr/utils/mamba_d5a_proposal.py
  adapointr_work/PoinTr/utils/mamba_d6a_slot_allocator.py
  adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_calibration_weighted_zero_step_archive.py
  adapointr_work/PoinTr/tools/preflight_mamba_v16_d6a_calibrated_weighted_zero_step.py
  adapointr_work/PoinTr/tools/test_mamba_v16_d6a_calibrated_weighted_zero_step.py
  adapointr_work/PoinTr/tools/run_mamba_v16_d6a_gradient_calibration_fold.py
  adapointr_work/PoinTr/tools/freeze_mamba_v16_d6a_gradient_calibration.py
  adapointr_work/PoinTr/scripts/run_mamba_v16_d6a_calibrated_weighted_zero_step.sh
  adapointr_work/PoinTr/scripts/archive_mamba_v16_d6a_calibration_weighted_zero_step.sh
  adapointr_work/PoinTr/cfgs/MUG500plus_models/generated_mamba_v16_d6a_gradient_calibration_seed0_authorized_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_slot32_mechanism_protocol_lock_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_synthetic_zero_step_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/development_generation_audit_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_gradient_ratio_calibration_protocol_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_gradient_calibration_execution_authorization_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_gradient_calibration_execution_preflight_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_gradient_calibration_seed0_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_gradient_calibration_completion_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_calibrated_weighted_zero_step_v1
  datasets/MUG500plusD6Development100_v1/data_locks/mug500plus_d6_development_generation_fourfold_protocol_lock_v1
)

cd "$HOME_ROOT"
for path in "${PATHS[@]}"; do
  [[ -e "$path" ]] || {
    echo "[error] missing archive input: $HOME_ROOT/$path"
    exit 1
  }
done

cp -a --parents "${PATHS[@]}" "$STAGE"

(
  cd "$STAGE"
  find . -type f ! -name payload_manifest.sha256 -print0 |
    sort -z |
    xargs -0 sha256sum > payload_manifest.sha256
)

python "$REPO/tools/verify_mamba_v16_d6a_calibration_weighted_zero_step_archive.py" \
  --restore_root "$STAGE"

tar -czf "$ARCHIVE" -C "$STAGE" .
tar -tzf "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.tar_contents.txt"
stat -c '%s' "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.bytes"
(
  cd "$ARCHIVE_ROOT"
  sha256sum "$BASE.tar.gz" > "$BASE.tar.gz.sha256"
)

tar -xzf "$ARCHIVE" -C "$RESTORE"
python "$RESTORE/adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_calibration_weighted_zero_step_archive.py" \
  --restore_root "$RESTORE"
(
  cd "$ARCHIVE_ROOT"
  sha256sum -c "$BASE.tar.gz.sha256"
)

echo "[ok] D6-A calibration/weighted-zero-step archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[excluded] checkpoints, NPZ, STL and sealed data"
ls -lh "$ARCHIVE_ROOT"

