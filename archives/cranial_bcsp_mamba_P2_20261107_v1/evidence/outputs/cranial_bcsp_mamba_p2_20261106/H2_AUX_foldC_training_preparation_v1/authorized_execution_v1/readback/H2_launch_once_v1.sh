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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2 || exit 122
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1 || exit 123
exec >>/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1/launch.log 2>&1
env \
CUDA_VISIBLE_DEVICES=GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52 \
CUBLAS_WORKSPACE_CONFIG=:4096:8 \
OMP_NUM_THREADS=2 \
MKL_NUM_THREADS=2 \
OPENBLAS_NUM_THREADS=2 \
PYTHONDONTWRITEBYTECODE=1 \
MPLBACKEND=Agg \
MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1/mplconfig \
CUDA_CACHE_DISABLE=1 \
TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1/tmp \
PYTHONHASHSEED=0 \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1/hf_cache \
XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1/cache \
TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1/triton_cache \
 /usr/bin/timeout \
 --signal=TERM \
 --kill-after=5s \
 86400s \
 /opt/conda/envs/adapointr-mamba/bin/python3.10 \
 -I \
 -S \
 -B \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_AUX_foldC_20261107_v1/bcsp_h2_aux_foldC_training_entry_v1.py \
 --request \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_AUX_foldC_20261107_v1/H2_AUX_foldC_seed0_training_execution_request_v1.json \
 --request-sha256 \
 0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517 \
 --authorization \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_AUX_foldC_20261107_v1/control/H2_authorization_v1.json \
 --authorization-sha256 \
 14ee04317e64014c34d9d071242d71c4c12c1ab7c7b3d8ed42ad95886da6575b \
 --runtime \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_AUX_foldC_20261107_v1/control/H2_runtime_v1.json \
 --runtime-sha256 \
 fc2174438b6eb872443a97418441664f91e0ab1a3c334830232d556fee0e0eba
result=$?
printf "%s\n" "$result" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1/exit_code.txt
exit "$result"
