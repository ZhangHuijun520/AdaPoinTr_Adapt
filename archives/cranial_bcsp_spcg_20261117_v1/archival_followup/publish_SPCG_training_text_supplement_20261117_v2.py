# -*- coding: utf-8 -*-
"""Add exact full training-text evidence and backup-tool compatibility follow-up; tagv1 retained."""
from pathlib import Path
import subprocess,os,json,hashlib,shutil,re,sys
R=Path(__file__).resolve().parent.parent;REPO=R/'outputs/p1pub';TARGET=REPO/'archives/cranial_bcsp_spcg_20261117_v1';D=R/'deliverables/spcg_20261117_v1';B=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_training_text_v1');BACK=B.parent/'2026-11-17_code_results_v1';BRANCH='archive/cranial-bcsp-spcg-20261117';TAG='cranial-bcsp-spcg-20261117-v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def emit(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def git(*args,check=True,timeout=180):
 env=os.environ.copy()
 for k in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy']:env.pop(k,None)
 p=subprocess.run(['git','-c','safe.directory='+REPO.as_posix(),'-c','core.longpaths=true','-c','http.proxy=http://127.0.0.1:12000','-c','http.lowSpeedLimit=1024','-c','http.lowSpeedTime=30','-C',str(REPO),*args],capture_output=True,env=env,timeout=timeout)
 if check and p.returncode:raise RuntimeError(p.stderr.decode(errors='replace')[-1800:])
 return p
phase=sys.argv[1]
if phase=='commit':
 v=read(B/'local_verification_receipt_v1.json');assert v['status']=='COMPLETE_SIX_RUN_TRAINING_TEXT_ARCHIVE_ALL_MEMBERS_VERIFIED';scope=read(B/'metadata/frozen_training_text_scope_v1.json')
 assert git('status','--porcelain').stdout==b'' and git('branch','--show-current').stdout.decode().strip()==BRANCH and git('rev-parse','HEAD').stdout.decode().strip()==read(D/'git_commit_tag_receipt_v1.json')['commit']
 files={};manifest=[];patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',rb'Bearer\s+[A-Za-z0-9_.-]{30,}',rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}']
 for r in scope['files']:
  src=B/'training_outputs'/r['run']/r['name'];assert src.stat().st_size==r['bytes'] and sha(src)==r['sha256'];b=src.read_bytes();assert not any(re.search(p,b) for p in patterns)
  dest=TARGET/'complete_training_outputs'/r['run']/r['name'];put(dest,b);files[dest.relative_to(REPO).as_posix()]=dest;manifest.append(dict(path=dest.relative_to(TARGET).as_posix(),**r))
 for name in ['local_verification_receipt_v1.json','spcg_complete_training_text_20261117_v1.tar.gz.sha256','spcg_complete_training_text_20261117_v1.tar.gz.bytes','spcg_complete_training_text_20261117_v1.tar.gz.contents.sha256']:
  dest=TARGET/'complete_training_outputs'/name;put(dest,(B/name).read_bytes());files[dest.relative_to(REPO).as_posix()]=dest
 for name in ['backup_SPCG_key_checkpoints_20261117_v2.py','backup_SPCG_training_text_20261117_v1.py','publish_SPCG_training_text_supplement_20261117_v2.py']:
  dest=TARGET/'archival_followup'/name;put(dest,(R/'local_tools'/name).read_bytes());files[dest.relative_to(REPO).as_posix()]=dest
 dest=TARGET/'complete_training_outputs/source_manifest_v1.json';emit(dest,dict(status='EXACT_84_FROZEN_TRAINING_TEXT_FILES',files=manifest,local_archive=v['archive'],no_weights_or_arrays=True));files[dest.relative_to(REPO).as_posix()]=dest
 readme=TARGET/'README.md';old=readme.read_bytes();readme.write_bytes(old+b'\n## Complete training records supplement (tagv2)\n\nThe `complete_training_outputs` folder preserves all84 frozen non-checkpoint outputs:3900 metric and geometry rows plus3902 resource rows for every run, exact order, initialization, optimizer, exposure and launch/completion evidence. Every file matches the original formal output inventory. A separate local training-text archive has full member verification. Tagv1 is retained; tagv2 adds this supplement without changing scientific scores or conclusions. Backup-toolv2 replaces a Python3.9-only path API with an equivalent ancestor check for the container basePython; failedv1 probe retained locally. All six real final weights remain excluded from GitHub.\n');files[readme.relative_to(REPO).as_posix()]=readme
 for name in files:git('add','-f','--',name)
 staged={p.decode('utf-8') for p in git('diff','--cached','--name-only','-z').stdout.split(b'\0') if p};assert staged==set(files)
 for raw in git('ls-files','--stage','-z','--',TARGET.relative_to(REPO).as_posix()).stdout.split(b'\0'):
  if not raw:continue
  meta,path=raw.split(b'\t',1);name=path.decode('utf-8')
  if name in files:
   mode,oid,stage=meta.split();b=files[name].read_bytes();assert mode==b'100644' and stage==b'0' and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid.decode()
 msg=D/'git_training_supplement_commit_message_v2.txt';put(msg,b'archive: preserve complete SPCG six-run per-step training records\n\nAdd84 exact frozen outputs (3900 metrics/geometry rows and3902 resources/run), order/init/optimizer/exposure/construction and terminal evidence. Include bounded backup-path compatibility follow-up. No changes to scientific scores, original freezes or candidate closure. No weights or binary prediction arrays published.\n');git('commit','--file',str(msg));commit=git('rev-parse','HEAD').stdout.decode().strip()
 tagmsg=D/'annotated_tag_message_v2.txt';put(tagmsg,('BCSP-SPCG complete archival evidence v2.\n\nTagv1 preserved. Adds84 full training text outputs with formal-inventory hashes. No scientific result changes, checkpoint or binary array uploads.\n\nOriginal code/results archive SHA256: '+read(D/'archive_verification_v1.json')['archive']['sha256']+'\nTraining-text archive SHA256: '+v['archive']['sha256']+'\n').encode());git('tag','-a',TAG,'--file',str(tagmsg))
 r=dict(status='SPCG_FULL_TRAINING_SUPPLEMENT_COMMITTED',branch=BRANCH,tag=TAG,commit=commit,tag_object=git('rev-parse',TAG).stdout.decode().strip(),added_or_modified_files=len(files),original_tag_retained=True);emit(D/'git_commit_tag_receipt_v2.json',r);print(json.dumps(r))
