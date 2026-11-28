"""Freeze only the four executable/config files and 275 missing label payloads locally."""
from pathlib import Path,PurePosixPath
import gzip,hashlib,io,json,tarfile
b=Path(__file__).resolve().parent
h=lambda raw:hashlib.sha256(raw).hexdigest()
qp=b/'EJTC_D1_J_D_training_execution_request_h7vvrr_v1.json';qraw=qp.read_bytes();rid=h(qraw)
assert rid=='325c229ee04e2e32bbb65b4c75a80c3a53be7e6c0e347e09d3d0da5f77917d86'
q=json.loads(qraw)
rp=b/'server_readonly_h7vvrr_v1/J_D_server_readiness_receipt_v1.json';r=json.loads(rp.read_bytes())
assert r['status']=='J_D_READ_ONLY_SERVER_READINESS_PASS' and r['request_sha256']==rid
assert r['proposed_reuse_labels_verified']==40 and r['proposed_new_label_targets_absent']==275
assert h((b/'J_D_P3_review_receipt_v1.json').read_bytes())==q['P3_review_sha256']
labels=json.loads((b/'J_D_315_label_binding_v1.json').read_bytes())
table=json.loads((b/'J_D_label_table_v1.json').read_bytes())
d=b/'transport_h7vvrr_v1';d.mkdir(exist_ok=False)
payload={};files=[]
def add(member,path,rec):
 raw=path.read_bytes()
 assert len(raw)==rec['bytes'] and h(raw)==rec['sha256']
 assert member not in payload and str(PurePosixPath(q['binding']['install_root'])/member)==rec['path']
 payload[member]=raw
 files.append(dict(member=member,target=rec['path'],bytes=len(raw),sha256=h(raw)))
for key in ['worker','label_table']:
 rec=q['files'][key];name=PurePosixPath(rec['path']).name;add(name,b/name,rec)
rec=q['launch']['launcher'];name=PurePosixPath(rec['path']).name;add(name,b/name,rec)
add(qp.name,qp,dict(path=q['launch']['request_path'],bytes=len(qraw),sha256=rid))
reuse=[]
for row in labels['cases']:
 rec=table['cases'][row['case_id']]['labels']
 assert rec['sha256']==row['sha256'] and rec['bytes']==row['bytes']
 if row['proposed_mode'].startswith('PROPOSED_REUSE'):
  assert r['files'][rec['path']]==[rec['bytes'],rec['sha256']]
  reuse.append(rec)
 else:
  member=str(PurePosixPath(rec['path']).relative_to(PurePosixPath(q['binding']['install_root'])))
  assert PurePosixPath(member).parent==PurePosixPath('labels')
  add(member,Path(row['local_path']),rec)
assert len(payload)==279 and len(reuse)==40
tarraw=io.BytesIO()
with tarfile.open(fileobj=tarraw,mode='w',format=tarfile.USTAR_FORMAT) as archive:
 for name in sorted(payload):
  info=tarfile.TarInfo(name);info.size=len(payload[name]);info.mode=0o644;info.mtime=0;info.uid=info.gid=0
  archive.addfile(info,io.BytesIO(payload[name]))
packed=gzip.compress(tarraw.getvalue(),compresslevel=9,mtime=0)
name='EJTC_J_D_h7vvrr_transport_v1.tar.gz';bp=d/name
with bp.open('xb') as f:f.write(packed)
with (d/(name+'.sha256')).open('x',encoding='ascii',newline='\n') as f:f.write(h(packed)+'  '+name+'\n')
with tarfile.open(fileobj=io.BytesIO(packed),mode='r:gz') as archive:
 members=archive.getmembers();assert len(members)==279 and sorted(x.name for x in members)==sorted(payload)
 for item in members:assert item.isfile() and archive.extractfile(item).read()==payload[item.name]
root=q['binding']['install_root']
mapping=dict(schema='bcsp-ejtc-j-d-install-mapping-v1',status='AWAITING_UPLOAD_VERIFICATION_AND_SEPARATE_INSTALL_AUTHORIZATION',request_sha256=rid,identity=q['binding']['identity'],upload=dict(path='/home/jovyan/'+name,bytes=len(packed),sha256=h(packed)),upload_checksum_path='/home/jovyan/'+name+'.sha256',new_install_root=root,directories_to_create=[root,str(PurePosixPath(root)/'labels')],files=files,new_file_count=279,new_label_file_count=275,reused_label_files=reuse,reused_label_file_count=40,reused_assets={p:dict(bytes=v[0],sha256=v[1]) for p,v in r['files'].items()},output_must_be_absent=q['binding']['output'],runtime_controls_must_be_absent=[q['launch'][k] for k in ['authorization_path','runtime_path','single_attempt_log','resource_log','dispatch_log','exit_code_path']],session_must_be_absent=q['launch']['session_name'],server_readiness_receipt=dict(local_path=str(rp),bytes=rp.stat().st_size,sha256=h(rp.read_bytes()),verified_assets=r['verified_assets'],training_inputs=315),pairing=q['pairing'],label_table=q['files']['label_table'],local_CPU_receipt_sha256=q['cpu_preparation_sha256'],local_P3_receipt_sha256=q['P3_review_sha256'],authorization_materializer=q['authorization_materializer'],overwrite=False,remote_install_authorized=False,execution_authorized=False,policy='Immediately before any installation recheck identity, resources, upload bytes/checksum/exact 279-member inventory, all reused assets including 40 label files and R/T evidence, safe parent directories and every new directory/target/control/output/session absence. Create only the two named directories and exclusively create only the 279 frozen files. Read back every installed file hash. Do not overwrite, delete, create runtime controls, run tests, forward, or training during installation.',snapshot_only=True)
mp=d/'EJTC_J_D_h7vvrr_install_mapping_v1.json'
with mp.open('x',encoding='utf-8',newline='\n') as f:json.dump(mapping,f,ensure_ascii=False,indent=2);f.write('\n')
assert h(qp.read_bytes())==rid
receipt=dict(status='J_D_MINIMAL_TRANSPORT_FREEZE_PASS',request_sha256=rid,bundle=dict(local_path=str(bp),bytes=len(packed),sha256=h(packed)),mapping=dict(local_path=str(mp),bytes=mp.stat().st_size,sha256=h(mp.read_bytes())),archive_member_count=279,non_label_files=4,new_label_files=275,reused_label_files=40,directories_to_create=2,all_member_bytes_verified=True,readiness_verified_assets=r['verified_assets'],training_inputs=315,server_readiness_receipt_sha256=h(rp.read_bytes()),server_writes=0,training_started=False,installation_authorized=False,execution_authorized=False)
with (d/'transport_freeze_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt,ensure_ascii=False))
