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
idx=json.loads(Path(q['input_index']['path']).read_bytes());count=0
for row in idx['inputs']:
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:
  assert len(z.files)==9 and set(z.files)=={'prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'}
  d,c,r,v=z['prediction'],z['coarse'],z['Qraw'],z['delta']
  assert d.shape==(8192,3) and c.shape==r.shape==v.shape==(256,3)
  assert all(x.dtype==n.float32 and n.isfinite(x).all() for x in [d,c,r,v])
  assert n.allclose(r+v,c,rtol=2e-5,atol=2e-6)
  a,b,e,f,g=z['Q0'],z['Q1'],z['Q2'],z['delta0'],z['delta1']
  assert all(x.shape==(256,3) and x.dtype==n.float32 and n.isfinite(x).all() for x in [a,b,e,f,g])
  assert n.array_equal(a,r) and n.array_equal(e,c) and n.allclose(a+f,b,rtol=2e-5,atol=2e-6) and n.allclose(b+g,e,rtol=2e-5,atol=2e-6)
  if row['variant']=='S':assert n.array_equal(b,e) and n.array_equal(f,v) and n.count_nonzero(g)==0
 count+=1
assert count==630 and not list((O/'context').iterdir()) and not list((O/'traces').iterdir())
print(json.dumps(dict(status='ALL630_FP32_FINITE_QRAW_QUSED_DELTA_P_PASS',predictions=count,context=0,traces=0,GT_arrays_read=0,GPU_calls=0)))
