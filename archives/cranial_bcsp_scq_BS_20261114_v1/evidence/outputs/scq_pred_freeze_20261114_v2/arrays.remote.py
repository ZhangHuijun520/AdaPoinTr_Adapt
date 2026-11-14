from pathlib import Path, PurePosixPath
import socket, os, subprocess, json, hashlib, time, sys
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0' and os.getuid() == 1000
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_BS_CD_native_development_20261114_v2')
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v2')
assert not any((p.is_symlink() for p in (O, *O.parents, I, *I.parents)))
qp = I / 'SCQ_BS_CD_native_prediction_execution_request_v2.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest() == 'ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a'
q = json.loads(qp.read_bytes())
sys.path.insert(0,'/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages')
import numpy as n
idx=json.loads(Path(q['input_index']['path']).read_bytes());count=0
for row in idx['inputs']:
 with n.load(O/row['prediction_filename'],allow_pickle=False) as z:
  assert len(z.files)==4 and set(z.files)=={'prediction','coarse','Qraw','delta'}
  d,c,r,v=z['prediction'],z['coarse'],z['Qraw'],z['delta']
  assert d.shape==(8192,3) and c.shape==r.shape==v.shape==(256,3)
  assert all(x.dtype==n.float32 and n.isfinite(x).all() for x in [d,c,r,v])
  assert n.allclose(r+v,c,rtol=2e-6,atol=2e-7)
  if row['variant']=='B':assert n.array_equal(r,c) and n.count_nonzero(v)==0
 count+=1
assert count==420 and not list((O/'context').iterdir()) and not list((O/'traces').iterdir())
print(json.dumps(dict(status='ALL420_FP32_FINITE_QRAW_QUSED_DELTA_P_PASS',predictions=count,context=0,traces=0,GT_arrays_read=0,GPU_calls=0)))
