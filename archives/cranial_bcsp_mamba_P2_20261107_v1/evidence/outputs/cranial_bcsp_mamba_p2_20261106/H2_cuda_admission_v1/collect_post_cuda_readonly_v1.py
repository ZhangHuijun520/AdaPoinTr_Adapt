"""Fixed short native SHA/stat commands and bounded downloads; no server writes."""
import hashlib,json,shlex,subprocess
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;R=S.parents[2];F=S/'post_cuda_freeze_audit_20261107_v1';F.mkdir();D=F/'downloads';D.mkdir();q=json.loads((S/'H2_artificial_cuda_execution_request_v1.json').read_text());L=q['launch_contract'];out=PurePosixPath(q['output']);install=PurePosixPath(q['entry']['path']).parent
BASE=['wsl.exe','-d','Ubuntu-20.04','--exec'];CLIENT='/home/zhj/.local/bin/hpc5000'
def call(label,cmd):
 assert len(cmd.encode())<2048
 try:r=subprocess.run(BASE+[CLIENT,'exec','--timeout','30','--',cmd],capture_output=True,timeout=40)
 except subprocess.TimeoutExpired as exc:
  for k,b in [('stdout',exc.stdout or b''),('stderr',exc.stderr or b'')]:
   with (F/(label+'_timeout_'+k+'.bin')).open('xb') as f:f.write(b)
  raise
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 if r.returncode:raise RuntimeError(label+' returncode '+str(r.returncode))
 print(json.dumps(dict(stage=label,returncode=0,stdout_bytes=len(r.stdout))),flush=True);return r.stdout.decode().replace('\r','')
