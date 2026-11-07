"""One bounded read-only collection of exact H2-AUX outputs and frozen assets."""
import hashlib,json,shlex,subprocess,time
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;F=S/'COUPLE_D_post_training_pair_freeze_audit_v1';F.mkdir();D=F/'downloads';D.mkdir()
QH='be3988719fce8860729c80daaa1dcd634000b50c5378605fb6fe377c511e6718'
Q=S/'COUPLE_D_pending_request_v1/transport_payload/H2_COUPLE_foldD_seed0_training_execution_request_v1.json';assert hashlib.sha256(Q.read_bytes()).hexdigest()==QH
P=S/'COUPLE_D_pending_request_v1/transport_payload'
q=json.loads(Q.read_bytes());out=PurePosixPath(q['output']);install=PurePosixPath(q['launch_contract']['request_path']).parent
expected={'worker.pid','resources.jsonl','order_plan.json','optimizer_actual_defaults.json','metrics.jsonl','model_construction.json','run_identity.json','ckpt-last.pth','completion.json','payload_manifest.json','launch.log','initialization.json','optimizer_parameter_groups.json','exposure.json','exit_code.txt'}
records={}
def add(r):
 r={k:r[k] for k in ['path','bytes','sha256']}
 if r['path'] in records:assert records[r['path']]==r
 else:records[r['path']]=r
