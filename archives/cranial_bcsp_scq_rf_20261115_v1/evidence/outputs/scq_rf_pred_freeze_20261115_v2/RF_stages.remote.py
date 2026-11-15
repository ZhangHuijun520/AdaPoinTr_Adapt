from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_sixmodel_native_development_20261115_v2')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'SCQ_RF_sixmodel_native_prediction_execution_request_v2.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == '5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9'
q = json.loads(qp.read_bytes())
sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['input_index']['path']).read_bytes());gs=[json.loads(x) for x in (O/'geometry_summary.jsonl').read_text().splitlines()];assert len(gs)==630
for row,g in zip(idx['inputs'],gs):
 assert g['run']==row['run'] and g['case_id']==row['case_id'] and g['RF_second_stage_applicable'] is (row['variant']!='S')
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:
  assert set(g['stage_centroids'])=={'Q0','Q1','Q2','delta0','delta1'}
  for k in g['stage_centroids']:assert n.array_equal(n.asarray(g['stage_centroids'][k]),z[k].mean(0))
print(json.dumps(dict(status='ALL630_RF_STAGE_CENTROID_LOGS_RECOMPUTED_PASS',predictions=630,new_forward=0,GT_read=False)))
