"""Freeze exact failed output/control files; no server writes or model execution."""
import ast,hashlib,json,shlex,subprocess,time
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;F=S/'failed_attempt_freeze_audit_v1';F.mkdir();D=F/'downloads';D.mkdir()
QP=S/'final_pending_request_v1/transport_payload/H2_COUPLE_foldC_seed0_training_execution_request_v1.json';QH='477522d9f7c5e7fc4e282a231f44ad5641588d5b34e303d7e433c3ba57ed6ce3';assert hashlib.sha256(QP.read_bytes()).hexdigest()==QH
q=json.loads(QP.read_bytes());out=PurePosixPath(q['output']);root=PurePosixPath(q['implementation']['entry']['path']).parent
expected={'startup_failure.json','exit_code.txt','launch.log','worker.pid','resources.jsonl'};records={}
for r in json.loads((S/'final_pending_request_v1/installation_mapping_v1.json').read_bytes())['files']:records[r['target']]=dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256'])
for p in (S/'authorized_execution_v1/readback').iterdir():records[str(root/'control'/p.name)]=dict(path=str(root/'control'/p.name),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
r=q['aux_pairing']['initialization'];records[r['path']]=r
def emit(n,v):
 with (F/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
emit('scope_v1.json',dict(request_sha256=QH,output=str(out),expected_files=sorted(expected),frozen_asset_records=list(records.values()),read_byte_limit=4*1024**2,wall_seconds=90,per_call_seconds=20,server_writes=0,forward=0))
B=['wsl.exe','-d','Ubuntu-20.04','--exec'];C='/home/zhj/.local/bin/hpc5000';start=time.monotonic()
def call(label,cmd):
 assert len(cmd.encode())<2048 and time.monotonic()-start<90
 p=subprocess.run(B+[C,'exec','--timeout','20','--',cmd],capture_output=True,timeout=30)
 for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
  with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 assert p.returncode==0,(label,p.returncode);return p.stdout.decode().replace('\r','')
def parse(text):
 d={}
 for line in text.splitlines():
  h,p=line.split(None,1);p=p.strip();assert p not in d and len(h)==64;d[p]=h
 return d
try:
 prefix='test "$(hostname)" = '+shlex.quote(q['identity']['hostname'])+' && test "$(id -u)" = 1000 && cd '+shlex.quote(str(out))+' && '
 state=call('stopped_state',prefix+'test "$(cat exit_code.txt)" = 1 && test ! -d /proc/$(cat worker.pid) && ! tmux has-session -t '+shlex.quote(q['launch_contract']['tmux_session'])+' 2>/dev/null && printf "EXIT1_WORKER_TMUX_ABSENT\\n"');assert 'EXIT1_WORKER_TMUX_ABSENT' in state
 before=call('inventory_before',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort")
 rows=[x.split(' ',5) for x in before.splitlines()];assert {x[5] for x in rows if x[0]=='d'}=={'.','./tmp'} and {x[5] for x in rows if x[0]=='f'}=={'./'+n for n in expected} and all(x[0] in ['d','f'] for x in rows)
 sizes={x[5][2:]:int(x[3]) for x in rows if x[0]=='f'};assert sizes['resources.jsonl']==0 and sum(sizes.values())+sum(r['bytes'] for r in records.values())<=4*1024**2
 hashes=parse(call('output_hashes',prefix+"find . -type f -print0 | sort -z | xargs -0 sha256sum"))
 group=[];groups=[]
 for p in records:
  if len(('sha256sum '+' '.join(map(shlex.quote,group+[p]))).encode())>1800:groups.append(group);group=[]
  group.append(p)
 if group:groups.append(group)
 actual={}
 for i,g in enumerate(groups):
  actual.update(parse(call('asset_hash_'+str(i),'sha256sum '+' '.join(map(shlex.quote,g)))))
  for row in call('asset_stat_'+str(i),"stat -c '%F|%s|%n' -- "+' '.join(map(shlex.quote,g))).splitlines():
   typ,size,p=row.split('|',2);assert typ=='regular file' and int(size)==records[p]['bytes']
 assert actual=={p:r['sha256'] for p,r in records.items()}
 for name in sorted(expected):
  target=D/name;p=subprocess.run(B+['wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0
  p=subprocess.run(B+[C,'get',str(out/name),p.stdout.decode().strip()],capture_output=True,timeout=20)
  for k,b in [('stdout',p.stdout),('stderr',p.stderr)]:
   with (F/(name+'_get_'+k+'.bin')).open('xb') as f:f.write(b)
  assert p.returncode==0 and target.stat().st_size==sizes[name] and hashlib.sha256(target.read_bytes()).hexdigest()==hashes['./'+name]
 after=call('inventory_after',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort");assert before==after
 rejected=q['aux_pairing']['initialization']['path'];failure=json.loads((D/'startup_failure.json').read_bytes());log=(D/'launch.log').read_text()
 assert rejected in failure['error'] and 'write/read boundary:' in failure['error'] and 'json_bound' in log and 'aux_initial=json_bound' in log
 controls=S/'authorized_execution_v1/readback';claim=json.loads((controls/'single_attempt_claim_v1.json').read_bytes());auth=json.loads((controls/'H2_authorization_v1.json').read_bytes());runtime=json.loads((controls/'H2_runtime_v1.json').read_bytes())
 assert claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=QH) and auth['request_sha256']==QH and auth['explicit_user_authorization'] is True and runtime['request_sha256']==QH and runtime['authorization_sha256']==hashlib.sha256((controls/'H2_authorization_v1.json').read_bytes()).hexdigest()
 source=(S/'bcsp_h2_couple_foldC_training_entry_v1.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='dispatch_training');text=ast.get_source_segment(source,node);assert text.index("aux_initial=json_bound")<text.index('dataset=')<text.index('return runtime.train_lifecycle')
 report=dict(status='FORMAL_COUPLE_V1_FAILED_STARTUP_FREEZE_AUDIT_PASS',request_sha256=QH,attempt_consumed=True,request_reusable=False,exit_code=1,worker_and_tmux_absent=True,exact_output_files=sorted(expected),output_hashes=hashes,output_bytes=sizes,inventory_stable_excluding_atime=True,frozen_assets_rehashed=len(records),authorization_claim_runtime_verified=True,rejected_initialization_binding_still_matches=True,rejected_initialization=q['aux_pairing']['initialization'],error=failure['error'],failure_stage='after model construction, before dataset construction and train_lifecycle',optimizer_steps=0,no_metrics_or_checkpoint_or_order_or_training_initialization_created=True,forward_count_basis='Bound source ordering plus exact absent training outputs; no independent CUDA kernel tracing',server_writes=0,new_forward=0,seconds=time.monotonic()-start)
 emit('audit_report_v1.json',report);print(json.dumps(report,indent=2))
except BaseException as exc:
 emit('audit_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)));raise
