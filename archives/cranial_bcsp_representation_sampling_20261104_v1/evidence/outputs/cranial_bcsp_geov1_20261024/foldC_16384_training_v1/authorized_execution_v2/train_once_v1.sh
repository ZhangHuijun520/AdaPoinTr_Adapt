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
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1/tmp
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v1/training_execution_request_v1.json | cut -d ' ' -f 1)" = 847ccee79e6a29241c7f0b5c8f67d790f856014fe24c75a2123b234c337a8404 ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v1/training_authorization_v1.json | cut -d ' ' -f 1)" = 64fcc5a83c271f9534fc168cd37ad128fb41ba6b7c3ead5507710d4add2d820e ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v1/training_runtime_v1.json | cut -d ' ' -f 1)" = 91f5431a4b6842f051b6f7f7e2f570cd8daaaaa8cf944ba2ead8d35dd35d06d6 ] || exit 65
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1 || exit 73
[ -d /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1 ] && [ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1 ] || exit 73
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_entry_research_v5.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v1/training_execution_request_v1.json --request-sha256 847ccee79e6a29241c7f0b5c8f67d790f856014fe24c75a2123b234c337a8404 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v1/training_authorization_v1.json --authorization-sha256 64fcc5a83c271f9534fc168cd37ad128fb41ba6b7c3ead5507710d4add2d820e --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v1/training_runtime_v1.json --runtime-sha256 91f5431a4b6842f051b6f7f7e2f570cd8daaaaa8cf944ba2ead8d35dd35d06d6 > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1/launch.log 2>&1
training_rc=$?
printf '%s\n' "$training_rc" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v1/exit_code.txt
save_rc=$?
[ "$save_rc" -eq 0 ] || exit 74
exit "$training_rc"
