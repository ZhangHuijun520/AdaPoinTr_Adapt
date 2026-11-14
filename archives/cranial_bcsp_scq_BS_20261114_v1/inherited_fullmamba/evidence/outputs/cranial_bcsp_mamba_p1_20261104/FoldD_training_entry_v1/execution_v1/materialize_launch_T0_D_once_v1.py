import os,json,socket,hashlib,subprocess,time
from pathlib import Path
def check(v,t):
 if not v:raise RuntimeError(t)
def clean(p):
 p=Path(p);check(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'link/path '+str(p));return p
def sha(p):return hashlib.sha256(clean(p).read_bytes()).hexdigest()
def exact(r):
 p=clean(r['path']);check(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'identity '+str(p));return p
def emit(p,obj):
 with clean(p).open('x',encoding='ascii') as f:json.dump(obj,f,indent=2);f.flush();os.fsync(f.fileno())
root=clean('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldD_training_20261106_v1')
qh='6a9e9bcdbfa60a6a9bc6b80c6d2d1374796aa02c919766c2fb70b3a0aa764f82';rp=root/'T0_foldD_seed0_training_execution_request_v1.json';check(sha(rp)==qh,'request hash');q=json.loads(rp.read_bytes());L=q['launch_contract'];I=q['identity']
check(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'],'identity');os.chdir(I['project'])
for r in [q['implementation']['entry'],q['pair_contract'],L['launcher_template']]:exact(r)
check(sha(root/'implementation_P3_v1.json')==q['provenance']['implementation_P3_sha256'] and sha(root/'CPU_contract_result_v1.json')==q['provenance']['CPU_contract_result_sha256'],'P3/CPU evidence')
check(not list((root/'control').iterdir()),'control directory must be empty')
check(not clean(q['output']).exists(),'output already exists')
check(not any(clean(p).exists() for p in [L['authorization'],L['runtime'],L['launcher'],q['launch_attempt']]),'controls already exist')
check(subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==1,'tmux already exists')
g=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,memory.used','--format=csv,noheader,nounits'],timeout=15,text=True).strip().split(',');check(g[0].strip()==I['gpu_uuid'] and int(g[1])<=256,'GPU idle')
a=dict(schema='bcsp-p1-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='User explicitly authorized request SHA256 6a9e9bcdbfa60a6a9bc6b80c6d2d1374796aa02c919766c2fb70b3a0aa764f82: uploaded, verify, exclusive install and unique T0 Fold D scratch training,3900steps; no M0/BNCal/evaluation/retry.')
emit(L['authorization'],a);ah=sha(L['authorization'])
emit(L['runtime'],dict(schema='bcsp-p1-training-runtime-v1',request_sha256=qh,authorization_sha256=ah));rh=sha(L['runtime'])
template=Path(L['launcher_template']['path']).read_text();text=template.replace('REQUEST_SHA256',qh).replace('AUTHORIZATION_SHA256',ah).replace('RUNTIME_SHA256',rh)
check(not any(x in text for x in ['REQUEST_SHA256','AUTHORIZATION_SHA256','RUNTIME_SHA256']),'launcher placeholders')
with clean(L['launcher']).open('x',encoding='ascii') as f:f.write(text);f.flush();os.fsync(f.fileno())
os.chmod(L['launcher'],0o700)
emit(q['launch_attempt'],dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh))
print(json.dumps(dict(phase='MATERIALIZED_SINGLE_ATTEMPT_CLAIMED',authorization_sha256=ah,runtime_sha256=rh,launcher_sha256=sha(L['launcher']))),flush=True)
r=subprocess.run(['tmux','new-session','-d','-s',L['tmux_session'],'-c',I['project'],'/bin/bash '+L['launcher']],capture_output=True,text=True,timeout=10)
check(r.returncode==0,'tmux start failed: '+r.stderr[:512]);time.sleep(2)
live=subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
print(json.dumps(dict(status='SINGLE_TMUX_START_RETURNED',tmux_returncode=r.returncode,session=L['tmux_session'],session_present=live,output=q['output'],exit_code=Path(L['exit_code']).read_text() if Path(L['exit_code']).exists() else None,log_tail=Path(L['log']).read_text(errors='replace')[-5000:] if Path(L['log']).exists() else None)),flush=True)
