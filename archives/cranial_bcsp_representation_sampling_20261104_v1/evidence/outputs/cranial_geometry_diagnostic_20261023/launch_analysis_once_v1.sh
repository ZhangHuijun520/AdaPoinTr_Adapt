#!/bin/bash
set -u
cd /home/jovyan/adapointr_work/PoinTr/logs/cranial_geometry_diagnostic_v1_20261023 || exit 90
test "$(hostname)" = shu-common-25721452-notebook-n9i64i-0 || exit 91
test ! -e run.pid && test ! -e run.log && test ! -e exit_code.txt || exit 92
set -o noclobber
printf '%s\n' "$$" > run.pid || exit 93
date -Is > started_at.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 timeout --signal=TERM --kill-after=10 300 /opt/conda/envs/adapointr-mamba/bin/python -I -B analyze_point_geometry_v1.py > run.log 2>&1
rc=$?
printf '%s\n' "$rc" > exit_code.txt
date -Is > ended_at.txt
exit "$rc"
