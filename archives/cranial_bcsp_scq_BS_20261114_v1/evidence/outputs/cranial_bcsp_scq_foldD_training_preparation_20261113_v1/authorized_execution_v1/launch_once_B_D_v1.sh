#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_scq_foldD_training_entry_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_B_FoldD_training_execution_request_v1.json --request-sha256 4f1db753d12693eb909d5d795997b542ca7a2082b73b6737521a1154f1777ed4 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/authorization_B_D_v1.json --authorization-sha256 a45e8318bac095c4a7b4b87a230c974f89f5584f51e119c31398b7522ef28c79 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_B_D_v1/runtime_B_D_v1.json --runtime-sha256 ad884af5b901824a22cd9b99ce31ee1dbd5383ba8307a8f21f35703ef5331534 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldD_seed0_train_20261113_v1/exit_code.txt
exit "$rc"
