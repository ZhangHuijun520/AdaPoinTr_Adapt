"""Freeze verified28 payload files +2 transport metadata members. Local bytes only."""
from pathlib import Path,PurePosixPath
import hashlib,json,tarfile,time
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_dac_r01_preparation_20261115_v1'
O=R/'server_uploads/scq_dac_r1_frozen20_20261115_v1';O.mkdir()
START=time.monotonic()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def rec(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def save(p,x):
 with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
qp=B/'pending_request_v1/SCQ_DAC_R1_execution_request_v1.json';QSHA='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8';assert sha(qp)==QSHA
readypath=B/'server_readiness_v2/readiness_verification_v1.json';ready=json.loads(readypath.read_bytes());assert ready['status']=='READONLY_READINESS_PASS_AWAITING_LOCAL_TRANSPORT_FREEZE' and ready['request_sha256']==QSHA and ready['targets_absent']==28 and ready['inputs']==20
root=PurePosixPath('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1')
files=json.loads((B/'pending_request_v1/candidate_no_overwrite_install_mapping_v1.json').read_bytes())['files'];assert len(files)==28
records=[];sources={}
for row in files:
 p=Path(row['local']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
 assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
 target=PurePosixPath(row['remote']);member='payload/'+str(target.relative_to(root));assert '..' not in PurePosixPath(member).parts
 records.append(dict(member=member,target=str(target),bytes=row['bytes'],sha256=row['sha256']));sources[member]=p
assert len(sources)==28
meta=O/'install_manifest_v1.json';save(meta,dict(status='FROZEN_AWAITING_SEPARATE_DEPLOYMENT_EXECUTION_AUTHORIZATION',request_sha256=QSHA,payload_count=28,root=str(root),files=records,no_overwrite=True,all_targets_absent_before_first_write=True,all_original_path_components_no_links=True,archive_member_names_posix=True,authorization_runtime_launcher_included=False,automatic_execution=False,readiness_snapshot=rec(readypath)))
sources['metadata/install_manifest_v1.json']=meta;sources['metadata/readiness_verification_v1.json']=readypath
expected={r['member']:(r['bytes'],r['sha256']) for r in records}
for name,p in sources.items():
 if name.startswith('metadata/'):expected[name]=(p.stat().st_size,sha(p))
archive=O/'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz'
print('packing_verified28_payloads',flush=True)
with archive.open('xb') as raw:
 with tarfile.open(fileobj=raw,mode='w:gz',compresslevel=5) as t:
  for name,p in sorted(sources.items()):
   before=p.stat();info=tarfile.TarInfo(name);info.size=before.st_size;info.mode=0o600;info.mtime=0
   with p.open('rb') as f:t.addfile(info,f)
   after=p.stat();assert (before.st_size,before.st_mtime_ns,before.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
print('verifying_all30_archive_members',flush=True)
seen=set()
with tarfile.open(archive,'r:gz') as t:
 for m in t:
  assert m.isfile() and m.name in expected and m.name not in seen and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts
  h=hashlib.sha256();size=0
  with t.extractfile(m) as f:
   for b in iter(lambda:f.read(4194304),b''):h.update(b);size+=len(b)
  assert (size,h.hexdigest())==expected[m.name];seen.add(m.name)
assert seen==set(expected) and len(seen)==30 and sha(qp)==QSHA
archive_record=rec(archive)
for suffix,text in [('.sha256',archive_record['sha256']+'  '+archive.name+'\n'),('.bytes',str(archive_record['bytes'])+'\n'),('.contents.sha256',''.join(v[1]+'  '+k+'\n' for k,v in sorted(expected.items())))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii') as f:f.write(text)
receipt=dict(status='TRANSPORT_FROZEN_ALL30_MEMBERS_VERIFIED_NOT_UPLOADED',archive=archive_record,sidecars=[rec(Path(str(archive)+s)) for s in ('.sha256','.bytes','.contents.sha256')],payload_files=28,metadata_members=2,weights=2,request_sha256=QSHA,readiness=rec(readypath),installation=False,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,checkpoint_deserialized=False,model_calls=0,seconds=time.monotonic()-START)
save(O/'transport_verification_receipt_v1.json',receipt)
save(B/'server_readiness_v2/transport_freeze_result_v1.json',receipt)
print(json.dumps(dict(status=receipt['status'],archive_bytes=archive_record['bytes'],archive_sha256=archive_record['sha256'],members=30,seconds=receipt['seconds'])),flush=True)
