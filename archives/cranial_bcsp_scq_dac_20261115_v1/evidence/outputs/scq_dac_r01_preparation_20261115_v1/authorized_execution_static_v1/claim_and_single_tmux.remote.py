from pathlib import Path
import socket, json, hashlib, subprocess, shlex, os
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000

def valid(p, h):
    p = Path(p)
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (hashlib.sha256(p.read_bytes()).hexdigest() == h)
valid('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/SCQ_DAC_R1_execution_request_v1.json', '129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8')
valid('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/authorization_v1.json', 'ccfd8c934d6a5677f6e6cf8491ebf6b7139e224b54755995fba9ab41bb952e45')
valid('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/runtime_v1.json', '7a650ae40ae1f0a392b520e4aa21e91b3eec5fbeb68b620d437251c2a451e804')
valid('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/launch_once_v1.sh', 'f4612ac70d273eed1909df4c2a6ae11bd133cd15a576d3c13fc3949e6b829300')
assert not Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1').exists() and subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_dac_r1_frozen20_20261115_v1'], capture_output=True).returncode == 1
m = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/attempt_claim_v1.json')
assert not m.exists() and (not any((x.is_symlink() for x in (m, *m.parents))))
with m.open('x') as f:
    json.dump(dict(status='CLAIMED_BEFORE_TMUX', request_sha256='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'), f)
x = subprocess.run(['tmux', 'new-session', '-d', '-s', 'bcsp_scq_dac_r1_frozen20_20261115_v1', shlex.join(['/bin/bash', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/launch_once_v1.sh'])], capture_output=True, text=True, timeout=10)
assert x.returncode == 0, dict(rc=x.returncode, stdout=x.stdout, stderr=x.stderr)
print(json.dumps(dict(status='SINGLE_DAC_R1_TMUX_ATTEMPT_SUBMITTED', session='bcsp_scq_dac_r1_frozen20_20261115_v1', request_sha256='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8', marker=str(m), automatic_retry=False)))