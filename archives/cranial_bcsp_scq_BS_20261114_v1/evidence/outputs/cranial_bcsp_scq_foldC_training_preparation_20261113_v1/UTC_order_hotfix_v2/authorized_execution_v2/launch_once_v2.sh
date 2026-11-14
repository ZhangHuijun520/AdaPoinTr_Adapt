#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/bcsp_scq_training_entry_v2.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_B_FoldC_training_execution_request_v2.json --request-sha256 95d6dfdb07a0e64a8f80646c65f84da38ff7297344e74541000fe1dbcc899b84 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_v2/authorization_v2.json --authorization-sha256 b95dce8e8f8131e61905e861c443b21ccd17ff9d948c118083d458b81a9b5c82 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/control_v2/runtime_v2.json --runtime-sha256 687769d89975a3803bbf2480f644e0ba24e17fb7d22b9dadbdfe7880779e8ee2 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_B_foldC_seed0_train_20261113_v2/exit_code.txt
exit "$rc"
