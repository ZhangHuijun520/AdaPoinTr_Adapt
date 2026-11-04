import datetime,hashlib,json,os,shlex,socket,subprocess,sys
from pathlib import Path
H='68938b967e6c84702e980d6d1ee43435d8cb6408d6b5748b83b33eef83d66738'
root=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rp=root/'evidence/execution_request_v1.json';assert sha(rp)==H
q=json.loads(rp.read_text(encoding='utf-8'));c=q['future_control_paths'];i=q['identity']
assert socket.gethostname()==i['hostname'] and os.getuid()==i['uid']
os.chdir(i['project']);assert Path.cwd()==Path(i['project'])
assert str(Path(sys.executable).resolve())==i['python_realpath'] and sys.version.split()[0]==i['python_version']
m=Path('/home/jovyan/bcsp_gpu_preflight_v1.contents.sha256')
assert sha(m)=='3c7d874fc9b31a4bd6ad0c53ada412ade1b6ec82e4c0de336bbdcfb59865db57'
rows=[line.split('  ',1) for line in m.read_text().splitlines()];assert len(rows)==26
for digest,name in rows:
 p=root/name;assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert sha(p)==digest,str(p)
for r in q['future_limited_deployment']['scope_provider_bindings']+q['future_limited_deployment']['scope_environment_metadata_bindings']:
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
a=Path(c['authorization']);auth=json.loads(a.read_text(encoding='utf-8'))
assert auth['request_sha256']==H and auth['explicit_user_authorization'] is True and 'runtime_sha256' not in auth
assert json.loads(Path(c['runtime']).read_text())=={'schema':'bcsp-preflight-runtime-v1','request_sha256':H,'authorization_sha256':sha(a)}
def smi(query):return subprocess.check_output(['/usr/bin/nvidia-smi','--id='+i['gpu_uuid'],query,'--format=csv,noheader,nounits'],text=True,timeout=5).strip()
gpu=[x.strip() for x in smi('--query-gpu=uuid,name,driver_version,memory.total,memory.used').split(',')]
assert gpu[:3]==[i['gpu_uuid'],i['gpu_name'],i['driver_version']] and int(gpu[3])==i['nvidia_smi_memory_total_MiB']
assert int(gpu[4])<=q['resources']['maximum_initial_gpu_used_MiB'] and not smi('--query-compute-apps=pid')
session=q['future_start_contract']['tmux_session']
assert subprocess.run(['tmux','has-session','-t',session],capture_output=True).returncode!=0
out=Path(c['summary']).parent
assert not out.exists() and not any(x.is_symlink() for x in (out,*out.parents))
marker=Path(c['attempt_marker']);assert marker.parent.is_dir() and not marker.parent.is_symlink()
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with marker.open('x',encoding='utf-8') as f:json.dump({'status':'CLAIMED_BEFORE_TMUX','request_sha256':H,'UTC':started,'launcher_sha256':sha(Path(c['launcher']))},f)
r=subprocess.run(['tmux','new-session','-d','-s',session,'bash '+shlex.quote(c['launcher'])],capture_output=True,text=True,timeout=10)
print(json.dumps([r.returncode,session,started]),flush=True)
assert r.returncode==0,r.stderr
