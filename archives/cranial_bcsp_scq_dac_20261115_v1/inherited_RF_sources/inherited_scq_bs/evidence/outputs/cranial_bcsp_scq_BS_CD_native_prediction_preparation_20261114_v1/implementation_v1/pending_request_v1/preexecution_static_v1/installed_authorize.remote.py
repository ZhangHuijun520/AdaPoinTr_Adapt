from pathlib import Path
import socket, hashlib, importlib.util, json
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/bcsp_scq_fourmodel_native_predict_v1.py')
assert hashlib.sha256(p.read_bytes()).hexdigest() == '177685386074462b0dddbeb4adc9b8500e6ad4a3b6296ded8bdf894dffdf645c'
s = importlib.util.spec_from_file_location('installed_scq_authorize', p)
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)

def rec(p, h):
    return dict(path=p, bytes=Path(p).stat().st_size, sha256=h)
q = m.authorize(rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/SCQ_BS_CD_native_prediction_execution_request_v1.json', '760191aeb674533e341d7050db58039eab6ddc7421a773bf36b05e816dea02c4'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_authorization_v1.json', 'abca69f30d2b23ac65f9a3277805ab9031708d55d08218e436623ce2a72a6e58'), rec('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_runtime_v1.json', 'd710dabeacfcdd16a0f894993c9f1e95921c5af6522ac06d4df5e8a5d9964806'))
index = m.bound(q['input_index'])
(runs, rows) = m.validate_index(index, m.bound(q['fold_binding']))
m.validate_source(index, None, [json.loads(x) for x in m.exact(q['source_manifest']).read_text().splitlines()])
m.validate_evidence(q, index)
assert len(runs) == 4 and len(rows) == 420
print(json.dumps(dict(status='INSTALLED_AUTHORIZE_AND_EVIDENCE_PASS', forwards=420, model_calls=0)))