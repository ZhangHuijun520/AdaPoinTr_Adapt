import pathlib, hashlib, json, importlib.util, socket, os
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
root = P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1')
p = root / 'bcsp_rive_training_entry_v1.py'
assert hashlib.sha256(p.read_bytes()).hexdigest() == '2b864497f28d1940af10bcb9d5b099e9846dfd0faf284785bd4e7b8b7980de15'
s = importlib.util.spec_from_file_location('rive_installed_contract_only', p)
e = importlib.util.module_from_spec(s)
s.loader.exec_module(e)
run = 'SCQ_RIVE_Requery_foldD_seed0_train_20261115_v1'
control = root / 'control' / run

def rec(p, h):
    return dict(path=str(p), bytes=p.stat().st_size, sha256=h)
result = e.authorize(rec(root / (run + '_execution_request_v1.json'), 'c7519213883f5ffd7014576ab482beac4456ace3e4656606bcc40714672efba1'), rec(control / 'authorization_v1.json', 'a9fdaf7ffb66bc7e04ed1d7b5ca7e740e7ea158a5fb23c205edac5ffe2837b2e'), rec(control / 'runtime_v1.json', '4fb7ad4408456198daabb01b81e6e8ff8cf877f67cb8f01437364b1a6b76bcb0'))
assert result[0]['arm'] == 'RF-Requery' and result[0]['fold'] == 'D' and (len(result[3]) == 315) and (result[1]['counts']['updates'] == 3900)
print(json.dumps(dict(status='INSTALLED_ACTUAL_AUTHORIZE_PASS', cases=len(result[3]), updates=3900, effective_wall=result[0]['resources']['wall_seconds'], legacy_wall=result[1]['resources']['wall_seconds'], model_calls=0)))
