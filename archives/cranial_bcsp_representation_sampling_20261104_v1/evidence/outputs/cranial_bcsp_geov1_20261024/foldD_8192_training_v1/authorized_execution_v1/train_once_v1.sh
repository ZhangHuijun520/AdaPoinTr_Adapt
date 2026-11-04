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
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in8192_out8192_seed0_train_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in8192_out8192_seed0_train_v1/tmp
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_8192_v1/training_execution_request_v1.json | cut -d ' ' -f 1)" = f5aea291adc26546fe5d8dc52c09649492115321cf583d555dca8463ee9b545c ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_8192_v1/training_authorization_v1.json | cut -d ' ' -f 1)" = ae6bbed0ae5b29fc54c96e96b61ed3252e15db74c5b0c2ddd0c595d06b621515 ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_8192_v1/training_runtime_v1.json | cut -d ' ' -f 1)" = 823b12b23c875e4c30fb0baa2d6021307ae9321c5ba0fcfc6978a3ea2a269b15 ] || exit 65
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in8192_out8192_seed0_train_v1 || exit 73
[ -d /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in8192_out8192_seed0_train_v1 ] && [ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in8192_out8192_seed0_train_v1 ] || exit 73
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_entry_foldD_8192_v7.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_8192_v1/training_execution_request_v1.json --request-sha256 f5aea291adc26546fe5d8dc52c09649492115321cf583d555dca8463ee9b545c --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_8192_v1/training_authorization_v1.json --authorization-sha256 ae6bbed0ae5b29fc54c96e96b61ed3252e15db74c5b0c2ddd0c595d06b621515 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldD_8192_v1/training_runtime_v1.json --runtime-sha256 823b12b23c875e4c30fb0baa2d6021307ae9321c5ba0fcfc6978a3ea2a269b15 > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in8192_out8192_seed0_train_v1/launch.log 2>&1
training_rc=$?
printf '%s\n' "$training_rc" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldD_in8192_out8192_seed0_train_v1/exit_code.txt
save_rc=$?
[ "$save_rc" -eq 0 ] || exit 74
exit "$training_rc"
