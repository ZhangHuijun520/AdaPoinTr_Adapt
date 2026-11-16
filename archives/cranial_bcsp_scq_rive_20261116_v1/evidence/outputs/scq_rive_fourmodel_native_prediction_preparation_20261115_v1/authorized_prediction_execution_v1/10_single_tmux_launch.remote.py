import pathlib,json,hashlib,os,socket
P=pathlib.Path
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/RIVE_fourmodel_native_prediction_execution_request_v1.json');b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q=json.loads(b);I=q['identity'];assert socket.gethostname()==I['hostname'] and os.getuid()==I['uid']==1000
import subprocess,shutil,shlex
controls={'/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/control/native_prediction_authorization_v1.json': '4eb6e3a82e1f45ba12a6f76bf11e938efe4aab5389858771ec680e16580091a6', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/control/native_prediction_runtime_v1.json': 'b51af90679fcbe8c16fd25d452eb0d2b8f42601ebffe9ecb1aa068239fc7bc31', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/control/native_prediction_launch_once_v1.sh': '7844b7236012252ba3f4684847db849e309e352147372cd9dcebebb9886dbbfb'}
for p,h in controls.items():
 x=P(p);assert x.is_file() and not any(y.is_symlink() for y in (x,*x.parents)) and hashlib.sha256(x.read_bytes()).hexdigest()==h
for p in (q['output'],q['launch_attempt']):
 x=P(p);assert not os.path.lexists(x) and not any(y.is_symlink() for y in (x,*x.parents))
assert shutil.disk_usage(I['project']).free>=q['limits']['output_bytes']+q['limits']['minimum_free_disk_bytes']
g=[s.strip() for s in subprocess.check_output(['/usr/bin/nvidia-smi','--id='+I['gpu_uuid'],'--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')]
assert g[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(g[4])<=256
L=q['launch_contract'];session=L['tmux_session'];assert subprocess.run(['tmux','has-session','-t','='+session],capture_output=True).returncode==1
with P(q['launch_attempt']).open('x') as f:json.dump(dict(status='CLAIMED_BEFORE_TMUX',request_sha256='ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'),f);f.flush();os.fsync(f.fileno())
r=subprocess.run(['tmux','new-session','-d','-s',session,'bash '+shlex.quote(L['launcher'])],capture_output=True,text=True,timeout=10)
print(json.dumps(dict(status='SINGLE_PREDICTION_TMUX_SUBMIT_RESULT',returncode=r.returncode,session=session,stdout=r.stdout,stderr=r.stderr,gpu=g)),flush=True)
assert r.returncode==0
