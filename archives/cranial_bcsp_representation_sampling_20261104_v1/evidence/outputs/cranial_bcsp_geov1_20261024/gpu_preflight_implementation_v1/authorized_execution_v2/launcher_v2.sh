#!/bin/bash
# Frozen single-use execution of request 18432038d32c4857452c96f0795dd4b072a57fa9d38916cf87e10e8215700bc7.
set -euo pipefail
umask 077
cd -- '/home/jovyan/adapointr_work/PoinTr'
'/opt/conda/envs/adapointr-mamba/bin/python3.10' -I -S -B - <<'PY'
import hashlib,json,os,socket,sys
from pathlib import Path
H="18432038d32c4857452c96f0795dd4b072a57fa9d38916cf87e10e8215700bc7"
rp=Path("/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v2/evidence/execution_request_v2.json")
assert hashlib.sha256(rp.read_bytes()).hexdigest()==H,'request hash'
q=json.loads(rp.read_text(encoding='utf-8'))
assert socket.gethostname()==q['identity']['hostname'] and os.getuid()==q['identity']['uid'],'identity'
assert Path.cwd()==Path(q['identity']['project']),'working directory'
assert str(Path(sys.executable).resolve())==q['identity']['python_realpath'],'interpreter'
for r in q['future_limited_deployment']['files']:
 p=Path(r['server_target']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],str(p)
a=Path(q['future_control_paths']['authorization']);t=Path(q['future_control_paths']['runtime'])
for p in (rp,a,t):assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
auth=json.loads(a.read_text(encoding='utf-8'));runtime=json.loads(t.read_text(encoding='utf-8'))
assert auth=={"schema":"bcsp-preflight-authorization-v1","request_sha256":"18432038d32c4857452c96f0795dd4b072a57fa9d38916cf87e10e8215700bc7","explicit_user_authorization":True,"user_authorization_text":"**单独授权 v2 request 对应的限定部署与唯一一次人工 GPU preflight**。"}
assert runtime=={'schema':'bcsp-preflight-runtime-v1','request_sha256':H,'authorization_sha256':hashlib.sha256(a.read_bytes()).hexdigest()}
assert hashlib.sha256(a.read_bytes()).hexdigest()=="596b4758ff481071f40b9b09c914134ae71d52f7dbd4d9f7c0665e4c728c0cbd",'authorization hash'
m=Path(q['future_control_paths']['attempt_marker'])
assert m.is_file() and not m.is_symlink(),'attempt marker'
marker=json.loads(m.read_text(encoding='utf-8'))
assert marker['request_sha256']==H and marker['status']=='CLAIMED_BEFORE_TMUX','attempt identity'
out=Path(q['future_control_paths']['summary']).parent
assert not out.exists() and not any(x.is_symlink() for x in (out,*out.parents)),'fresh output'
print('LAUNCHER_BINDINGS_PASS',flush=True)
PY
mkdir -p -- '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1'
mkdir -- '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/artificial_gpu_zero_update_v2'
set -C
exec > '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/artificial_gpu_zero_update_v2/launch.log' 2>&1
record_exit() {
  rc=$?
  trap - EXIT
  set -C
  printf '%s\n' "$rc" > '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/artificial_gpu_zero_update_v2/exit_code.txt' || exit 125
  exit "$rc"
}
trap record_exit EXIT
export CUDA_VISIBLE_DEVICES='GPU-2f32f6fb-ea5d-730a-4ea2-2f6063e31065'
export CUBLAS_WORKSPACE_CONFIG=':4096:8'
export OMP_NUM_THREADS='2'
export MKL_NUM_THREADS='2'
export OPENBLAS_NUM_THREADS='2'
export PYTHONDONTWRITEBYTECODE='1'
export MPLBACKEND='Agg'
export MPLCONFIGDIR='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/artificial_gpu_zero_update_v2/mplconfig'
export CUDA_CACHE_DISABLE='1'
export TMPDIR='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/artificial_gpu_zero_update_v2/tmp'
printf 'BCSP_SINGLE_ATTEMPT_START %s\n' "$(date -Is)"
set +e
'/usr/bin/timeout' '--signal=TERM' '--kill-after=5s' '900s' '/opt/conda/envs/adapointr-mamba/bin/python3.10' '-I' '-S' '-B' '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v2/bcsp_artificial_gpu_preflight_v2.py' '--request' '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v2/evidence/execution_request_v2.json' '--request-sha256' '18432038d32c4857452c96f0795dd4b072a57fa9d38916cf87e10e8215700bc7' '--authorization' '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v2/control/authorization_v2.json' '--runtime' '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v2/control/runtime_v2.json' '--scope' '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v2/evidence/frozen_scope_v2.json'
rc=$?
set -e
exit "$rc"
