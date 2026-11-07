import hashlib,json,pathlib,tarfile
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1')
q=json.loads((R/'H1_C_D_development_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
c=json.loads((O/'completion.json').read_bytes());a=c['archive'];A=pathlib.Path(a['path'])
assert c['status']=='PREDICTIONS_ARCHIVED_AWAITING_LOCAL_SCORING' and c['forwards']==210 and c['request_sha256']=='90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147'
assert A==O/'development_predictions_v1.tar.gz' and A.stat().st_size==a['bytes']==19059283
assert sha(A)==a['sha256']=='48d93ab773d62fe5a59f89f98a7ce97743e6a261e997e23861bbcb35a0f8e1ed'
members={r['name']:r for r in a['members']};assert len(members)==len(a['members'])==215
expected={'predictions/'+p.name for p in (O/'predictions').iterdir()}|set('inference_manifest.jsonl forward_attempts.jsonl geometry_summary.jsonl inference_complete.json resources.jsonl'.split())
assert set(members)==expected
with tarfile.open(A) as t:
 names=t.getnames();assert len(names)==len(set(names))==215 and set(names)==expected
 for m in t.getmembers():
  assert m.isfile() and not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts
  record=members[m.name];raw=t.extractfile(m).read()
  assert len(raw)==m.size==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256']==sha(O/m.name)
side={line.split(None,1)[1]:line.split(None,1)[0] for line in pathlib.Path(str(A)+'.contents.sha256').read_text().splitlines()}
assert len(pathlib.Path(str(A)+'.contents.sha256').read_text().splitlines())==215 and side=={n:r['sha256'] for n,r in members.items()}
assert pathlib.Path(str(A)+'.sha256').read_text().split()==[a['sha256'],A.name]
assert int(pathlib.Path(str(A)+'.bytes').read_text())==A.stat().st_size
downloads=[]
for p in [A]+[pathlib.Path(str(A)+s) for s in ['.sha256','.bytes','.contents.sha256']]:downloads.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
print(json.dumps(dict(status='ARCHIVE215_MEMBERS_AND_ALL_SIDECARS_PASS',archive=a['sha256'],member_count=215,download_files=downloads,server_writes=0)),flush=True)
