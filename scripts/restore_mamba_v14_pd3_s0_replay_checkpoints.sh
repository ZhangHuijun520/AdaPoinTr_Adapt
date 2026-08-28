#!/usr/bin/env bash
set -euo pipefail

ROOT="${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"
ARCHIVE_DIR="${1:-$HOME/baseline_archives/mamba_v14_pd3_s0_replay_restore_v1}"
BASE="mamba_v14_pd3_s0_replay_checkpoints_seed0_v1"

EXPECTED_ARCHIVE_DIR="$HOME/baseline_archives/mamba_v14_pd3_s0_replay_restore_v1"
[[ -d "$ARCHIVE_DIR" ]] || { echo "[error] missing archive directory: $ARCHIVE_DIR"; exit 1; }
[[ "$(realpath -e "$ARCHIVE_DIR")" == "$(realpath -e "$EXPECTED_ARCHIVE_DIR")" ]] || {
  echo "[error] unexpected archive directory: $ARCHIVE_DIR"
  exit 1
}
[[ -d "$ROOT" ]] || { echo "[error] missing repository root: $ROOT"; exit 1; }

cd "$ARCHIVE_DIR"
sha256sum -c "$BASE.parts.sha256"

expected_count="$(tr -d '[:space:]' < "$BASE.parts.count")"
actual_count="$(find . -maxdepth 1 -type f -name "$BASE.part-*" | wc -l)"
[[ "$actual_count" == "$expected_count" ]] || {
  echo "[error] part count mismatch: $actual_count != $expected_count"
  exit 1
}

expected_bytes="$(tr -d '[:space:]' < "$BASE.bytes")"
actual_bytes="$(cat "$BASE".part-* | wc -c)"
[[ "$actual_bytes" == "$expected_bytes" ]] || {
  echo "[error] split-stream byte count mismatch"
  exit 1
}

expected_tar_sha="$(awk 'NR==1 {print $1}' "$BASE.tar.sha256")"
actual_tar_sha="$(cat "$BASE".part-* | sha256sum | awk '{print $1}')"
[[ "$actual_tar_sha" == "$expected_tar_sha" ]] || {
  echo "[error] split-stream tar SHA256 mismatch"
  exit 1
}

WORKING="$ARCHIVE_DIR/.restore_working"
[[ ! -e "$WORKING" ]] || { echo "[error] restore working path already exists: $WORKING"; exit 1; }
mkdir -p "$WORKING"
trap 'rm -rf -- "$WORKING"' EXIT
cat "$BASE".part-* | tar -xf - -C "$WORKING"

while read -r expected relative; do
  relative="${relative#\*}"
  source="$WORKING/$relative"
  target="$ROOT/$relative"
  [[ -f "$source" ]] || { echo "[error] restored member missing: $relative"; exit 1; }
  [[ "$(sha256sum "$source" | awk '{print $1}')" == "$expected" ]] || {
    echo "[error] restored member hash mismatch: $relative"
    exit 1
  }
  if [[ -e "$target" ]]; then
    [[ -f "$target" && "$(sha256sum "$target" | awk '{print $1}')" == "$expected" ]] || {
      echo "[error] refusing to overwrite non-identical target: $target"
      exit 1
    }
    echo "[kept-identical] $relative"
  else
    mkdir -p "$(dirname "$target")"
    install -m 0644 "$source" "$target"
    echo "[restored] $relative"
  fi
done < "$BASE.members.sha256"

echo "[ok] four frozen S0 checkpoints/configs restored hash-exactly"
echo "[temporary] delete the four restored checkpoints only after P-D3 output is archived"
