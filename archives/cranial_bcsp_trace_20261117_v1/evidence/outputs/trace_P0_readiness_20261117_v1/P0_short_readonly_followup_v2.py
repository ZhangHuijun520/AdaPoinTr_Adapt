# -*- coding: utf-8 -*-
"""Finish the same P0 with fixed short commands after the long query timed out.
No previous query is resubmitted. Process listing confirmed no residual probe Python.
"""
import argparse,base64,hashlib,json,subprocess,zlib,time
from pathlib import Path
O=Path(__file__).resolve().parent
Q='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_native_prediction_20261117_v1/SPCG_sixmodel_native_execution_request_v1.json'
prefix="import pathlib as p,json,hashlib as h,os,socket;assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000;q=json.loads(p.Path("+repr(Q)+").read_bytes());"
snippets={
'resource': prefix+r'''
import shutil,subprocess
r=shutil.disk_usage('/home/jovyan/adapointr_work/PoinTr')
c=['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used,utilization.gpu','--format=csv,noheader,nounits']
s=subprocess.run(c,capture_output=True,timeout=10)
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),disk=r._asdict(),SMI_command=c,SMI_rc=s.returncode,SMI_stdout=s.stdout.decode(),SMI_stderr=s.stderr.decode(),python_exists=p.Path(q['identity']['python_realpath']).is_file(),request_sha256=h.sha256(p.Path('''+repr(Q)+r''').read_bytes()).hexdigest())))
''',
'assets':prefix+r'''
s=json.loads(p.Path(q['preflight_scope']['path']).read_bytes());rows=[]
for r in list(q['implementation'].values())+[q[k] for k in ['helper','mother_source','static_config','preflight_scope','input_index','probe_asset','head_initialization']]+s['bindings']['provider']:
 f=p.Path(r['path']);a=dict(expected=r,exists=f.is_file(),symlink=any(x.is_symlink() for x in (f,*f.parents)))
 if f.is_file() and not a['symlink']:
  a['bytes']=f.stat().st_size
  if a['bytes']<=16*1024**2:a['sha256']=h.sha256(f.read_bytes()).hexdigest()
 rows.append(a)
raw=p.Path(q['mother_source']['path']).read_text();start=raw.index('class PCTransformer');text=raw[start:];start=text.index('    def forward(');text=text[start:];end=text.find('\n    def ',1)
print(json.dumps(dict(records=rows,mother_forward=text[:end if end!=-1 else 14000],provider=s['bindings']['provider'],CUDA_binaries=[dict(**r,exists=p.Path(r['path']).is_file(),actual_bytes=p.Path(r['path']).stat().st_size if p.Path(r['path']).is_file() else None) for r in q['dependencies'] if r['path'].endswith('.so')])))
''',
'inputs':prefix+r'''
idx=json.loads(p.Path(q['input_index']['path']).read_bytes());selected=[]
mandatory={'C':['train__051__random_1','train__072__random_1','train__012__parietotemporal'],'D':['train__008__random_2','train__046__parietotemporal']}
for fold in ('C','D'):
 pool=[r for r in idx['inputs'] if r['run']=='G1_'+fold];pick=[r for r in pool if r['case_id'] in mandatory[fold]];seen={r['source_id'] for r in pick}
 for t in ('bilateral','frontoorbital','parietotemporal','random_1','random_2'):
  n=sum(r['defect_type']==t for r in pick)
  for r in sorted([r for r in pool if r['defect_type']==t],key=lambda r:h.sha256(('BCSP_TRACE_D0_v2|'+fold+'|'+r['case_id']).encode()).hexdigest()):
   if n==4:break
   if r['source_id'] in seen:continue
   pick.append(r);seen.add(r['source_id']);n+=1
 selected+=pick
out=[]
for r in selected:
 f=p.Path(r['input']['path']);x=dict(fold=r['fold'],case_id=r['case_id'],expected=r['input'],exists=f.is_file(),symlink=any(a.is_symlink() for a in (f,*f.parents)))
 if x['exists'] and not x['symlink']:x.update(bytes=f.stat().st_size,sha256=h.sha256(f.read_bytes()).hexdigest())
 out.append(x)
print(json.dumps(dict(records=out,NPZ_decoded=0)))
''',
'weights':prefix+r'''
idx=json.loads(p.Path(q['input_index']['path']).read_bytes());out=[]
for r in idx['runs']:
 if r['label'] not in ('G1_C','G2_C','G1_D','G2_D'):continue
 f=p.Path(r['checkpoint']['path']);x=dict(run=r['label'],expected=r['checkpoint'],exists=f.is_file(),symlink=any(a.is_symlink() for a in (f,*f.parents)))
 if x['exists'] and not x['symlink']:
  before=f.stat();x['bytes']=before.st_size;v=h.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(4194304),b''):v.update(b)
  after=f.stat();x['sha256']=v.hexdigest();x['unchanged_during_read']=(before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 out.append(x)
print(json.dumps(dict(records=out,checkpoint_deserialized=0)))
''',
}
commands={}
for name,code in snippets.items():
 compile(code,'<P0-readonly-'+name+'>','exec')
 packed=base64.b64encode(zlib.compress(code.encode(),9)).decode()
 command='/opt/conda/bin/python -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+packed+'\')))"'
 assert len(command.encode())<=2048,(name,len(command))
 commands[name]=dict(source=code,command=command,command_bytes=len(command.encode()),source_sha256=hashlib.sha256(code.encode()).hexdigest(),timeout=45 if name=='weights' else 20)
