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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2 || exit 122
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1 || exit 123
exec >>/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1/launch.log 2>&1
env \
CUDA_VISIBLE_DEVICES=GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52 \
CUBLAS_WORKSPACE_CONFIG=:4096:8 \
OMP_NUM_THREADS=2 \
MKL_NUM_THREADS=2 \
OPENBLAS_NUM_THREADS=2 \
PYTHONDONTWRITEBYTECODE=1 \
MPLBACKEND=Agg \
MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1/mplconfig \
CUDA_CACHE_DISABLE=1 \
TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1/tmp \
PYTHONHASHSEED=0 \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1/hf_cache \
XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1/cache \
TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1/triton_cache \
/usr/bin/timeout \
--signal=TERM \
--kill-after=5s \
900s \
/opt/conda/envs/adapointr-mamba/bin/python3.10 \
-I \
-S \
-B \
/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h2_cuda_admission_20261107_v1/bcsp_h2_cuda_admission_v1.py \
--request \
/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h2_cuda_admission_20261107_v1/H2_artificial_cuda_execution_request_v1.json \
--request-sha256 \
6e20c58d6ceee32b2f77858b9bb394535d39d999630302e0a115299e66de6e7a \
--authorization \
/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h2_cuda_admission_20261107_v1/control/authorization_v1.json \
--authorization-sha256 \
2a32cc3abe8527411f050313b3bb0136608ab9ddbfdb798b3a75e1d7f756b142 \
--runtime \
/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h2_cuda_admission_20261107_v1/control/runtime_v1.json \
--runtime-sha256 \
9ef5c588f5a3a485b772a32296b16428339f892cb95d1832f4fb81d7d510ebe9
result=$?
printf "%s\n" "$result" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_COUPLE_artificial_cuda_20261107_v1/exit_code.txt
exit "$result"
