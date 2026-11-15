"""One explicitly hash-authorized CPU score invocation. No retry/server/model calls."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
S=Path(__file__).resolve().parent;A=S/'authorized_execution_v1'
SHA='b394b3b8814ac729d07a79fe607cbf0636b1ee596546304f8f416bc66e88304a'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def check(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p);return p
def dump(n,x):
 p=A/n
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=True,indent=2,allow_nan=False);f.write('\n')
 return p
def main():
 sys.stdout.reconfigure(encoding='utf-8')
 request=S/'local_scoring_execution_request_v1.json';assert sha(request)==SHA
 q=json.loads(request.read_bytes());assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and not q['execution_authorized']
 assert q['counts']==dict(unique_cases=210,sources=42,model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168)
 assert not A.exists() and not A.is_symlink() and not Path(q['output']).exists() and not Path(q['output']).is_symlink()
 for r in q['implementation'].values():check(r)
 for r in q['evidence'].values():check(r)
 for k in ['P3','reference_manifest','prediction_index','score_case_index']:check(q[k])
 check(q['environment']['python']);check(q['frozen_baseline_scores'])
 for spec in q['archive_inputs'].values():
  for k in ['archive','prediction_index','prediction_protocol']:check(spec[k])
  for r in spec['sidecars']:check(r)
 index=json.loads(Path(q['score_case_index']['path']).read_bytes());assert len(index['cases'])==210
 for c in index['cases']:check(c['reference']);check(c['point_file'])
 assert Path(q['output']).resolve()==(S/'unified_scores_v1').resolve() and S.resolve() in Path(q['output']).resolve().parents
 version_code='import sys,json,importlib.metadata as m; print(json.dumps(dict(python=sys.version,packages={n:m.version(n) for n in '+repr(list(q['environment']['packages']))+'})))'
 probe=subprocess.run([q['environment']['python']['path'],'-I','-B','-c',version_code],capture_output=True,timeout=15,env={**os.environ,**q['invocation_contract']['environment']})
 assert probe.returncode==0;versions=json.loads(probe.stdout);assert versions['packages']==q['environment']['packages'] and versions['python']==q['environment']['python_version'],'CPU environment drift'
 A.mkdir()
 text='下一步仅改用保留执行会话的前台托管启动，单独授权一次新尝试，无需修改科研实现。' 
 receipt=dump('score_authorization_v1.json',dict(schema=q['future_authorization']['schema'],request_sha256=SHA,explicit_user_authorization=True,user_authorization_text=text+'\nReference resolution (not quotation): '+SHA+'; one local CPU scoring attempt,840case rows168source rows, no server/GPU/forward/retry.'))
 assert str(receipt)==q['future_authorization']['path']
 args=[q['environment']['python']['path'],*q['environment']['flags'],q['implementation']['scorer']['path'],'--request',str(request),'--request-sha256',SHA,'--authorization',str(receipt),'--authorization-sha256',sha(receipt)]
 dump('invocation_materialization_v1.json',dict(request_sha256=SHA,authorization_sha256=sha(receipt),argv=args,timeout_seconds=q['invocation_contract']['external_wall_timeout_seconds'],prelaunch_bound_hashes_verified=True,backup_writes=0,real_scoring_started=False))
 dump('attempt_started_v1.json',dict(status='CLAIMED_BEFORE_LOCAL_SUBPROCESS',request_sha256=SHA,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),no_retry=True))
 env=os.environ.copy();env.update(q['invocation_contract']['environment'])
 start=time.monotonic();code=None;timed=False;error=None
 with (A/'stdout_v1.txt').open('xb') as stdout,(A/'stderr_v1.txt').open('xb') as stderr:
  try:
   child=subprocess.Popen(args,stdout=stdout,stderr=stderr,env=env,cwd=str(S))
   dump('worker_started_v1.json',dict(pid=child.pid,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),request_sha256=SHA))
   print(json.dumps(dict(status='UNIQUE_LOCAL_LQI_F0_CPU_SCORING_STARTED',PID=child.pid,request_sha256=SHA)),flush=True)
   try:code=child.wait(timeout=q['invocation_contract']['external_wall_timeout_seconds'])
   except subprocess.TimeoutExpired:timed=True;child.kill();child.wait();code=124
  except BaseException as exc:error=repr(exc)
 out=Path(q['output']);done=json.loads((out/'completion.json').read_bytes()) if (out/'completion.json').is_file() else None
 fail=json.loads((out/'failure.json').read_bytes()) if (out/'failure.json').is_file() else None
 ok=code==0 and not timed and error is None and fail is None and done is not None and done['status']=='LOCAL_LQI_F0_TWO_ARM_TWOFOLD_CPU_SCORING_COMPLETE' and done['model_predictions']==420 and done['controls']==420 and done['score_rows']==840 and done['source_rows']==168 and done['frozen_baseline_rows_verified']==630 and done['request_sha256']==SHA
 result=dict(status='LOCAL_CPU_SCORING_FINISHED_PENDING_FORMAL_FREEZE_AUDIT' if ok else 'FAILED_STOP_NO_RETRY',request_sha256=SHA,returncode=code,timeout=timed,error=error,failure=fail,completion=done,elapsed_seconds=time.monotonic()-start,stdout_sha256=sha(A/'stdout_v1.txt'),stderr_sha256=sha(A/'stderr_v1.txt'),results_interpreted=False,formal_freeze_audit=False,server_operations=0,model_calls=0,retries=0)
 dump('execution_result_v1.json',result);print(json.dumps(result),flush=True)
 if not ok:raise SystemExit(code if isinstance(code,int) and 0<code<256 else 1)
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  p=S/'score_foreground_invocation_failure_v2.json'
  if not p.exists():
   with p.open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',request_sha256=SHA,error=repr(exc)),f,indent=2)
  raise
