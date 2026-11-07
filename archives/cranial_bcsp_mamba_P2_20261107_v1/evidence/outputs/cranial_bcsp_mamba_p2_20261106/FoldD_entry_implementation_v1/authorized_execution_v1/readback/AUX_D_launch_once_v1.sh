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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2 || exit 122
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1 || exit 123
exec >>/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1/launch.log 2>&1
env \
CUDA_VISIBLE_DEVICES=GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52 \
CUBLAS_WORKSPACE_CONFIG=:4096:8 \
OMP_NUM_THREADS=2 \
MKL_NUM_THREADS=2 \
OPENBLAS_NUM_THREADS=2 \
PYTHONDONTWRITEBYTECODE=1 \
MPLBACKEND=Agg \
MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1/mplconfig \
CUDA_CACHE_DISABLE=1 \
TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1/tmp \
PYTHONHASHSEED=0 \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1/hf_cache \
XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1/cache \
TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1/triton_cache \
 /usr/bin/timeout \
 --signal=TERM \
 --kill-after=5s \
 86400s \
 /opt/conda/envs/adapointr-mamba/bin/python3.10 \
 -I \
 -S \
 -B \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_foldD_20261107_v1/bcsp_h2_foldD_training_entry_v1.py \
 --request \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_foldD_20261107_v1/H2_AUX_foldD_seed0_training_execution_request_v1.json \
 --request-sha256 \
 efba40fdc78db788798ba326d9a393c5e0cac48189bb507a8ec4e9fe1d5f2db9 \
 --authorization \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_foldD_20261107_v1/control/AUX_D_authorization_v1.json \
 --authorization-sha256 \
 12f42884708bb718dec9c31aeb15370a5024cca7b0b7f4ea33d820a546001fb2 \
 --runtime \
 /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_foldD_20261107_v1/control/AUX_D_runtime_v1.json \
 --runtime-sha256 \
 cd9bc06bde278ea8b4d2e180adca81adcbfee33954042a8557ebac74a0791c55
result=$?
printf "%s\n" "$result" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1/exit_code.txt
exit "$result"
