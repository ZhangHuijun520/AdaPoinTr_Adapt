from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_fourmodel_native_development_20261115_v1')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'RIVE_fourmodel_native_prediction_execution_request_v1.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == 'ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q = json.loads(qp.read_bytes())
assert (O / 'exit_code.txt').read_text().strip() == '0' and (not (O / 'failure.json').exists())
pid = (O / 'worker.pid').read_text().strip()
p = Path('/proc/' + pid)
assert not p.exists() or q['entry']['path'].encode() not in (p / 'cmdline').read_bytes()
assert subprocess.run(['tmux', 'has-session', '-t', q['launch_contract']['tmux_session']], capture_output=True, timeout=5).returncode == 1
print(json.dumps(dict(status='EXIT0_TMUX_WORKER_ABSENT', hostname=socket.gethostname(), uid=os.getuid(), free_disk_bytes=__import__('shutil').disk_usage(O).free)))
