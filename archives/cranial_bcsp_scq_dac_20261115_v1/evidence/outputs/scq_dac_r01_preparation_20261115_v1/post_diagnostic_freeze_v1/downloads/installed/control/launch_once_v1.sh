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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1
export CUDA_VISIBLE_DEVICES=GPU-383d118a-368c-94e3-166a-cad3efab8fd7
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 600s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/bcsp_scq_dac_r1_entry_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/SCQ_DAC_R1_execution_request_v1.json --request-sha256 129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/authorization_v1.json --authorization-sha256 ccfd8c934d6a5677f6e6cf8491ebf6b7139e224b54755995fba9ab41bb952e45 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/runtime_v1.json --runtime-sha256 7a650ae40ae1f0a392b520e4aa21e91b3eec5fbeb68b620d437251c2a451e804 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1/launch.log 2>&1
rc=$?
set -e
printf '%s\n' "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1/exit_code.txt
exit "$rc"
