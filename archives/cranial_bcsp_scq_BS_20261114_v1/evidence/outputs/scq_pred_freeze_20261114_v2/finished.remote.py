from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'SCQ_BS_CD_native_prediction_execution_request_v2.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == 'ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a'
q = json.loads(qp.read_bytes())
assert (O/'exit_code.txt').read_text().strip()=='0' and not (O/'failure.json').exists()
pid=(O/'worker.pid').read_text().strip();p=Path('/proc/'+pid)
assert not p.exists() or q['entry']['path'].encode() not in (p/'cmdline').read_bytes()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
print(json.dumps(dict(status='EXIT0_TMUX_WORKER_ABSENT',hostname=socket.gethostname(),uid=os.getuid(),free_disk_bytes=__import__('shutil').disk_usage(O).free)))
