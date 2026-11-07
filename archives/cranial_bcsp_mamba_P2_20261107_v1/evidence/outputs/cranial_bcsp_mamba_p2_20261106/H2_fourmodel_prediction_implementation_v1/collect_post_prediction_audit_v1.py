"""Exact read-only output/source freeze and tar/NPZ validation; no model or checkpoint loading."""
import hashlib,json,shlex,subprocess,time
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;R=S.parents[2];F=S/'post_prediction_freeze_audit_v1';F.mkdir();D=F/'downloads';D.mkdir()
Q=S/'pending_request_v1/transport_payload/H2_C_D_fourmodel_native_prediction_execution_request_v1.json';QH='b95b866a6b3a0eaeb1e840e003ecd426847ed47b07675b6c1f7644b5aee97170';assert hashlib.sha256(Q.read_bytes()).hexdigest()==QH;q=json.loads(Q.read_bytes());idx=json.loads((S/'pending_request_v1/transport_payload/H2_C_D_fourmodel_input_index_v1.json').read_bytes());proto=json.loads((S/'pending_request_v1/transport_payload/H2_fourmodel_native_prediction_protocol_v1.json').read_bytes());out=PurePosixPath(q['output']);install=PurePosixPath(q['launch_contract']['request_path']).parent
pred={'predictions/'+r['run']+'__'+r['case_id']+'.npz' for r in idx['inputs']};archive='development_predictions_v1.tar.gz'
top={'inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','resources.jsonl','inference_complete.json','completion.json','worker.pid','launch.log','exit_code.txt',archive,archive+'.sha256',archive+'.bytes',archive+'.contents.sha256'};expected=pred|top;records={}
def add(r):
 r={k:r[k] for k in ['path','bytes','sha256']}
 if r['path'] in records:assert records[r['path']]==r
 else:records[r['path']]=r
