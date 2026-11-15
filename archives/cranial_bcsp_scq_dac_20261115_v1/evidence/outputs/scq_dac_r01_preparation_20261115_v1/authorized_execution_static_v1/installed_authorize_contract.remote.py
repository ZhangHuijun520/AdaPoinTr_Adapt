from pathlib import Path
import importlib.util, json, hashlib, socket, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/bcsp_scq_dac_r1_entry_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'b1a1de8833c4699d947bc33878430d5bebf3d9dd83629ddf3ddf4d2617ae8296'
s = importlib.util.spec_from_file_location('dac_installed_authorize_only', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def record(path, h):
    return dict(path=path, bytes=Path(path).stat().st_size, sha256=h)
q = m.authorize(record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/SCQ_DAC_R1_execution_request_v1.json', '129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/authorization_v1.json', 'ccfd8c934d6a5677f6e6cf8491ebf6b7139e224b54755995fba9ab41bb952e45'), record('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/runtime_v1.json', '7a650ae40ae1f0a392b520e4aa21e91b3eec5fbeb68b620d437251c2a451e804'))
assert q['calls'] == dict(native=20, decoder_only=40, decoder=60, h1_new=20, h1_old=20, first_head=20)
assert not any((x in sys.modules for x in ('torch', 'numpy', 'models.AdaPoinTr')))
print(json.dumps(dict(status='INSTALLED_AUTHORIZE_PATH_PASS_NO_MODEL_IMPORT', request_sha256='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8')))