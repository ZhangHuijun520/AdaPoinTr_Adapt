#!/usr/bin/env bash
set -euo pipefail

export PS1="${PS1-}"
source "$HOME/conda/etc/profile.d/conda.sh"
conda activate "${CONDA_ENV:-adapointr-mamba}"

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
LOGS="$ROOT/logs/mamba_v15_d5_contact_support"
LOCKS="$HOME/datasets/MUG500plusD5Development100_v1/data_locks"
ARCHIVE_ROOT="${MAMBA_V15_D5A_ZERO_STEP_ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v15_d5a_zero_step_v1}"
BASE="mamba_v15_d5a_v0_v1_zero_step_seed0_v1"
PAYLOAD="$ARCHIVE_ROOT/.payload"
RESTORE="$ARCHIVE_ROOT/.verification_restore"
ARCHIVE="$ARCHIVE_ROOT/$BASE.tar.gz"

EXPECTED_PARENT="$(realpath -m "$HOME/baseline_archives")"
ARCHIVE_ROOT_REAL="$(realpath -m "$ARCHIVE_ROOT")"
[[ "$ARCHIVE_ROOT_REAL" == "$EXPECTED_PARENT"/* ]]
[[ "$PAYLOAD" == "$ARCHIVE_ROOT/.payload" ]]
[[ "$RESTORE" == "$ARCHIVE_ROOT/.verification_restore" ]]
[[ ! -e "$ARCHIVE_ROOT" ]] || {
  echo "[error] archive root already exists: $ARCHIVE_ROOT"
  exit 1
}

for path in \
  "$LOGS/candidate_training_protocol_v1" \
  "$LOGS/d5a_zero_step_preflight_v1" \
  "$LOGS/d5a_zero_step_result_freeze_v1" \
  "$LOGS/d5a_overlay_transport_normalization_v1" \
  "$LOGS/d5a_d4_parent_lineage_hotfix1_v1" \
  "$LOGS/development_generation_audit_v1" \
  "$LOCKS/mug500plus_d5_development100_qc_lock_v1" \
  "$LOCKS/mug500plus_d5_development400_fourfold_protocol_lock_v1"
do
  [[ -e "$path" ]] || { echo "[error] missing required path: $path"; exit 1; }
done

echo "===== Verify frozen zero-step inputs and result ====="
for root in \
  "$LOGS/candidate_training_protocol_v1" \
  "$LOGS/d5a_zero_step_preflight_v1" \
  "$LOGS/d5a_zero_step_result_freeze_v1" \
  "$LOGS/development_generation_audit_v1" \
  "$LOCKS/mug500plus_d5_development100_qc_lock_v1" \
  "$LOCKS/mug500plus_d5_development400_fourfold_protocol_lock_v1"
do
  (cd "$root" && sha256sum -c files.sha256)
done
sha256sum -c "$LOGS/d5a_overlay_transport_normalization_v1/overlay_transport_normalization_receipt.json.sha256"
sha256sum -c "$LOGS/d5a_d4_parent_lineage_hotfix1_v1/d4_parent_lineage_hotfix_receipt.json.sha256"
python "$ROOT/tools/test_mamba_v15_d5a_zero_step_result_freeze.py"

mkdir -p "$PAYLOAD/environment_v1"
cd "$HOME"

cp -a --parents \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/candidate_training_protocol_v1 \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/d5a_zero_step_preflight_v1 \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/d5a_zero_step_result_freeze_v1 \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/d5a_overlay_transport_normalization_v1 \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/d5a_d4_parent_lineage_hotfix1_v1 \
  adapointr_work/PoinTr/logs/mamba_v15_d5_contact_support/development_generation_audit_v1 \
  datasets/MUG500plusD5Development100_v1/data_locks/mug500plus_d5_development100_qc_lock_v1 \
  datasets/MUG500plusD5Development100_v1/data_locks/mug500plus_d5_development400_fourfold_protocol_lock_v1 \
  "$PAYLOAD"

for relative in \
  docs/mamba_v14_d4a_complete_experiment_report_and_next_plan_zh.md \
  docs/mamba_v15_d5_development400_generation_audit_complete_result_zh.md \
  docs/mamba_v15_d5_candidate_training_protocol_v1.json \
  docs/mamba_v15_d5_candidate_training_preregistered_protocol_zh.md \
  docs/mamba_v15_d5a_zero_step_preflight_protocol_v1.json \
  docs/mamba_v15_d5a_zero_step_result_freeze_protocol_v1.json \
  utils/mamba_d4a_proposal.py \
  utils/mamba_d5a_proposal.py \
  tools/lock_mamba_v15_d5_candidate_training_protocol.py \
  tools/test_mamba_v15_d5_candidate_training_protocol.py \
  tools/preflight_mamba_v15_d5a_zero_step.py \
  tools/test_mamba_v15_d5a_implementation.py \
  tools/freeze_mamba_v15_d5a_zero_step_result.py \
  tools/test_mamba_v15_d5a_zero_step_result_freeze.py \
  tools/verify_mamba_v15_d5a_zero_step_archive.py \
  scripts/prepare_mamba_v15_d5_candidate_training_protocol.sh \
  scripts/run_mamba_v15_d5a_zero_step_preflight.sh \
  scripts/freeze_mamba_v15_d5a_zero_step_result.sh \
  scripts/archive_mamba_v15_d5a_zero_step.sh
do
  [[ -f "$ROOT/$relative" ]] || { echo "[error] missing code: $relative"; exit 1; }
  cp -a --parents "adapointr_work/PoinTr/$relative" "$PAYLOAD"
done

cat > "$PAYLOAD/archive_metadata.json" <<'JSON'
{
  "archive_id": "mamba-v15-d5a-v0-v1-zero-step-seed0-v1",
  "source_commit": "1480a9bc0957528182c11bfddd722b53517b5388",
  "source_tag": "mamba-adapter-v15-d5a-zero-step-preflight-v1",
  "candidates": ["V0", "V1"],
  "folds": 4,
  "training_probe_cases": 4,
  "backward_passes": 8,
  "optimizer_steps": 0,
  "model_updates": 0,
  "checkpoints_archived": 0,
  "npz_archived": 0,
  "stl_archived": 0,
  "sealed_geometry_archived": false,
  "training_started": false,
  "next_step": "restore_verify_locally_then_freeze_git_result_milestone"
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

if find "$PAYLOAD" -type f \( \
  -name '*.pth' -o -name '*.pt' -o -name '*.ckpt' -o \
  -name '*.npz' -o -name '*.stl' \
\) -print -quit | grep -q .; then
  echo "[error] forbidden checkpoint or geometry entered the payload"
  exit 1
fi

(
  cd "$PAYLOAD"
  find . -type f ! -name payload_manifest.sha256 -print0 |
    sort -z |
    xargs -0 sha256sum > payload_manifest.sha256
)

echo "===== Create and restore-verify zero-step archive ====="
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
python "$ROOT/tools/verify_mamba_v15_d5a_zero_step_archive.py" \
  --restore_root "$RESTORE"

[[ "$PAYLOAD" == "$ARCHIVE_ROOT/.payload" ]]
[[ "$RESTORE" == "$ARCHIVE_ROOT/.verification_restore" ]]
rm -rf -- "$PAYLOAD" "$RESTORE"

sha256sum -c "$ARCHIVE.sha256"
echo "[ok] D5-A V0/V1 zero-step archive created and restore-verified"
echo "[archive-root] $ARCHIVE_ROOT"
echo "[excluded] checkpoints, NPZ, STL and sealed geometry"
echo "[locked] training=false seed1=false D5B=false selection=false sealed=false"
ls -lh "$ARCHIVE_ROOT"
