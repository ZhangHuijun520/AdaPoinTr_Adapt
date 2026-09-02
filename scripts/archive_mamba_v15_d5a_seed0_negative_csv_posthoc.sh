#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${MAMBA_V15_D5A_ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v15_d5a_seed0_negative_csv_posthoc_v1}"
BASE="mamba_v15_d5a_v0_v1_seed0_negative_csv_posthoc_v1"
PAYLOAD="$ARCHIVE_ROOT/.payload"
RESTORE="$ARCHIVE_ROOT/.verification_restore"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"
LOGS="$ROOT/logs/mamba_v15_d5_contact_support"

[[ -d "$ROOT" ]]
ARCHIVE_ROOT_REAL="$(realpath -m "$ARCHIVE_ROOT")"
ARCHIVE_PARENT_REAL="$(realpath -m "$HOME/baseline_archives")"
[[ "$ARCHIVE_ROOT_REAL" == "$ARCHIVE_PARENT_REAL"/* ]]
[[ "$PAYLOAD" == "$ARCHIVE_ROOT/.payload" ]]
[[ "$RESTORE" == "$ARCHIVE_ROOT/.verification_restore" ]]
[[ ! -e "$ARCHIVE_ROOT" ]] || {
  echo "[error] archive root already exists: $ARCHIVE_ROOT"
  exit 1
}

REQUIRED_LOG_DIRS=(
  candidate_training_protocol_v1
  development_generation_audit_v1
  d5a_zero_step_preflight_v1
  d5a_overlay_transport_normalization_v1
  d5a_d4_parent_lineage_hotfix1_v1
  d5a_zero_step_report_lf_normalization_hotfix2_v1
  d5a_seed0_training_authorization_v1
  d5a_seed0_head_only_v1
  d5a_seed0_training_completion_v1
  d5a_seed0_csv_posthoc_v1
  d5a_seed0_training_tmux
)
for relative in "${REQUIRED_LOG_DIRS[@]}"; do
  [[ -d "$LOGS/$relative" ]] || {
    echo "[error] missing required log directory: $LOGS/$relative"
    exit 1
  }
done

for root in \
  "$LOGS/candidate_training_protocol_v1" \
  "$LOGS/development_generation_audit_v1" \
  "$LOGS/d5a_zero_step_preflight_v1" \
  "$LOGS/d5a_seed0_training_authorization_v1" \
  "$LOGS/d5a_seed0_training_completion_v1" \
  "$LOGS/d5a_seed0_csv_posthoc_v1"
do
  (
    cd "$root"
    sha256sum -c files.sha256
  )
done

for candidate in V0 V1; do
  for fold in A B C D; do
    fold_root="$LOGS/d5a_seed0_head_only_v1/${candidate}_fold${fold}_seed0"
    (
      cd "$fold_root"
      sha256sum -c files.sha256
    )
  done
done

mkdir -p "$PAYLOAD/environment_v1"
cd "$HOME"

for relative in "${REQUIRED_LOG_DIRS[@]}"; do
  source_path="adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/$relative"
  cp -a --parents "$source_path" "$PAYLOAD"
done

cp -a --parents \
  adapointr_work/PoinTr/cfgs/MUG500plus_models/generated_mamba_v15_d5a_seed0_authorized_v1 \
  datasets/MUG500plusD5Development100_v1/data_locks \
  "$PAYLOAD"

while IFS= read -r path; do
  relative="${path#$HOME/}"
  cp -a --parents "$relative" "$PAYLOAD"
done < <(
  find \
    "$ROOT/docs" "$ROOT/tools" "$ROOT/scripts" \
    -maxdepth 1 -type f \
    \( -name '*mamba_v15_d5*' -o -name '*mamba_v14_d4a*' \) \
    -print | sort
)

cp -a --parents \
  adapointr_work/PoinTr/utils/mamba_d4a_proposal.py \
  adapointr_work/PoinTr/utils/mamba_d5a_proposal.py \
  "$PAYLOAD"

find datasets/MUG500plusD5Development400_v1 -maxdepth 1 -type f -print0 |
  sort -z |
  xargs -0 -r cp -a --parents -t "$PAYLOAD"

ENV_DIR="$PAYLOAD/environment_v1"
conda list --explicit > "$ENV_DIR/conda_explicit.txt"
python -m pip freeze --all > "$ENV_DIR/python_packages.txt"
nvidia-smi -q > "$ENV_DIR/nvidia_smi_q.txt"
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$ROOT" rev-parse HEAD > "$ENV_DIR/git_head.txt"
  git -C "$ROOT" status --short > "$ENV_DIR/git_status_short.txt"
  git -C "$ROOT" diff --binary > "$ENV_DIR/git_diff.patch"
  printf '{"git_repository": true}\n' > "$ENV_DIR/git_repository.json"
else
  printf 'unavailable: deployed server tree is not a Git worktree\n' \
    > "$ENV_DIR/git_head.txt"
  : > "$ENV_DIR/git_status_short.txt"
  : > "$ENV_DIR/git_diff.patch"
  printf '{"git_repository": false, "reason": "deployed_server_tree_without_git_metadata"}\n' \
    > "$ENV_DIR/git_repository.json"
fi

python - <<'PY' > "$ENV_DIR/runtime.json"
import json
import platform
import sys

import numpy
import torch

print(json.dumps({
    "python": sys.version,
    "platform": platform.platform(),
    "numpy": numpy.__version__,
    "torch": torch.__version__,
    "cuda": torch.version.cuda,
    "cudnn": torch.backends.cudnn.version(),
    "cuda_available": torch.cuda.is_available(),
    "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}, indent=2, sort_keys=True))
PY

(
  cd "$PAYLOAD"
  find . -type f ! -name payload_manifest.sha256 -print0 |
    sort -z |
    xargs -0 sha256sum > payload_manifest.sha256
)

tar -czf "$ARCHIVE" -C "$PAYLOAD" .
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
stat -c '%s' "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.bytes"
tar -tzf "$ARCHIVE" > "$ARCHIVE_ROOT/$BASE.tar_contents.txt"

mkdir -p "$RESTORE"
tar -xzf "$ARCHIVE" -C "$RESTORE"
(
  cd "$RESTORE"
  sha256sum -c payload_manifest.sha256
)

python "$ROOT/tools/verify_mamba_v15_d5a_seed0_negative_archive.py" \
  --restore_root "$RESTORE"

rm -rf -- "$PAYLOAD" "$RESTORE"

sha256sum -c "$ARCHIVE.sha256"
echo "[ok] D5-A seed-0 negative/CSV-post-hoc archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[kept] eight final heads, receipts, reports, code and environment"
echo "[excluded] 400 derived NPZ cases, source STL and sealed data"
ls -lh "$ARCHIVE_ROOT"
