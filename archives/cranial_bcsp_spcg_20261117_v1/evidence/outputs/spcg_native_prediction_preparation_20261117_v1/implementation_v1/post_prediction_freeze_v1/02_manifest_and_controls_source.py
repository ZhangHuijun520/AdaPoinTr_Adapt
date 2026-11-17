from pathlib import Path
import os,socket,json,hashlib
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_native_prediction_20261117_v1');b=(r/'SPCG_sixmodel_native_execution_request_v1.json').read_bytes();assert hashlib.sha256(b).hexdigest()=='c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc';q=json.loads(b);o=Path(q['output'])
def read(p):return json.loads(p.read_bytes())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<128*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns);return dict(bytes=s.st_size,sha256=h.hexdigest())
idx=read(Path(q['input_index']['path']));assert record(Path(q['input_index']['path']))=={k:q['input_index'][k] for k in ['bytes','sha256']}
from collections import Counter
M=[json.loads(l) for l in (o/'inference_manifest.jsonl').read_text().splitlines()];J=[json.loads(l) for l in (o/'forward_attempts.jsonl').read_text().splitlines()];G=[json.loads(l) for l in (o/'geometry_summary.jsonl').read_text().splitlines()];assert len(M)==len(J)==len(G)==630
for i,(m,j,g,x) in enumerate(zip(M,J,G,idx['inputs']),1):
 assert m['forward_index']==j['forward_index']==i and j['status']=='CLAIMED_BEFORE_FORWARD'
 assert all(m[k]==x[k] for k in ['run','case_id','source_id','fold','n_input','n_output','normalization']) and (g['run'],g['case_id'])==(x['run'],x['case_id']) and (j['run'],j['case_id'])==(x['run'],x['case_id'])
 assert m['input_sha256']==x['input']['sha256'] and m['prediction']['name']==x['prediction_filename'] and record(o/x['prediction_filename'])=={k:m['prediction'][k] for k in ['bytes','sha256']}
 pin=next(v for v in idx['runs'] if v['label']==m['run']);assert m['checkpoint_sha256']==pin['checkpoint']['sha256']
json.dumps(G,allow_nan=False);control=Path(q['launch_contract']['authorization']).parent;co={p.name:dict(**record(p),text=p.read_text()) for p in control.iterdir()};installed={p.name:record(p) for p in r.iterdir() if p.is_file()}
print(json.dumps(dict(checks=dict(all630_manifest_journal_geometry=True,each105=dict(Counter(x['run'] for x in M))=={x['label']:105 for x in idx['runs']}),controls=co,installed=installed)))
