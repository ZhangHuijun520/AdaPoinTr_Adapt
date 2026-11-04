#!/usr/bin/env bash
set -u
set -o pipefail
set -o noclobber
umask 077
cd /home/jovyan/adapointr_work/PoinTr || exit 65
export CUDA_VISIBLE_DEVICES=GPU-e763d389-b4c2-4dc8-9571-d7343ec328b1
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export OMP_NUM_THREADS=2
export MKL_NUM_THREADS=2
export OPENBLAS_NUM_THREADS=2
export PYTHONDONTWRITEBYTECODE=1
export MPLBACKEND=Agg
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in16384_out8192_seed0_train_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in16384_out8192_seed0_train_v1/tmp
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_16384_v1/training_execution_request_v1.json | cut -d ' ' -f 1)" = 054fb1f9cd33712058ff888c3bf097a59c7a86d7210b39f421acb361422a7741 ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_16384_v1/training_authorization_v1.json | cut -d ' ' -f 1)" = 339997b4ac96cb12a58ecd3e6dffaa3219887565fc3d06b6c3b2ed9d83a4bad3 ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_16384_v1/training_runtime_v1.json | cut -d ' ' -f 1)" = b178e74446ff5352e81d0dda82ba731dafe40edb3596a6138b578525b4dc512a ] || exit 65
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in16384_out8192_seed0_train_v1 || exit 73
[ -d /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in16384_out8192_seed0_train_v1 ] && [ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in16384_out8192_seed0_train_v1 ] || exit 73
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_entry_foldD_16384_v8.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_16384_v1/training_execution_request_v1.json --request-sha256 054fb1f9cd33712058ff888c3bf097a59c7a86d7210b39f421acb361422a7741 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_16384_v1/training_authorization_v1.json --authorization-sha256 339997b4ac96cb12a58ecd3e6dffaa3219887565fc3d06b6c3b2ed9d83a4bad3 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_16384_v1/training_runtime_v1.json --runtime-sha256 b178e74446ff5352e81d0dda82ba731dafe40edb3596a6138b578525b4dc512a > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in16384_out8192_seed0_train_v1/launch.log 2>&1
training_rc=$?
printf '%s\n' "$training_rc" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in16384_out8192_seed0_train_v1/exit_code.txt
save_rc=$?
[ "$save_rc" -eq 0 ] || exit 74
exit "$training_rc"
