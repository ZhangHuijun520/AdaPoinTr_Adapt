# -*- coding: utf-8 -*-
"""Six exact final checkpoints, no server writes/model loading; phase-separated backup."""
from pathlib import Path
import importlib.util,json,hashlib,subprocess,base64,shutil,sys
R=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('archive_utils',R/'local_tools/archive_scq_BS_20261114_v1.py');u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
BASE=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_key_checkpoints_v1');META=BASE/'metadata';HOST='shu-common-25721452-notebook-yxwd3w-0';ARGS=['wsl.exe','--exec','/home/zhj/.local/bin/hpc5000']
def read(p):return json.loads(u.read(p))
def emit(**v):print(json.dumps(v),flush=True)
phase=sys.argv[1]
if phase=='prepare':
 assert not BASE.exists();decision=read(R/'outputs/spcg_scientific_decision_20261117_v1/scientific_decision_record_v1.json');rows=[]
 for r in decision['training_matrix']:
  audit=read(Path(r['audit']['path']));assert u.sha(Path(r['audit']['path']))==r['audit']['sha256'] and all(audit['checks'].values()) and audit['checkpoint']==r['checkpoint'] and audit['updates']==3900
  rows.append(dict(run=r['run'],**r['checkpoint'],training_audit=r['audit']))
 assert [r['run'] for r in rows]==['G0_C','G1_C','G2_C','G0_D','G1_D','G2_D']
 assert shutil.disk_usage(BASE.parent).free>3*sum(r['bytes'] for r in rows)
 BASE.mkdir();META.mkdir();(BASE/'weights').mkdir()
 u.js(META/'frozen_backup_scope_v1.json',dict(status='SIX_FINAL_SPCG_CHECKPOINTS_USER_AUTHORIZED_LOCAL_BACKUP',hostname=HOST,uid=1000,project='/home/jovyan/adapointr_work/PoinTr',files=rows,total_bytes=sum(r['bytes'] for r in rows),server_writes=0,server_deletions=0,checkpoint_deserialization=False,weights_on_GitHub=False))
 for r in rows:u.put(META/(r['run']+'_training_freeze.json'),u.read(Path(r['training_audit']['path'])))
 emit(status='FROZEN_SIX_CHECKPOINT_SCOPE_PREPARED',files=6,total_bytes=sum(r['bytes'] for r in rows))
elif phase=='probe':
 scope=read(META/'frozen_backup_scope_v1.json');run=sys.argv[2];row=next(r for r in scope['files'] if r['run']==run)
 assert not (META/(run+'_probe_exit.json')).exists()
 code="import pathlib,hashlib,json,socket,os;assert socket.gethostname()=="+repr(HOST)+" and os.getuid()==1000;p=pathlib.Path("+repr(row['path'])+");root=pathlib.Path('/home/jovyan/adapointr_work/PoinTr');assert p.is_relative_to(root) and root.resolve()==root and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));a=p.stat();h=hashlib.sha256()\nwith p.open('rb') as f:\n for b in iter(lambda:f.read(4194304),b''):h.update(b)\nz=p.stat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns);print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),path=str(p),bytes=a.st_size,sha256=h.hexdigest())),flush=True)"
 command="/opt/conda/bin/python -I -S -B -c \"exec(__import__('base64').b64decode('"+base64.b64encode(code.encode()).decode()+"'))\"";assert len(command)<=2048
 u.js(META/(run+'_readonly_probe_command.json'),dict(command=command,bytes=len(command),server_writes=0))
 p=subprocess.run(ARGS+['exec','--timeout','90','--',command],capture_output=True,timeout=110)
 u.put(META/(run+'_probe_stdout.bin'),p.stdout);u.put(META/(run+'_probe_stderr.bin'),p.stderr);u.js(META/(run+'_probe_exit.json'),dict(returncode=p.returncode))
 assert p.returncode==0,('READONLY_PROBE_FAILED_STOP',run,p.returncode)
 got=json.loads(p.stdout.decode('utf-8').strip());assert got==dict(hostname=HOST,uid=1000,**{k:row[k] for k in ['path','bytes','sha256']})
 u.js(META/(run+'_remote_hash.json'),dict(status='FRESH_REMOTE_CHECKPOINT_HASH_PASS',run=run,**got));emit(status='FRESH_REMOTE_CHECKPOINT_HASH_PASS',run=run,bytes=got['bytes'])
elif phase=='download':
 scope=read(META/'frozen_backup_scope_v1.json');run=sys.argv[2];row=next(r for r in scope['files'] if r['run']==run)
 for r in scope['files']:assert read(META/(r['run']+'_remote_hash.json'))['status']=='FRESH_REMOTE_CHECKPOINT_HASH_PASS'
 dest=BASE/'weights'/(run+'_epoch99_step3900.pth');assert not dest.exists() and not (META/(run+'_download_claim.json')).exists()
 u.js(META/(run+'_download_claim.json'),dict(source=row['path'],destination=str(dest),automatic_retry=False,expected_sha256=row['sha256']))
 emit(status='CHECKPOINT_DOWNLOAD_STARTED',run=run,bytes=row['bytes']);wsl='/mnt/e/'+dest.as_posix()[3:]
 with (META/(run+'_download_stdout.bin')).open('xb') as out,(META/(run+'_download_stderr.bin')).open('xb') as err:p=subprocess.run(ARGS+['get',row['path'],wsl,'--timeout','1200'],stdout=out,stderr=err,timeout=1230)
 u.js(META/(run+'_download_exit.json'),dict(returncode=p.returncode));assert p.returncode==0,('CHECKPOINT_TRANSFER_FAILED_STOP',run,p.returncode)
 assert dest.stat().st_size==row['bytes'] and u.sha(dest)==row['sha256']
 u.js(META/(run+'_local_verification.json'),dict(status='LOCAL_CHECKPOINT_EXACT_FROZEN_BYTES_PASS',run=run,path=str(dest),bytes=row['bytes'],sha256=row['sha256']));emit(status='LOCAL_CHECKPOINT_EXACT_FROZEN_BYTES_PASS',run=run)
elif phase=='pack':
 scope=read(META/'frozen_backup_scope_v1.json');weights=[]
 for r in scope['files']:
  got=read(META/(r['run']+'_local_verification.json'));p=Path(got['path']);assert p.stat().st_size==r['bytes'] and u.sha(p)==r['sha256'];weights.append(got)
 u.put(BASE/'README.md',b'# SPCG all six final checkpoints\n\nG0/G1/G2 x C/D, epoch99/step3900. Preserve complete positive/negative paired evidence, not a best-only selection. Fresh server and local hashes match formal training freezes. No torch.load, new model call or restore/resume test. Runtime, provider, data and code restoration remain separate. Never publish weights to GitHub. No server writes/deletions. D_G0 training-device confound remains disclosed.\n')
 result=u.pack(BASE,u.inventory(BASE),BASE/'spcg_key_checkpoints_20261117_v1.tar.gz')
 receipt=dict(status='SIX_SPCG_FINAL_CHECKPOINTS_AND_ALL_ARCHIVE_MEMBERS_VERIFIED',weights=weights,archive=result,checkpoint_deserialized=False,restore_executed=False,weights_on_GitHub=False,server_writes=0,server_deletions=0)
 u.js(BASE/'local_verification_receipt_v1.json',receipt);emit(**receipt)
else:raise ValueError('prepare/probe RUN/download RUN/pack only')
