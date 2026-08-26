#!/usr/bin/env bash
set -euo pipefail

ARCHIVE_ROOT="${ARCHIVE_ROOT:-$HOME/baseline_archives/mamba_v13_d3_round_a_negative_seed0}"
BASE="${ARCHIVE_NAME:-mamba_v13_d3_round_a_s0_s1_s2_negative_seed0_v1}"

cd "$ARCHIVE_ROOT"
sha256sum -c "$BASE.parts.sha256"

shopt -s nullglob
parts=("$BASE".part-*)
shopt -u nullglob
expected_count="$(cat "$BASE.parts.count")"
[[ "${#parts[@]}" -eq "$expected_count" ]] || {
  echo "[error] expected $expected_count parts, found ${#parts[@]}" >&2
  exit 1
}

actual_bytes="$(stat -c '%s' "${parts[@]}" | awk '{sum += $1} END {printf "%.0f", sum}')"
expected_bytes="$(awk 'NR==1 {print $1}' "$BASE.bytes")"
[[ "$actual_bytes" == "$expected_bytes" ]] || {
  echo "[error] concatenated byte count mismatch" >&2
  exit 1
}

actual_hash="$(cat "${parts[@]}" | sha256sum | awk '{print $1}')"
expected_hash="$(awk 'NR==1 {print $1}' "$BASE.tar.sha256")"
[[ "$actual_hash" == "$expected_hash" ]] || {
  echo "[error] concatenated tar SHA256 mismatch" >&2
  exit 1
}

cat "${parts[@]}" | tar -tf - >/dev/null
echo "[ok] all parts, byte count, tar stream hash, and tar structure match"
echo "[locked] seed1=false holdout=false official_test=false rule_revision=false"
