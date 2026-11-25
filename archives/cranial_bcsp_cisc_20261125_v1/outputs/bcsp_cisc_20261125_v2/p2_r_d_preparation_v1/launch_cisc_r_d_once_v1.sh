#!/bin/bash
set -eu
umask 077
[ "$#" -eq 3 ]
project=/home/jovyan/adapointr_work/PoinTr
install=$project/third_party/bcsp_cisc_p2_r_d_20261125_v1
out=$project/logs/cranial_bcsp_fullmamba/CISC_P2_R_D_seed2026112601_zrtpob_v1
cd "$project"
export CUDA_VISIBLE_DEVICES=GPU-e763d389-b4c2-4dc8-9571-d7343ec328b1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1 CUDA_CACHE_DISABLE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MPLBACKEND=Agg
export TMPDIR="$out/tmp" XDG_CACHE_HOME="$out/cache" MPLCONFIGDIR="$out/mplconfig"
export TRITON_CACHE_DIR="$out/triton" HF_HOME="$out/hf"
python=/opt/conda/envs/adapointr-mamba/bin/python3.10
args=("$install/cisc_train_r_d_v1.py"
      --request "$install/CISC_P2_R_D_training_execution_request_v1.json" --request-sha256 "$1"
      --authorization "$install/authorization_v1.json" --authorization-sha256 "$2"
      --runtime "$install/runtime_v1.json" --runtime-sha256 "$3"
      --launcher "$install/launch_cisc_r_d_once_v1.sh")
/usr/bin/timeout --signal=TERM --kill-after=5s 30s "$python" -I -S -B "${args[@]}" --check
mkdir -- "$out"
printf '%s\n' "$$" >"$out/launcher.pid"
set +e
/usr/bin/timeout --signal=TERM --kill-after=10s 86400s "$python" -I -S -B "${args[@]}" >"$out/launch.log" 2>&1
rc=$?
set -e
printf '%s\n' "$rc" >"$out/exit_code.txt"
exit "$rc"
