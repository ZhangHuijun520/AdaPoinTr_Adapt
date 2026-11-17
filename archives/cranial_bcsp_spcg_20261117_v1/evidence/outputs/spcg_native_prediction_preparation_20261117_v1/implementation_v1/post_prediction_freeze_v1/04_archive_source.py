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
import tarfile
c=read(o/'completion.json')['archive'];a=Path(c['path']);assert a==o/'development_predictions_v1.tar.gz' and record(a)=={k:c[k] for k in ['bytes','sha256']};records=c['members'];expected={x['prediction_filename'] for x in idx['inputs']}|{'inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl'};assert len(records)==len({x['name'] for x in records})==635 and {x['name'] for x in records}==expected
with tarfile.open(a) as t:
 members=t.getmembers();assert len(members)==635 and [x.name for x in members]==[x['name'] for x in records]
 for m,x in zip(members,records):
  assert m.isfile() and m.name in expected and m.size==x['bytes'];h=hashlib.sha256()
  with t.extractfile(m) as f:
   for z in iter(lambda:f.read(1048576),b''):h.update(z)
  assert h.hexdigest()==x['sha256'] and record(o/m.name)=={k:x[k] for k in ['bytes','sha256']}
assert (o/(a.name+'.sha256')).read_text()==c['sha256']+'  '+a.name+'\n' and int((o/(a.name+'.bytes')).read_text())==c['bytes']
assert (o/(a.name+'.contents.sha256')).read_text()==''.join(x['sha256']+'  '+x['name']+'\n' for x in records)
print(json.dumps(dict(checks=dict(archive_hash_bytes=True,members635_exact=True,all_archive_members_match_live=True,sidecars=True),archive={k:c[k] for k in ['path','bytes','sha256']},download_files=[dict(path=str(p),**record(p)) for p in [a,*[o/(a.name+x) for x in ['.sha256','.bytes','.contents.sha256']]]])))
