from pathlib import Path
import socket, hashlib, importlib.util, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/bcsp_scq_fourmodel_native_predict_v2.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'c74e0da099d170dca3f4d1e002998ad0ce634aae702f0d2e6b324cc469ef5d81'
s = importlib.util.spec_from_file_location('installed_scq_authorize', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def rec(p, h):
    return dict(path=p, bytes=Path(p).stat().st_size, sha256=h)
q = m.authorize(rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/SCQ_BS_CD_native_prediction_execution_request_v2.json', 'ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_authorization_v2.json', '057e9e4b39812cae59bafa29ddf2938be1ea4d2cf711304a2fb88e86e6b769e4'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2/control/native_prediction_runtime_v2.json', 'f49b1980e1efb3d0248ddf0581228d7f1a9244f80158b076a9dbd162b523e042'))
index = m.bound(q['input_index'])
(runs, rows) = m.validate_index(index, m.bound(q['fold_binding']))
m.validate_source(index, None, [json.loads(x) for x in m.exact(q['source_manifest']).read_text().splitlines()])
m.validate_evidence(q, index)
assert len(runs) == 4 and len(rows) == 420
print(json.dumps(dict(status='INSTALLED_AUTHORIZE_AND_EVIDENCE_PASS', forwards=420, model_calls=0)))