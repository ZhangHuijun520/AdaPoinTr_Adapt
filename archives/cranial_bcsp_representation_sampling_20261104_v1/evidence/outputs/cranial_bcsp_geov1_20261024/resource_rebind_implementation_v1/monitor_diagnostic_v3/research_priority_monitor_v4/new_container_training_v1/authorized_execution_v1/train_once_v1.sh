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
export MPLCONFIGDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/mplconfig
export CUDA_CACHE_DISABLE=1
export TMPDIR=/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/tmp
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_v3/training_execution_request_v1.json | cut -d ' ' -f 1)" = 5cf2b4f93eb903c77702e9b493a8e8dd2700ceda448d77ea518ecc4c76e9ee0c ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_v3/training_authorization_v1.json | cut -d ' ' -f 1)" = 28fa91cc547a0cb469b5bbdc7cd7afac4e877b80fd5ae74f3801575e4a142313 ] || exit 65
[ "$(sha256sum -- /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_v3/training_runtime_v1.json | cut -d ' ' -f 1)" = d41b37a083255ad5e5f758575ca4f55de8a338f6311fc41256b174bcfb98843e ] || exit 65
mkdir -- /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3 || exit 73
[ -d /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3 ] && [ ! -L /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3 ] || exit 73
set +e
/usr/bin/timeout --signal=TERM --kill-after=5s 86400s /opt/conda/envs/adapointr-mamba/bin/python3.10 -I -S -B /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_entry_research_v5.py --request /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_v3/training_execution_request_v1.json --request-sha256 5cf2b4f93eb903c77702e9b493a8e8dd2700ceda448d77ea518ecc4c76e9ee0c --authorization /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_v3/training_authorization_v1.json --authorization-sha256 28fa91cc547a0cb469b5bbdc7cd7afac4e877b80fd5ae74f3801575e4a142313 --runtime /home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_train_v3/training_runtime_v1.json --runtime-sha256 d41b37a083255ad5e5f758575ca4f55de8a338f6311fc41256b174bcfb98843e > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/launch.log 2>&1
training_rc=$?
printf '%s\n' "$training_rc" > /home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/b0_foldC_in8192_out8192_seed0_train_v3/exit_code.txt
save_rc=$?
[ "$save_rc" -eq 0 ] || exit 74
exit "$training_rc"
