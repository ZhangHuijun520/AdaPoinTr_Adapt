#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1
export CUDA_VISIBLE_DEVICES=GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/bcsp_lqi_training_entry_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/LQI_FoldC_training_execution_request_v1.json --request-sha256 b616a762783fd4f43af4467c6c47e41e73aa40a24fac223317e710ee7372825e --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/control/authorization_v1.json --authorization-sha256 d23a93c763d7a865f5e5b4a3c23b6def42c85a9e37b88562c2872343dc48e5f6 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1/control/runtime_v1.json --runtime-sha256 da25502013a6f6e5b3f7a74508ce45d4e9a1c2ee303431009fc191ddc6d6bb39 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1/exit_code.txt
exit "$rc"
