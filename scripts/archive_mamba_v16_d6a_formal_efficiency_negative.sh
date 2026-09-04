#!/usr/bin/env bash
set -euo pipefail

HOME_ROOT="${HOME}"
REPO="$HOME_ROOT/adapointr_work/PoinTr"
ARCHIVE_ROOT="${D6_FORMAL_EFFICIENCY_ARCHIVE_ROOT:-$HOME_ROOT/baseline_archives/mamba_v16_d6a_formal_efficiency_negative_v1}"
EXPECTED_ROOT="$HOME_ROOT/baseline_archives/mamba_v16_d6a_formal_efficiency_negative_v1"
BASE="mamba_v16_d6a_formal_efficiency_negative_v1"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"

[[ "$(realpath -m "$ARCHIVE_ROOT")" == "$(realpath -m "$EXPECTED_ROOT")" ]] || {
  echo "[error] unexpected archive root: $ARCHIVE_ROOT"
  exit 1
}
[[ ! -e "$ARCHIVE_ROOT" ]] || {
  echo "[error] archive root already exists: $ARCHIVE_ROOT"
  exit 1
}

WORKING="${ARCHIVE_ROOT}.working"
[[ ! -e "$WORKING" ]] || {
  echo "[error] archive working path already exists: $WORKING"
  exit 1
}
mkdir -p "$WORKING/payload"
cleanup() {
  rm -rf -- "$WORKING"
}
trap cleanup EXIT

PATHS=(
  adapointr_work/PoinTr/docs/mamba_v16_d6a_candidate_training_efficiency_preregistered_protocol_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_candidate_training_efficiency_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_efficiency_implementation_zero_step_preregistered_protocol_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_efficiency_implementation_zero_step_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_efficiency_zero_step_import_hotfix1_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_efficiency_implementation_zero_step_complete_result_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_formal_efficiency_execution_authorization_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_formal_efficiency_execution_authorization_preregistered_protocol_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_formal_efficiency_complete_negative_result_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_gradient_calibration_weighted_zero_step_complete_result_zh.md
  adapointr_work/PoinTr/utils/mamba_d5a_proposal.py
  adapointr_work/PoinTr/utils/mamba_d6a_slot_allocator.py
  adapointr_work/PoinTr/utils/mamba_d6a_efficiency.py
  adapointr_work/PoinTr/tools/lock_mamba_v16_d6a_candidate_training_efficiency_protocol.py
  adapointr_work/PoinTr/tools/test_mamba_v16_d6a_candidate_training_efficiency_protocol.py
  adapointr_work/PoinTr/tools/preflight_mamba_v16_d6a_efficiency_implementation_zero_step.py
  adapointr_work/PoinTr/tools/test_mamba_v16_d6a_efficiency_implementation.py
  adapointr_work/PoinTr/tools/authorize_mamba_v16_d6a_formal_efficiency_execution.py
  adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_formal_efficiency_authorization.py
  adapointr_work/PoinTr/tools/preflight_mamba_v16_d6a_formal_efficiency_execution.py
  adapointr_work/PoinTr/tools/run_mamba_v16_d6a_formal_efficiency.py
  adapointr_work/PoinTr/tools/test_mamba_v16_d6a_formal_efficiency_execution_contract.py
  adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_formal_efficiency_negative_archive.py
  adapointr_work/PoinTr/scripts/prepare_mamba_v16_d6a_candidate_training_efficiency_protocol.sh
  adapointr_work/PoinTr/scripts/run_mamba_v16_d6a_efficiency_implementation_zero_step.sh
  adapointr_work/PoinTr/scripts/authorize_mamba_v16_d6a_formal_efficiency_execution.sh
  adapointr_work/PoinTr/scripts/preflight_mamba_v16_d6a_formal_efficiency_execution.sh
  adapointr_work/PoinTr/scripts/run_mamba_v16_d6a_formal_efficiency.sh
  adapointr_work/PoinTr/scripts/launch_mamba_v16_d6a_formal_efficiency_tmux.sh
  adapointr_work/PoinTr/scripts/archive_mamba_v16_d6a_formal_efficiency_negative.sh
  adapointr_work/PoinTr/cfgs/MUG500plus_models/generated_mamba_v16_d6a_formal_efficiency_authorized_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_candidate_training_efficiency_protocol_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_efficiency_implementation_zero_step_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_formal_efficiency_execution_authorization_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_formal_efficiency_execution_preflight_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_formal_efficiency_result_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_candidate_training_parent_normalization_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_candidate_protocol_lock_lf_repair_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_efficiency_zero_step_overlay_normalization_v1
  adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_formal_efficiency_parent_normalization_v1
)

cd "$HOME_ROOT"
for path in "${PATHS[@]}"; do
  [[ -e "$path" ]] || {
    echo "[error] missing archive input: $HOME_ROOT/$path"
    exit 1
  }
done

tar -cf - "${PATHS[@]}" | tar -xf - -C "$WORKING/payload"
(
  cd "$WORKING/payload"
  find adapointr_work -type f -print0 | sort -z | xargs -0 sha256sum > payload_manifest.sha256
)

python "$REPO/tools/verify_mamba_v16_d6a_formal_efficiency_negative_archive.py" \
  --restore_root "$WORKING/payload"

mkdir -p "$ARCHIVE_ROOT"
tar -czf "$ARCHIVE" -C "$WORKING/payload" .
tar -tzf "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.tar_contents.txt"
stat -c '%s' "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.bytes"
(
  cd "$ARCHIVE_ROOT"
  sha256sum "$BASE.tar.gz" > "$BASE.tar.gz.sha256"
)

mkdir -p "$WORKING/restore"
tar -xzf "$ARCHIVE" -C "$WORKING/restore"
python "$WORKING/restore/adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_formal_efficiency_negative_archive.py" \
  --restore_root "$WORKING/restore"
(
  cd "$ARCHIVE_ROOT"
  sha256sum -c "$BASE.tar.gz.sha256"
)

echo "[ok] D6-A formal-efficiency frozen-negative archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[excluded] checkpoints, NPZ, STL and sealed data"
echo "[locked] rerun=false training=false seed1=false D6B=false sealed=false"
ls -lh "$ARCHIVE_ROOT"