prefix='test "$(hostname)" = '+shlex.quote(q['identity']['hostname'])+' && test "$(id -u)" = 1000 && cd '+shlex.quote(str(out))+' && '
before=call('output_metadata_before',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort")
expected={'AUX_optimizer_groups.json','AUX_result.json','COUPLE_optimizer_groups.json','COUPLE_result.json','attempts.jsonl','completion.json','native_SSM_origins.json','resources.jsonl','payload_manifest.json','worker.pid','exit_code.txt','launch.log'}
meta=[r.split(' ',5) for r in before.splitlines()];assert all(r[0] in ['f','d'] for r in meta),'nonregular output';assert {r[5] for r in meta if r[0]=='d'}=={'.','./tmp'};assert {r[5] for r in meta if r[0]=='f'}=={'./'+n for n in expected}
hashes=call('output_SHA256',prefix+"find . -type f -print0 | sort -z | xargs -0 sha256sum")
after=call('output_metadata_after',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort");assert before==after,'output drift excluding atime'
scopep=R/'outputs/cranial_bcsp_geov1_20261024/actual_proxy_trace_20261102_v1/observed_server_frozen_scope_v3.json';scopeblob=scopep.read_bytes();assert hashlib.sha256(scopeblob).hexdigest()==q['preflight_scope']['sha256'];scope=json.loads(scopeblob)
records={}
def add(r):
 if r['path'] in records:assert all(records[r['path']][k]==r[k] for k in ['bytes','sha256'])
 else:records[r['path']]={k:r[k] for k in ['path','bytes','sha256']}
for key in ['entry','h2_range','h2_adapter','h2_training_runtime','artificial_input','fixture_definition','P3','H2_implementation_P3','parent_entry','helper','preflight_scope','static_config','numeric_policy']:add(q[key])
add(L['launcher_template'])
for r in [*q['implementation'].values(),*q['dependencies'],*scope['bindings']['provider'],*scope['bindings']['environment_metadata']]:add(r)
for r in scope['bindings']['candidate']:add(dict(r,path=str(PurePosixPath(q['model_root'])/r['relative_target'])))
for r in scope['bindings']['isolated_model_project_sources']:add(dict(r,path=str(PurePosixPath(q['model_root'])/r['relative_path'])))
requestpath=L['request_path'];requestblob=(S/'H2_artificial_cuda_execution_request_v1.json').read_bytes();add(dict(path=requestpath,bytes=len(requestblob),sha256=hashlib.sha256(requestblob).hexdigest()))
startup_local=S/'authorized_execution_v1/readback';known=json.loads((startup_local/'startup_receipt_v1.json').read_bytes())
for key,name,hkey in [('authorization_path','authorization_v1.json','authorization_sha256'),('runtime_path','runtime_v1.json','runtime_sha256'),('launcher_path','launch_once_v1.sh','launcher_sha256')]:
 b=(startup_local/name).read_bytes();assert hashlib.sha256(b).hexdigest()==known[hkey];add(dict(path=L[key],bytes=len(b),sha256=known[hkey]))
claim=json.dumps(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=hashlib.sha256(requestblob).hexdigest()),indent=2).encode();add(dict(path=q['launch_attempt'],bytes=len(claim),sha256=hashlib.sha256(claim).hexdigest()))
assert sum(r['bytes'] for r in records.values())<2*1024**3,'fixed verification read budget'
groups=[];group=[]
for p in records:
 candidate=group+[p]
 if len(('sha256sum '+' '.join(map(shlex.quote,candidate))).encode())>1800:groups.append(group);group=[p]
 else:group=candidate
if group:groups.append(group)
source_hashes=''
for i,g in enumerate(groups):source_hashes+=call('frozen_assets_SHA256_'+str(i),'sha256sum '+' '.join(map(shlex.quote,g)))
def parse(text):
 result={}
 for line in text.splitlines():
  h,p=line.split(None,1);p=p.strip();assert len(h)==64 and p not in result;result[p]=h
 return result
actual_sources=parse(source_hashes);assert set(actual_sources)==set(records) and all(actual_sources[p]==r['sha256'] for p,r in records.items()),'frozen assets hash'
state=call('process_state',prefix+'test "$(cat exit_code.txt)" = 0 && test ! -e failure.json && test ! -d /proc/$(cat worker.pid) && ! tmux has-session -t '+shlex.quote(L['tmux_session'])+' 2>/dev/null && printf "EXIT0_WORKER_ABSENT_TMUX_ABSENT_NO_FAILURE\\n"');assert 'EXIT0_WORKER_ABSENT_TMUX_ABSENT_NO_FAILURE' in state
for name in sorted(expected):
 target=D/name;p=subprocess.run(BASE+['wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0
 r=subprocess.run(BASE+[CLIENT,'get',str(out/name),p.stdout.decode().strip()],capture_output=True,timeout=30)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (F/(name+'.get_'+k+'.bin')).open('xb') as f:f.write(b)
 if r.returncode:raise RuntimeError('download '+name)
 print(json.dumps(dict(downloaded=name,bytes=target.stat().st_size)),flush=True)
output_hashes=parse(hashes);sizes={r[5]:int(r[3]) for r in meta if r[0]=='f'}
for name in expected:
 p=D/name;b=p.read_bytes();assert len(b)==sizes['./'+name] and hashlib.sha256(b).hexdigest()==output_hashes['./'+name],'download identity'
report=dict(status='REMOTE_POST_CUDA_READONLY_FILES_PASS',request_sha256=hashlib.sha256(requestblob).hexdigest(),exact_output_files=12,output_metadata_before_after_equal=True,atime_excluded=True,output_SHA256=output_hashes,frozen_asset_bindings=list(records.values()),frozen_asset_count=len(records),exact_frozen_asset_bytes=sum(r['bytes'] for r in records.values()),worker_absent=True,tmux_absent=True,exit_code=0,server_writes=0,GPU_calls=0,new_forward=0,new_backward=0)
with (F/'remote_file_audit_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps({k:v for k,v in report.items() if k not in ['output_SHA256','frozen_asset_bindings']}),flush=True)
