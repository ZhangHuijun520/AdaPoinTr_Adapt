from pathlib import Path
import socket, os, subprocess, hashlib, json, time
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v1')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
assert hashlib.sha256((I / 'SCQ_RF_artificial_cuda_execution_request_v1.json').read_bytes()).hexdigest() == '85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32'
q = json.loads((I / 'SCQ_RF_artificial_cuda_execution_request_v1.json').read_bytes())
assert (O/'exit_code.txt').read_text().strip()=='1' and (O/'failure.json').is_file() and not (O/'completion.json').exists()
pid=(O/'worker.pid').read_text().strip();assert pid.isdigit()
p=Path('/proc/'+pid);assert not p.exists() or q['entry']['path'].encode() not in (p/'cmdline').read_bytes()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
a=[x.strip() for x in subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')]
v=q['identity'];assert a==[v['gpu_uuid'],v['gpu_name'],v['driver_version'],str(v['nvidia_smi_memory_total_MiB'])]
print(json.dumps(dict(status='FAILED_EXIT1_TMUX_AND_WORKER_ABSENT',hostname=socket.gethostname(),uid=os.getuid(),GPU=a,worker_PID=pid)))
