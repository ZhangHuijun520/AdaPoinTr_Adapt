#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/output
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/output/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/output/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/output/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/output/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/output/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 900s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/worker.py /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/scope.json aae21199c94e4545444beb5a72cf0bce2bf00640cfd910c3926d51a9641a1948 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/output/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/exit_code
exit "$rc"
