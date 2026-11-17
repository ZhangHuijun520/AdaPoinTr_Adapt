# -*- coding: utf-8 -*-
"""Publish TRACE text/code snapshot with annotated tag. Checkpoints/arrays stay local."""
import hashlib,json,os,shutil,socket,subprocess,sys
from pathlib import Path

R=Path(__file__).resolve().parent.parent;D=R/'deliverables/trace_20261117_v1'
REPO=R/'outputs/p1pub';PUB=D/'public_payload';TARGET=REPO/'archives/cranial_bcsp_trace_20261117_v1'
BRANCH='archive/cranial-bcsp-trace-20261117';TAG='cranial-bcsp-trace-20261117-v1'
URL='https://github.com/ZhangHuijun520/AdaPoinTr_Adapt.git'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def emit(p,x):put(p,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args,network=False,check=True,timeout=120):
    env=dict(os.environ)
    for key in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy']:env.pop(key,None)
    proxy=''
    if network:
        for port in [12000,7890]:
            s=socket.socket();s.settimeout(1)
            try:ok=s.connect_ex(('127.0.0.1',port))==0
            finally:s.close()
            if ok:proxy='http://127.0.0.1:'+str(port);break
    p=subprocess.run(['git','-c','safe.directory='+REPO.as_posix(),'-c','core.longpaths=true','-c','http.proxy='+proxy,'-c','http.lowSpeedLimit=1024','-c','http.lowSpeedTime=30','-C',str(REPO),*args],capture_output=True,env=env,timeout=timeout)
    if check and p.returncode:raise RuntimeError(dict(args=args,returncode=p.returncode,stderr=p.stderr.decode('utf-8','replace')[-1800:]))
    return p

def commit():
    assert read(D/'long_term_backup_receipt_v1.json')['status']=='TRACE_LONG_TERM_BACKUP_ALL_MEMBER_READBACK_PASS'
    assert git('status','--porcelain').stdout==b'' and git('remote','get-url','origin').stdout.decode().strip()==URL
    assert not TARGET.exists();parent=git('rev-parse','HEAD').stdout.decode().strip();assert parent=='8527cdf92044a0e6b8cf5afa5bfc23ce466b88e8'
    assert git('show-ref','--verify','--quiet','refs/heads/'+BRANCH,check=False).returncode==1
    assert git('show-ref','--verify','--quiet','refs/tags/'+TAG,check=False).returncode==1
    git('switch','-c',BRANCH);files={}
    for p in sorted(PUB.rglob('*')):
        if not p.is_file():continue
        assert not p.is_symlink() and p.suffix.lower() not in {'.npz','.npy','.pth','.pt','.bin','.gz','.whl','.so','.dll','.pyd','.exe','.html'}
        dest=TARGET/p.relative_to(PUB);put(dest,p.read_bytes());assert sha(dest)==sha(p);files[dest.relative_to(REPO).as_posix()]=dest
    for name in ['trace_code_results_20261117_v1.tar.gz.sha256','trace_code_results_20261117_v1.tar.gz.bytes','trace_code_results_20261117_v1.tar.gz.contents.sha256','archive_verification_v1.json','long_term_backup_receipt_v1.json']:
        dest=TARGET/name;put(dest,(D/name).read_bytes());files[dest.relative_to(REPO).as_posix()]=dest
    dest=TARGET/'.gitattributes';put(dest,b'* -text -filter\n');files[dest.relative_to(REPO).as_posix()]=dest
    git('add','-f','--',TARGET.relative_to(REPO).as_posix(),timeout=240)
    staged={s.decode('utf-8') for s in git('diff','--cached','--name-only','-z').stdout.split(b'\0') if s};assert staged==set(files)
    objects={}
    for raw in git('ls-files','--stage','-z','--',TARGET.relative_to(REPO).as_posix()).stdout.split(b'\0'):
        if not raw:continue
        meta,name=raw.split(b'\t',1);mode,oid,stage=meta.split();name=name.decode('utf-8');b=files[name].read_bytes()
        assert mode==b'100644' and stage==b'0' and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==oid.decode();objects[name]=oid.decode()
    assert set(objects)==set(files)
    emit(D/'public_index_verification_v1.json',dict(status='TRACE_PUBLIC_INDEX_EXACT_BYTES_PASS',files=len(files),parent_commit=parent,objects=objects,weights_or_binary_arrays=False))
    msg=D/'git_commit_message_v1.txt';put(msg,b'archive: close BCSP-TRACE frozen-weight spatial evidence diagnostic\n\nPreserve four G1/G2 C/D roles, 40 fixed sources/cases and80 zero-update forward traces. Q/P replay exactly matches history. Main C17/D18 correlations do not jointly meet the preregistered investment condition; do not activate G3 or six training runs.\n\nInclude code, original failed fixture evidence, corrected CPU30/P3, formal GPU/CPU freeze audits, case summaries, detailed report and closure. Real checkpoints, raw arrays and artificial weight fixtures remain local only. Historical execution material is inert evidence, not reusable authorization.\n')
    git('commit','--file',str(msg),timeout=240);commit=git('rev-parse','HEAD').stdout.decode().strip()
    tagmsg=D/'annotated_tag_message_v1.txt';put(tagmsg,('BCSP-TRACE formal closure, 2026-11-17.\n\n80 frozen-weight observations; exact historical Q/P replay; NO_SUPPORT_OR_INCONCLUSIVE. No G3 training, no claim all spatial conditions fail.\nLocal complete code/results archive SHA256: '+read(D/'archive_verification_v1.json')['archive']['sha256']+'\nWeights and arrays not published.\n').encode())
    git('tag','-a',TAG,'--file',str(tagmsg));assert git('cat-file','-t',TAG).stdout.strip()==b'tag'
    receipt=dict(status='TRACE_COMMIT_AND_ANNOTATED_TAG_CREATED',repository=URL,branch=BRANCH,tag=TAG,commit=commit,tag_object=git('rev-parse',TAG).stdout.decode().strip(),files=len(files),parent_commit=parent)
    emit(D/'git_commit_tag_receipt_v1.json',receipt);print(json.dumps(receipt),flush=True)

