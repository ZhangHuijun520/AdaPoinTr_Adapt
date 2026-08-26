#!/usr/bin/env bash
set -euo pipefail

RESTORE_ROOT="${1:-.}"
cd "$RESTORE_ROOT"

python tools/verify_mamba_v13_d3_s2_feasibility_archive.py --root .

echo "[ok] D3 S2 feasibility negative archive is independently valid"
echo "[locked] S2 calibration=false S2 full=false holdout=false selection=false"
echo "[next] S1 calibration still requires a separate authorization receipt"
