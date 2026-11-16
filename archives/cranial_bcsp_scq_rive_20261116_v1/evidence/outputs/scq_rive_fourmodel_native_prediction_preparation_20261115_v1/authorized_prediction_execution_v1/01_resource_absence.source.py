import pathlib,json,hashlib,os,socket
P=pathlib.Path
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/RIVE_fourmodel_native_prediction_execution_request_v1.json');b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q=json.loads(b);I=q['identity'];assert socket.gethostname()==I['hostname'] and os.getuid()==I['uid']==1000
import sys,subprocess,shutil
assert str(P(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version']
os.chdir(I['project']);assert str(P.cwd().resolve())==I['project']
root=P(q['entry']['path']).parent;assert root.is_dir() and not any(x.is_symlink() for x in (root,*root.parents))
absent=[str(root/'control'),q['output'],q['launch_attempt']]+[q['launch_contract'][k] for k in ('authorization','runtime','launcher','log','pid','exit_code')]
for s in absent:
 p=P(s);assert not os.path.lexists(p) and not any(x.is_symlink() for x in (p,*p.parents)),s
assert P(q['output']).parent.is_dir()
g=[x.strip() for x in subprocess.check_output(['/usr/bin/nvidia-smi','--id='+I['gpu_uuid'],'--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')]
assert g[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(g[4])<=256
free=shutil.disk_usage(I['project']).free;assert free>=q['limits']['output_bytes']+q['limits']['minimum_free_disk_bytes']
assert subprocess.run(['tmux','has-session','-t','='+q['launch_contract']['tmux_session']],capture_output=True).returncode==1
print(json.dumps(dict(status='FRESH_PREDICTION_RESOURCE_ABSENCE_PASS',hostname=socket.gethostname(),uid=os.getuid(),gpu=g,free_bytes=free,control_output_claim_session_absent=True,server_writes=0)))
