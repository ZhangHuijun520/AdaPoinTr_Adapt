#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1
export CUDA_VISIBLE_DEVICES=GPU-dabcc897-ac69-efac-4438-a6186dea9aaa
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/bcsp_scq_rf_Static_C_training_entry_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/SCQ_RF_Static_C_training_execution_request_v1.json --request-sha256 a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/control/authorization_v1.json --authorization-sha256 bfa00d971bd19ef18b0fdd355834186706875053b334bd1ddfbe338e42d405f4 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1/control/runtime_v1.json --runtime-sha256 93c79a1cc0b3c330ec026b25eb077795a5d2cc15d2a634aa98af917f5d0365cd >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldC_seed0_train_20261114_v1/exit_code.txt
exit "$rc"