a=argparse.ArgumentParser();a.add_argument('--stage',choices=['prepare',*snippets]);arg=a.parse_args()
if arg.stage=='prepare':
 with (O/'P0_short_queries_static_scope_v2.json').open('x',encoding='utf-8') as f:json.dump(dict(status='STATIC_READONLY_QUERIES_NO_EXPERIMENT',long_query_not_retried=True,residual_probe_absent_by_ps=True,queries=commands),f,indent=2)
 print(json.dumps({k:v['command_bytes'] for k,v in commands.items()}))
else:
 frozen=json.loads((O/'P0_short_queries_static_scope_v2.json').read_text());r=frozen['queries'][arg.stage];assert r==commands[arg.stage]
 start=time.monotonic();stem='P0_short_'+arg.stage+'_v2'
 assert not (O/(stem+'_claim.json')).exists(),'single call per short query'
 (O/(stem+'_claim.json')).write_text(json.dumps(dict(stage=arg.stage,attempt=1)),encoding='utf-8')
 try:
  p=subprocess.run(['wsl.exe','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout',str(r['timeout']),'--',r['command']],capture_output=True,timeout=r['timeout']+10)
  (O/(stem+'_stdout.bin')).write_bytes(p.stdout);(O/(stem+'_stderr.bin')).write_bytes(p.stderr)
  exit=dict(returncode=p.returncode,elapsed_seconds=time.monotonic()-start);(O/(stem+'_transport.json')).write_text(json.dumps(exit),encoding='utf-8')
  assert p.returncode==0,'query failed; do not retry'
  result=json.loads(p.stdout.decode('utf-8').strip());(O/(stem+'_result.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
  print(json.dumps(dict(stage=arg.stage,status='READONLY_RESULT_SAVED',records=len(result.get('records',[])),elapsed_seconds=exit['elapsed_seconds'])))
 except subprocess.TimeoutExpired as e:
  (O/(stem+'_stdout.bin')).write_bytes(e.stdout or b'');(O/(stem+'_stderr.bin')).write_bytes(e.stderr or b'')
  (O/(stem+'_transport.json')).write_text(json.dumps(dict(status='TIMEOUT_STOP',elapsed_seconds=time.monotonic()-start)),encoding='utf-8')
  raise
