"""Download four formally audited files, verify every local archive member. No scoring."""
from pathlib import Path
import datetime,hashlib,json,shutil,subprocess,tarfile
b=Path(__file__).resolve().parent;e=b/'local_download_verification_v2';e.mkdir(exist_ok=False)
h=lambda b:hashlib.sha256(b).hexdigest()
auditpath=b/'post_prediction_freeze_audit_v2/formal_post_prediction_freeze_audit_v2.json';audit=json.loads(auditpath.read_bytes())
assert audit['status']=='FORMAL_READ_ONLY_EJTC_NATIVE315_V2_POST_PREDICTION_FREEZE_AUDIT_PASS'
q=json.loads((b/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json').read_bytes())
dest=Path('E:/ResearchBackups/AdaPoinTr/BCSP_EJTC/2026-11-28_native_development_eval');dest.mkdir(parents=True,exist_ok=False)
for name in q['archive_contract']['download_files']:
 target=dest/name;assert not target.exists()
 linux='/mnt/e/'+target.relative_to('E:/').as_posix()
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','get',q['binding']['output']+'/'+name,linux,'--timeout','40'],capture_output=True,timeout=55)
 log=dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8','replace'),stderr=r.stderr.decode('utf-8','replace'))
 with (e/(name+'.download.json')).open('x',encoding='utf-8') as f:json.dump(log,f,indent=2)
 assert r.returncode==0 and target.is_file(),log
 print('Downloaded '+name,flush=True)
archive=dest/'EJTC_RTJ_D_native315.tar.gz';listing=dest/'archive_members.json'
assert archive.stat().st_size==audit['archive']['bytes'] and h(archive.read_bytes())==audit['archive']['sha256']
assert h(listing.read_bytes())==audit['listing_sha256']
for p in (archive,listing):assert Path(str(p)+'.sha256').read_text().split()==[h(p.read_bytes()),p.name]
members=json.loads(listing.read_bytes());assert len(members)==320
rows=[]
with tarfile.open(archive,'r:gz') as a:
 for t in a:
  assert t.isfile() and not t.name.startswith('/') and '..' not in Path(t.name).parts and len(rows)<320 and t.size<=2097152
  raw=a.extractfile(t).read();rows.append(dict(name=t.name,bytes=len(raw),sha256=h(raw)))
assert rows==members and len(set(r['name'] for r in rows))==320
receipt=dict(status='EJTC_NATIVE315_LOCAL_DOWNLOAD_AND_ALL_MEMBERS_VERIFIED',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),request_sha256=audit['request_sha256'],backup_directory=str(dest),files=[dict(name=n,bytes=(dest/n).stat().st_size,sha256=h((dest/n).read_bytes())) for n in q['archive_contract']['download_files']],archive_members=320,predictions=315,paired_cases=105,arms=['R','T','J'],formal_remote_audit_sha256=h(auditpath.read_bytes()),all_local_member_hashes_match=True,scoring_started=False)
with (e/'local_download_verification_receipt_v2.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
shutil.copyfile(auditpath,dest/'formal_remote_post_prediction_freeze_audit_v2.json')
shutil.copyfile(e/'local_download_verification_receipt_v2.json',dest/'local_download_verification_receipt_v2.json')
print(json.dumps(receipt,ensure_ascii=False))
