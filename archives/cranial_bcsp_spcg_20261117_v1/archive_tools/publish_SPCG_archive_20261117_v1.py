# -*- coding: utf-8 -*-
"""Publish exact public SPCG snapshot, branch plus annotated tag; no binary arrays/weights."""
from pathlib import Path
import os,json,hashlib,subprocess,shutil,sys
R=Path(__file__).resolve().parent.parent;D=R/'deliverables/spcg_20261117_v1';PUB=D/'public_payload';REPO=R/'outputs/p1pub';TARGET=REPO/'archives/cranial_bcsp_spcg_20261117_v1';BACK=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_code_results_v1');BRANCH='archive/cranial-bcsp-spcg-20261117';TAG='cranial-bcsp-spcg-20261117-v1'
def lp(p):return Path('\\\\?\\'+str(p.absolute())) if os.name=='nt' else p
def read(p):return json.loads(lp(p).read_bytes())
def sha(p):return hashlib.sha256(lp(p).read_bytes()).hexdigest()
def put(p,b):
 lp(p.parent).mkdir(parents=True,exist_ok=True)
 with lp(p).open('xb') as f:f.write(b)
def emit(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def inventory(root):return [Path(str(Path(d)/n).removeprefix('\\\\?\\')) for d,_,fs in os.walk(lp(root)) for n in fs]
def git(*args,timeout=120,check=True):
 env=os.environ.copy()
 for k in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy']:env.pop(k,None)
 proxy=os.environ.get('SPCG_GIT_HTTP_PROXY','');assert proxy in ['','http://127.0.0.1:12000','http://127.0.0.1:7890']
 cmd=['git','-c','safe.directory='+REPO.as_posix(),'-c','core.longpaths=true','-c','http.proxy='+proxy,'-c','http.lowSpeedLimit=1024','-c','http.lowSpeedTime=30','-C',str(REPO),*args]
 p=subprocess.run(cmd,capture_output=True,env=env,timeout=timeout)
 if check and p.returncode:raise RuntimeError(dict(args=args,code=p.returncode,stderr=p.stderr.decode(errors='replace')[-1600:]))
 return p
phase=sys.argv[1]
if phase=='stage':
 assert read(D/'archive_verification_v1.json')['status']=='SPCG_CODE_RESULTS_ALL_MEMBERS_HASH_VERIFIED' and read(D/'long_term_backup_receipt_v1.json')['status']=='SPCG_LONG_TERM_BACKUP_ALL_MEMBER_READBACK_PASS'
 assert git('status','--porcelain').stdout==b'' and git('remote','get-url','origin').stdout.decode().strip()=='https://github.com/ZhangHuijun520/AdaPoinTr_Adapt.git'
 assert not TARGET.exists();parent=git('rev-parse','HEAD').stdout.decode().strip();git('switch','-c',BRANCH)
 files={}
 for p in inventory(PUB):
  assert p.suffix not in {'.pth','.pt','.npz','.npy','.bin','.gz','.whl','.so','.dll','.pyd','.exe','.html'}
  rel=p.relative_to(PUB);dest=TARGET/rel;lp(dest.parent).mkdir(parents=True,exist_ok=True);shutil.copyfile(lp(p),lp(dest));assert sha(dest)==sha(p);files[dest.relative_to(REPO).as_posix()]=dest
 for name in ['spcg_code_results_20261117_v1.tar.gz.bytes','spcg_code_results_20261117_v1.tar.gz.sha256','spcg_code_results_20261117_v1.tar.gz.contents.sha256','archive_verification_v1.json','long_term_backup_receipt_v1.json']:
  dest=TARGET/name;shutil.copyfile(D/name,dest);assert sha(dest)==sha(D/name);files[dest.relative_to(REPO).as_posix()]=dest
 put(TARGET/'.gitattributes',b'* -text -filter\n');files[(TARGET/'.gitattributes').relative_to(REPO).as_posix()]=TARGET/'.gitattributes'
 rel=TARGET.relative_to(REPO).as_posix();git('add','-f','--',rel,timeout=240);indexed={}
 for raw in git('ls-files','--stage','-z','--',rel).stdout.split(b'\0'):
  if not raw:continue
  meta,path=raw.split(b'\t',1);mode,oid,stage=meta.split();assert mode==b'100644' and stage==b'0';name=path.decode('utf-8');assert name in files;b=lp(files[name]).read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid.decode();indexed[name]=oid.decode()
 assert set(indexed)==set(files)
 receipt=dict(status='SPCG_PUBLIC_INDEX_EXACT_BYTES_VERIFIED',branch=BRANCH,parent_commit=parent,target=str(TARGET),files=len(files),indexed_objects=indexed,no_checkpoints_or_arrays=True)
 emit(D/'public_staging_receipt_v1.json',receipt);print(json.dumps(dict(status=receipt['status'],files=len(files))))
elif phase=='commit':
 assert read(D/'public_staging_receipt_v1.json')['status']=='SPCG_PUBLIC_INDEX_EXACT_BYTES_VERIFIED' and git('branch','--show-current').stdout.decode().strip()==BRANCH
 msg=D/'git_commit_message_v1.txt';put(msg,b'archive: close BCSP-SPCG fixed spatial-probe coarse candidate\n\nPreserve G0/G1/G2 x C/D final3900-step training evidence,630 Native predictions identities,1050 scoring rows, preregistered2000 source-bootstrap draws per fold, all risk transitions and fixed5 coarse/dense diagnostics. G2 is not reliably superior; newly severe9/7 versus rescued4/0.\n\nSingle seed, exposed development data, D_G0 device confounding and missing plannedMemory are disclosed. All binary prediction/initializer/bootstrap arrays and six final checkpoints remain local-only. Historical execution materials are inert evidence; no new experiments or deletion.\n')
 git('commit','--file',str(msg),timeout=240);commit=git('rev-parse','HEAD').stdout.decode().strip();tagmsg=D/'annotated_tag_message_v1.txt'
 put(tagmsg,('BCSP-SPCG research closure,2026-11-17.\n\nSix finalG0/G1/G2 C/D runs, mixed/negative local8 results, source-bootstrap and fixed5 diagnostics frozen. No claim all spatial conditioning fails. Arrays and all six weights local-only.\n\nComplete local code/results archive SHA256: '+read(D/'archive_verification_v1.json')['archive']['sha256']+'\n').encode())
 git('tag','-a',TAG,'--file',str(tagmsg));assert git('cat-file','-t',TAG).stdout.strip()==b'tag'
 receipt=dict(status='SPCG_COMMIT_ANNOTATED_TAG_CREATED',commit=commit,branch=BRANCH,tag=TAG,tag_object=git('rev-parse',TAG).stdout.decode().strip());emit(D/'git_commit_tag_receipt_v1.json',receipt);print(json.dumps(receipt))
elif phase=='push':
 receipt=read(D/'git_commit_tag_receipt_v1.json');assert git('status','--porcelain').stdout==b''
 attempt=sys.argv[2] if len(sys.argv)>2 else 'v1';assert not (D/('push_'+attempt+'_exit.json')).exists()
 p=git('push','--atomic','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH,'refs/tags/'+TAG+':refs/tags/'+TAG,timeout=240,check=False)
 put(D/('push_'+attempt+'_stdout.bin'),p.stdout);put(D/('push_'+attempt+'_stderr.bin'),p.stderr);emit(D/('push_'+attempt+'_exit.json'),dict(returncode=p.returncode))
 assert p.returncode==0,('PUSH_FAILED',p.stderr.decode(errors='replace')[-1800:]);emit(D/'git_push_receipt_v1.json',{**receipt,'status':'ATOMIC_BRANCH_AND_ANNOTATED_TAG_PUSH_EXIT0'});print('ATOMIC_BRANCH_AND_ANNOTATED_TAG_PUSH_EXIT0')
elif phase=='verify':
 receipt=read(D/'git_commit_tag_receipt_v1.json');p=git('ls-remote','origin','refs/heads/'+BRANCH,'refs/tags/'+TAG,'refs/tags/'+TAG+'^{}',timeout=90)
 refs={r.split()[1]:r.split()[0] for r in p.stdout.decode().splitlines()};assert refs=={'refs/heads/'+BRANCH:receipt['commit'],'refs/tags/'+TAG:receipt['tag_object'],'refs/tags/'+TAG+'^{}':receipt['commit']}
 result=dict(repository='https://github.com/ZhangHuijun520/AdaPoinTr_Adapt',refs=refs,**receipt,archive=read(D/'archive_verification_v1.json')['archive'],local_backup=str(BACK),weights_uploaded=False,raw_arrays_uploaded=False,server_deletions=0)
 # Keep final status explicit after merging historical commit metadata.
 result['status']='SPCG_INDEPENDENT_REMOTE_BRANCH_TAG_PEELED_COMMIT_VERIFIED';emit(D/'publication_receipt_v1.json',result)
 for name in ['public_staging_receipt_v1.json','git_commit_tag_receipt_v1.json','git_push_receipt_v1.json','publication_receipt_v1.json']:
  shutil.copyfile(D/name,BACK/name);assert sha(D/name)==sha(BACK/name)
 print(json.dumps(result))
else:raise ValueError('stage/commit/push/verify only')