mapping=json.loads((S/'COUPLE_D_pending_request_v1/installation_mapping_v1.json').read_bytes())
for r in mapping['files']:add(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
ready=json.loads((S/'AUX_D_pending_request_v1/transport_payload/FoldD_readiness_snapshot_v1.json').read_bytes())
for r in ready['metadata_bindings_verified']:add(r)
# Exact reused source/provider/environment bindings inherited from the frozen installed request.
for r in [*q['implementation'].values(),q['static_config'],q['baseline_request'],q['baseline_audit'],q['p3'],q['readiness'],q['cuda_audit'],q['order_plan'],q['initialization_reference'],q['numeric_policy'],q['numeric_protocol'],q['pair_contract'],q['preflight_scope'],q['QC']['qualified_receipt'],q['QC']['verification'],q['QC']['fold_binding'],*q['QC']['manifests'].values(),*q['dependencies']]:add(r)
R=S.parents[2];scope=json.loads((R/'outputs/cranial_bcsp_geov1_20261024/actual_proxy_trace_20261102_v1/observed_server_frozen_scope_v3.json').read_bytes())
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:add(r)
for key,rel in [('candidate','relative_target'),('isolated_model_project_sources','relative_path')]:
 for r in scope['bindings'][key]:add(dict(path=str(PurePosixPath(q['model_root'])/r[rel]),bytes=r['bytes'],sha256=r['sha256']))
C=S/'COUPLE_D_authorized_execution_v1/readback'
for p in C.iterdir():
 assert p.is_file();add(dict(path=str(install/'control'/p.name),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
# Rehash frozen AUX_D outputs and installed evidence to verify the pair remains intact.
AP=S/'AUX_D_pending_request_v1/transport_payload'
aq=json.loads((AP/'H2_AUX_foldD_seed0_training_execution_request_v1.json').read_bytes())
af=S/'post_training_freeze_audit_v1/audit_report_v1.json'
assert hashlib.sha256(af.read_bytes()).hexdigest()=='6809ed3590807458efe3b36f4964436e03efbd27aa9d6584a56199fc80788e7d'
audit=json.loads(af.read_bytes());assert audit['status']=='FORMAL_H2_AUX_FOLDD_POST_TRAINING_FREEZE_AUDIT_PASS'
for r in audit['files']:add(dict(path=str(PurePosixPath(aq['output'])/r['name']),bytes=r['bytes'],sha256=r['sha256']))
for r in json.loads((S/'post_training_freeze_audit_v1/remote_readonly_receipt_v1.json').read_bytes())['frozen_asset_records']:add(r)
for r in q['aux_pairing'].values():add(r)
def emit(n,v):
 with (F/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
emit('audit_scope_v1.json',dict(request_sha256=QH,output=str(out),expected_output_files=sorted(expected),expected_directories=['.','./tmp'],frozen_asset_records=list(records.values()),maximum_hashed_bytes=2*1024**3,maximum_download_bytes=32*1024**2,wall_seconds=180,per_call_seconds=30,maximum_command_bytes=2048,no_checkpoint_download_or_load=True,server_writes=0,forward=0))
B=['wsl.exe','-d','Ubuntu-20.04','--exec'];CLIENT='/home/zhj/.local/bin/hpc5000';start=time.monotonic()
def call(label,cmd):
 assert len(cmd.encode())<=2048 and time.monotonic()-start<180
 emit(label+'_command.json',dict(command=cmd,bytes=len(cmd.encode())))
 p=subprocess.run(B+[CLIENT,'exec','--timeout','30','--',cmd],capture_output=True,timeout=40)
 for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
  with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 assert p.returncode==0,(label,p.returncode,p.stderr[:256]);print(json.dumps(dict(stage=label,stdout_bytes=len(p.stdout))),flush=True)
 return p.stdout.decode().replace('\r','')
def hashes(text):
 result={}
 for line in text.splitlines():
  h,p=line.split(None,1);p=p.strip();assert len(h)==64 and p not in result;result[p]=h
 return result
try:
 prefix='test "$(hostname)" = '+shlex.quote(q['identity']['hostname'])+' && test "$(id -u)" = 1000 && cd '+shlex.quote(str(out))+' && '
 state=call('finished_state',prefix+'test "$(cat exit_code.txt)" = 0 && test ! -d /proc/$(cat worker.pid) && ! tmux has-session -t '+shlex.quote(q['launch_contract']['tmux_session'])+' 2>/dev/null && test ! -e failure.json && test ! -e startup_failure.json && printf "EXIT0_WORKER_ABSENT_TMUX_ABSENT_NO_FAILURE\\n"')
 assert 'EXIT0_WORKER_ABSENT_TMUX_ABSENT_NO_FAILURE' in state
 before=call('inventory_before',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort")
 rows=[r.split(' ',5) for r in before.splitlines()];assert all(r[0] in ['f','d'] for r in rows)
 assert {r[5] for r in rows if r[0]=='d'}=={'.','./tmp'} and {r[5] for r in rows if r[0]=='f'}=={'./'+n for n in expected},'exact output set'
 sizes={r[5][2:]:int(r[3]) for r in rows if r[0]=='f'}
 assert sum(sizes.values())+sum(r['bytes'] for r in records.values())<=2*1024**3
 oh=hashes(call('output_SHA256',prefix+"find . -type f -print0 | sort -z | xargs -0 sha256sum"))
 groups=[];group=[]
 for p in records:
  if len(('sha256sum '+' '.join(map(shlex.quote,group+[p]))).encode())>1800:groups.append(group);group=[]
  group.append(p)
 if group:groups.append(group)
 actual={}
 for i,g in enumerate(groups):actual.update(hashes(call('asset_SHA256_'+str(i),'sha256sum '+' '.join(map(shlex.quote,g)))))
 assert set(actual)==set(records) and all(actual[p]==r['sha256'] for p,r in records.items()),'frozen asset drift'
 for i,g in enumerate(groups):
  for line in call('asset_stat_'+str(i),"stat -c '%F|%s|%n' -- "+' '.join(map(shlex.quote,g))).splitlines():
   typ,size,p=line.split('|',2);assert typ=='regular file' and int(size)==records[p]['bytes'],'asset type/size'
 downloaded=0
 for name in sorted(expected-{'ckpt-last.pth'}):
  downloaded+=sizes[name];assert downloaded<=32*1024**2
  target=D/name;p=subprocess.run(B+['wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0
  p=subprocess.run(B+[CLIENT,'get',str(out/name),p.stdout.decode().strip()],capture_output=True,timeout=30)
  for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
   with (F/(name+'_get_'+k+'.bin')).open('xb') as f:f.write(b)
  assert p.returncode==0 and target.stat().st_size==sizes[name] and hashlib.sha256(target.read_bytes()).hexdigest()==oh['./'+name],name
 after=call('inventory_after',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort");assert before==after,'inventory drift excluding atime'
 emit('remote_readonly_receipt_v1.json',dict(status='REMOTE_H2_COUPLE_D_POST_TRAINING_PAIR_FILES_PASS',request_sha256=QH,exact_output_files=len(expected),output_SHA256=oh,output_bytes=sizes,inventory_unchanged_excluding_atime=True,frozen_asset_records=list(records.values()),frozen_assets=len(records),downloaded_bytes=downloaded,hashed_bytes=sum(sizes.values())+sum(r['bytes'] for r in records.values()),checkpoint_hashed_not_loaded=True,exit_code=0,worker_absent=True,tmux_absent=True,seconds=time.monotonic()-start,server_writes=0,forward=0))
 print('REMOTE_H2_COUPLE_D_POST_TRAINING_PAIR_FILES_PASS',flush=True)
except BaseException as exc:
 emit('collection_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),seconds=time.monotonic()-start));raise
