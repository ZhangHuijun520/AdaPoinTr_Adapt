#!/bin/bash
set -eu
umask 077
[ "$#" -eq 3 ]
project=/home/USER/adapointr_work/PoinTr
install=$project/third_party/bcsp_oasg_sf_native_20261125_hwk2fy_v2
out=$project/logs/cranial_bcsp_fullmamba/OASG_SF_seed2026112102_native_20261125_hwk2fy_v2
cd "$project"
export CUDA_VISIBLE_DEVICES=GPU-4d777f4d-1445-fddb-2761-49fdd667fd17
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1 CUDA_CACHE_DISABLE=1
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 MPLBACKEND=Agg
export TMPDIR="$out/tmp" XDG_CACHE_HOME="$out/cache" MPLCONFIGDIR="$out/mplconfig"
export TRITON_CACHE_DIR="$out/triton" HF_HOME="$out/hf"
python=/opt/conda/envs/adapointr-mamba/bin/python3.10
args=("$install/oasg_sf_native_v2.py"
      --request "$install/OASG_SF_native_execution_request_v2.json" --request-sha256 "$1"
      --authorization "$install/authorization_v1.json" --authorization-sha256 "$2"
      --runtime "$install/runtime_v1.json" --runtime-sha256 "$3"
      --launcher "$install/launch_oasg_sf_native_once_v2.sh")
[ "$(hostname)" = notebook-hwk2fy-0 ] && [ "$(id -u)" -eq 1000 ] || exit 11
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
