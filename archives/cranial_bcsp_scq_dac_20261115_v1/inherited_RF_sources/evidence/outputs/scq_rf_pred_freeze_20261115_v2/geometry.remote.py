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
idx=json.loads(Path(q['input_index']['path']).read_bytes());logs=[json.loads(x) for x in (O/'geometry_summary.jsonl').read_text().splitlines()];assert len(logs)==630
maxerr=0.
for row,g in zip(idx['inputs'],logs):
 assert g['run']==row['run'] and g['case_id']==row['case_id']
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:c=z['coarse'].astype('float64');d=z['prediction'].astype('float64');raw=z['Qraw'].astype('float64');delta=z['delta']
 for key,x in [('coarse',c),('dense',d),('Qraw',raw)]:
  mean=x.mean(0);v=x-mean;expected=dict(centroid=mean,bbox_min=x.min(0),bbox_max=x.max(0),radius_gyration=n.sqrt((v*v).sum(1).mean()),covariance_eigenvalues=n.linalg.eigvalsh(v.T@v/len(x)))
  for k,value in expected.items():
   err=float(n.max(n.abs(n.asarray(g[key][k])-value)));maxerr=max(maxerr,err);assert n.allclose(g[key][k],value,rtol=1e-10,atol=1e-12)
 assert g['coarse']['finite_count']==256 and g['dense']['finite_count']==8192
 offsets=d.reshape(256,32,3)-c[:,None,:]
 assert n.allclose(g['mean_dense_minus_coarse'],offsets.mean((0,1)),rtol=1e-10,atol=1e-12) and n.allclose(g['offset_mean_squared_radius'],(offsets**2).sum(2).mean(),rtol=1e-10,atol=1e-12)
 assert g['delta_mean_norm']==float(n.linalg.norm(delta,axis=-1).mean()) and g['delta_max_norm']==float(n.linalg.norm(delta,axis=-1).max())
print(json.dumps(dict(status='ALL630_GEOMETRY_LOGS_RECOMPUTED_PASS',predictions=630,max_absolute_stat_error=maxerr,GT_read=False,scoring=False)))
