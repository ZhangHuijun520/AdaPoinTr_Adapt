#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives}"
ARCHIVE_NAME="${ARCHIVE_NAME:-skullbreak_mamba_v11_o0_multiseed_r1_p1_seed012_v1}"
CONDA_ENV="${CONDA_ENV:-adapointr-mamba}"
OVERWRITE="${OVERWRITE:-0}"
MIN_FREE_GB="${MIN_FREE_GB:-4}"
CREATE_PARTS="${CREATE_PARTS:-1}"
PART_SIZE_MB="${PART_SIZE_MB:-128}"

CONFIG="cfgs/SkullBreak_models/MambaAdapterV11OrderingO0_xyz_out8192_monitor.yaml"
DATASET_CONFIG="cfgs/dataset_configs/SkullBreak.yaml"
DATASET_MANIFEST="data/SkullBreakPC_out8192/manifest.jsonl"
R1_ROOT="logs/skullbreak_mamba_v11_o0_multiseed"
P1_ROOT="$R1_ROOT/posthoc_full_monitor"
P1_SUMMARY="$P1_ROOT/analysis/posthoc_summary.json"
P1_TREE="$P1_ROOT/posthoc_tree_sha256.txt"
P1_TREE_SHA="$P1_TREE.sha256"
SEED0_MONITOR="logs/skullbreak_mamba_ordering_v11_out8192_eval/O0_xyz_monitor"

SEED0_RUN="experiments/MambaAdapterV11OrderingO0_xyz_out8192_monitor/SkullBreak_models/skullbreak_mamba_v11_ordering_o0_xyz_seed0"
SEED1_RUN="experiments/MambaAdapterV11OrderingO0_xyz_out8192_monitor/SkullBreak_models/skullbreak_mamba_v11_o0_xyz_seed1_replication"
SEED2_RUN="experiments/MambaAdapterV11OrderingO0_xyz_out8192_monitor/SkullBreak_models/skullbreak_mamba_v11_o0_xyz_seed2_replication"

SEED0_CKPT="$SEED0_RUN/ckpt-last-bncal.pth"
SEED1_CKPT="$SEED1_RUN/ckpt-last-bncal.pth"
SEED2_CKPT="$SEED2_RUN/ckpt-last-bncal.pth"

SEED0_METRICS="$SEED0_MONITOR/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"
SEED1_METRICS="$R1_ROOT/monitor/seed1/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"
SEED2_METRICS="$R1_ROOT/monitor/seed2/MambaAdapterV11OrderingO0_xyz_out8192_monitor_val_per_sample.csv"

ARCHIVE_PATH="$ARCHIVE_ROOT/$ARCHIVE_NAME.tar"
CHECKSUM_PATH="$ARCHIVE_PATH.sha256"
PART_PREFIX="$ARCHIVE_ROOT/$ARCHIVE_NAME.part-"
PARTS_CHECKSUM_PATH="$ARCHIVE_ROOT/$ARCHIVE_NAME.parts.sha256"

cd "$REPO_ROOT"
mkdir -p "$ARCHIVE_ROOT"

shopt -s nullglob
existing_parts=("$PART_PREFIX"*)
shopt -u nullglob

