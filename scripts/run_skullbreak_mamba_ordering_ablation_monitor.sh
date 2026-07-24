#!/usr/bin/env bash
set -euo pipefail

cd "${POINTR_ROOT:-$HOME/adapointr_work/PoinTr}"

CANDIDATES="${CANDIDATES:-O0 O1 O2 O3}"
for candidate in $CANDIDATES; do
  bash scripts/run_skullbreak_mamba_ordering_candidate_monitor.sh "$candidate"
done

echo "[done] all requested strict-monitor candidates: $CANDIDATES"
echo "[next] run scripts/select_skullbreak_mamba_ordering_monitor.sh"
