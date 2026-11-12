#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/bcsp_f0_foldD_training_entry_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/F0_FoldD_training_execution_request_v1.json --request-sha256 ea45165142676c16b0c18e5616494ee78e1231970590ce4b314bf4c479bcd8b0 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/control/authorization_v1.json --authorization-sha256 76213e469fd782dd77ee2d46d1e5a8cad666f305f10fa273591a9771edb67b7d --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/control/runtime_v1.json --runtime-sha256 4bd10b148376c90220189409d2c4c5a10983fa0fbed28eb15a8f0787b7813111 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_foldD_seed0_train_20261110_v1/exit_code.txt
exit "$rc"
