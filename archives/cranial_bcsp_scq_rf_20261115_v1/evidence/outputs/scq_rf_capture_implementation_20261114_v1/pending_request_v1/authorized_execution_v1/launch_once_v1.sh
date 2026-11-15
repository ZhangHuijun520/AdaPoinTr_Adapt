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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1
export CUDA_VISIBLE_DEVICES=GPU-dabcc897-ac69-efac-4438-a6186dea9aaa
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 1800s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/bcsp_scq_rf_memory_capture_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/SCQ_RF_ten_memory_execution_request_v1.json --request-sha256 51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/authorization_v1.json --authorization-sha256 235c1a571a16d8d1fe756397a5b4f901b4e57b5ff45e24be72d20fee1ef556c9 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/runtime_v1.json --runtime-sha256 4457700eecf38cde42eb90034f918209c0baf75152332d01278c481fd48f54f0 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1/exit_code.txt
exit "$rc"
