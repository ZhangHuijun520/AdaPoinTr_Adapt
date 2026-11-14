#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
[ ! -L /home ] || exit 121
[ ! -L /home/jovyan ] || exit 121
[ ! -L /home/jovyan/adapointr_work ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1 ] || exit 121
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=10s 1800s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_cuda_admission_v3.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/SCQ_artificial_cuda_execution_request_v1.json --request-sha256 0f5aec8c30d0044547cd8806c5663aeb4f0f9643e254a65ce562f5d45641521b --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/control/authorization_v1.json --authorization-sha256 1dc78f1c2c9662bae6a2798e72b22ceaa70fe4e38d39fb3336728d84da11306e --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/control/runtime_v1.json --runtime-sha256 e405a679c6b18425c4980e4fefc4e23a628c7cfe862a834f7293d7efeacba8b9 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_artificial_cuda_20261113_v1/exit_code.txt
exit "$rc"
