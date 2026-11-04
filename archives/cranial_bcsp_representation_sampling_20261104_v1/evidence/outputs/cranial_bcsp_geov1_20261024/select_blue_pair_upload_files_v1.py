"""Collect the five byte-identical frozen upload files for manual upload."""
import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent/'blue_pair_eval_v1'
request=N/'development_execution_request_v1.json';raw=request.read_bytes();scope=json.loads(raw)
assert hashlib.sha256(raw).hexdigest()=='4fd0d2736e58530326c37d77fdbd5e76242339c36ea0a7905290a58d0b31ab43'
out=N/'upload_v1';out.mkdir()
records=[]
for r in [scope['upload']]+scope['upload_sidecars']:
    p=N/Path(r['path']).name;data=p.read_bytes();assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
    dest=out/p.name
    with dest.open('xb') as f:f.write(data)
    assert hashlib.sha256(dest.read_bytes()).hexdigest()==r['sha256']
    records.append({'local_path':str(dest),'server_upload_path':r['path'],'bytes':r['bytes'],'sha256':r['sha256']})
assert len(records)==5
with (N/'upload_selection_receipt_v1.json').open('x') as f:json.dump({'request_sha256':hashlib.sha256(raw).hexdigest(),'files':records,'server_calls':0,'request_unchanged':True},f,indent=2)
print(json.dumps({'request_sha256':hashlib.sha256(raw).hexdigest(),'upload_directory':str(out),'files':5,'archive_bytes':scope['upload']['bytes']}))
