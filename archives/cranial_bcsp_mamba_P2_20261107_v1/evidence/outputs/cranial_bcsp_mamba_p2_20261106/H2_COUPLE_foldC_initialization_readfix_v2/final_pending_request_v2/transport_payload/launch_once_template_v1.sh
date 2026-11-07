#!/bin/bash
set -u
umask 077
cd /home/jovyan/adapointr_work/PoinTr || exit 120
[ ! -L /home ] || exit 121
[ ! -L /home/jovyan ] || exit 121
[ ! -L /home/jovyan/adapointr_work ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2 ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2 || exit 122
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2 || exit 123
exec >>/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2/launch.log 2>&1
env \
CUDA_VISIBLE_DEVICES=GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52 \
CUBLAS_WORKSPACE_CONFIG=:4096:8 \
OMP_NUM_THREADS=2 \
MKL_NUM_THREADS=2 \
OPENBLAS_NUM_THREADS=2 \
PYTHONDONTWRITEBYTECODE=1 \
MPLBACKEND=Agg \
MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2/mplconfig \
CUDA_CACHE_DISABLE=1 \
TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2/tmp \
PYTHONHASHSEED=0 \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2/hf_cache \
XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2/cache \
TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2/triton_cache \
 /usr/bin/timeout \
 --signal=TERM \
 --kill-after=5s \
 86400s \
 /opt/conda/envs/adapointr-mamba/bin/python3.10 \
 -I \
 -S \
 -B \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v2/bcsp_h2_couple_foldC_training_entry_v2.py \
 --request \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v2/H2_COUPLE_foldC_seed0_training_execution_request_v2.json \
 --request-sha256 \
 REQUEST_SHA256 \
 --authorization \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v2/control/H2_authorization_v1.json \
 --authorization-sha256 \
 AUTHORIZATION_SHA256 \
 --runtime \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v2/control/H2_runtime_v1.json \
 --runtime-sha256 \
 RUNTIME_SHA256
result=$?
printf "%s\n" "$result" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v2/exit_code.txt
exit "$result"
