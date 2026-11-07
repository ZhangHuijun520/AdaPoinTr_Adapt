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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2 || exit 122
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1 || exit 123
exec >>/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1/launch.log 2>&1
env \
CUDA_VISIBLE_DEVICES=GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52 \
CUBLAS_WORKSPACE_CONFIG=:4096:8 \
OMP_NUM_THREADS=2 \
MKL_NUM_THREADS=2 \
OPENBLAS_NUM_THREADS=2 \
PYTHONDONTWRITEBYTECODE=1 \
MPLBACKEND=Agg \
MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1/mplconfig \
CUDA_CACHE_DISABLE=1 \
TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1/tmp \
PYTHONHASHSEED=0 \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1/hf_cache \
XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1/cache \
TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1/triton_cache \
 /usr/bin/timeout \
 --signal=TERM \
 --kill-after=5s \
 86400s \
 /opt/conda/envs/adapointr-mamba/bin/python3.10 \
 -I \
 -S \
 -B \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v1/bcsp_h2_couple_foldC_training_entry_v1.py \
 --request \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v1/H2_COUPLE_foldC_seed0_training_execution_request_v1.json \
 --request-sha256 \
 477522d9f7c5e7fc4e282a231f44ad5641588d5b34e303d7e433c3ba57ed6ce3 \
 --authorization \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v1/control/H2_authorization_v1.json \
 --authorization-sha256 \
 3e9570c846f7ec8954f147ce96a94f51bd561c5639759fe9d9158b0f753ba4f9 \
 --runtime \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v1/control/H2_runtime_v1.json \
 --runtime-sha256 \
 c874e229eaf995497556ec81c3b32e92986887495f5e7e168842a03323762813
result=$?
printf "%s\n" "$result" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1/exit_code.txt
exit "$result"
