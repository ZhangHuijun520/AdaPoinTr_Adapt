#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
mkdir -p /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1
export CUDA_VISIBLE_DEVICES=GPU-383d118a-368c-94e3-166a-cad3efab8fd7
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 3600s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/bcsp_rive_training_entry_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1_execution_request_v1.json --request-sha256 c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/authorization_v1.json --authorization-sha256 a9fdaf7ffb66bc7e04ed1d7b5ca7e740e7ea158a5fb23c205edac5ffe2837b2e --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1/control/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/runtime_v1.json --runtime-sha256 4fb7ad4408456198daabb01b81e6e8ff8cf877f67cb8f01437364b1a6b76bcb0 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1/exit_code.txt
exit "$rc"
