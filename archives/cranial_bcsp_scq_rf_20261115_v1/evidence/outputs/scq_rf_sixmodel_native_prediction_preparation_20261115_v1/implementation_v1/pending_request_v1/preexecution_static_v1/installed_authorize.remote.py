from pathlib import Path
import socket, hashlib, importlib.util, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/bcsp_scq_rf_sixmodel_native_predict_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '7cb29c907a0feb373abe8bf2d35f9d0de9caf36f5619c74fa8d26df48e495f18'
s = importlib.util.spec_from_file_location('installed_scq_authorize', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def rec(p, h):
    return dict(path=p, bytes=Path(p).stat().st_size, sha256=h)
q = m.authorize(rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json', 'b503b487e2ed3a00b60400f2e71c98a2d56931dbdf25a77ff32e717b4ff1e561'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_authorization_v1.json', '56ef2d970f5b384018b48df1e7bb813d91ef4b46f191ef14d1cacbb8764cda49'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_runtime_v1.json', '7a25572a9068db05f2db1427182f58e2bd4d62ea7624f0b862d0653c3343e416'))
index = m.bound(q['input_index'])
(runs, rows) = m.validate_index(index, m.bound(q['fold_binding']))
m.validate_source(index, None, [json.loads(x) for x in m.exact(q['source_manifest']).read_text().splitlines()])
m.validate_evidence(q, index)
assert len(runs) == 6 and len(rows) == 630
print(json.dumps(dict(status='INSTALLED_AUTHORIZE_AND_EVIDENCE_PASS', forwards=630, model_calls=0)))