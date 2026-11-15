"""One batch of four bounded readonly WebShell calls; no remote writes or numerical imports."""
from pathlib import Path,PurePosixPath
import ast,base64,hashlib,json,shlex,subprocess,sys,zlib
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_dac_r01_preparation_20261115_v1';O=B/'server_readiness_v2'
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
O.mkdir(exist_ok=True)
qp=B/'pending_request_v1/SCQ_DAC_R1_execution_request_v1.json';assert digest(qp)=='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8';q=json.loads(qp.read_bytes())
mapping=json.loads((B/'pending_request_v1/candidate_no_overwrite_install_mapping_v1.json').read_bytes())['files'];rows=json.loads((B/'selected20_cases_v1.json').read_bytes())['cases']
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1'
targets=[str(PurePosixPath(r['remote']).relative_to(remote)) for r in mapping];assert len(targets)==28
ids=[(r['run'],r['case_id']) for r in rows]
common='''from pathlib import Path
import os,socket,hashlib,json,time,subprocess,shutil,ast
T=time.monotonic();used=0;seen={};last=None
P=Path('/home/jovyan/adapointr_work/PoinTr')
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
def clean(p):
 p=Path(p);assert p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),str(p);return p
def exact(r):
 global used,last
 p=clean(r['path']);last=str(p)
 if str(p) in seen:
  assert (r['bytes'],r['sha256'])==(seen[str(p)]['bytes'],seen[str(p)]['sha256']);return p
 s=p.stat();assert p.is_file() and s.st_size==r['bytes'],str(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):
   used+=len(b);assert used<=805306368 and time.monotonic()-T<55;h.update(b)
 assert h.hexdigest()==r['sha256'],str(p)
 assert (s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)
 seen[str(p)]={'path':str(p),'bytes':r['bytes'],'sha256':r['sha256']};assert len(seen)<=96;return p
old=P/'third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json'
q=json.loads(exact(dict(path=str(old),bytes=18606,sha256='5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9')).read_bytes())
'''
identity=common+'''
g=subprocess.run(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10)
assert g.returncode==0,g.stderr
gpu=[x.strip() for x in g.stdout.strip().split(',')];I=q['identity']
assert gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256
version=subprocess.run([I['python_realpath'],'-I','-S','-B','--version'],capture_output=True,text=True,timeout=5)
assert version.returncode==0 and version.stdout.strip()=='Python '+I['python_version']
assert clean(P).is_dir() and P.resolve()==P and clean(P/'third_party').is_dir()
new=clean(P/'third_party/bcsp_scq_dac_r1_20261115_v1');out=clean(P/'logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1')
targets='''+repr(targets)+'''
assert not new.exists() and not out.exists()
for rel in targets:assert not clean(new/rel).exists()
tm=subprocess.run(['tmux','list-sessions','-F','#{session_name}'],capture_output=True,text=True,timeout=5)
assert tm.returncode in (0,1) and 'bcsp_scq_dac_r1_frozen20_20261115_v1' not in tm.stdout.splitlines()
mem={k:int(v.split()[0])*1024 for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines()) if k in ('MemTotal','MemAvailable')}
free=shutil.disk_usage(P).free;assert free>=4294967296+982218001
print(json.dumps(dict(status='IDENTITY_RESOURCE_AND28_ABSENT_TARGETS_PASS',hostname=socket.gethostname(),uid=os.getuid(),GPU=gpu,python=version.stdout.strip(),free_disk_bytes=free,host_memory=mem,new_root=str(new),absent_targets=[str(new/x) for x in targets],output_absent=True,seconds=time.monotonic()-T,server_writes=0,CUDA_contexts=0)))
'''
code=common+'''
records=list(q['implementation'].values())+[q[k] for k in ('entry','helper','static_config','preflight_scope','initialization','rf_initialization','input_index')]+q['dependencies']
for r in records:exact(r)
s=json.loads(Path(q['preflight_scope']['path']).read_bytes());b=s['bindings'];root=Path(q['model_root'])
for r in b['candidate']:exact(dict(r,path=str(root/r['relative_target'])))
for r in b['isolated_model_project_sources']:exact(dict(r,path=str(root/r['relative_path'])))
exact(dict(b['base_config'],path=str(root/'base_model.yaml')))
for r in b['provider']+b['environment_metadata']:exact(r)
v=dict(link='/usr/share/zoneinfo/UTC',link_text='Etc/UTC',target='/usr/share/zoneinfo/Etc/UTC',bytes=118,sha256='ab1ddb33c7187e56408033a8165ea3b1432e024710e7ab2aafec036a8bd7f09a')
assert Path(v['link']).is_symlink() and os.readlink(v['link'])==v['link_text'] and str(Path(v['link']).resolve())==v['target']
assert not any(p.is_symlink() for p in Path(v['link']).parents);exact(dict(path=v['target'],bytes=v['bytes'],sha256=v['sha256']))
print(json.dumps(dict(status='FROZEN_CODE_PROVIDER_AND_EXACT_DEPENDENCIES_PASS',records=list(seen.values()),hashed_bytes=used,UTC_contract=v,seconds=time.monotonic()-T,package_imports=0,server_writes=0)))
'''
inputs=common+'''
index=json.loads(exact(q['input_index']).read_bytes());wanted=set('''+repr(ids)+''')
rows=[r for r in index['inputs'] if (r['run'],r['case_id']) in wanted]
assert len(rows)==20 and {(r['run'],r['case_id']) for r in rows}==wanted
for r in rows:exact(r['input'])
print(json.dumps(dict(status='EXACT20_INPUT_BYTES_HASHES_PASS_NO_NPZ_DECODE',records=list(seen.values()),rows=[{k:r[k] for k in ('run','fold','case_id','input','normalization')} for r in rows],hashed_bytes=used,seconds=time.monotonic()-T,NPZ_decodes=0,server_writes=0)))
'''
commands=[]
pre,post=identity.split('\ntargets=',1)
resource_tail='\ntm='+post.split('\ntm=',1)[1]
resource_tail=resource_tail.replace(',absent_targets=[str(new/x) for x in targets]','')
resource_tail=resource_tail.replace('IDENTITY_RESOURCE_AND28_ABSENT_TARGETS_PASS','IDENTITY_RESOURCE_PASS').replace(',output_absent=True','')
identity_resources=pre+resource_tail
target_only=common+"\nnew=clean(P/'third_party/bcsp_scq_dac_r1_20261115_v1');out=clean(P/'logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1')\ntargets="+repr(targets)+"\nassert not new.exists() and not out.exists()\nfor rel in targets:assert not clean(new/rel).exists()\nprint(json.dumps(dict(status='ALL28_TARGETS_AND_NEW_ROOT_ABSENT',absent_targets=[str(new/x) for x in targets],output_absent=True,server_writes=0)))\n"
for label,codeblock in [('identity_targets',identity_resources),('target_absence',target_only),('frozen_sources_provider',code),('twenty_inputs',inputs)]:
 ast.parse(codeblock);blob=base64.b85encode(zlib.compress(codeblock.encode(),9)).decode();wrapper='import base64,zlib;exec(zlib.decompress(base64.b85decode('+repr(blob)+')))'
 command=shlex.join(['/usr/bin/python3','-I','-S','-B','-c',wrapper]);assert len(command.encode())<=2048,(label,len(command.encode()))
 commands.append((label,command));sourcefile=O/(label+'_readonly_source.py')
 if sourcefile.exists():assert sourcefile.read_text(encoding='utf-8')==codeblock
 else:sourcefile.write_text(codeblock,encoding='utf-8')
