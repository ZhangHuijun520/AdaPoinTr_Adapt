"""Single authorized foreground-managed CPU run; no retry or gate decision."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys,time
d=Path(__file__).resolve().parent
h=lambda b:hashlib.sha256(b).hexdigest()
request=d/'EJTC_RTJ_D_CPU_scoring_execution_request_v1.json';raw=request.read_bytes();rid=h(raw)
assert rid=='d45c5342e22ba09a937354efa928f42d2462999c5affa63a9d4f559a8237438e'
q=json.loads(raw)
def exact(rec):
 p=Path(rec['path']);assert p.resolve()==p and p.is_file() and p.stat().st_size==rec['bytes'] and h(p.read_bytes())==rec['sha256'];return p
assert Path(sys.executable).resolve()==Path(q['interpreter']['path'])
import numpy,scipy,psutil
assert [sys.version.split()[0],numpy.__version__,scipy.__version__]==q['runtime_versions']
for v in q.values():
 if isinstance(v,dict) and {'path','bytes','sha256'}<=set(v):exact(v)
index=json.loads(exact(q['case_index']).read_bytes())
for r in index['cases']:
 exact(r['reference']);exact(r['point_file'])
assert not os.path.lexists(q['output'])
names=['score315_user_authorization_v1.json','score315_single_attempt_claim_v1.json','score315_single_attempt_v1.log','score315_resource_monitor_v1.jsonl','score315_execution_exit_v1.json']
assert all(not os.path.lexists(d/n) for n in names)
auth=dict(schema='bcsp-development-authorization-v1',request_sha256=rid,explicit_user_authorization=True,user_authorization_text='User separately authorized the preceding complete SHA256 '+rid+' for one local CPU scoring run; stop on failure, no automatic retry; no gate decision.')
spec=importlib.util.spec_from_file_location('score315_authorize_prewrite',q['entry']['path']);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
w.authorize(q,rid,auth)
def save(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
save(d/names[0],auth);authraw=(d/names[0]).read_bytes()
save(d/names[1],dict(request_sha256=rid,single_attempt_claimed=True,asset_and_runtime_recheck_pass=True,reference_files_verified=210))
cmd=[sys.executable,'-I','-B',q['entry']['path'],'--request',str(request),'--request-sha256',rid,'--authorization',str(d/names[0]),'--authorization-sha256',h(authraw)]
env={**os.environ,'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','MKL_NUM_THREADS':'2'}
start=time.monotonic();last_progress=-1
with (d/names[2]).open('xb',buffering=0) as log,(d/names[3]).open('x',encoding='utf-8') as monitor:
 job=subprocess.Popen(cmd,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=log)
 print(json.dumps(dict(status='CPU_SCORING_STARTED',pid=job.pid,request_sha256=rid,model_rows=315)),flush=True)
 try:
  while job.poll() is None:
   elapsed=time.monotonic()-start
   try:rss=psutil.Process(job.pid).memory_info().rss
   except psutil.NoSuchProcess:
    if job.poll() is not None:break
    raise
   output=Path(q['output']);size=sum(p.stat().st_size for p in output.iterdir() if p.is_file()) if output.exists() else 0
   rowfile=output/'model_scores.jsonl';count=len(rowfile.read_bytes().splitlines()) if rowfile.exists() else 0
   sample=dict(elapsed_seconds=elapsed,RSS_bytes=rss,output_bytes=size,model_rows=count)
   monitor.write(json.dumps(sample)+'\n');monitor.flush()
   assert elapsed<=q['limits']['wall_seconds'] and rss<=q['limits']['RSS_bytes'] and size<=q['limits']['output_bytes'],'Frozen resource budget exceeded'
   if count//30!=last_progress:
    last_progress=count//30;print(json.dumps(sample),flush=True)
   try:job.wait(timeout=5)
   except subprocess.TimeoutExpired:pass
  rc=job.wait();assert rc==0 and (Path(q['output'])/'completion.json').is_file(),'Scoring worker failed: '+str(rc)
 except BaseException as error:
  if job.poll() is None:
   job.terminate()
   try:job.wait(timeout=10)
   except subprocess.TimeoutExpired:job.kill();job.wait()
  save(d/names[4],dict(status='FAILED_STOP_NO_RETRY',request_sha256=rid,exit_code=job.returncode,error=repr(error)));raise
save(d/names[4],dict(status='CPU_SCORING_PROCESS_EXIT_ZERO_AWAITING_FREEZE_AUDIT',request_sha256=rid,exit_code=rc,seconds=time.monotonic()-start))
print(json.dumps(dict(status='CPU_SCORING_PROCESS_EXIT_ZERO_AWAITING_FREEZE_AUDIT',exit_code=rc)),flush=True)