elif phase=='push':
 r=read(D/'git_commit_tag_receipt_v2.json');assert git('status','--porcelain').stdout==b''
 p=git('push','--atomic','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH,'refs/tags/'+TAG+':refs/tags/'+TAG,check=False,timeout=240);put(D/'push_v2_training_supplement_stdout.bin',p.stdout);put(D/'push_v2_training_supplement_stderr.bin',p.stderr);emit(D/'push_v2_training_supplement_exit.json',dict(returncode=p.returncode));assert p.returncode==0;print('SPCG_TRAINING_TEXT_ATOMIC_PUSH_EXIT0')
elif phase=='verify':
 r=read(D/'git_commit_tag_receipt_v2.json');p=git('ls-remote','origin','refs/heads/'+BRANCH,'refs/tags/'+TAG,'refs/tags/'+TAG+'^{}');refs={line.split()[1]:line.split()[0] for line in p.stdout.decode().splitlines()};assert refs=={'refs/heads/'+BRANCH:r['commit'],'refs/tags/'+TAG:r['tag_object'],'refs/tags/'+TAG+'^{}':r['commit']}
 r.update(status='SPCG_V2_INDEPENDENT_REMOTE_REFS_VERIFIED',refs=refs,repository='https://github.com/ZhangHuijun520/AdaPoinTr_Adapt',weights_uploaded=False,arrays_uploaded=False);emit(D/'publication_receipt_v2.json',r)
 for base in [BACK,B]:
  for name in ['git_commit_tag_receipt_v2.json','publication_receipt_v2.json']:put(base/name,(D/name).read_bytes())
 print(json.dumps(r))
else:raise ValueError('commit/push/verify')
