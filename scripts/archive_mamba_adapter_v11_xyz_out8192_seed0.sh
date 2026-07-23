#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives}"
CONDA_ENV="${CONDA_ENV:-adapointr-mamba}"
OVERWRITE="${OVERWRITE:-0}"
MIN_FREE_GB="${MIN_FREE_GB:-2}"

cd "$REPO_ROOT"
mkdir -p "$ARCHIVE_ROOT"

free_kb="$(df -Pk "$ARCHIVE_ROOT" | awk 'NR==2 {print $4}')"
required_kb="$((MIN_FREE_GB * 1024 * 1024))"
if (( free_kb < required_kb )); then
  echo "[error] less than ${MIN_FREE_GB} GiB free below $ARCHIVE_ROOT" >&2
  df -h "$ARCHIVE_ROOT"
  exit 1
fi

archive_run() {
  local dataset="$1"
  local archive_name="$2"
  local run_name="$3"
  local exp_dir="$4"
  local config="$5"
  local dataset_config="$6"
  local train_log_dir="$7"
  local eval_dir="$8"
  local prediction_dir="$9"
  local vis_dir="${10}"
  local run_script="${11}"
  local protocol="${12}"
  local additional_eval_dir="${13:-}"

  local ckpt="$exp_dir/ckpt-last-bncal.pth"
  local archive_path="$ARCHIVE_ROOT/$archive_name.tar"
  local checksum_path="$archive_path.sha256"
  local tmp_root
  local metadata_dir
  local file_list

  tmp_root="$(mktemp -d)"
  metadata_dir="$tmp_root/metadata"
  file_list="$tmp_root/archive_paths.txt"
  mkdir -p "$metadata_dir"

  cleanup_archive_run() {
    rm -rf "$tmp_root"
  }
  trap cleanup_archive_run RETURN

  if [[ -e "$archive_path" || -e "$checksum_path" ]]; then
    if [[ "$OVERWRITE" != "1" ]]; then
      echo "[error] archive already exists: $archive_path" >&2
      echo "        Set OVERWRITE=1 only after verifying replacement is intended." >&2
      exit 1
    fi
    rm -f "$archive_path" "$checksum_path"
  fi

  local required_paths=(
    "$ckpt"
    "$ckpt.json"
    "$config"
    "$dataset_config"
    "$train_log_dir"
    "$eval_dir"
    "$prediction_dir"
    "$vis_dir"
    "$run_script"
    "models/AdaPoinTr.py"
    "tools/runner.py"
    "tools/evaluate_skullfix_implant.py"
    "tools/recalibrate_skullfix_batchnorm.py"
  )
  if [[ -n "$additional_eval_dir" ]]; then
    required_paths+=("$additional_eval_dir")
  fi

  local path
  for path in "${required_paths[@]}"; do
    if [[ ! -e "$path" ]]; then
      echo "[error] $dataset required artifact is missing: $path" >&2
      exit 1
    fi
  done

  cat > "$metadata_dir/README.txt" <<EOF
Mamba Adapter v1.1 xyz 8192-output seed-0 diagnostic baseline

Created: $(date --iso-8601=seconds)
Dataset: $dataset
Run: $run_name
Protocol: $protocol
Mamba adapter: depth=2, order=xyz, alpha_init=0.01, alpha warmup=20 epochs

Included:
- experiment config and canonical BN-calibrated checkpoint
- training logs, point/rim evaluation outputs, prediction NPZ files
- visualizations and the source files required by the v1.1 implementation
- environment, Git state, archive path list, and per-file SHA256 manifest

Not included:
- raw or converted datasets
- Windows-only voxel evaluation outputs
- non-canonical intermediate and optimizer checkpoints
EOF

  {
    echo "created=$(date --iso-8601=seconds)"
    echo "hostname=$(hostname)"
    echo "user=$(id -un)"
    echo "repo_root=$REPO_ROOT"
    echo "dataset=$dataset"
    echo "run_name=$run_name"
    echo "checkpoint=$ckpt"
    echo "checkpoint_sha256=$(sha256sum "$ckpt" | awk '{print $1}')"
    echo "conda_environment=$CONDA_ENV"
    df -h "$HOME" 2>&1 || true
    nvidia-smi 2>&1 || true
  } > "$metadata_dir/system_info.txt"

  if command -v conda >/dev/null 2>&1; then
    conda list -n "$CONDA_ENV" > "$metadata_dir/conda-list.txt" 2>&1 || true
    conda run -n "$CONDA_ENV" python -m pip freeze \
      > "$metadata_dir/pip-freeze.txt" 2>&1 || true
    conda run -n "$CONDA_ENV" python - <<'PY' \
      > "$metadata_dir/python-runtime.txt" 2>&1 || true
import sys

print(f"python={sys.version}")
try:
    import numpy
    import torch

    print(f"numpy={numpy.__version__}")
    print(f"torch={torch.__version__}")
    print(f"torch_cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()}")
except Exception as exc:
    print(f"runtime_probe_failed={exc!r}")
PY
  fi

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git rev-parse HEAD > "$metadata_dir/git_head.txt"
    git status --short > "$metadata_dir/git_status.txt"
    git diff --binary HEAD > "$metadata_dir/git_worktree.patch"
    git ls-files --others --exclude-standard \
      > "$metadata_dir/git_untracked_files.txt"
  fi

  {
    echo "---- point/rim summaries ----"
    find "$eval_dir" -type f -name '*summary.json' -print -exec cat {} \;
    if [[ -n "$additional_eval_dir" ]]; then
      find "$additional_eval_dir" -type f -name '*summary.json' \
        -print -exec cat {} \;
    fi
    echo
    echo "---- checkpoint metadata ----"
    cat "$ckpt.json"
  } > "$metadata_dir/results_summary.txt"

  cat > "$file_list" <<EOF
$ckpt
$ckpt.json
$config
$dataset_config
$train_log_dir
$eval_dir
$prediction_dir
$vis_dir
$run_script
models/AdaPoinTr.py
tools/runner.py
tools/evaluate_skullfix_implant.py
tools/recalibrate_skullfix_batchnorm.py
utils/misc.py
requirements_mamba.txt
scripts/archive_mamba_adapter_v11_xyz_out8192_seed0.sh
EOF

  if [[ -n "$additional_eval_dir" ]]; then
    echo "$additional_eval_dir" >> "$file_list"
  fi

  if [[ -f "$exp_dir/config.yaml" ]]; then
    echo "$exp_dir/config.yaml" >> "$file_list"
  fi
  if [[ -f "docs/mamba_adapter_implant_out8192_v11_v12c_diagnostic_report_zh.md" ]]; then
    echo "docs/mamba_adapter_implant_out8192_v11_v12c_diagnostic_report_zh.md" \
      >> "$file_list"
  fi

  awk '!seen[$0]++' "$file_list" > "$file_list.tmp"
  mv "$file_list.tmp" "$file_list"

  while IFS= read -r path; do
    if [[ -d "$path" ]]; then
      find "$path" -type f -print0
    elif [[ -f "$path" ]]; then
      printf '%s\0' "$path"
    fi
  done < "$file_list" \
    | sort -zu \
    | xargs -0 sha256sum > "$metadata_dir/MANIFEST.sha256"

  cp "$file_list" "$metadata_dir/ARCHIVE_PATHS.txt"

  echo "[archive:$dataset] selected artifacts:"
  du -sh "$ckpt" "$train_log_dir" "$eval_dir" "$prediction_dir" "$vis_dir"
  if [[ -n "$additional_eval_dir" ]]; then
    du -sh "$additional_eval_dir"
  fi
  echo "[archive:$dataset] destination filesystem:"
  df -h "$ARCHIVE_ROOT"

  tar -cf "$archive_path" \
    -C "$tmp_root" metadata \
    -C "$REPO_ROOT" \
    --files-from "$file_list"

  (
    cd "$ARCHIVE_ROOT"
    sha256sum "$(basename "$archive_path")" \
      > "$(basename "$checksum_path")"
  )

  echo "[ok:$dataset] archive: $archive_path"
  echo "[ok:$dataset] checksum: $checksum_path"
  ls -lh "$archive_path" "$checksum_path"

  trap - RETURN
  cleanup_archive_run
}

