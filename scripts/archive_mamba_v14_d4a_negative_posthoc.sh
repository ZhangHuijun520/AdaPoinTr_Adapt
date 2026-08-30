#!/usr/bin/env bash

set -euo pipefail

set +u
source /opt/conda/etc/profile.d/conda.sh
conda activate "${CONDA_ENV:-adapointr-mamba}"
set -u

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${MAMBA_V14_D4A_ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v14_d4a_negative_posthoc_seed0}"
BASE="mamba_v14_d4a_head_only_negative_posthoc_seed0_v1"
PAYLOAD="$ARCHIVE_ROOT/.payload"
RESTORE="$ARCHIVE_ROOT/.verification_restore"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"

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

mkdir -p "$PAYLOAD/environment_v1"

cd "$HOME"

cp -a --parents \
  adapointr_work/PoinTr/logs/mamba_v14_d4_contact_support \
  datasets/MUG500plusD4Source100_v1/data_locks \
  "$PAYLOAD"

while IFS= read -r path; do
  relative="${path#$HOME/}"
  cp -a --parents "$relative" "$PAYLOAD"
done < <(
  find \
    "$ROOT/docs" "$ROOT/tools" "$ROOT/scripts" \
    -maxdepth 1 -type f \
    \( -name '*mamba_v14_d4*' -o -name '*mamba_v14_pd3*' \) \
    -print | sort
)

cp -a --parents \
  adapointr_work/PoinTr/utils/mamba_d4a_proposal.py \
  "$PAYLOAD"

find datasets/MUG500plusD4M2_v1 -maxdepth 1 -type f -print0 |
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

python "$ROOT/tools/verify_mamba_v14_d4a_negative_archive.py" \
  --restore_root "$RESTORE"

rm -rf -- "$PAYLOAD" "$RESTORE"

sha256sum -c "$ARCHIVE.sha256"
echo "[ok] D4-A negative/post-hoc archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[kept] four final head checkpoints, receipts, reports, code and environment"
echo "[excluded] 400 derived NPZ cases and protected data"
ls -lh "$ARCHIVE_ROOT"
