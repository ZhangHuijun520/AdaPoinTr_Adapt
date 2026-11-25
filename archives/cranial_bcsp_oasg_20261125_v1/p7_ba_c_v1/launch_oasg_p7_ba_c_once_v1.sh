#!/bin/bash
set -eu
umask 077
[ "$#" -eq 3 ]
project=/home/USER/adapointr_work/PoinTr
install=$project/third_party/bcsp_oasg_p7_ba_c_20261124_v1
out=$project/logs/cranial_bcsp_fullmamba/OASG_BA_C_native_20261124_v1
cd "$project"
export CUDA_VISIBLE_DEVICES=GPU-3fea2502-c54e-30e1-ae67-8696c29238d2
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1 CUDA_CACHE_DISABLE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MPLBACKEND=Agg
export TMPDIR="$out/tmp" XDG_CACHE_HOME="$out/cache" MPLCONFIGDIR="$out/mplconfig"
export TRITON_CACHE_DIR="$out/triton" HF_HOME="$out/hf"
python=/opt/conda/envs/adapointr-mamba/bin/python3.10
args=("$install/oasg_native_ba_c_v1.py"
      --request "$install/OASG_BA_C_native_execution_request_v1.json" --request-sha256 "$1"
      --authorization "$install/authorization_v1.json" --authorization-sha256 "$2"
      --runtime "$install/runtime_v1.json" --runtime-sha256 "$3"
      --launcher "$install/launch_oasg_p7_ba_c_once_v1.sh")
[ "$(hostname)" = notebook-a7jkrj-0 ] && [ "$(id -u)" -eq 1000 ] || exit 11
[ "$(realpath -e "$(dirname "$out")")" = "$(dirname "$out")" ]
[ ! -e "$out" ] && [ ! -L "$out" ] || exit 12
mkdir -- "$out"
printf '%s\n' "$$" >"$out/launcher.pid"
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 7200s "$python" -I -S -B "${args[@]}" >"$out/launch.log" 2>&1
rc=$?
set -e
printf '%s\n' "$rc" >"$out/exit_code.txt"
exit "$rc"
