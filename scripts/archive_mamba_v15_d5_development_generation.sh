#!/usr/bin/env bash
set -euo pipefail

export PS1="${PS1-}"
source "$HOME/conda/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV:-adapointr-mamba}"

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${MAMBA_V15_D5_ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v15_d5_development_generation_v1}"
BASE="mamba_v15_d5_development400_generation_audit_v1"
PAYLOAD="$ARCHIVE_ROOT/.payload"
RESTORE="$ARCHIVE_ROOT/.verification_restore"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"
DATASET="$HOME/datasets/MUG500plusD5Development400_v1"
SOURCE_LOCKS="$HOME/datasets/MUG500plusD5Development100_v1/data_locks"
LOGS="$ROOT/logs/mamba_v15_d5_contact_support"

EXPECTED_ARCHIVE_PARENT="$(realpath -m "$HOME/baseline_archives")"
ARCHIVE_ROOT_REAL="$(realpath -m "$ARCHIVE_ROOT")"
[[ "$ARCHIVE_ROOT_REAL" == "$EXPECTED_ARCHIVE_PARENT"/* ]]
[[ "$PAYLOAD" == "$ARCHIVE_ROOT/.payload" ]]
[[ "$RESTORE" == "$ARCHIVE_ROOT/.verification_restore" ]]
[[ ! -e "$ARCHIVE_ROOT" ]] || {
  echo "[error] archive root already exists: $ARCHIVE_ROOT"
  exit 1
}

for path in \
  "$ROOT/tools" \
  "$DATASET" \
  "$SOURCE_LOCKS/mug500plus_d5_source150_acquisition_lock_v1" \
  "$SOURCE_LOCKS/mug500plus_d5_development100_qc_lock_v1" \
  "$SOURCE_LOCKS/mug500plus_d5_development400_fourfold_protocol_lock_v1" \
  "$LOGS/development_generation_audit_v1" \
  "$LOGS/d5_overlay_transport_normalization_v1"
do
  [[ -e "$path" ]] || { echo "[error] missing required path: $path"; exit 1; }
done

echo "===== Verify retained generation and audit ====="
(
  cd "$DATASET"
  sha256sum -c files.sha256
)
(
  cd "$LOGS/development_generation_audit_v1"
  sha256sum -c files.sha256
)
(
  cd "$LOGS/d5_overlay_transport_normalization_v1"
  sha256sum -c files.sha256
)
python "$ROOT/tools/test_mamba_v15_d5_development_generation_archive.py"

mkdir -p "$PAYLOAD/environment_v1"
cd "$HOME"

cp -a --parents \
  datasets/MUG500plusD5Development400_v1 \
  datasets/MUG500plusD5Development100_v1/data_locks \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/development_generation_audit_v1 \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/d5_overlay_transport_normalization_v1 \
  "$PAYLOAD"

for optional in \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/development_generation_tmux \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/development_generation_audit_tmux
do
  if [[ -d "$optional" ]]; then
    cp -a --parents "$optional" "$PAYLOAD"
  fi
done

while IFS= read -r path; do
  relative="${path#$HOME/}"
  cp -a --parents "$relative" "$PAYLOAD"
done < <(
  find "$ROOT/docs" "$ROOT/tools" "$ROOT/scripts" \
    -maxdepth 1 -type f -name '*mamba_v15_d5*' -print | sort
)

cp -a --parents \
  adapointr_work/PoinTr/docs/mamba_v13_d3_mug500plus_phase_m2_synthetic_defect_protocol_v1.json \
  adapointr_work/PoinTr/tools/generate_mug500plus_m2_synthetic_defects.py \
  "$PAYLOAD"

cat > "$PAYLOAD/archive_metadata.json" <<'JSON'
{
  "archive_id": "mamba-v15-d5-development400-generation-audit-v1",
  "source_archive_bytes": 9288781774,
  "source_archive_sha256": "9d3544766188369783d8adfa99a6592dc32ccea7715d9b43a97ab1f493091a21",
  "source_stl_count": 100,
  "source_stl_bytes": 16820263850,
  "source_stl_archived": false,
  "derived_cases_archived": 400,
  "sealed_geometry_archived": false,
  "model_or_training_artifacts_archived": false,
  "next_step": "restore_verify_locally_then_freeze_git_milestone"
}
JSON

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

echo "===== Create and restore-verify archive ====="
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
python "$ROOT/tools/verify_mamba_v15_d5_development_generation_archive.py" \
  --restore_root "$RESTORE"

[[ "$PAYLOAD" == "$ARCHIVE_ROOT/.payload" ]]
[[ "$RESTORE" == "$ARCHIVE_ROOT/.verification_restore" ]]
rm -rf -- "$PAYLOAD" "$RESTORE"

sha256sum -c "$ARCHIVE.sha256"
echo "[ok] D5 development400 generation milestone archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[kept] 400 derived cases, locks, audit, logs, code and environment"
echo "[excluded] source STL, sealed geometry, models and checkpoints"
ls -lh "$ARCHIVE_ROOT"
