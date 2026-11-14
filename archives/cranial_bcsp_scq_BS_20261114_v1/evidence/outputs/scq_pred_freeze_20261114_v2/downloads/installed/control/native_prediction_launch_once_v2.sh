#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
[ ! -L /home ] || exit 121
[ ! -L /home/jovyan ] || exit 121
[ ! -L /home/jovyan/adapointr_work ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba ] || exit 121
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2
export CUDA_VISIBLE_DEVICES=GPU-dabcc897-ac69-efac-4438-a6186dea9aaa
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 7200s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/bcsp_scq_fourmodel_native_predict_v2.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/SCQ_BS_CD_native_prediction_execution_request_v2.json --request-sha256 ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_authorization_v2.json --authorization-sha256 057e9e4b39812cae59bafa29ddf2938be1ea4d2cf711304a2fb88e86e6b769e4 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_runtime_v2.json --runtime-sha256 f49b1980e1efb3d0248ddf0581228d7f1a9244f80158b076a9dbd162b523e042 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2/exit_code.txt
exit "$rc"
