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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2 || exit 122
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1 || exit 123
exec >>/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1/launch.log 2>&1
env \
CUDA_VISIBLE_DEVICES=GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52 \
CUBLAS_WORKSPACE_CONFIG=:4096:8 \
OMP_NUM_THREADS=2 \
MKL_NUM_THREADS=2 \
OPENBLAS_NUM_THREADS=2 \
PYTHONDONTWRITEBYTECODE=1 \
MPLBACKEND=Agg \
MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1/mplconfig \
CUDA_CACHE_DISABLE=1 \
TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1/tmp \
PYTHONHASHSEED=0 \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1/hf_cache \
XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1/cache \
TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1/triton_cache \
/usr/bin/timeout \
--signal=TERM \
--kill-after=5s \
7200s \
/opt/conda/envs/adapointr-mamba/bin/python3.10 \
-I \
-S \
-B \
/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_condition_probe_20261107_v1/condition_probe_entry_v1.py \
--request \
/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_condition_probe_20261107_v1/condition_probe_execution_request_v1.json \
--request-sha256 \
9f2a04c381070d54d9e82cc70e800403b12ac7867124ff4b5e52043c1997549c \
--authorization \
/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_condition_probe_20261107_v1/control/authorization_v1.json \
--authorization-sha256 \
c56e1a82425c65b377d9258e5a9406bb1fca040dbd374416f806713d16e85300 \
--runtime \
/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_condition_probe_20261107_v1/control/runtime_v1.json \
--runtime-sha256 \
8c91649ecac1e402a202c0764ebe9851a46ba57d42d4dca6f3ef1f49764eb8d9
result=$?
printf "%s\n" "$result" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/condition_probe_C_D_20261107_v1/exit_code.txt
exit "$result"
