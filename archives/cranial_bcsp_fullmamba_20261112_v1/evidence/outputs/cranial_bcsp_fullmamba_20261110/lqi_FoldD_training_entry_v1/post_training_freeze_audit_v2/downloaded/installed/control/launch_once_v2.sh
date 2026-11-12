#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2
export CUDA_VISIBLE_DEVICES=GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2/bcsp_lqi_foldD_training_entry_v2.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2/LQI_FoldD_training_execution_request_v2.json --request-sha256 317870937023da177930437f39b3179956e72e3773f53f4010eb86f25ed21da9 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2/control/authorization_v2.json --authorization-sha256 a20dff168edfa4bcb10d7608118bcb211cb4b3570472684141f13551d747200b --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldD_training_20261111_v2/control/runtime_v2.json --runtime-sha256 2a3831f997afae8038cf14c683379ed17e279dd5b600a403ac45ec55be60e334 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldD_seed0_train_20261111_v2/exit_code.txt
exit "$rc"
