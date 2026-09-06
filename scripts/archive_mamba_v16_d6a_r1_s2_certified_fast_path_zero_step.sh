#!/usr/bin/env bash
set -euo pipefail

HOME_ROOT="$HOME"
REPO="$HOME_ROOT/adapointr_work/PoinTr"
LOGS="$REPO/logs/mamba_v16_d6_contact_support"
ARCHIVE_ROOT="${D6_R1_S2_ZERO_STEP_ARCHIVE_ROOT:-$HOME_ROOT/baseline_archives/mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_positive_v1}"
EXPECTED_ROOT="$HOME_ROOT/baseline_archives/mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_positive_v1"
BASE="mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_positive_v1"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"

[[ "$(realpath -m "$ARCHIVE_ROOT")" == "$(realpath -m "$EXPECTED_ROOT")" ]] || {
  echo "[error] unexpected archive root: $ARCHIVE_ROOT"
  exit 1
}
[[ ! -e "$ARCHIVE_ROOT" ]] || { echo "[error] archive root already exists: $ARCHIVE_ROOT"; exit 1; }

PARENT="$LOGS/d6a_r1_s2_certified_fast_path_feasibility_protocol_v1"
BACKUP="$LOGS/d6a_r1_s2_certified_fast_path_feasibility_protocol_crlf_backup_v1"
NORMALIZATION="$LOGS/d6a_r1_s2_parent_repo_normalization_v1"
RESTORE="$LOGS/d6a_r1_s2_parent_lock_lf_restore_v1"
AUTH="$LOGS/d6a_r1_s2_certified_fast_path_zero_step_authorization_v1"
PRELAUNCH="$LOGS/d6a_r1_s2_certified_fast_path_zero_step_prelaunch_lock_v1"
RESULT="$LOGS/d6a_r1_s2_certified_fast_path_artificial_zero_step_v1"
CONFIG="$REPO/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_authorized_v1"

echo "===== Reverify frozen S2 lineage ====="
for directory in "$PARENT" "$BACKUP" "$NORMALIZATION" "$RESTORE" "$AUTH" "$PRELAUNCH" "$RESULT" "$CONFIG"; do
  [[ -d "$directory" ]] || { echo "[error] missing: $directory"; exit 1; }
done
(cd "$PARENT" && sha256sum -c files.sha256)
(cd "$BACKUP" && sha256sum -c files.sha256)
(cd "$NORMALIZATION" && sha256sum -c files.sha256)
(cd "$RESTORE" && sha256sum -c files.sha256)
(cd "$AUTH" && sha256sum -c files.sha256)
(cd "$CONFIG" && sha256sum -c "$AUTH/runtime_config.sha256")
(cd "$PRELAUNCH" && sha256sum -c files.sha256)
sha256sum -c "$PRELAUNCH/key_artifacts.sha256"
(cd "$RESULT" && sha256sum -c files.sha256)

WORKING="${ARCHIVE_ROOT}.working"
[[ ! -e "$WORKING" ]] || { echo "[error] working path already exists: $WORKING"; exit 1; }
mkdir -p "$WORKING/payload"
cleanup() { rm -rf -- "$WORKING"; }
trap cleanup EXIT

PATHS=(
  adapointr_work/PoinTr/docs/mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_preregistered_protocol_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_r1_s2_certified_fast_path_implementation_zero_step_authorization_protocol_v1.json
  adapointr_work/PoinTr/docs/mamba_v16_d6a_r1_s2_certified_fast_path_implementation_zero_step_authorization_preregistered_protocol_zh.md
  adapointr_work/PoinTr/docs/mamba_v16_d6a_r1_s2_certified_fast_path_artificial_zero_step_complete_result_zh.md
  adapointr_work/PoinTr/scripts/prepare_mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_protocol.sh
  adapointr_work/PoinTr/scripts/authorize_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.sh
  adapointr_work/PoinTr/scripts/run_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.sh
  adapointr_work/PoinTr/scripts/archive_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.sh
  adapointr_work/PoinTr/tools/lock_mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_protocol.py
  adapointr_work/PoinTr/tools/test_mamba_v16_d6a_r1_s2_certified_fast_path_feasibility_protocol.py
  adapointr_work/PoinTr/tools/authorize_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py
  adapointr_work/PoinTr/tools/preflight_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py
  adapointr_work/PoinTr/tools/test_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step.py
  adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_authorization.py
  adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_archive.py
  adapointr_work/PoinTr/tools/preflight_mamba_v16_d6a_r1_s1_exact_assignment_zero_step.py
  adapointr_work/PoinTr/utils/mamba_d6a_slot_allocator.py
  adapointr_work/PoinTr/utils/mamba_d6a_r1_s1_exact_assignment.py
  adapointr_work/PoinTr/utils/mamba_d6a_r1_s2_certified_fast_path.py
)

add_tree() {
  local relative="$1"
  while IFS= read -r -d '' path; do
    PATHS+=("${path#"$HOME_ROOT/"}")
  done < <(find "$HOME_ROOT/$relative" -type f -print0 | sort -z)
}
add_tree adapointr_work/PoinTr/cfgs/MUG500plus_models/generated_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_authorized_v1
add_tree adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_feasibility_protocol_v1
add_tree adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_feasibility_protocol_crlf_backup_v1
add_tree adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_s2_parent_repo_normalization_v1
add_tree adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_s2_parent_lock_lf_restore_v1
add_tree adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_zero_step_authorization_v1
add_tree adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_zero_step_prelaunch_lock_v1
add_tree adapointr_work/PoinTr/logs/mamba_v16_d6_contact_support/d6a_r1_s2_certified_fast_path_artificial_zero_step_v1

cd "$HOME_ROOT"
for path in "${PATHS[@]}"; do
  [[ -f "$path" ]] || { echo "[error] missing archive input: $path"; exit 1; }
done

echo "===== Stage and verify payload ====="
tar -cf - "${PATHS[@]}" | tar -xf - -C "$WORKING/payload"
(
  cd "$WORKING/payload"
  find adapointr_work -type f -print0 | sort -z | xargs -0 sha256sum > payload_manifest.sha256
)
python "$REPO/tools/verify_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_archive.py" \
  --restore_root "$WORKING/payload"

echo "===== Create and restore-verify archive ====="
mkdir -p "$ARCHIVE_ROOT"
tar -czf "$ARCHIVE" -C "$WORKING/payload" .
tar -tzf "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.tar_contents.txt"
stat -c '%s' "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.bytes"
(cd "$ARCHIVE_ROOT" && sha256sum "$BASE.tar.gz" > "$BASE.tar.gz.sha256")

mkdir -p "$WORKING/restore"
tar -xzf "$ARCHIVE" -C "$WORKING/restore"
python "$WORKING/restore/adapointr_work/PoinTr/tools/verify_mamba_v16_d6a_r1_s2_certified_fast_path_zero_step_archive.py" \
  --restore_root "$WORKING/restore"
(cd "$ARCHIVE_ROOT" && sha256sum -c "$BASE.tar.gz.sha256")

echo "[ok] D6-A R1 S2 positive zero-step archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[excluded] checkpoints, NPZ, STL, D6 cases, tmux logs and sealed data"
echo "[locked] benchmark=false production=false training=false seed1=false D6B=false sealed=false"
ls -lh "$ARCHIVE_ROOT"
