"""Fixed read-only assets/data-byte readiness; no imports/providers/NPZ decoding on server."""
import hashlib,json,shlex,subprocess,time
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;R=S.parents[2];O=S/'server_readiness_v1'
base=json.loads((R/'outputs/cranial_bcsp_mamba_p1_20261104/M0_training_entry_v2/transport_payload/M0_foldC_seed0_training_execution_request_v1.json').read_bytes())
cuda=json.loads((S.parent/'H2_cuda_admission_v1/H2_artificial_cuda_execution_request_v1.json').read_bytes())
scope=json.loads((R/'outputs/cranial_bcsp_geov1_20261024/actual_proxy_trace_20261102_v1/observed_server_frozen_scope_v3.json').read_bytes())
project='/home/jovyan/adapointr_work/PoinTr';install=project+'/third_party/bcsp_p2_H2_AUX_foldC_20261107_v1';output=project+'/logs/cranial_bcsp_mamba_p2/H2_AUX_foldC_seed0_20261107_v1'
records={}
def add(r):
 if r['path'] in records:assert records[r['path']]==r
 else:records[r['path']]={k:r[k] for k in ['path','bytes','sha256']}
for k,r in base['implementation'].items():
 if k not in ('entry','runtime'):add(r)
for k in ['static_config','order_plan','initialization_reference','preflight_scope','numeric_policy','pair_contract']:add(base[k])
for r in base['dependencies']+scope['bindings']['provider']+scope['bindings']['environment_metadata']:add(r)
for r in [base['QC']['qualified_receipt'],base['QC']['verification'],base['QC']['fold_binding'],*base['QC']['manifests'].values()]:add(r)
for key,rel in [('candidate','relative_target'),('isolated_model_project_sources','relative_path')]:
 for r in scope['bindings'][key]:add(dict(path=str(PurePosixPath(base['model_root'])/r[rel]),bytes=r['bytes'],sha256=r['sha256']))
O.mkdir();start=time.monotonic();commands=[]
def emit(n,v):
 with (O/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
def call(label,cmd):
 assert len(cmd.encode())<=2048 and time.monotonic()-start<300
 commands.append(dict(label=label,command=cmd,bytes=len(cmd.encode())))
 emit('command_'+str(len(commands)).zfill(2)+'.json',commands[-1])
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',cmd],capture_output=True,timeout=40)
 for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
  with (O/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 assert p.returncode==0,(label,p.returncode,p.stderr[:512])
 print(json.dumps(dict(stage=label,returncode=0,stdout_bytes=len(p.stdout))),flush=True)
 return p.stdout.decode().replace('\r','')
def hashes(text):
 d={}
 for line in text.splitlines():
  h,p=line.split(None,1);p=p.strip();assert len(h)==64 and p not in d;d[p]=h
 return d
try:
 emit('frozen_scope_before_calls_v1.json',dict(identity=cuda['identity'],asset_records=list(records.values()),asset_bytes=sum(r['bytes'] for r in records.values()),maximum_wall_seconds=300,per_call_timeout_seconds=30,maximum_command_bytes=2048,data_root=base['data_root'],payload_policy='Only fixed315 train NPZ byte hashing after exact directory filename/type set; no array decode',targets_must_be_absent=[install,output],server_writes=0))
 prefix='test "$(hostname)" = '+shlex.quote(cuda['identity']['hostname'])+' && test "$(id -u)" = 1000 && '
 resource=call('identity_resources',prefix+'hostname && id -u && nvidia-smi --query-gpu=uuid,name,driver_version,memory.total,memory.used --format=csv,noheader,nounits && df -B1 --output=avail /home/jovyan && test ! -e '+install+' && test ! -L '+install+' && test ! -e '+output+' && test ! -L '+output)
 lines=resource.splitlines();gpu=[s.strip() for s in lines[2].split(',')];I=cuda['identity']
 assert gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256
 free=int(lines[-1].strip());assert free>=4294967296
 groups=[];group=[]
 for p in records:
  if len(('sha256sum '+' '.join(map(shlex.quote,group+[p]))).encode())>1800:groups.append(group);group=[]
  group.append(p)
 if group:groups.append(group)
 actual={}
 for i,g in enumerate(groups):actual.update(hashes(call('asset_hash_'+str(i),'sha256sum '+' '.join(map(shlex.quote,g)))))
 assert set(actual)==set(records) and all(actual[p]==r['sha256'] for p,r in records.items()),'asset hash drift'
 # stat/link metadata for every frozen file, no broad tree scan.
 for i,g in enumerate(groups):
  text=call('asset_stat_'+str(i),"stat -c '%F|%s|%n' -- "+' '.join(map(shlex.quote,g)))
  for line in text.splitlines():
   typ,size,path=line.split('|',2);assert typ=='regular file' and int(size)==records[path]['bytes'],path
 G=R/'outputs/cranial_bcsp_geov1_20261024'
 rows=[json.loads(x) for x in (G/'real_data_qc_v1/manifest_8192.jsonl').read_text().splitlines()]
 fold=json.loads((G/'consolidated_binding_v1/fold_binding.json').read_bytes())['folds']['C'];ids=set(fold['train_case_ids'])
 expected={r['point_path'].removeprefix('points/'):r['sha256'] for r in rows if r['case_id'] in ids};assert len(expected)==315
 points=base['data_root']+'/points'
 listing=call('training_point_names',prefix+'cd '+shlex.quote(points)+" && find . -mindepth 1 -maxdepth 1 -printf '%y %f\\n' | sort")
 assert {x[2:] for x in listing.splitlines()}==set(expected) and all(x.startswith('f ') for x in listing.splitlines()),'exact regular315 file set'
 ph=hashes(call('training_point_hashes',prefix+'cd '+shlex.quote(points)+" && find . -maxdepth 1 -type f -print0 | sort -z | xargs -0 sha256sum"))
 assert ph=={'./'+p:h for p,h in expected.items()},'315 point hashes'
 # Exact original initialization metadata is downloaded, not a checkpoint.
 D=O/'metadata';D.mkdir();r=base['initialization_reference'];target=D/'M0_construction.json'
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','get',r['path'],p.stdout.decode().strip()],capture_output=True,timeout=35)
 for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
  with (O/('get_initialization_'+k+'.bin')).open('xb') as f:f.write(b)
 assert p.returncode==0 and target.stat().st_size==r['bytes'] and hashlib.sha256(target.read_bytes()).hexdigest()==r['sha256']
 ev=json.loads(target.read_bytes());assert ev['factory']['variant']=='M0' and not ev['factory']['artificial_fixture']
 emit('readiness_receipt_v1.json',dict(status='BOUNDED_H2_AUX_C_READINESS_PASS',identity=I,training_payloads=315,training_payload_hashes=ph,assets=list(records.values()),all_hashes_and_sizes_match=True,original_initialization_metadata_matches=True,GPU_used_MiB=int(gpu[4]),free_disk_bytes=free,install_and_output_absent=True,seconds=time.monotonic()-start,server_writes=0,forward=0,checkpoint_loads=0,NPZ_arrays_decoded=0,limitations=['Point semantic limitations inherited from frozen QC','Readiness snapshot is not exclusive resource reservation','Per-step monitoring is not cgroup hard isolation','CUDA eval/autograd admission is not batch8 training-mode stability proof']))
 print('BOUNDED_H2_AUX_C_READINESS_PASS',flush=True)
except BaseException as exc:
 emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),seconds=time.monotonic()-start));raise
