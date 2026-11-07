import ast,hashlib,json,math,pathlib,struct,zipfile
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1')
q=json.loads((R/'H1_C_D_development_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output'])
idx=json.loads(pathlib.Path(q['input_index']['path']).read_bytes());protocol=json.loads(pathlib.Path(q['protocol']['path']).read_bytes())
counts={'C':0,'D':0};values=0
for row in idx['inputs']:
 p=O/'predictions'/(row['run']+'__'+row['case_id']+'.npz');has_coarse=row['case_id'] in protocol['coarse_tensor_cases_by_fold'][row['fold']]
 with zipfile.ZipFile(p) as z:
  names=['prediction.npy']+(['coarse.npy'] if has_coarse else [])
  assert len(z.namelist())==len(names) and set(z.namelist())==set(names)
  for name in names:
   raw=z.read(name);assert raw[:6]==b'\x93NUMPY'
   version=tuple(raw[6:8]);assert version in ((1,0),(2,0))
   width=2 if version==(1,0) else 4;offset=8+width
   size=int.from_bytes(raw[8:offset],'little');header=ast.literal_eval(raw[offset:offset+size].decode('latin1'))
   n=8192 if name=='prediction.npy' else 256
   assert header==dict(descr='<f4',fortran_order=False,shape=(n,3))
   data=raw[offset+size:];assert len(data)==n*3*4
   assert all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',data));values+=n*3
 if has_coarse:counts[row['fold']]+=1
assert counts=={'C':7,'D':5}
print(json.dumps(dict(status='ALL210_NPZ_SCHEMA_FINITE_ARRAYS_PASS',prediction_arrays=210,coarse_arrays=counts,finite_float32_values=values,GT_arrays_present=False,checkpoint_loaded=False,new_forward_calls=0,server_writes=0)),flush=True)