if [[ -e "$ARCHIVE_PATH" || -e "$CHECKSUM_PATH" || \
      -e "$PARTS_CHECKSUM_PATH" || ${#existing_parts[@]} -gt 0 ]]; then
  if [[ "$OVERWRITE" != "1" ]]; then
    echo "[error] archive already exists: $ARCHIVE_PATH" >&2
    echo "        Set OVERWRITE=1 only after confirming replacement is intended." >&2
    exit 1
  fi
  rm -f -- "$ARCHIVE_PATH" "$CHECKSUM_PATH" "$PARTS_CHECKSUM_PATH" \
    "${existing_parts[@]}"
fi

required_paths=(
  "$CONFIG"
  "$DATASET_CONFIG"
  "$DATASET_MANIFEST"
  "$R1_ROOT"
  "$P1_SUMMARY"
  "$P1_TREE"
  "$P1_TREE_SHA"
  "$SEED0_MONITOR"
  "$SEED0_CKPT"
  "$SEED0_CKPT.json"
  "$SEED1_CKPT"
  "$SEED1_CKPT.json"
  "$SEED2_CKPT"
  "$SEED2_CKPT.json"
)

missing_paths=()
for path in "${required_paths[@]}"; do
  if [[ ! -e "$path" ]]; then
    missing_paths+=("$path")
  fi
done
if (( ${#missing_paths[@]} > 0 )); then
  echo "[error] required frozen artifacts are missing:" >&2
  printf '  - %s\n' "${missing_paths[@]}" >&2
  exit 1
fi

echo "[verify] checking frozen P1 hash chain"
sha256sum -c "$P1_TREE_SHA"
sha256sum -c "$P1_TREE" >/dev/null
echo "[ok] all files in the frozen P1 tree match"

echo "[verify] checking frozen monitor and post-hoc semantics"
python - "$SEED0_METRICS" "$SEED1_METRICS" "$SEED2_METRICS" "$P1_SUMMARY" <<'PY'
import csv
import json
import math
import sys
from pathlib import Path

metric_paths = [Path(value) for value in sys.argv[1:4]]
summary_path = Path(sys.argv[4])
case_sets = []

for path in metric_paths:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    case_ids = [row["case_id"] for row in rows]
    if len(rows) != 50 or len(set(case_ids)) != 50:
        raise SystemExit(
            f"[error] expected 50 unique monitor cases in {path}, "
            f"found rows={len(rows)} unique={len(set(case_ids))}"
        )
    case_sets.append(set(case_ids))

if not all(case_sets[0] == cases for cases in case_sets[1:]):
    raise SystemExit("[error] seed-0/1/2 monitor case sets differ")

summary = json.loads(summary_path.read_text(encoding="utf-8"))
expected_catastrophes = {"0": 0, "1": 2, "2": 3}
checks = {
    "posthoc": summary.get("posthoc") is True,
    "selection_allowed": summary.get("selection_allowed") is False,
    "official_test_used": summary.get("official_test_used") is False,
    "catastrophe_threshold_mm": summary.get("catastrophe_threshold_mm") == 50.0,
    "num_records": summary.get("num_records") == 150,
    "num_cases": summary.get("num_cases") == 50,
    "catastrophes_by_seed": summary.get("catastrophes_by_seed") == expected_catastrophes,
    "token_all_equal": summary.get("token_equality", {}).get("all_equal") is True,
    "token_maximum_delta": math.isclose(
        float(summary.get("token_equality", {}).get("maximum_coordinate_delta", math.inf)),
        0.0,
        rel_tol=0.0,
        abs_tol=0.0,
    ),
}
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("[error] frozen P1 semantic checks failed: " + ", ".join(failed))

print("[ok] three identical 50-case monitor sets")
print("[ok] P1 records=150 cases=50 catastrophes=0/2/3 tokens_equal=True")
print("[ok] selection_allowed=False official_test_used=False")
PY

free_kb="$(df -Pk "$ARCHIVE_ROOT" | awk 'NR==2 {print $4}')"
required_kb="$((MIN_FREE_GB * 1024 * 1024))"
if (( free_kb < required_kb )); then
  echo "[error] less than ${MIN_FREE_GB} GiB free below $ARCHIVE_ROOT" >&2
  df -h "$ARCHIVE_ROOT"
  exit 1
fi

tmp_root="$(mktemp -d)"
metadata_dir="$tmp_root/metadata"
file_list="$tmp_root/archive_paths.txt"
mkdir -p "$metadata_dir"

cleanup() {
  rm -rf -- "$tmp_root"
}
trap cleanup EXIT

cat > "$metadata_dir/README.txt" <<EOF
Mamba Adapter v1.1 O0=xyz out8192 R1/P1 frozen archive

Created: $(date --iso-8601=seconds)
Candidate: Mamba Adapter v1.1 O0=xyz out8192
Seeds: 0, 1, 2
R1: frozen multi-seed stability replication and strict-train instrumentation
P1: declared post-hoc complete-monitor instrumentation and analysis
Catastrophe rule: rim_contact_hd95_mm > 50.0 mm or non-finite
Base tag: mamba-adapter-v11-ordering-o0-xyz-out8192-seed0
Base commit: 0cbdf8d8d379f4d57e6a2a60d5b5c71c00319721

This archive contains three canonical BN-calibrated checkpoints, monitor-only
R1 evidence, P1 post-hoc evidence, protocols, reports, and source files.
It excludes raw datasets and official-test outputs. It must not be used to
reselect a seed or ordering, modify the catastrophe threshold, or tune on the
consumed monitor split.
EOF

cp "$DATASET_MANIFEST" "$metadata_dir/skullbreak_out8192_manifest.jsonl"

{
  echo "created=$(date --iso-8601=seconds)"
  echo "hostname=$(hostname)"
  echo "user=$(id -un)"
  echo "repo_root=$REPO_ROOT"
  echo "conda_environment=$CONDA_ENV"
  echo "base_git_tag=mamba-adapter-v11-ordering-o0-xyz-out8192-seed0"
  echo "base_git_commit=0cbdf8d8d379f4d57e6a2a60d5b5c71c00319721"
  echo "archive_name=$ARCHIVE_NAME.tar"
  echo "official_test_included=false"
  echo "selection_allowed=false"
  df -h "$HOME" 2>&1 || true
  nvidia-smi 2>&1 || true
} > "$metadata_dir/runtime_environment.txt"

if command -v conda >/dev/null 2>&1; then
  conda list -n "$CONDA_ENV" > "$metadata_dir/conda-list.txt" 2>&1 || true
  conda run -n "$CONDA_ENV" python -m pip freeze \
    > "$metadata_dir/pip-freeze.txt" 2>&1 || true
  conda run -n "$CONDA_ENV" python - <<'PY' \
    > "$metadata_dir/python-runtime.txt" 2>&1 || true
import importlib.metadata
import sys

import torch

print(f"python={sys.version}")
print(f"torch={torch.__version__}")
print(f"torch_cuda={torch.version.cuda}")
print(f"cuda_available={torch.cuda.is_available()}")
print(f"cudnn={torch.backends.cudnn.version()}")
if torch.cuda.is_available():
    print(f"gpu={torch.cuda.get_device_name(0)}")
for package in ("mamba-ssm", "causal-conv1d", "triton"):
    try:
        print(f"{package}={importlib.metadata.version(package)}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{package}=missing")
PY
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git rev-parse HEAD > "$metadata_dir/git_head.txt"
  git status --short > "$metadata_dir/git_status.txt"
else
  cat > "$metadata_dir/git_status.txt" <<'EOF'
Git metadata is unavailable on this experiment server deployment.
The frozen base tag and commit are recorded in runtime_environment.txt.
The archived source files are independently covered by MANIFEST.sha256.
EOF
fi

sha256sum "$SEED0_CKPT" "$SEED1_CKPT" "$SEED2_CKPT" \
  > "$metadata_dir/CHECKPOINTS.sha256"

cat > "$file_list" <<EOF
$CONFIG
$DATASET_CONFIG
$SEED0_CKPT
$SEED0_CKPT.json
$SEED1_CKPT
$SEED1_CKPT.json
$SEED2_CKPT
$SEED2_CKPT.json
$SEED0_MONITOR
$R1_ROOT
models/AdaPoinTr.py
datasets/__init__.py
datasets/SkullBreakDataset.py
tools/builder.py
tools/runner.py
tools/audit_skullbreak_ordering_protocol.py
tools/evaluate_skullfix_implant.py
tools/recalibrate_skullfix_batchnorm.py
tools/instrument_mamba_adapter_tokens.py
tools/select_skullbreak_mamba_instrumentation_panel.py
tools/verify_mamba_instrumentation_zero_perturbation.py
tools/test_mamba_adapter_instrumentation.py
tools/lock_skullbreak_mamba_posthoc_monitor_panel.py
tools/analyze_skullbreak_mamba_multiseed_posthoc.py
tools/test_mamba_multiseed_posthoc_analysis.py
utils/config.py
utils/evaluation_statistics.py
utils/misc.py
utils/skullfix_metrics.py
scripts/instrument_skullbreak_mamba_v11_o0_checkpoint.sh
scripts/run_skullbreak_mamba_v11_o0_seed_replication.sh
scripts/run_skullbreak_mamba_v11_o0_seed1_seed2.sh
scripts/run_skullbreak_mamba_v11_o0_multiseed_posthoc_monitor.sh
scripts/launch_skullbreak_mamba_v11_o0_multiseed_tmux.sh
scripts/launch_skullbreak_mamba_v11_o0_posthoc_monitor_tmux.sh
scripts/archive_skullbreak_mamba_v11_o0_multiseed_r1_p1.sh
scripts/verify_skullbreak_mamba_v11_o0_multiseed_r1_p1_archive.sh
docs/protocols/mamba_v11_o0_xyz_multiseed_instrumentation_seed1_seed2.json
docs/protocols/mamba_v11_o0_multiseed_full_monitor_posthoc_v1.json
docs/protocols/mamba_v11_o0_multiseed_r1_p1_freeze_v1.json
docs/mamba_adapter_v11_o0_multiseed_instrumentation_preregistered_protocol_zh.md
docs/mamba_adapter_v11_o0_multiseed_full_monitor_posthoc_protocol_zh.md
docs/mamba_adapter_v11_o0_multiseed_full_monitor_posthoc_diagnosis_zh.md
docs/mamba_adapter_v11_o0_multiseed_r1_p1_freeze_zh.md
EOF

# Run-local config.yaml is an optional framework-generated copy. The canonical
# frozen config above is required and always archived.
for run_dir in "$SEED0_RUN" "$SEED1_RUN" "$SEED2_RUN"; do
  if [[ -f "$run_dir/config.yaml" ]]; then
    echo "$run_dir/config.yaml" >> "$file_list"
  fi
done

# These provide useful historical context but may not exist on an overlay-only
# experiment server. Their absence is recorded and does not weaken R1/P1 data.
optional_paths=(
  "scripts/run_skullbreak_mamba_ordering_candidate_monitor.sh"
  "docs/mamba_adapter_v11_ordering_ablation_preregistered_protocol_zh.md"
  "docs/mamba_adapter_v11_ordering_ablation_skullbreak_seed0_experiment_report_zh.md"
  "docs/mamba_adapter_v11_ordering_catastrophe_posthoc_diagnosis_zh.md"
  "requirements_mamba.txt"
)
for path in "${optional_paths[@]}"; do
  if [[ -e "$path" ]]; then
    echo "$path" >> "$file_list"
  else
    echo "$path" >> "$metadata_dir/OPTIONAL_PATHS_NOT_PRESENT.txt"
  fi
done

awk '!seen[$0]++' "$file_list" > "$file_list.tmp"
mv "$file_list.tmp" "$file_list"

while IFS= read -r path; do
  if [[ ! -e "$path" ]]; then
    echo "[error] selected archive path is missing: $path" >&2
    exit 1
  fi
  if [[ -d "$path" ]]; then
    find "$path" -type f -print0
  else
    printf '%s\0' "$path"
  fi
done < "$file_list" \
  | LC_ALL=C sort -zu \
  | xargs -0 sha256sum > "$metadata_dir/MANIFEST.sha256"

cp "$file_list" "$metadata_dir/ARCHIVE_PATHS.txt"

echo "[verify] checking selected payload before archive creation"
sha256sum -c "$metadata_dir/MANIFEST.sha256" >/dev/null

echo "[archive] selected payload size"
du -ch "$SEED0_CKPT" "$SEED1_CKPT" "$SEED2_CKPT" \
  "$SEED0_MONITOR" "$R1_ROOT" | tail -1
df -h "$ARCHIVE_ROOT"

tar -cf "$ARCHIVE_PATH" \
  -C "$tmp_root" metadata \
  -C "$REPO_ROOT" \
  --files-from "$file_list"

echo "[verify] checking selected payload after archive creation"
sha256sum -c "$metadata_dir/MANIFEST.sha256" >/dev/null
tar -tf "$ARCHIVE_PATH" >/dev/null

(
  cd "$ARCHIVE_ROOT"
  sha256sum "$(basename "$ARCHIVE_PATH")" \
    > "$(basename "$CHECKSUM_PATH")"
  sha256sum -c "$(basename "$CHECKSUM_PATH")"
)

if [[ "$CREATE_PARTS" == "1" ]]; then
  echo "[archive] splitting download copy into ${PART_SIZE_MB} MiB parts"
  split -b "${PART_SIZE_MB}M" -d -a 3 \
    "$ARCHIVE_PATH" "$PART_PREFIX"
  (
    cd "$ARCHIVE_ROOT"
    sha256sum "$ARCHIVE_NAME".part-* > "$ARCHIVE_NAME.parts.sha256"
    sha256sum -c "$ARCHIVE_NAME.parts.sha256"
  )
fi

echo "[ok] archive: $ARCHIVE_PATH"
echo "[ok] checksum: $CHECKSUM_PATH"
ls -lh "$ARCHIVE_PATH" "$CHECKSUM_PATH"
if [[ "$CREATE_PARTS" == "1" ]]; then
  echo "[ok] parts checksum: $PARTS_CHECKSUM_PATH"
  ls -lh "$PARTS_CHECKSUM_PATH" "$PART_PREFIX"*
fi
echo "[next] download the parts and checksum files before server cleanup"
