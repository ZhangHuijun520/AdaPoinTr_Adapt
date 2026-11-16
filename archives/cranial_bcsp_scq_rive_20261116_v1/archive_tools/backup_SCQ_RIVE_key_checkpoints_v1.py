"""Exact four-final-checkpoint archival; no server writes or checkpoint loading."""
from pathlib import Path
import importlib.util,json,hashlib,subprocess,base64,shutil,sys
R=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('archive_utils',R/'local_tools/archive_scq_BS_20261114_v1.py');u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
BASE=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RIVE/2026-11-16_key_checkpoints_v1')
META=BASE/'metadata'
T=R/'outputs/scq_rive_training_implementation_20261115_v1'
HOST='shu-common-25721452-notebook-lwwgl9-0'
ARGS=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000']
def read(p):return json.loads(u.read(p))
def emit(**x):print(json.dumps(x),flush=True)

if sys.argv[1]=='prepare':
    assert not BASE.exists();rows=[]
    for run,sub in [('Static_C',''),('Requery_C','Requery_C_request_preparation_v1'),('Static_D','Static_D_request_preparation_v1'),('Requery_D','Requery_D_request_preparation_v1')]:
        audit=T/sub/'post_training_freeze_v1/freeze_verification_v1.json';a=read(audit)
        assert a['status'].endswith('PASS') and all(a['checks'].values()) and a['updates']==3900
        candidates=list((T/sub).glob('SCQ_RIVE_*execution_request_v1.json')) if sub else list((T/'pending_request_v1').glob('SCQ_RIVE_*execution_request_v1.json'))
        matches=[p for p in candidates if u.sha(p)==a['request_sha256']];assert len(matches)==1
        request=matches[0];q=read(request)
        rows.append(dict(run=run,path=q['output']+'/ckpt-last.pth',**a['checkpoint'],training_audit=str(audit),training_audit_sha256=u.sha(audit),request=str(request),request_sha256=u.sha(request)))
    assert len(rows)==4 and shutil.disk_usage(BASE.parent).free>3*sum(x['bytes'] for x in rows)
    BASE.mkdir();META.mkdir();(BASE/'weights').mkdir()
    scope=dict(status='USER_AUTHORIZED_FOUR_RIVE_FINAL_CHECKPOINT_BACKUPS',hostname=HOST,uid=1000,project='/home/jovyan/adapointr_work/PoinTr',files=rows,total_bytes=sum(x['bytes'] for x in rows),server_writes=0,server_deletions=0,checkpoint_deserialization=False,GitHub_weights=False)
    u.js(META/'frozen_backup_scope_v1.json',scope)
    for x in rows:u.put(META/(x['run']+'_training_freeze.json'),u.read(Path(x['training_audit'])))
    code="""import pathlib,hashlib,json,socket,os,time
assert socket.gethostname()==HOST and os.getuid()==1000
root=pathlib.Path('/home/jovyan/adapointr_work/PoinTr');assert root.resolve()==root
rows=[];start=time.monotonic()
for row in ITEMS:
 p=pathlib.Path(row['path']);assert p.is_relative_to(root) and p.is_file() and not any(x.is_symlink() for x in (p,*p.parents))
 a=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.stat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 assert a.st_size==row['bytes'] and h.hexdigest()==row['sha256']
 rows.append(dict(run=row['run'],path=str(p),bytes=a.st_size,sha256=h.hexdigest()))
print(json.dumps(dict(status='FOUR_RIVE_CHECKPOINTS_FRESH_REMOTE_HASH_PASS',hostname=socket.gethostname(),uid=os.getuid(),files=rows,seconds=time.monotonic()-start,server_writes=0)),flush=True)
""".replace('HOST',repr(HOST)).replace('ITEMS',repr([{k:x[k] for k in ['run','path','bytes','sha256']} for x in rows]))
    command="/opt/conda/bin/python -I -S -B -c \"exec(__import__('base64').b64decode('"+base64.b64encode(code.encode()).decode()+"'))\""
    assert len(command)<6000
    u.put(META/'remote_hash_probe_v1.py',code.encode());u.js(META/'remote_hash_command_v1.json',dict(command=command,bytes=len(command),scope='Exact four frozen paths; no model import or writes'))
    emit(status=scope['status'],files=4,bytes=scope['total_bytes'],probe_command_bytes=len(command))
elif sys.argv[1]=='probe':
    scope=read(META/'frozen_backup_scope_v1.json');command=read(META/'remote_hash_command_v1.json')['command']
    assert not (META/'probe_exit_v1.json').exists()
    p=subprocess.run(ARGS+['exec','--timeout','90','--',command],capture_output=True,timeout=110)
    u.put(META/'probe_stdout_v1.bin',p.stdout);u.put(META/'probe_stderr_v1.bin',p.stderr);u.js(META/'probe_exit_v1.json',dict(returncode=p.returncode))
    assert p.returncode==0,('READONLY_HASH_PROBE_FAILED_STOP',p.returncode)
    a=json.loads(p.stdout.decode('utf-8').strip());assert a['hostname']==HOST and a['uid']==1000
    assert a['files']==[{k:x[k] for k in ['run','path','bytes','sha256']} for x in scope['files']]
    u.js(META/'fresh_remote_hash_verification_v1.json',a);emit(status=a['status'],files=4)
