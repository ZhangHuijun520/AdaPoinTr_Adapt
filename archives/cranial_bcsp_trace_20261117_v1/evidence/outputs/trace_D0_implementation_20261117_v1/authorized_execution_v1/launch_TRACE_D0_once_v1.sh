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
[ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1 ] || exit 121
mkdir -p -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1
export CUDA_VISIBLE_DEVICES=GPU-4b19574a-832d-b4fe-e655-a57462954d6a
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 900s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1/bcsp_trace_D0_entry_v1.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1/TRACE_D0_execution_request_v1.json --request-sha256 7ad5a27aee302b877af7903b00da107c47560250d18135566315609b12a01b0f --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1/TRACE_D0_authorization_v1.json --authorization-sha256 5dc550b8d8e6e571f6b76270905c4ee96c2c3d04517e071a4a6f8c063dd9de8d --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1/TRACE_D0_runtime_v1.json --runtime-sha256 b40dfb1e0577c9032051039b8571c86344021fe075ec40aa380b67f4b936c58c >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1/exit_code
exit "$rc"
