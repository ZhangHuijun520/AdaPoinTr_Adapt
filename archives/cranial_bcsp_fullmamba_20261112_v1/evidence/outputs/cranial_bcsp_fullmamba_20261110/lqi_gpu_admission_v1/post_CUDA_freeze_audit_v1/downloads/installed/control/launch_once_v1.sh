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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1 ] || exit 121
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1
export CUDA_VISIBLE_DEVICES=GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=10s 1800s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1/bcsp_lqi_cuda_admission_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1/LQI_artificial_cuda_execution_request_v1.json --request-sha256 d1324b1b754e2eea91e00ea5ede802c6bd506815b82db82f3c41a070811e9812 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1/control/authorization_v1.json --authorization-sha256 4d0c4d6d7be296c80bed348d63bb93e088cc180ce449072ca7c307a80e66319a --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_cuda_20261111_v1/control/runtime_v1.json --runtime-sha256 c1504dd514e789bbf17ce07c77a1582d04d807fb38b6887aaf0262e4eadc2157 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_artificial_cuda_20261111_v1/exit_code.txt
exit "$rc"