archive_run \
  "SkullFix" \
  "skullfix_mamba_adapter_v11_xyz_out8192_seed0_v1" \
  "skullfix_mamba_adapter_v11_full100_out8192_bncal" \
  "experiments/MambaAdapterV11_implant_full100_out8192_bncal/SkullFix_models/skullfix_mamba_adapter_v11_full100_out8192_bncal" \
  "cfgs/SkullFix_models/MambaAdapterV11_implant_full100_out8192_bncal.yaml" \
  "cfgs/dataset_configs/SkullFix.yaml" \
  "logs/skullfix_mamba_adapter_v11_out8192" \
  "logs/skullfix_mamba_adapter_v11_out8192_eval/full100_out8192_bncal_test" \
  "logs/skullfix_mamba_adapter_v11_out8192_eval/full100_out8192_predictions_test" \
  "experiments/visualizations/skullfix_mamba_adapter_v11_full100_out8192_bncal_test" \
  "scripts/run_skullfix_mamba_adapter_v11_full100_out8192_bncal.sh" \
  "SkullFix seed-0 split; input=8192 defective-skull points; output=8192 implant points" \
  ""

archive_run \
  "SkullBreak" \
  "skullbreak_mamba_adapter_v11_xyz_out8192_seed0_v1" \
  "skullbreak_mamba_adapter_v11_full100_out8192_bncal" \
  "experiments/MambaAdapterV11_implant_full100_out8192_bncal/SkullBreak_models/skullbreak_mamba_adapter_v11_full100_out8192_bncal" \
  "cfgs/SkullBreak_models/MambaAdapterV11_implant_full100_out8192_bncal.yaml" \
  "cfgs/dataset_configs/SkullBreak.yaml" \
  "logs/skullbreak_mamba_adapter_v11_out8192" \
  "logs/skullbreak_mamba_adapter_v11_out8192_eval/full100_out8192_bncal_official_test" \
  "logs/skullbreak_mamba_adapter_v11_out8192_eval/full100_out8192_predictions_test" \
  "experiments/visualizations/skullbreak_mamba_adapter_v11_full100_out8192_bncal_test" \
  "scripts/run_skullbreak_mamba_adapter_v11_full100_out8192_bncal.sh" \
  "SkullBreak official train=570 cases/114 skulls; monitor=50/10; test=100/20; input/output=8192" \
  "logs/skullbreak_mamba_adapter_v11_out8192_eval/full100_out8192_bncal_monitor"

echo
echo "[done] Mamba Adapter v1.1 xyz archives are ready:"
ls -lh \
  "$ARCHIVE_ROOT/skullfix_mamba_adapter_v11_xyz_out8192_seed0_v1.tar"* \
  "$ARCHIVE_ROOT/skullbreak_mamba_adapter_v11_xyz_out8192_seed0_v1.tar"*
echo
echo "Download all four files and verify each SHA256 locally before cleanup."
