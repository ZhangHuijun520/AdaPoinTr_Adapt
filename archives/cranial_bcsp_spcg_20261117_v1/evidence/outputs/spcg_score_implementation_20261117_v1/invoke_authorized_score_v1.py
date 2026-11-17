"""Single foreground managed invocation of the explicitly authorized frozen request."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
S=Path(__file__).resolve().parent
Q=S/'SPCG_local_scoring_execution_request_v1.json'
SHA='7b6b3e5f6ade721540397e2c7977a85e2c73298f7e5cedb489b79f257eae27f8'
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def check(r):
 p=Path(r['path']);assert p.is_absolute() and p.is_file() and not any(x.is_symlink() for x in [p,*p.parents]),str(p)
 assert p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],'hash/size '+str(p)
def emit(p,obj):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
 assert digest(Q)==SHA,'exact authorized request'
 q=json.loads(Q.read_bytes());assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
 out=Path(q['output']);control=Path(q['future_authorization']['path']).parent
 assert control==S/'authorized_execution_v1' and not control.exists() and not out.exists(),'fresh unique execution paths'
 assert not any(p.is_symlink() for p in [control,*control.parents,out,*out.parents])
 for r in list(q['implementation'].values())+list(q['evidence'].values())+[q['P3'],q['environment']['python'],q['reference_manifest'],q['prediction_index'],q['score_case_index'],q['frozen_baseline_scores']]:check(r)
 for a in q['archive_inputs'].values():
  for r in [a['archive'],a['prediction_index'],a['prediction_protocol']]+a['sidecars']:check(r)
 ix=json.loads(Path(q['score_case_index']['path']).read_bytes());assert len(ix['cases'])==210 and len(ix['prediction_records'])==630
 for c in ix['cases']:check(c['point_file']);check(c['reference'])
 env=os.environ.copy();env.update(q['invocation_contract']['environment'])
 probe="import importlib.metadata as m,json,sys;print(json.dumps({'packages':{n:m.version(n) for n in ['numpy','scipy','psutil','scikit-image']},'python':sys.version}))"
 result=subprocess.run([q['environment']['python']['path'],'-I','-B','-c',probe],env=env,capture_output=True,timeout=30,check=True)
 observed=json.loads(result.stdout);assert observed['packages']==q['environment']['packages'] and observed['python']==q['environment']['python_version'],'fixed CPU environment'
 control.mkdir(exist_ok=False)
 emit(control/'readiness_v1.json',dict(status='READINESS_PASS',utc=now(),request_sha256=SHA,reference_files=210,point_files=210,predictions=630,environment=observed,no_server_operations=True))
 auth=Path(q['future_authorization']['path'])
 emit(auth,dict(schema=q['future_authorization']['schema'],request_sha256=SHA,explicit_user_authorization=True,user_authorization_text='下一步单独授权该完整哈希；对应紧邻上一轮报告的完整SHA256 '+SHA))
 ash=digest(auth)
 cmd=[q['environment']['python']['path'],'-I','-B',q['implementation']['scorer']['path'],'--request',str(Q),'--request-sha256',SHA,'--authorization',str(auth),'--authorization-sha256',ash]
 emit(control/'process_attempt_v1.json',dict(status='CLAIMED_BEFORE_UNIQUE_SUBPROCESS',utc=now(),request_sha256=SHA,authorization_sha256=ash,command=cmd,automatic_retry=False,startup_mode='foreground managed subprocess; parent waits; stdout and stderr persisted',wall_timeout_seconds=q['invocation_contract']['external_wall_timeout_seconds']))
 start=time.monotonic();rc=None;timed_out=False
 try:
  with (control/'stdout.log').open('xb') as stdout,(control/'stderr.log').open('xb') as stderr:
   child=subprocess.Popen(cmd,cwd=str(S),env=env,stdout=stdout,stderr=stderr)
   emit(control/'process_identity_v1.json',dict(supervisor_pid=os.getpid(),worker_pid=child.pid,utc=now(),request_sha256=SHA))
   print(json.dumps(dict(status='CPU_SCORING_STARTED',worker_pid=child.pid,supervisor_pid=os.getpid(),request_sha256=SHA,control_directory=str(control))),flush=True)
   try:rc=child.wait(timeout=q['invocation_contract']['external_wall_timeout_seconds'])
   except subprocess.TimeoutExpired:timed_out=True;child.kill();rc=child.wait()
  emit(control/'process_exit_v1.json',dict(status='PROCESS_EXITED' if rc==0 and not timed_out else 'FAILED_STOP_NO_RETRY',returncode=rc,timed_out=timed_out,seconds=time.monotonic()-start,utc=now(),request_sha256=SHA))
  print(json.dumps(dict(status='PROCESS_EXITED' if rc==0 else 'FAILED_STOP_NO_RETRY',returncode=rc,timed_out=timed_out)),flush=True)
  return 1 if timed_out else rc
 except BaseException as e:
  emit(control/'startup_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(e),utc=now(),request_sha256=SHA));raise
if __name__=='__main__':sys.exit(main())
