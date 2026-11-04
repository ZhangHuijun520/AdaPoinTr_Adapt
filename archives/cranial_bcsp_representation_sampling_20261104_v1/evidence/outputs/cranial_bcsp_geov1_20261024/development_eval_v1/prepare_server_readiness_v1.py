"""Freeze one finite read-only readiness payload; does not invoke the client."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parent;B=N.parent
q=json.loads((B/'foldD_16384_training_v1/training_entry_request_v1.json').read_bytes())
index=json.loads((N/'development_input_index_v1.json').read_bytes())
scope=json.loads((B/'gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json').read_bytes())
records=[r['input'] for r in index['inputs']]+[r['checkpoint'] for r in index['runs']]+[q['static_config'],q['QC']['fold_binding'],q['preflight_scope'],q['implementation']['preflight_helper']]
root=Path(q['model_root']).as_posix()
for r in scope['bindings']['candidate']:records.append(dict(path=root+'/'+r['relative_target'],bytes=r['bytes'],sha256=r['sha256']))
for r in scope['bindings']['isolated_model_project_sources']:records.append(dict(path=root+'/'+r['relative_path'],bytes=r['bytes'],sha256=r['sha256']))
records+=scope['bindings']['provider']+scope['bindings']['environment_metadata']
records.append(dict(path=root+'/base_model.yaml',bytes=scope['bindings']['base_config']['bytes'],sha256=scope['bindings']['base_config']['sha256']))
base='/home/jovyan/adapointr_work/PoinTr';code=base+'/third_party/bcsp_geov1_training_foldc_8192_seed0_v1'
targets=[code+'/bcsp_development_predict_v1.py',code+'/evidence/development_input_index_v1.json',code+'/control_eval_four_models_v1',base+'/logs/cranial_bcsp_geov1/development_four_models_seed0_v1']
spec=dict(identity=q['identity'],files=records,absent_targets=targets,limits=dict(read_bytes=2147483648,wall_seconds=90,file_count=480),CUDA_calls=0,checkpoint_deserialization=False,server_writes=0)
with (N/'server_readiness_scope_v1.json').open('x') as f:json.dump(spec,f,indent=2)
source='SPEC='+repr(spec)+'''\nimport hashlib,json,os,shutil,socket,subprocess,time
from pathlib import Path
start=time.monotonic();total=0;checked=[]
try:
 assert socket.gethostname()==SPEC['identity']['hostname'] and os.getuid()==SPEC['identity']['uid'],'container identity'
 os.chdir('/home/jovyan/adapointr_work/PoinTr')
 assert len(SPEC['files'])<=SPEC['limits']['file_count']
 for r in SPEC['files']:
  p=Path(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file() and p.stat().st_size==r['bytes'],str(p)
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):
    total+=len(b);assert total<=SPEC['limits']['read_bytes'] and time.monotonic()-start<=SPEC['limits']['wall_seconds'],'read/time budget';h.update(b)
  assert h.hexdigest()==r['sha256'],'hash '+str(p)
  checked.append(r)
 for target in SPEC['absent_targets']:
  p=Path(target);assert not any(x.is_symlink() for x in (p,*p.parents)) and not p.exists(),'occupied target '+target
  assert p.parent.is_dir(),'missing parent '+str(p.parent)
 gpu=subprocess.run(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.decode().strip()
 fields=[x.strip() for x in gpu.split(',')];i=SPEC['identity']
 assert fields[:4]==[i['gpu_uuid'],i['gpu_name'],i['driver_version'],str(i['nvidia_smi_memory_total_MiB'])],'GPU identity'
 pids=subprocess.run(['/usr/bin/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.decode().strip()
 assert int(fields[4])<=256 and not pids,'GPU not idle'
 free=shutil.disk_usage('/home/jovyan/adapointr_work/PoinTr').free;assert free>=4294967296,'disk'
 print(json.dumps(dict(status='FOUR_MODEL_DEVELOPMENT_READINESS_PASS',hostname=socket.gethostname(),uid=os.getuid(),files=checked,targets_absent=SPEC['absent_targets'],GPU=gpu,free_disk_bytes=free,read_bytes=total,seconds=time.monotonic()-start,checkpoint_deserialization=False,CUDA_calls=0,server_writes=0)))
except BaseException as exc:
 print(json.dumps(dict(status='READINESS_FAILED_STOP',error=repr(exc),checked_files=len(checked),read_bytes=total,seconds=time.monotonic()-start,server_writes=0)));raise
'''
compile(source,'frozen_readonly_readiness','exec')
with (N/'server_readiness_payload_v1.py').open('x') as f:f.write(source)
template=B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py'
t=template.read_bytes();assert hashlib.sha256(t).hexdigest()=='c705224bc0ffa2e094ff0b4a69ed4ba582480178a63a2bb3fa2e91757e31fd26'
with (N/'server_readiness_short_driver_v1.py').open('xb') as f:f.write(t.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',hashlib.sha256(source.encode()).hexdigest().encode()))
