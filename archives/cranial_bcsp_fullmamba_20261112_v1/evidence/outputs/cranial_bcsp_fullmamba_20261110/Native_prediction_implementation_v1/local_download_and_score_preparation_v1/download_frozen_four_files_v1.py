"""Download exactly four frozen files. Raw client responses, no remote mutations."""
import hashlib,json,shlex,shutil,subprocess,sys,time
from pathlib import Path
S=Path(__file__).resolve().parent;P=S.parent/'resource_rebind_v2/post_prediction_freeze_audit_v1'
MAN=P/'download_four_files_manifest_v1.json';plan=json.loads(MAN.read_bytes());DEST=Path(plan['suggested_local_directory'])
BASE=['wsl.exe','-d','Ubuntu-20.04','--exec'];CLIENT='/home/zhj/.local/bin/hpc5000'
events=[]
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def invoke(label,args,timeout):
 try:r=subprocess.run(args,capture_output=True,timeout=timeout);out,err,rc=r.stdout,r.stderr,r.returncode
 except subprocess.TimeoutExpired as exc:out,err,rc=exc.stdout or b'',exc.stderr or b'',None
 for k,b in [('stdout',out),('stderr',err)]:
  with (S/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 events.append(dict(stage=label,returncode=rc,stdout_bytes=len(out),stderr_bytes=len(err)))
 print(json.dumps(events[-1]),flush=True)
 if rc!=0:raise RuntimeError('download stage failed; no automatic retry: '+label)
 return out
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 start=time.monotonic()
 try:
  assert DEST==Path(r'E:\ResearchBackups\AdaPoinTr\BCSP_FULLMAMBA_F0\2026-11-11_native_development_eval') and not DEST.exists()
  assert not any(p.is_symlink() for p in (DEST,*DEST.parents)) and shutil.disk_usage(Path(r'E:\ResearchBackups\AdaPoinTr')).free>=2*1024**3
  audit=json.loads((P/'post_prediction_freeze_audit_result_v1.json').read_bytes());assert audit['status']=='FORMAL_F0_CD_POST_PREDICTION_FREEZE_AUDIT_PASS' and all(audit['checks'].values()) and len(plan['files'])==4
  emit(S/'download_scope_v1.json',dict(status='AUTHORIZED_FOUR_FILE_DOWNLOAD',manifest=dict(path=str(MAN.absolute()),sha256=digest(MAN)),target=str(DEST),files=plan['files'],server_writes=0,overwrite=False,ML_calls=0))
  code="import os,socket,pathlib,json; assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000; p=pathlib.Path("+repr(plan['files'][0]['path'])+"); assert not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file() and p.stat().st_size==180647685; print(json.dumps(dict(status='CURRENT_CONTAINER_AND_FROZEN_ARCHIVE_PRESENT',hostname=socket.gethostname(),archive_bytes=p.stat().st_size)))"
  command=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',code]);assert len(command.encode())<=2048
  raw=invoke('identity_before_download',BASE+[CLIENT,'exec','--timeout','15','--',command],25);assert json.loads(raw)['status']=='CURRENT_CONTAINER_AND_FROZEN_ARCHIVE_PRESENT'
  DEST.mkdir(parents=True,exist_ok=False)
  actual=[]
  for i,r in enumerate(sorted(plan['files'],key=lambda r:r['name'].endswith('.tar.gz'))):
   local=DEST/r['name'];assert not local.exists() and not local.is_symlink()
   wsl=invoke('resolve_target_'+str(i),BASE+['wslpath','-a',str(local)],15).decode('utf-8').strip();assert wsl.startswith('/mnt/e/') and '\n' not in wsl
   invoke('download_'+str(i),BASE+[CLIENT,'get',r['path'],wsl],300)
   assert local.is_file() and local.stat().st_size==r['bytes'] and digest(local)==r['sha256'],str(local)
   actual.append(dict(path=str(local),bytes=local.stat().st_size,sha256=digest(local)))
   print(json.dumps(dict(verified=r['name'],bytes=r['bytes'])),flush=True)
  receipt=dict(status='FOUR_FILES_DOWNLOADED_AND_BYTE_HASH_VERIFIED_AWAITING_MEMBER_RESTORE_VERIFICATION',files=actual,target=str(DEST),events=events,seconds=time.monotonic()-start,server_writes=0,scoring_executed=False,archive_extracted=False)
  emit(S/'four_file_download_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=True),flush=True)
 except BaseException as exc:emit(S/'download_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),events=events,seconds=time.monotonic()-start));raise
if __name__=='__main__':main()
