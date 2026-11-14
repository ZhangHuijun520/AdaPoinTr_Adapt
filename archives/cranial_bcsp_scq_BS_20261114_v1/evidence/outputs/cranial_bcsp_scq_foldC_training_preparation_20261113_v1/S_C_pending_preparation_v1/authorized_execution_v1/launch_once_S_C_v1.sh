#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_scq_training_entry_v2.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_S_FoldC_training_execution_request_v1.json --request-sha256 1aed46b99b11f83b6707b1a3fe81b7e90a971ec7419019327d3c224b2d2adc86 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/authorization_S_C_v1.json --authorization-sha256 c22bafc024fa45c006a9c3186af7eccbe58a77b6abca81f671ca7e7afcaf88a6 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_S_C_v1/runtime_S_C_v1.json --runtime-sha256 8f537a9cc4bbf26f4099f54598a57d226f6896cffe1536355ac7ecac93d7b4f5 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_S_foldC_seed0_train_20261113_v1/exit_code.txt
exit "$rc"
