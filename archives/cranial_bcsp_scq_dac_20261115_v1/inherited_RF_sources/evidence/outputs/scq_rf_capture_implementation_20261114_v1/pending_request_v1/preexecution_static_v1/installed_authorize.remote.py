from pathlib import Path
import socket, hashlib, importlib.util, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/bcsp_scq_rf_memory_capture_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '678a6fffcba13a7b4dec354833fc8275bcd3081adffe5b4581673b977086e5c9'
s = importlib.util.spec_from_file_location('installed_scq_authorize', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def rec(p, h):
    return dict(path=p, bytes=Path(p).stat().st_size, sha256=h)
q = m.authorize(rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/SCQ_RF_ten_memory_execution_request_v1.json', '51ee9e42bc29c93002b71c8449b59ed14453aeb6d57cda242857e045cd536945'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/authorization_v1.json', '235c1a571a16d8d1fe756397a5b4f901b4e57b5ff45e24be72d20fee1ef556c9'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/runtime_v1.json', '4457700eecf38cde42eb90034f918209c0baf75152332d01278c481fd48f54f0'))
p = m.source('readonly_capture_parent', q['parent_entry'])
m.validate_reuse(q, p, m.bound(q['parent_request']))
assert len(q['runs']) == 2 and len(q['cases']) == 10
print(json.dumps(dict(status='INSTALLED_AUTHORIZE_AND_EVIDENCE_PASS', forwards=10, model_calls=0)))