#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldC_training_20261110_v1/bcsp_f0_training_entry_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldC_training_20261110_v1/F0_FoldC_training_execution_request_v1.json --request-sha256 afd2750a3738f65d6fcfc308153c4358a4ded5e242a7e74796f9d8dec519d32d --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldC_training_20261110_v1/control/authorization_v1.json --authorization-sha256 3c731d939db45c1a8fcef1f2bf634b56699e04308452de62f5d760810d23198e --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldC_training_20261110_v1/control/runtime_v1.json --runtime-sha256 c02da22983ad43dc02e603826542e69ca94696108b12514e6c3582ff9481129e >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldC_seed0_train_20261110_v1/exit_code.txt
exit "$rc"
