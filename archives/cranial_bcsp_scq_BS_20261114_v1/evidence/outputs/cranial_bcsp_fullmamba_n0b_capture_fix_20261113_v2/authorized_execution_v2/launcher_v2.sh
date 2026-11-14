#!/bin/bash
set -eu
umask 077
cd /home/jovyan/adapointr_work/PoinTr
/usr/bin/python3 -I -S -B -c 'import pathlib,json,hashlib;p=pathlib.Path('"'"'/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2'"'"');a=json.loads((p/'"'"'authorization_v2.json'"'"').read_bytes());r=json.loads((p/'"'"'runtime_scope_v2.json'"'"').read_bytes());assert a['"'"'explicit_user_authorization'"'"'] is True and a['"'"'request_sha256'"'"']==r['"'"'request_sha256'"'"']=='"'"'4a554bc7bd23eaebf62982cda6cecc99948f47c9511cedcd9fbfa28e69630baf'"'"';assert r['"'"'authorization_sha256'"'"']==hashlib.sha256((p/'"'"'authorization_v2.json'"'"').read_bytes()).hexdigest()'
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/output
export CUDA_VISIBLE_DEVICES=GPU-aa9e6ffb-fdbb-1836-1c32-7244231d3714
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/output/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/output/tmp
export PYTHONHASHSEED=0
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/output/hf_cache
export XDG_CACHE_HOME=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/output/cache
export TRITON_CACHE_DIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/output/triton_cache
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 900s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/worker_v2.py /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/runtime_scope_v2.json 22d7a24a83db766bf4e729de96bddcb762eba476a755c402e911525e47372d79 >/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/output/launch.log 2>&1
rc=$?
set -e
printf "%s\n" "$rc" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v2/exit_code_v2
exit "$rc"