for x in json.loads((S/'pending_request_v1/installation_mapping_v1.json').read_bytes())['files']:add(dict(path=x['target'],bytes=x['bytes'],sha256=x['sha256']))
for p in (S/'authorized_execution_v1/readback').iterdir():add(dict(path=str(install/'control'/p.name),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
for r in [q['helper'],q['preflight_scope'],q['static_config'],q['numeric_policy'],q['source_index'],q['source_manifest'],q['fold_binding'],*q['implementation'].values(),*q['dependencies'],*[x['checkpoint'] for x in idx['runs']]]:add(r)
scope=json.loads((R/'outputs/cranial_bcsp_geov1_20261024/actual_proxy_trace_20261102_v1/observed_server_frozen_scope_v3.json').read_bytes())
for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:add(r)
for key,rel in [('candidate','relative_target'),('isolated_model_project_sources','relative_path')]:
 for r in scope['bindings'][key]:add(dict(path=str(PurePosixPath(q['model_root'])/r[rel]),bytes=r['bytes'],sha256=r['sha256']))
def emit(n,v):
 with (F/n).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
emit('audit_scope_v1.json',dict(request_sha256=QH,expected_files=sorted(expected),expected_directories=['.','./predictions','./tmp'],frozen_records=list(records.values()),wall_seconds=180,per_call_seconds=30,command_limit_bytes=2048,maximum_hashed_bytes=4*1024**3,maximum_download_text_bytes=16*1024**2,tar_scope='Exact425 archive members; hash/size match current regular files;420 NPZ finite FP32 prediction8192x3, fixed representative coarse256x3 only; no models/GT',server_writes=0,new_forward=0))
B=['wsl.exe','-d','Ubuntu-20.04','--exec'];CLIENT='/home/zhj/.local/bin/hpc5000';start=time.monotonic()
def call(label,cmd):
 assert len(cmd.encode())<=2048 and time.monotonic()-start<180
 emit(label+'_command.json',dict(command=cmd,bytes=len(cmd.encode())))
 r=subprocess.run(B+[CLIENT,'exec','--timeout','30','--',cmd],capture_output=True,timeout=40)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 assert r.returncode==0,(label,r.returncode,r.stderr[:512]);print(json.dumps(dict(stage=label,stdout_bytes=len(r.stdout))),flush=True);return r.stdout.decode().replace('\r','')
def hashes(t):
 d={}
 for row in t.splitlines():
  h,p=row.split(None,1);p=p.strip();assert len(h)==64 and p not in d;d[p]=h
 return d
try:
 prefix='test "$(hostname)" = '+shlex.quote(q['identity']['hostname'])+' && test "$(id -u)" = 1000 && cd '+shlex.quote(str(out))+' && '
 assert 'EXIT0_WORKER_TMUX_ABSENT' in call('finished_state',prefix+'test "$(cat exit_code.txt)" = 0 && test ! -d /proc/$(cat worker.pid) && ! tmux has-session -t '+shlex.quote(q['launch_contract']['tmux_session'])+' 2>/dev/null && test ! -e failure.json && printf "EXIT0_WORKER_TMUX_ABSENT\\n"')
 before=call('inventory_before',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort");rows=[x.split(' ',5) for x in before.splitlines()]
 assert all(x[0] in ['f','d'] for x in rows) and {x[5] for x in rows if x[0]=='d'}=={'.','./tmp','./predictions'} and {x[5][2:] for x in rows if x[0]=='f'}==expected
 sizes={x[5][2:]:int(x[3]) for x in rows if x[0]=='f'};assert len(expected)==433 and sum(sizes.values())+sum(r['bytes'] for r in records.values())<=4*1024**3
 outputhash=hashes(call('all_output_SHA256',prefix+"find . -type f -print0 | sort -z | xargs -0 sha256sum"))
 groups=[];group=[]
 for p in records:
  if len(('sha256sum '+' '.join(map(shlex.quote,group+[p]))).encode())>1800:groups.append(group);group=[]
  group.append(p)
 if group:groups.append(group)
 actual={}
 for i,g in enumerate(groups):
  actual.update(hashes(call('frozen_hash_'+str(i),'sha256sum '+' '.join(map(shlex.quote,g)))))
  for line in call('frozen_stat_'+str(i),"stat -c '%F|%s|%n' -- "+' '.join(map(shlex.quote,g))).splitlines():
   typ,size,p=line.split('|',2);assert typ=='regular file' and int(size)==records[p]['bytes']
 assert actual=={p:r['sha256'] for p,r in records.items()}
 # Read archive bytes, member hashes, and predicted arrays without extracting any server file.
 code="""import pathlib,json,tarfile,hashlib,io; import numpy as n
p=pathlib.Path(OUT);c=json.loads((p/'completion.json').read_bytes());a=c['archive'];d={r['name']:r for r in a['members']};assert len(d)==425;coarse=0;count=0
with tarfile.open(p/'development_predictions_v1.tar.gz','r:gz') as t:
 m=t.getmembers();assert len(m)==425 and {v.name for v in m}==set(d)
 for v in m:
  assert v.isfile() and not pathlib.PurePosixPath(v.name).is_absolute() and '..' not in pathlib.PurePosixPath(v.name).parts
  b=t.extractfile(v).read();r=d[v.name];assert len(b)==r['bytes']==(p/v.name).stat().st_size and hashlib.sha256(b).hexdigest()==r['sha256']==hashlib.sha256((p/v.name).read_bytes()).hexdigest()
  if v.name.endswith('.npz'):
   with n.load(io.BytesIO(b),allow_pickle=False) as z:
    assert set(z.files) in ({'prediction'},{'prediction','coarse'});x=z['prediction'];assert x.shape==(8192,3) and x.dtype==n.float32 and n.isfinite(x).all()
    if 'coarse' in z.files:
     x=z['coarse'];assert x.shape==(256,3) and x.dtype==n.float32 and n.isfinite(x).all();coarse+=1
   count+=1
assert count==420 and coarse==20;print(json.dumps(dict(status='TAR_425_HASHES_AND420_FINITE_ARRAYS_PASS',members=425,prediction_arrays=420,coarse_arrays=coarse,server_extractions=0)))
""".replace('OUT',repr(str(out)))
 tar=json.loads(call('archive_members_and_arrays',shlex.join([q['identity']['python_realpath'],'-I','-B','-c',code])))
 downloaded=0
 for name in sorted(top-{archive}):
  downloaded+=sizes[name];assert downloaded<=16*1024**2
  target=D/name;r=subprocess.run(B+['wslpath','-a',str(target)],capture_output=True,timeout=10);assert r.returncode==0
  r=subprocess.run(B+[CLIENT,'get',str(out/name),r.stdout.decode().strip()],capture_output=True,timeout=30)
  for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
   with (F/(name+'_get_'+k+'.bin')).open('xb') as f:f.write(b)
  assert r.returncode==0 and target.stat().st_size==sizes[name] and hashlib.sha256(target.read_bytes()).hexdigest()==outputhash['./'+name]
 after=call('inventory_after',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort");assert before==after,'content inventory drift excluding atime'
 emit('remote_readonly_receipt_v1.json',dict(status='REMOTE_H2_NATIVE_PREDICTION_FREEZE_FILES_PASS',request_sha256=QH,exit_code=0,worker_and_tmux_absent=True,exact_output_files=433,predictions=420,output_SHA256=outputhash,output_bytes=sizes,archive_member_array_audit=tar,frozen_asset_records=list(records.values()),frozen_assets=len(records),inventory_unchanged_excluding_atime=True,downloaded_text_bytes=downloaded,seconds=time.monotonic()-start,server_writes=0,new_forward=0,checkpoint_loaded=False,archive_downloaded=False))
 print('REMOTE_H2_NATIVE_PREDICTION_FREEZE_FILES_PASS')
except BaseException as exc:
 emit('collection_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),seconds=time.monotonic()-start));raise
