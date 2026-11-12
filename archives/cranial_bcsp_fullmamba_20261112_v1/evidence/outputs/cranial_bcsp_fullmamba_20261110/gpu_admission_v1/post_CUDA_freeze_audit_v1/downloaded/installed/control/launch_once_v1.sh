#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=10s 1800s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/bcsp_f0_cuda_admission_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/F0_artificial_cuda_execution_request_v1.json --request-sha256 a9fbc819da73415008ac5643f5b6cea9ab1b3818029129e6f93e2e67bcc23efc --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/control/authorization_v1.json --authorization-sha256 38d65b8aecfbbf5bc78f98ef3915264257381523b47dd7d0507875fe0be1381d --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_cuda_20261110_v1/control/runtime_v1.json --runtime-sha256 2593b016d2efd09036045bded2e1f1b71b333c24a2ffb3c274a7f60ec2cb7dc5 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_artificial_cuda_20261110_v1/exit_code.txt
exit "$rc"
