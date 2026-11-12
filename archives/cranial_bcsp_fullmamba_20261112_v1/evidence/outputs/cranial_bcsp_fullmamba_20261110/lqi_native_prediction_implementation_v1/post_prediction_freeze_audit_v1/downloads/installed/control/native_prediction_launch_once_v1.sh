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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1
export CUDA_VISIBLE_DEVICES=GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 7200s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1/bcsp_lqi_twofold_native_predict_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1/LQI_CD_native_prediction_execution_request_v1.json --request-sha256 cab2831f27913766d7009101ec86d9a6e642a40b9330359dbfc8ff5928610fb6 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1/control/native_prediction_authorization_v1.json --authorization-sha256 7f04f29f985f74d0fdbd68af1213e733ea0da9b1005f9c1c06a986ff0101dd98 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_CD_native_prediction_20261111_v1/control/native_prediction_runtime_v1.json --runtime-sha256 1126705659bf2752482eabaa28075c5539245208985f709a946d8c1fb3079055 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_CD_native_development_20261111_v1/exit_code.txt
exit "$rc"
