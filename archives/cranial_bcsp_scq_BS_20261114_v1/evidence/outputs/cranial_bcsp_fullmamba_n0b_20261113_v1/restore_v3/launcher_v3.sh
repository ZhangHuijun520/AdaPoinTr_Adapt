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
/usr/bin/timeout --signal=TERM --kill-after=5s 900s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/worker.py /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/scope_v3.json aceb4434ecebe1ed1dd5cb4e49a4e77e77d24aa7fce7e32aa9bf3ae928ce06ee >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/output/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1/exit_code
exit "$rc"
