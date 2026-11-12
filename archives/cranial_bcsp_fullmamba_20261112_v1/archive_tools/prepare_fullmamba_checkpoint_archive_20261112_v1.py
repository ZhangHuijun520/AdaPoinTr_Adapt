"""Freeze four final weights and the existing decoder diagnostic archive for read-only transfer."""
from pathlib import Path
import json,hashlib,shutil,base64
R=Path(__file__).resolve().parent.parent;B=R/'outputs/cranial_bcsp_fullmamba_20261110'
O=B/'final_archival_20261112_v1';assert not O.exists();O.mkdir()
specs=[
 ('F0_C','training_entry_v1/F0_FoldC_training_execution_request_v1.json','training_entry_v1/post_training_freeze_audit_v1/post_training_freeze_audit_result_v1.json'),
 ('F0_D','FoldD_training_entry_v1/F0_FoldD_training_execution_request_v1.json','FoldD_training_entry_v1/post_training_freeze_audit_v1/post_training_freeze_audit_result_v1.json'),
 ('LQI_C','lqi_training_entry_v1/LQI_FoldC_training_execution_request_v1.json','lqi_training_entry_v1/post_training_freeze_audit_v1/post_training_freeze_audit_result_v1.json'),
 ('LQI_D','lqi_FoldD_training_entry_v1/failed_startup_freeze_and_bridge_fix_v2/pending_transport_v2/LQI_FoldD_training_execution_request_v2.json','lqi_FoldD_training_entry_v1/post_training_freeze_audit_v2/post_training_freeze_audit_result_v1.json')]
rows=[]
for run,q,a in specs:
 request=json.loads((B/q).read_bytes());audit=json.loads((B/a).read_bytes())
 assert audit['status'].endswith('AUDIT_PASS') and audit['counts']['updates']==3900
 assert hashlib.sha256((B/q).read_bytes()).hexdigest()==audit['request_sha256']
 rows.append(dict(run=run,path=request['output']+'/ckpt-last.pth',bytes=audit['checkpoint']['bytes'],sha256=audit['checkpoint']['sha256'],audit=str(B/a),request=str(B/q)))
diag_path=B/'conditional_diagnostic_implementation_v1/post_diagnostic_freeze_audit_v1/formal_post_diagnostic_freeze_audit_result_v1.json'
diag=json.loads(diag_path.read_bytes());assert diag['status'].endswith('PASS')
attachments=[dict(label='F0_condition_diagnostic',audit=str(diag_path),**{k:diag['archive'][k] for k in ['path','bytes','sha256']})]
assert shutil.disk_usage('E:/ResearchBackups').free>sum(x['bytes'] for x in rows)*3+2*attachments[0]['bytes']
scope=dict(status='USER_AUTHORIZED_FINAL_ARCHIVAL_SCOPE',hostname='shu-common-25721452-notebook-r4cjpa-0',uid=1000,weights=rows,result_archives=attachments,weights_destination='E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA/2026-11-12_key_checkpoints_v1',diagnostic_destination='E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA/2026-11-12_decoder_diagnostic_v1',server_writes=0,server_deletions=0,checkpoint_load=False,model_calls=0,GitHub_checkpoint_upload=False)
(O/'archive_scope_v1.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2),encoding='utf-8')
code='''import pathlib,hashlib,json,socket,os,time,shutil
assert socket.gethostname()==HOST and os.getuid()==1000
root=pathlib.Path('/home/jovyan/adapointr_work/PoinTr')
assert root.is_dir() and root.resolve()==root
start=time.monotonic();rows=[]
for item in ITEMS:
 p=pathlib.Path(item['path']);assert p.is_relative_to(root)
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 before=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 after=p.stat();assert (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
 assert before.st_size==item['bytes'] and h.hexdigest()==item['sha256'],str(p)
 rows.append(dict(path=str(p),bytes=before.st_size,sha256=h.hexdigest(),uid=before.st_uid))
print(json.dumps(dict(status='FROZEN_ARCHIVAL_ASSETS_READONLY_REHASH_PASS',hostname=socket.gethostname(),uid=os.getuid(),root=str(root),files=rows,seconds=time.monotonic()-start,free_bytes=shutil.disk_usage(root).free,server_writes=0,checkpoint_deserialization=False)),flush=True)
'''.replace('HOST',repr(scope['hostname'])).replace('ITEMS',repr([{k:r[k] for k in ['path','bytes','sha256']} for r in rows+attachments]))
(O/'remote_hash_probe_v1.py').write_text(code,encoding='utf-8')
command="/opt/conda/bin/python -c \"exec(__import__('base64').b64decode('"+base64.b64encode(code.encode()).decode()+"'))\""
(O/'remote_hash_command_v1.json').write_text(json.dumps(dict(command=command)),encoding='utf-8')
print(json.dumps(dict(status=scope['status'],weights=len(rows),bytes=sum(x['bytes'] for x in rows),diagnostic_bytes=attachments[0]['bytes'])))
