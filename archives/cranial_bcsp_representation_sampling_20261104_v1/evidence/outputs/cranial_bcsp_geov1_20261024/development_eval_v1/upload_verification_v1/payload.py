SPEC={'request_sha256': '85de7ec1c3f33e88009a177b2dd9532233f3da183df635fc15167079e0de12ea', 'identity': {'hostname': 'shu-common-25721452-notebook-01dt08-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-e763d389-b4c2-4dc8-9571-d7343ec328b1', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '570.190', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.'}, 'upload': {'path': '/home/jovyan/bcsp_four_model_development_eval_v1.tar.gz', 'bytes': 31808, 'sha256': '87160bb7ec986d6b813098a5ffaf12a54da0d27d27a155fc1d1221ef101cd047'}, 'members': [{'member': 'bcsp_development_predict_v1.py', 'target': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_development_predict_v1.py', 'bytes': 14497, 'sha256': '1728c72eebb9548ceb9a3ce272dc01a5f8358e40d9e07020f724d65b20fefc6e'}, {'member': 'development_input_index_v1.json', 'target': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/development_input_index_v1.json', 'bytes': 208927, 'sha256': '7fbae8f119757dad3d4c3195a53b75a7f023eb1af6242a752e5d30da3a8f5b8e'}], 'targets': ['/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_development_predict_v1.py', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/development_input_index_v1.json', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/control_eval_four_models_v1', '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/development_four_models_seed0_v1'], 'limits': {'wall_seconds': 30, 'archive_bytes': 1048576, 'member_bytes': 1048576}, 'server_writes': 0, 'model_calls': 0}
import datetime,hashlib,json,os,socket,tarfile,time
from pathlib import Path
start=time.monotonic()
try:
 assert socket.gethostname()==SPEC['identity']['hostname'] and os.getuid()==SPEC['identity']['uid'],'current container identity mismatch'
 p=Path(SPEC['upload']['path'])
 assert not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file(),'archive type/link'
 assert p.stat().st_size==SPEC['upload']['bytes']<=SPEC['limits']['archive_bytes'],'archive size'
 raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==SPEC['upload']['sha256'],'archive SHA256'
 members=[]
 with tarfile.open(p,'r:gz') as t:
  items=t.getmembers();assert len(items)==2 and len({x.name for x in items})==2,'member count/duplicates'
  assert {x.name for x in items}=={r['member'] for r in SPEC['members']},'exact member names'
  for r in SPEC['members']:
   m=t.getmember(r['member']);assert m.isfile() and m.size==r['bytes']<=SPEC['limits']['member_bytes'],'member type/size'
   data=t.extractfile(m).read();assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],'member SHA256'
   members.append(dict(member=m.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
 assert p.stat().st_size==len(raw) and hashlib.sha256(p.read_bytes()).hexdigest()==SPEC['upload']['sha256'],'archive changed during check'
 targets=[]
 for name in SPEC['targets']:
  target=Path(name);assert not any(x.is_symlink() for x in (target,*target.parents)),'target parent/link'
  targets.append(dict(path=name,exists=target.exists(),parent_exists=target.parent.is_dir()))
 assert time.monotonic()-start<=SPEC['limits']['wall_seconds'],'read-only budget'
 print(json.dumps(dict(status='UPLOAD_VERIFIED_READONLY_PASS',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),hostname=socket.gethostname(),uid=os.getuid(),archive=SPEC['upload'],members=members,targets=targets,request_sha256=SPEC['request_sha256'],seconds=time.monotonic()-start,server_writes=0,installed_files=0,model_calls=0,execution_authorized=False)))
except BaseException as exc:
 print(json.dumps(dict(status='UPLOAD_VERIFY_FAILED_STOP',error=repr(exc),server_writes=0,model_calls=0)));raise
