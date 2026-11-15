#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3
export CUDA_VISIBLE_DEVICES=GPU-dabcc897-ac69-efac-4438-a6186dea9aaa
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/bcsp_scq_rf_Sref_C_training_entry_v3.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/SCQ_RF_Sref_C_training_execution_request_v3.json --request-sha256 6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/control/authorization_v3.json --authorization-sha256 bdf484027aa76644a3fe1f7c8689ed6c90d22ee128f670882b3333658d1ece9d --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v3/control/runtime_v3.json --runtime-sha256 999199588332093163fbb1823784114fca841352fff776b02abbb9e146fafbf5 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Sref_foldC_seed0_train_20261114_v3/exit_code.txt
exit "$rc"
