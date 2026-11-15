from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_ten_actual_memory_20261114_v1')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'SCQ_RF_ten_memory_execution_request_v1.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == '51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945'
q = json.loads(qp.read_bytes())
assert (O/'exit_code.txt').read_text().strip()=='0' and not (O/'failure.json').exists()
pid=(O/'worker.pid').read_text().strip();p=Path('/proc/'+pid)
assert not p.exists() or q['entry']['path'].encode() not in (p/'cmdline').read_bytes()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
gpu=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total','--format=csv,noheader,nounits'],text=True,timeout=10).strip();a=[x.strip() for x in gpu.split(',')];I=q['identity'];assert a==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])]
print(json.dumps(dict(status='EXIT0_TMUX_WORKER_ABSENT',hostname=socket.gethostname(),uid=os.getuid(),GPU=a,free_disk_bytes=__import__('shutil').disk_usage(O).free)))
