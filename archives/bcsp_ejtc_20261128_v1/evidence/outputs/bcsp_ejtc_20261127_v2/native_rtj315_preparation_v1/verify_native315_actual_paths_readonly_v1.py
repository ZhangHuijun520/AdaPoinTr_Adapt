"""Resolve only the fixed 105 cases in the two existing 8k point directories."""
from pathlib import Path
source=Path(__file__).with_name('verify_native315_server_readonly_v1.py').read_text()
source=source.split("first=run(scan,")[0].replace("e=d/'server_readonly_h7vvrr_v1'","e=d/'server_actual_paths_v1'")
exec(compile(source,'<readonly-definitions>','exec'))
code='''import ast,io,struct,zipfile
roots=[Path('/home/jovyan/adapointr_work/PoinTr/data')/('bcsp_geov1_fold'+f+'_8192_seed0_v1/points') for f in ('c','d')]
def verify(name):
 found=[]
 for root in roots:
  p=root/name
  if not p.exists():continue
  a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<1048576
  raw=p.read_bytes()
  with zipfile.ZipFile(io.BytesIO(raw)) as z:b=z.read('partial.npy')
  f=io.BytesIO(b);assert f.read(6)==b'\\x93NUMPY';v=f.read(2)
  assert v in (b'\\x01\\x00',b'\\x02\\x00')
  n=struct.unpack('<H' if v[0]==1 else '<I',f.read(2 if v[0]==1 else 4))[0]
  header=ast.literal_eval(f.read(n).decode('latin1'));partial=f.read()
  assert header==dict(descr='<f4',fortran_order=False,shape=(8192,3)) and len(partial)==98304
  z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
  found.append(dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),partial_array_sha256=hashlib.sha256(partial).hexdigest()))
 return found
'''
resolved=[]
for j in range(0,105,10):
 rows=scope['inputs'][j:j+10];names=[PurePosixPath(r['input']['path']).name for r in rows]
 got=run(code+'print(json.dumps([verify(n) for n in '+repr(names)+']))','actual_paths_'+str(j//10+1).zfill(2))
 for row,matches in zip(rows,got):
  assert len(matches)==1,(row['case_id'],matches)
  m=matches[0];assert [m['bytes'],m['sha256'],m['partial_array_sha256']]==[row['input']['bytes'],row['input']['sha256'],row['partial_array_sha256']]
  resolved.append(dict(case_id=row['case_id'],frozen_path=row['input']['path'],actual=m,path_matches=m['path']==row['input']['path']))
 print('Resolved fixed inputs '+str(len(resolved))+'/105',flush=True)
receipt=dict(status='READINESS_BLOCKED_EXACT_INPUT_PATH_BINDING_MISMATCH',request_sha256=rid,verified_fixed_cases=105,unique_actual_paths=True,all_file_and_partial_hashes_match=True,path_mismatches=sum(not r['path_matches'] for r in resolved),cases=resolved,
 current_identity=i,checkpoint_hashes_verified=3,remote_mutations=False,forward_calls=0,request_modified=False,transport_frozen=False,
 next_scope='Limited input path binding correction and matching CPU regression/P3, then new request hash; scientific cohort and bytes unchanged')
with (e/'Native315_actual_path_readonly_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k!='cases'}))
