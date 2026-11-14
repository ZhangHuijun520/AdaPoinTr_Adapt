"""One explicitly authorized local CPU scoring attempt; no server or retry."""
import datetime,hashlib,json,os,subprocess,sys,time
from pathlib import Path
S=Path(__file__).resolve().parent;N=S.parent;A=S/'authorized_execution_v1'
SHA='749de9cffe7aaba667108347f93ad86bf7cea447c4e97f58e60897122048f897'

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def check(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in [p,*p.parents]);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];return p
def dump(name,value):
 p=A/name
 with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=True,indent=2,allow_nan=False)
 return p
def main():
 sys.stdout.reconfigure(encoding='utf-8');request=S/'local_scoring_execution_request_v1.json';assert sha(request)==SHA
 q=json.loads(request.read_bytes());assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
 for r in q['implementation'].values():check(r)
 for r in q['evidence'].values():check(r)
 for key in ['P3','reference_manifest','prediction_index','score_case_index','downloaded_prediction_archive','prediction_protocol']:check(q[key])
 check(q['environment']['python'])
 for r in q['download_sidecars']:check(r)
 index=json.loads(Path(q['score_case_index']['path']).read_bytes());assert len(index['cases'])==105
 for c in index['cases']:
  check(c['reference'])
  check(c['point_file'])
 assert not Path(q['output']).exists() and not Path(q['output']).is_symlink() and not A.exists()
 A.mkdir()
 text='下一步单独授权上述完整哈希，即可启动唯一一次本机 CPU 评分：210份模型预测＋210份共享控制，共420行病例评分。'
 receipt=dump('score_authorization_v1.json',dict(schema=q['future_authorization']['schema'],request_sha256=SHA,explicit_user_authorization=True,user_authorization_text=text+'\nReference resolution (not quotation): current paired CPU scoring request SHA256 '+SHA+'; sole local CPU attempt, no server/model/GPU/retry.'))
 assert str(receipt)==q['future_authorization']['path']
 args=[q['environment']['python']['path'],*q['environment']['flags'],q['implementation']['scorer']['path'],'--request',str(request),'--request-sha256',SHA,'--authorization',str(receipt),'--authorization-sha256',sha(receipt)]
 dump('invocation_materialization_v1.json',dict(request_sha256=SHA,authorization_sha256=sha(receipt),argv=args,timeout_seconds=q['invocation_contract']['external_wall_timeout_seconds'],user_verbatim=text,prelaunch_bound_hashes_verified=True,real_scoring_started=False))
 dump('attempt_started_v1.json',dict(status='CLAIMED_BEFORE_LOCAL_SUBPROCESS',request_sha256=SHA,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),no_retry=True))
 env=os.environ.copy();env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',PYTHONDONTWRITEBYTECODE='1')
 start=time.monotonic();code=None;timed=False;error=None
 with (A/'stdout_v1.txt').open('xb') as stdout,(A/'stderr_v1.txt').open('xb') as stderr:
  try:
   child=subprocess.Popen(args,stdout=stdout,stderr=stderr,env=env,cwd=str(N))
   dump('worker_started_v1.json',dict(pid=child.pid,UTC=datetime.datetime.now(datetime.timezone.utc).isoformat(),request_sha256=SHA))
   print(json.dumps(dict(status='SINGLE_LOCAL_CPU_SCORE_PROCESS_STARTED',PID=child.pid,request_sha256=SHA)),flush=True)
   try:code=child.wait(timeout=q['invocation_contract']['external_wall_timeout_seconds'])
   except subprocess.TimeoutExpired:
    timed=True;child.kill();child.wait();code=124
  except BaseException as exc:error=repr(exc)
 out=Path(q['output']);completion=out/'completion.json';failure=out/'failure.json'
 done=json.loads(completion.read_bytes()) if completion.is_file() else None
 fail=json.loads(failure.read_bytes()) if failure.is_file() else None
 ok=code==0 and not timed and error is None and fail is None and done is not None and done['status']=='LOCAL_PAIRED_CPU_SCORING_COMPLETE' and done['model_predictions']==210 and done['controls']==210 and done['score_rows']==420 and done['source_rows']==84 and done['request_sha256']==SHA
 result=dict(status='LOCAL_CPU_SCORING_FINISHED_PENDING_FORMAL_FREEZE_AUDIT' if ok else 'FAILED_STOP_NO_RETRY',request_sha256=SHA,returncode=code,timeout=timed,error=error,failure=fail,completion=done,elapsed_seconds=time.monotonic()-start,stdout_sha256=sha(A/'stdout_v1.txt'),stderr_sha256=sha(A/'stderr_v1.txt'),real_score_result_interpreted=False,formal_freeze_audit=False,server_operations=0,model_calls=0,retries=0)
 dump('execution_result_v1.json',result)
 print(json.dumps(result),flush=True)
 if not ok:raise SystemExit(code if isinstance(code,int) and 0<code<256 else 1)
if __name__=='__main__':main()
