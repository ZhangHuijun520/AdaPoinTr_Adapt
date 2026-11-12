"""Byte-preserving downloads and local archives; never deserialize checkpoints or run models."""
from pathlib import Path
import json,hashlib,subprocess,sys,tarfile,shutil
R=Path(__file__).resolve().parent.parent;O=R/'outputs/cranial_bcsp_fullmamba_20261110/final_archival_20261112_v1'
S=json.loads((O/'archive_scope_v1.json').read_bytes());V=json.loads((O/'remote_hash_verification_v1.json').read_bytes())
assert V['status']=='FROZEN_ARCHIVAL_ASSETS_READONLY_REHASH_PASS' and V['hostname']==S['hostname']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def write(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def js(p,v):write(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def emit(**v):print(json.dumps(v),flush=True)
def get(remote,local,label,timeout=2400):
 assert remote.startswith('/home/jovyan/adapointr_work/PoinTr/') and not local.exists()
 local.parent.mkdir(parents=True,exist_ok=True)
 wsl='/mnt/e/'+local.as_posix()[3:]
 emit(stage='download_started',label=label,path=str(local))
 with (O/(label+'_get_stdout.bin')).open('xb') as out,(O/(label+'_get_stderr.bin')).open('xb') as err:
  r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','get',remote,wsl,'--timeout',str(timeout)],stdout=out,stderr=err,timeout=timeout+30)
 assert r.returncode==0,('DOWNLOAD_FAILED_STOP_NO_AUTO_RETRY',label,r.returncode)
 emit(stage='download_completed',label=label,bytes=local.stat().st_size)
def tar_verify(archive,checks):
 seen=set()
 with tarfile.open(archive,'r|gz') as tar:
  for m in tar:
   if m.isdir():continue
   assert m.isfile() and m.name in checks and m.name not in seen
   h=hashlib.sha256();size=0
   with tar.extractfile(m) as f:
    for b in iter(lambda:f.read(4194304),b''):size+=len(b);h.update(b)
   assert h.hexdigest()==checks[m.name]['sha256'] and size==checks[m.name]['bytes'],m.name
   seen.add(m.name)
 assert seen==set(checks)
 return len(seen)
if sys.argv[1]=='diagnostic':
 d=Path(S['diagnostic_destination']);assert not d.exists();d.mkdir(parents=True)
 item=S['result_archives'][0];name='development_predictions_v1.tar.gz';p=d/name
 get(item['path'],p,'decoder_diagnostic_archive')
 assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256']
 a=json.loads(Path(item['audit']).read_bytes());checks={x['name']:x for x in a['archive']['members']}
 count=tar_verify(p,checks)
 # Download and validate the original three sidecars, preserving their exact bytes.
 for suffix in ['.sha256','.bytes','.contents.sha256']:get(item['path']+suffix,d/(name+suffix),'decoder_diagnostic_'+suffix.replace('.','_'),120)
 assert (d/(name+'.sha256')).read_text().split()[0]==item['sha256']
 assert int((d/(name+'.bytes')).read_text().strip())==item['bytes']
 listed={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (d/(name+'.contents.sha256')).read_text().splitlines() if line}
 assert listed=={k:v['sha256'] for k,v in checks.items()}
 js(d/'server_post_diagnostic_freeze_audit_result_v1.json',a)
 receipt=dict(status='DIAGNOSTIC_ARCHIVE_LOCAL_ALL_MEMBERS_VERIFIED',archive=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)),members=count,server_writes=0,array_deserialization=False)
 js(d/'local_verification_receipt_v1.json',receipt);js(O/'diagnostic_local_receipt_v1.json',receipt);emit(**receipt)
elif sys.argv[1]=='weights':
 d=Path(S['weights_destination']);assert not d.exists();d.mkdir(parents=True)
 assert shutil.disk_usage(d).free>3*sum(x['bytes'] for x in S['weights'])
 records=[]
 for item in S['weights']:
  p=d/'weights'/(item['run']+'_epoch99_step3900.pth');get(item['path'],p,item['run'])
  assert p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],('WEIGHT_HASH_MISMATCH_STOP',item['run'])
  records.append(dict(run=item['run'],path=str(p),member=p.relative_to(d).as_posix(),bytes=p.stat().st_size,sha256=item['sha256'],server_source=item['path']))
  write(d/'metadata'/(item['run']+'_training_freeze_audit.json'),Path(item['audit']).read_bytes())
  write(d/'metadata'/(item['run']+'_execution_request.json'),Path(item['request']).read_bytes())
  emit(stage='weight_hash_verified',run=item['run'],completed=len(records))
 for name,source in [('archive_scope_v1.json',O/'archive_scope_v1.json'),('remote_hash_verification_v1.json',O/'remote_hash_verification_v1.json'),('publication_receipt_v1.json',R/'deliverables/cranial_bcsp_fullmamba_20261112_v1/publication_receipt_v1.json'),('FullMamba_complete_report_zh.md',R/'reports/cranial_bcsp_fullmamba_20261112_v1/Cranial_BCSP_FullMamba_本轮完整实验报告_zh_2026-11-12_v1.md')]:write(d/'metadata'/name,source.read_bytes())
 js(d/'metadata/weight_manifest_v1.json',records)
 write(d/'metadata/README.md',b'# FullMamba final checkpoints\n\nFour exact epoch99/step3900 checkpoints: F0 C/D and LQI C/D. These preserve the complete original checkpoint bytes, not converted state dictionaries. Negative and unstable candidates are retained for scientific reproducibility. No torch.load, inference or restore test was performed. Architecture code, original data and compiled runtime dependencies remain separately required. All four files were freshly hashed on the user-confirmed current container before download and local bytes matched the formal training-audit SHA256. Every compressed archive member was independently streamed back. No weights were uploaded to GitHub, and no server files were deleted.\n')
 files=sorted(p for folder in [d/'weights',d/'metadata'] for p in folder.rglob('*') if p.is_file());checks={p.relative_to(d).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
 archive=d/'cranial_bcsp_fullmamba_key_checkpoints_20261112_v1.tar.gz';emit(stage='checkpoint_compression_started',members=len(files))
 with tarfile.open(archive,'x:gz',compresslevel=1,format=tarfile.PAX_FORMAT) as tar:
  for p in files:tar.add(p,arcname=p.relative_to(d).as_posix(),recursive=False)
 count=tar_verify(archive,checks);ah=sha(archive)
 write(d/(archive.name+'.sha256'),(ah+'  '+archive.name+'\n').encode());write(d/(archive.name+'.bytes'),(str(archive.stat().st_size)+'\n').encode());write(d/(archive.name+'.contents.sha256'),''.join(v['sha256']+'  '+k+'\n' for k,v in checks.items()).encode())
 receipt=dict(status='FOUR_FULLMAMBA_FINAL_CHECKPOINTS_LOCAL_ARCHIVE_VERIFIED',directory=str(d),weights=records,archive=dict(path=str(archive),bytes=archive.stat().st_size,sha256=ah),archive_members=count,every_member_hash_verified=True,checkpoint_deserialized=False,restore_test=False,server_writes=0,server_deletions=0,GitHub_weights_uploaded=False)
 js(d/'local_verification_receipt_v1.json',receipt);js(O/'checkpoint_local_receipt_v1.json',receipt);emit(**receipt)
else:raise ValueError('exact phase required')