frozen=dict(status='FROZEN_BEFORE_CONNECTION',request_sha256=digest(qp),calls=[dict(phase=k,command_bytes=len(v.encode()),timeout_seconds=60) for k,v in commands],file_limit_per_call=96,hash_byte_limit_per_call=805306368,server_writes=0,model_imports=0,targets=28,inputs=20)
if (O/'frozen_call_scope_v1.json').exists():assert json.loads((O/'frozen_call_scope_v1.json').read_bytes())==frozen
else:save(O/'frozen_call_scope_v1.json',frozen)
if sys.argv[1:]!=['--execute']:print('FROZEN; no connection');raise SystemExit(0)
save(O/'readonly_batch_claim_v1.json',dict(status='ONE_READONLY_BATCH_CLAIMED',automatic_retry=False,request_sha256=digest(qp)))
answers={}
for label,command in commands:
 print(label,flush=True)
 try:x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--',command],capture_output=True,timeout=75)
 except subprocess.TimeoutExpired as exc:
  save(O/'failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',phase=label,error='local transport timeout',server_writes=0));raise
 for name,data in [('stdout',x.stdout),('stderr',x.stderr)]:
  with (O/(label+'_'+name+'.bin')).open('xb') as f:f.write(data)
 if x.returncode:
  save(O/'failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',phase=label,returncode=x.returncode,stdout=x.stdout.decode(errors='replace')[-2400:],stderr=x.stderr.decode(errors='replace')[-2400:],server_writes=0));raise RuntimeError('readonly call failed: '+label)
 answer=json.loads(x.stdout);save(O/(label+'_result_v1.json'),answer);answers[label]=answer
current={(r['run'],r['case_id']):r for r in answers['twenty_inputs']['rows']}
assert all(all(current[(r['run'],r['case_id'])][k]==r[k] for k in ('fold','input','normalization')) for r in rows)
assert len(answers['target_absence']['absent_targets'])==28
save(O/'readiness_verification_v1.json',dict(status='READONLY_READINESS_PASS_AWAITING_LOCAL_TRANSPORT_FREEZE',request_sha256=digest(qp),calls=4,identity=answers['identity_targets'],target_check=answers['target_absence'],source_files=len(answers['frozen_sources_provider']['records']),source_hash_bytes=answers['frozen_sources_provider']['hashed_bytes'],inputs=20,targets_absent=28,server_writes=0,installs=0,checkpoint_loads=0,forwards=0,source_metadata_only=True))
print(json.dumps(dict(status='READONLY_READINESS_PASS',sources=len(answers['frozen_sources_provider']['records']),inputs=20,targets_absent=28,free_disk_bytes=answers['identity_targets']['free_disk_bytes'])))
