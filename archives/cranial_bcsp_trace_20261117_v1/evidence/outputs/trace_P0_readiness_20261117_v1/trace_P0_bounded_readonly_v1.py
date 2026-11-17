# -*- coding: utf-8 -*-
"""Single bounded P0 read-only query. No imports of numerical/model packages or remote writes."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import time
import zlib

ROOT = Path(r'E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution')
OUT = Path(__file__).resolve().parent
PARENT = ROOT/'outputs/spcg_native_prediction_preparation_20261117_v1/implementation_v1'
REQUEST = PARENT/'pending_transport_v1/payload/SPCG_sixmodel_native_execution_request_v1.json'
CASES = ROOT/'outputs/trace_plan_review_20261117_v1/TRACE_D0_proposed_cases_v2.json'
PLAN = ROOT/'docs/cranial_bcsp_trace_20261117_v2/Cranial_BCSP_FullMamba_BCSP_TRACE_正式实验计划书_审阅修订v2_2026-11-17.md'

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, obj):
    with (OUT/name).open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

q=read(REQUEST);selection=read(CASES);index=read(PARENT/'SPCG_sixmodel_input_index_v1.json')
wanted={(c['fold'],c['case_id']):c for c in selection['cases']}
inputs=[r for r in index['inputs'] if r['variant']=='G1' and (r['fold'],r['case_id']) in wanted]
assert len(inputs)==40 and len({r['input']['path'] for r in inputs})==40
assert all(r['input']['sha256']==wanted[(r['fold'],r['case_id'])]['point_file']['sha256'] for r in inputs)
spec=dict(hostname='shu-common-25721452-notebook-yxwd3w-0',uid=1000,project='/home/jovyan/adapointr_work/PoinTr',
          request=dict(path='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_native_prediction_20261117_v1/SPCG_sixmodel_native_execution_request_v1.json',bytes=REQUEST.stat().st_size,sha256=sha(REQUEST)),
          selected=[dict(fold=r['fold'],case_id=r['case_id'],input=r['input']) for r in inputs],
          roles=['G1_C','G2_C','G1_D','G2_D'],
          future_install_root='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_trace_D0_20261117_v1',
          future_output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/TRACE_D0_memory_evidence_20261117_v1',
          budget=dict(wall_seconds=60,records=96,small_hashed_bytes=64*1024**2,checkpoint_hashed_bytes=2*1024**3),
          mode='READ_ONLY_NO_IMPORT_NO_CUDA_NO_FORWARD_NO_WRITES')
save('P0_frozen_query_scope_v1.json',dict(status='READ_ONLY_QUERY_SCOPE_NOT_EXPERIMENT_AUTHORIZATION',plan_sha256=sha(PLAN),case_manifest_sha256=sha(CASES),**spec))

code=r'''
import os,socket,json,pathlib,hashlib,time,subprocess,shutil,ast
spec=SPEC
started=time.monotonic();records=[];small=0;weightbytes=0
assert socket.gethostname()==spec['hostname'] and os.getuid()==spec['uid'],'identity differs: stop before reading assets'
P=pathlib.Path(spec['project']);assert P.is_dir() and str(P.resolve())==str(P)
def budget():
 assert time.monotonic()-started<spec['budget']['wall_seconds'],'P0 wall budget'
 assert len(records)<spec['budget']['records'],'P0 record budget'
def rec(r,mode='HASH'):
 global small,weightbytes
 budget();p=pathlib.Path(r['path']);item=dict(path=str(p),mode=mode,expected_bytes=r.get('bytes'),expected_sha256=r.get('sha256'))
 try:
  assert not any(x.is_symlink() for x in (p,*p.parents)),'symlink'
  if not p.exists():item['status']='MISSING';records.append(item);return item
  before=p.stat();item['bytes']=before.st_size;assert p.is_file(),'not regular file'
  assert 'bytes' not in r or before.st_size==r['bytes'],'size differs'
  if mode=='STAT_ONLY':item['status']='SIZE_MATCH_HASH_INHERITED_NOT_FRESH';records.append(item);return item
  if mode=='CHECKPOINT_HASH':
   weightbytes+=before.st_size;assert weightbytes<=spec['budget']['checkpoint_hashed_bytes'],'checkpoint read cap'
  else:
   small+=before.st_size;assert small<=spec['budget']['small_hashed_bytes'],'small-file read cap'
  h=hashlib.sha256()
  with p.open('rb') as f:
   for chunk in iter(lambda:f.read(4194304),b''):budget();h.update(chunk)
  after=p.stat();assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'changed during read'
  item['sha256']=h.hexdigest();assert 'sha256' not in r or item['sha256']==r['sha256'],'hash differs'
  item['status']='FRESH_HASH_PASS'
 except Exception as e:item.update(status='CHECK_FAILED',error=repr(e))
 records.append(item);return item
result=dict(hostname=socket.gethostname(),uid=os.getuid(),project=str(P),utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),records=records)
try:
 r=rec(spec['request']);assert r['status']=='FRESH_HASH_PASS','frozen Native request unavailable'
 q=json.loads(pathlib.Path(r['path']).read_bytes())
 for r in list(q['implementation'].values())+[q[k] for k in ['helper','mother_source','static_config','preflight_scope','input_index','probe_asset','head_initialization']]:rec(r)
 pre=json.loads(pathlib.Path(q['preflight_scope']['path']).read_bytes())
 for r in pre['bindings']['provider']:rec(r,'HASH' if r['bytes']<=16*1024**2 else 'STAT_ONLY')
 for r in q['dependencies']:
  if pathlib.Path(r['path']).suffix=='.so':rec(r,'STAT_ONLY')
 for r in spec['selected']:rec(r['input'])
 idx=json.loads(pathlib.Path(q['input_index']['path']).read_bytes())
 result['weights']=[]
 for run in idx['runs']:
  if run['label'] in spec['roles']:result['weights'].append(dict(run=run['label'],record=rec(run['checkpoint'],'CHECKPOINT_HASH')))
 # Parse fixed mother source, do not import it or construct a model.
 raw=pathlib.Path(q['mother_source']['path']).read_bytes();tree=ast.parse(raw)
 cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PCTransformer')
 method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
 source=raw.decode('utf-8').splitlines();snippet=[]
 for n in ast.walk(method):
  if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='learned_coarse' for t in n.targets):
   snippet.append(dict(line=n.lineno,expression=ast.unparse(n.value)))
 result['coarse_assignment']=snippet
 result['mother_forward_source']='\n'.join(source[method.lineno-1:method.end_lineno])
 result['provider_bindings']=pre['bindings']['provider']
 result['future_paths']=[dict(path=p,exists=pathlib.Path(p).exists(),symlink=any(x.is_symlink() for x in (pathlib.Path(p),*pathlib.Path(p).parents)),parent_exists=pathlib.Path(p).parent.is_dir()) for p in [spec['future_install_root'],spec['future_output']]]
 exe=pathlib.Path(q['identity']['python_realpath']);result['python']=dict(path=str(exe),exists=exe.is_file(),realpath=str(exe.resolve()))
 result['disk']=dict(shutil.disk_usage(P)._asdict())
 cmd=['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits']
 smi=subprocess.run(cmd,capture_output=True,timeout=12)
 result['SMI']=dict(command=cmd,returncode=smi.returncode,stdout=smi.stdout.decode('utf-8','replace').strip(),stderr=smi.stderr.decode('utf-8','replace')[:2048])
 result['status']='P0_QUERY_COMPLETE' if all(r['status'] in ('FRESH_HASH_PASS','SIZE_MATCH_HASH_INHERITED_NOT_FRESH') for r in records) else 'P0_QUERY_COMPLETE_WITH_ASSET_GAPS'
except Exception as e:result.update(status='P0_QUERY_FAILED_STOP',error=repr(e))
result.update(elapsed_seconds=time.monotonic()-started,small_hashed_bytes=small,checkpoint_hashed_bytes=weightbytes,models_loaded=0,forward=0,remote_writes=0)
print(json.dumps(result,ensure_ascii=True))
'''.replace('SPEC',repr(spec),1)
(OUT/'P0_remote_readonly_source_v1.txt').write_text(code,encoding='utf-8')
packed=base64.b64encode(zlib.compress(code.encode('utf-8'),9)).decode('ascii')
command='/opt/conda/bin/python -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+packed+'\')))"'
assert len(command)<=16000
save('P0_readonly_command_binding_v1.json',dict(command_bytes=len(command.encode()),command_sha256=hashlib.sha256(command.encode()).hexdigest(),source_sha256=hashlib.sha256(code.encode()).hexdigest(),command=command,timeout_seconds=75))
args=['wsl.exe','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','70','--',command]
start=time.monotonic()
try:
    completed=subprocess.run(args,capture_output=True,timeout=85)
    (OUT/'P0_query_stdout.bin').write_bytes(completed.stdout)
    (OUT/'P0_query_stderr.bin').write_bytes(completed.stderr)
    save('P0_query_transport_v1.json',dict(returncode=completed.returncode,elapsed_seconds=time.monotonic()-start,attempts=1))
    assert completed.returncode==0, 'readonly query transport failed; no retry'
    remote=json.loads(completed.stdout.decode('utf-8').strip())
    save('P0_remote_result_v1.json',remote)
    print(json.dumps({k:remote.get(k) for k in ['status','hostname','elapsed_seconds','disk','SMI','small_hashed_bytes','checkpoint_hashed_bytes']},ensure_ascii=True))
except subprocess.TimeoutExpired as e:
    (OUT/'P0_query_stdout.bin').write_bytes(e.stdout or b'')
    (OUT/'P0_query_stderr.bin').write_bytes(e.stderr or b'')
    save('P0_query_transport_v1.json',dict(status='TIMEOUT_STOP_NO_RETRY',elapsed_seconds=time.monotonic()-start,attempts=1))
    raise
