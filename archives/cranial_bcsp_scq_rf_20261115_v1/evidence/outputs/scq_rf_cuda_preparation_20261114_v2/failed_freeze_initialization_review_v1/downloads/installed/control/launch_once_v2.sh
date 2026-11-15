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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2 ] || exit 121
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2
export CUDA_VISIBLE_DEVICES=GPU-dabcc897-ac69-efac-4438-a6186dea9aaa
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=10s 1800s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/bcsp_scq_rf_cuda_admission_v2.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/SCQ_RF_artificial_cuda_execution_request_v2.json --request-sha256 09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/control/authorization_v2.json --authorization-sha256 0324997a169380ebbd6a76c8bd878763911a7be207f15714c2cc1dadc3b50de9 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/control/runtime_v2.json --runtime-sha256 dd767335fe3255fdf0078217179b8c74974470749ee729ab7ba02c18f466c510 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v2/exit_code.txt
exit "$rc"
