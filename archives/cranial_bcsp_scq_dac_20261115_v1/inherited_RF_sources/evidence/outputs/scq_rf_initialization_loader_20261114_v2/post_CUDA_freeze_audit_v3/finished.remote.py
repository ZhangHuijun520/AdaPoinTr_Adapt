from pathlib import Path
import socket, os, subprocess, hashlib, json, time
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_artificial_cuda_20261114_v3')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v3')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
assert hashlib.sha256((I / 'SCQ_RF_artificial_cuda_execution_request_v3.json').read_bytes()).hexdigest() == '8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'
q = json.loads((I / 'SCQ_RF_artificial_cuda_execution_request_v3.json').read_bytes())
assert (O/'exit_code.txt').read_text().strip()=='0' and not (O/'failure.json').exists() and not (O/'monitor_failure.json').exists() and (O/'completion.json').is_file()
pid=(O/'worker.pid').read_text().strip();assert pid.isdigit()
p=Path('/proc/'+pid);assert not p.exists() or q['entry']['path'].encode() not in (p/'cmdline').read_bytes()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
a=[x.strip() for x in subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')]
v=q['identity'];assert a==[v['gpu_uuid'],v['gpu_name'],v['driver_version'],str(v['nvidia_smi_memory_total_MiB'])]
print(json.dumps(dict(status='EXIT0_TMUX_AND_WORKER_ABSENT',hostname=socket.gethostname(),uid=os.getuid(),GPU=a,worker_PID=pid)))
