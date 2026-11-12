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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1
export CUDA_VISIBLE_DEVICES=GPU-41b45aa3-f5e3-e609-53cb-9c48bc7716ed
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 7200s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_condition_diagnostic_20261111_v1/bcsp_f0_condition_diagnostic_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_condition_diagnostic_20261111_v1/F0_CD_decoder_diagnostic_execution_request_v1.json --request-sha256 a21965cdefdf4a7903b5cb52b235dc5e30f0cd9d25a25915734967ee6ff7eda2 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_condition_diagnostic_20261111_v1/control/decoder_diagnostic_authorization_v1.json --authorization-sha256 79cb3da951023312c7f7b0ff83c45ebb9e74a1e4c362001ce6d020a03d3d5ee5 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_CD_condition_diagnostic_20261111_v1/control/decoder_diagnostic_runtime_v1.json --runtime-sha256 74910259a1b551664ffd26076ceca6808a8fe7512226f02d5cda2f57005d6916 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1/exit_code.txt
exit "$rc"