def push():
    r=read(D/'git_commit_tag_receipt_v1.json');assert git('status','--porcelain').stdout==b''
    result=git('push','--atomic','origin','refs/heads/'+BRANCH+':refs/heads/'+BRANCH,'refs/tags/'+TAG+':refs/tags/'+TAG,network=True,check=False,timeout=240)
    put(D/'git_push_stdout.bin',result.stdout);put(D/'git_push_stderr.bin',result.stderr);emit(D/'git_push_exit_v1.json',dict(returncode=result.returncode))
    assert result.returncode==0,result.stderr.decode('utf-8','replace')[-1800:]
    print('TRACE_BRANCH_AND_ANNOTATED_TAG_ATOMIC_PUSH_EXIT0',flush=True)

def verify():
    r=read(D/'git_commit_tag_receipt_v1.json');p=git('ls-remote','origin','refs/heads/'+BRANCH,'refs/tags/'+TAG,'refs/tags/'+TAG+'^{}',network=True,timeout=90)
    refs={s.split()[1]:s.split()[0] for s in p.stdout.decode().splitlines()}
    assert refs=={'refs/heads/'+BRANCH:r['commit'],'refs/tags/'+TAG:r['tag_object'],'refs/tags/'+TAG+'^{}':r['commit']}
    result=dict(**r,refs=refs,weights_uploaded=False,binary_arrays_uploaded=False,server_deletions=0);result['status']='TRACE_INDEPENDENT_REMOTE_BRANCH_TAG_PEELED_COMMIT_VERIFIED'
    emit(D/'publication_receipt_v1.json',result)
    dest=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_TRACE/2026-11-17_code_results_v1')
    for name in ['public_index_verification_v1.json','git_commit_tag_receipt_v1.json','git_push_exit_v1.json','publication_receipt_v1.json']:put(dest/name,(D/name).read_bytes())
    print(json.dumps(result),flush=True)

if __name__=='__main__':
    {'commit':commit,'push':push,'verify':verify}[sys.argv[1]]()
