from pathlib import Path
import socket, hashlib, importlib.util, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/bcsp_scq_rf_sixmodel_native_predict_v2.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '221210ca3e51fe4178be068abab1cb2e6c98d9731efb474d1ee08f31ec4c7857'
s = importlib.util.spec_from_file_location('installed_scq_authorize', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def rec(p, h):
    return dict(path=p, bytes=Path(p).stat().st_size, sha256=h)
q = m.authorize(rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json', '5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_authorization_v2.json', 'f2eb8524530bda209dd065bcfa5a1c3dfd9d46911b06f344a95b880313ceaa6e'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/control/native_prediction_runtime_v2.json', '7053851f0aa1eeff3fcdd0ae58a83ddbaf5ed658cfd3dc496ad4d1669ffc350b'))
index = m.bound(q['input_index'])
(runs, rows) = m.validate_index(index, m.bound(q['fold_binding']))
m.validate_source(index, None, [json.loads(x) for x in m.exact(q['source_manifest']).read_text().splitlines()])
m.validate_evidence(q, index)
assert len(runs) == 6 and len(rows) == 630
print(json.dumps(dict(status='INSTALLED_AUTHORIZE_AND_EVIDENCE_PASS', forwards=630, model_calls=0)))