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
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v2/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v2/tmp
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v2/training_execution_request_v1.json | cut -d ' ' -f 1)" = 32c1dad0c6150a11faeab65436c20c7192e762722b74b06ce91b7fd0dd90a9e3 ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v2/training_authorization_v1.json | cut -d ' ' -f 1)" = 34bd55fc56bd89e665d3bdfaff83f1178aaba4dc2283d7fa6421b7619120d126 ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v2/training_runtime_v1.json | cut -d ' ' -f 1)" = 2c8089e54d83f6b1291746df15906a0403dea0257cf1c3e800e6aabb5f37c654 ] || exit 65
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v2 || exit 73
[ -d /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v2 ] && [ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v2 ] || exit 73
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_entry_foldC_16384_v6.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v2/training_execution_request_v1.json --request-sha256 32c1dad0c6150a11faeab65436c20c7192e762722b74b06ce91b7fd0dd90a9e3 --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v2/training_authorization_v1.json --authorization-sha256 34bd55fc56bd89e665d3bdfaff83f1178aaba4dc2283d7fa6421b7619120d126 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_foldC_16384_v2/training_runtime_v1.json --runtime-sha256 2c8089e54d83f6b1291746df15906a0403dea0257cf1c3e800e6aabb5f37c654 > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v2/launch.log 2>&1
training_rc=$?
printf '%s\n' "$training_rc" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in16384_out8192_seed0_train_v2/exit_code.txt
save_rc=$?
[ "$save_rc" -eq 0 ] || exit 74
exit "$training_rc"