elif sys.argv[1]=='probe_each':
    scope=read(META/'frozen_backup_scope_v1.json');run=sys.argv[2];row=next(x for x in scope['files'] if x['run']==run)
    code="import pathlib,hashlib,json,socket,os;assert socket.gethostname()=="+repr(HOST)+" and os.getuid()==1000;p=pathlib.Path("+repr(row['path'])+");assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));a=p.stat();h=hashlib.sha256()\nwith p.open('rb') as f:\n for b in iter(lambda:f.read(4194304),b''):h.update(b)\nz=p.stat();assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns);print(json.dumps(dict(bytes=a.st_size,sha256=h.hexdigest())),flush=True)"
    command="/opt/conda/bin/python -I -S -B -c \"exec(__import__('base64').b64decode('"+base64.b64encode(code.encode()).decode()+"'))\""
    assert len(command)<=2048 and not (META/(run+'_probe_v2_exit.json')).exists()
    u.js(META/(run+'_probe_v2_command.json'),dict(command=command,bytes=len(command),identity=HOST))
    p=subprocess.run(ARGS+['exec','--timeout','90','--',command],capture_output=True,timeout=110)
    u.put(META/(run+'_probe_v2_stdout.bin'),p.stdout);u.put(META/(run+'_probe_v2_stderr.bin'),p.stderr);u.js(META/(run+'_probe_v2_exit.json'),dict(returncode=p.returncode))
    assert p.returncode==0,('SHORT_READONLY_HASH_PROBE_FAILED_STOP',run,p.returncode)
    a=json.loads(p.stdout.decode('utf-8').strip());assert a=={k:row[k] for k in ['bytes','sha256']}
    u.js(META/(run+'_remote_hash_v2.json'),dict(run=run,path=row['path'],**a));emit(status='ONE_RIVE_CHECKPOINT_FRESH_REMOTE_HASH_PASS',run=run,command_bytes=len(command))
    paths=[META/(r['run']+'_remote_hash_v2.json') for r in scope['files']]
    if all(p.exists() for p in paths):u.js(META/'fresh_remote_hash_verification_v2.json',dict(status='FOUR_RIVE_CHECKPOINTS_FRESH_REMOTE_HASH_PASS',hostname=HOST,uid=1000,files=[read(p) for p in paths],method='Four exact short commands; original long call timed out and no process remained.'))
elif sys.argv[1]=='download':
    scope=read(META/'frozen_backup_scope_v1.json');assert read(META/'fresh_remote_hash_verification_v2.json')['status'].endswith('PASS')
    run=sys.argv[2];row=next(x for x in scope['files'] if x['run']==run);dest=BASE/'weights'/(run+'_epoch99_step3900.pth')
    assert not dest.exists() and not (META/(run+'_download_claim.json')).exists()
    u.js(META/(run+'_download_claim.json'),dict(run=run,source=row['path'],destination=str(dest),automatic_retry=False))
    emit(status='CHECKPOINT_DOWNLOAD_STARTED',run=run,bytes=row['bytes'])
    wsl='/mnt/e/'+dest.as_posix()[3:]
    with (META/(run+'_download_stdout.bin')).open('xb') as out,(META/(run+'_download_stderr.bin')).open('xb') as err:
        p=subprocess.run(ARGS+['get',row['path'],wsl,'--timeout','1200'],stdout=out,stderr=err,timeout=1230)
    u.js(META/(run+'_download_exit.json'),dict(returncode=p.returncode))
    assert p.returncode==0,('TRANSFER_FAILED_STOP',run,p.returncode)
    assert dest.stat().st_size==row['bytes'] and u.sha(dest)==row['sha256']
    u.js(META/(run+'_local_verification.json'),dict(status='EXACT_FROZEN_CHECKPOINT_BYTES_VERIFIED',run=run,local_path=str(dest),bytes=row['bytes'],sha256=row['sha256']))
    emit(status='CHECKPOINT_LOCAL_SHA256_PASS',run=run,sha256=row['sha256'])
elif sys.argv[1]=='pack':
    scope=read(META/'frozen_backup_scope_v1.json');weights=[]
    for row in scope['files']:
        a=read(META/(row['run']+'_local_verification.json'));p=Path(a['local_path']);assert p.stat().st_size==row['bytes'] and u.sha(p)==row['sha256'];weights.append(a)
    u.put(BASE/'README.md',b'# SCQ-RIVE four final checkpoints\n\nStatic/Requery x Fold C/D, epoch99/step3900. Fresh server SHA256 and local bytes match formal training audits. All four models retained to preserve paired mixed/negative evidence. No checkpoint deserialization, model execution, restore or resume test. Code, provider, raw data and runtime dependencies require separate restoration. Weights never published to GitHub. No server writes or deletion.\n')
    archive=u.pack(BASE,u.inventory(BASE),BASE/'scq_RIVE_key_checkpoints_20261116_v1.tar.gz')
    receipt=dict(status='FOUR_RIVE_FINAL_CHECKPOINTS_AND_ARCHIVE_MEMBER_READBACK_PASS',weights=weights,archive=archive,checkpoint_deserialization=False,restore_execution=False,GitHub_weights=False,server_writes=0,server_deletions=0)
    u.js(BASE/'local_verification_receipt_v1.json',receipt);emit(status=receipt['status'],archive=archive)
else:raise ValueError('prepare/probe/download RUN/pack only')
