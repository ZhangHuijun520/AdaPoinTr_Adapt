"""Two bounded, stdlib-only remote read-only queries. No deployment or imports."""
import base64,hashlib,json,shlex,subprocess,sys,zlib
from pathlib import Path
B=Path(__file__).resolve().parent
O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1'
R=O/'server_readiness_v1'
PROJECT='/home/jovyan/adapointr_work/PoinTr'
HOST='shu-common-25721452-notebook-v2iwsa-0'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)

def source(mode):
    head="""import os,socket,json,subprocess,time,hashlib,stat,shutil
from pathlib import Path
t=time.monotonic()
P=Path('/home/jovyan/adapointr_work/PoinTr')
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
assert P.resolve()==P and P.is_dir()
def call(a):return subprocess.check_output(a,cwd=str(P),timeout=8,stderr=subprocess.STDOUT).decode().strip()
"""
    if mode=='identity':
        return head+"""roots=[P/'third_party/bcsp_blue_noise_ab_foldc_seed0_v1',P/'data/bcsp_blue_noise_ab_foldc_seed0_v1',P/'logs/cranial_bcsp_blue_noise_ab_v1']
parents={}
for x in roots:
 assert not x.exists() and not x.is_symlink(),str(x)
 for y in x.parents:
  assert not y.is_symlink(),str(y)
 parents[str(x.parent)]={'is_directory':x.parent.is_dir(),'writable':os.access(x.parent,os.W_OK)}
v={'hostname':socket.gethostname(),'uid':os.getuid(),'project':str(P),'disk_free':shutil.disk_usage(P).free,'gpu':call(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader']),'compute':call(['nvidia-smi','--query-compute-apps=pid,process_name,used_gpu_memory','--format=csv,noheader']),'python_exists':Path('/opt/conda/envs/adapointr-mamba/bin/python3.10').is_file(),'python_realpath':str(Path('/opt/conda/envs/adapointr-mamba/bin/python3.10').resolve()),'python_version':call(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','--version']),'new_roots_absent':[str(x) for x in roots],'parents':parents,'git_head':call(['git','rev-parse','HEAD']),'git_status':call(['git','status','--short']),'memory':Path('/proc/meminfo').read_text().splitlines()[:3],'tmux_sessions':subprocess.run(['tmux','list-sessions','-F','#{session_name}'],capture_output=True,text=True,timeout=5).stdout.strip(),'server_writes':0}
assert v['disk_free']>4*1024**3 and not v['compute']
print(json.dumps(v))
"""
    old=B/'sampling_model_AB_foldC_seed0_20261103_v1/server_assets_observation_v1.json'
    path=PROJECT+'/third_party/bcsp_sampling_ab_foldc_seed0_v1/evidence/server_assets_observation_v1.json'
    return head+f"p=Path({path!r});raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=={sha(old)!r}\n"+"""expected=json.loads(raw)['assets'];assert len(expected)==30
assets=[];total=0
for r in expected:
 p=Path(r['path']);assert p.is_file() and not p.is_symlink(),str(p)
 for parent in p.parents:assert not parent.is_symlink(),str(parent)
 assert p.stat().st_size==r['bytes'],str(p)
 total+=r['bytes'];assert total<=20*1024**2 and time.monotonic()-t<35
 assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],str(p)
 assets.append(r)
print(json.dumps({'status':'SELECTED30_HASH_PASS','assets':assets,'hashed_bytes':total,'server_writes':0,'seconds':time.monotonic()-t}))
"""

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    mode=sys.argv[1];assert mode in ('identity','identity_v2','assets')
    R.mkdir(exist_ok=True)
    value=source('identity' if mode=='identity_v2' else mode)
    if mode=='identity_v2':
        anchor="v={'hostname':socket.gethostname()"
        value=value.replace(anchor,"def git(args):\n r=subprocess.run(['git']+args,cwd=str(P),capture_output=True,text=True,timeout=8);return {'returncode':r.returncode,'stdout':r.stdout.strip(),'stderr':r.stderr.strip()}\n"+anchor)
        value=value.replace("'git_head':call(['git','rev-parse','HEAD'])","'git_head':git(['rev-parse','HEAD'])").replace("'git_status':call(['git','status','--short'])","'git_status':git(['status','--short'])")
    raw=value.encode('ascii');p=R/(mode+'_probe_v1.py')
    with p.open('xb') as f:f.write(raw)
    encoded=base64.b64encode(zlib.compress(raw,9)).decode()
    code="import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('"+encoded+"')),'blue_readonly','exec'))"
    cmd='/usr/bin/timeout --signal=TERM --kill-after=2s 40s /opt/conda/bin/python -I -S -B -c '+shlex.quote(code)
    assert len(cmd.encode())<=4096
    dump(R/(mode+'_scope_v1.json'),{'source_sha256':sha(p),'command_bytes':len(cmd.encode()),'remote_seconds':40,'transport_seconds':50,'local_seconds':60,'assets_exact_count':30 if mode=='assets' else 0,'max_hash_bytes':20*1024**2 if mode=='assets' else 0,'server_writes':0,'no_model_import_or_payload':True})
    try:
        r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','50','--',cmd],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
        rc,out,err=r.returncode,r.stdout,r.stderr
    except subprocess.TimeoutExpired as e:
        rc,out,err=None,e.stdout or b'',e.stderr or b''
    dump(R/(mode+'_capture_v1.json'),{'returncode':rc,'stdout_base64':base64.b64encode(out).decode(),'stderr_sha256':hashlib.sha256(err).hexdigest()})
    assert rc==0,'read-only query failed; stop, no retry'
    v=json.loads(out.decode('utf-8'));dump(R/(mode+'_observation_v1.json'),v)
    print(json.dumps(v if mode=='identity' else {k:v[k] for k in ['status','hashed_bytes','seconds','server_writes']}))
if __name__=='__main__':main()
