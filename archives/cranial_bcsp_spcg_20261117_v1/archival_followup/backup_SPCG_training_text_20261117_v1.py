# -*- coding: utf-8 -*-
"""Read-only get of exact14x6 frozen training text artifacts; no server packing/writes."""
from pathlib import Path,PurePosixPath
import importlib.util,json,subprocess,shutil,sys
R=Path(__file__).resolve().parent.parent;sp=importlib.util.spec_from_file_location('archive_utils',R/'local_tools/archive_scq_BS_20261114_v1.py');u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
B=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_training_text_v1');M=B/'metadata';TR=R/'outputs/spcg_training_20261116_v1'
mapping={'G0_C':'UTC_order_hotfix_v3/post_training_freeze_v3','G1_C':'G1_C_implementation_v1/post_training_freeze_v1','G2_C':'G2_C_implementation_v1/post_training_freeze_v1','G0_D':'G0_D_implementation_v1/post_training_freeze_v1','G1_D':'G1_D_rebind_v2/post_training_freeze_v2','G2_D':'G2_D_implementation_v1/post_training_freeze_v1'}
def read(p):return json.loads(u.read(p))
def emit(**v):print(json.dumps(v),flush=True)
phase=sys.argv[1]
if phase=='prepare':
 assert not B.exists();d=read(R/'outputs/spcg_scientific_decision_20261117_v1/scientific_decision_record_v1.json');items=[]
 for run in d['training_matrix']:
  inv=TR/mapping[run['run']]/'01_inventory_checkpoint_result.json';v=read(inv);assert all(v['checks'].values());root=PurePosixPath(run['checkpoint']['path']).parent
  for name,r in v['files'].items():
   if name=='ckpt-last.pth':continue
   assert PurePosixPath(name).name==name and name.endswith(('.json','.jsonl','.txt','.log','.pid')) and 0<r['bytes']<16*1024**2
   items.append(dict(run=run['run'],name=name,remote_path=str(root/name),**r))
 B.mkdir();M.mkdir();u.put(M/'backup_source.py',Path(__file__).read_bytes());u.js(M/'frozen_training_text_scope_v1.json',dict(hostname='shu-common-25721452-notebook-yxwd3w-0',files=items,total_bytes=sum(r['bytes'] for r in items),server_writes=0,server_deletions=0,source='Six formal training output inventories; no checkpoint in this supplement'))
 emit(status='FROZEN_TRAINING_TEXT_SCOPE',files=len(items),bytes=sum(r['bytes'] for r in items))
elif phase=='download':
 scope=read(M/'frozen_training_text_scope_v1.json');base=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_key_checkpoints_v1/metadata')
 for run in mapping:assert read(base/(run+'_remote_hash.json'))['hostname']==scope['hostname']
 for i,row in enumerate(scope['files'],1):
  dest=B/'training_outputs'/row['run']/row['name'];dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();token=row['run']+'_'+row['name'].replace('.','_');claim=M/(token+'_transfer.json');assert not claim.exists()
  p=subprocess.run(['wsl.exe','--exec','/home/zhj/.local/bin/hpc5000','get',row['remote_path'],'/mnt/e/'+dest.as_posix()[3:],'--timeout','180'],capture_output=True,timeout=200)
  u.put(M/(token+'_stdout.bin'),p.stdout);u.put(M/(token+'_stderr.bin'),p.stderr);u.js(claim,dict(returncode=p.returncode,source=row['remote_path'],destination=str(dest)))
  assert p.returncode==0,('TRAINING_TEXT_TRANSFER_FAILED_STOP',row['run'],row['name'],p.returncode)
  assert dest.stat().st_size==row['bytes'] and u.sha(dest)==row['sha256'],('FROZEN_TEXT_HASH_MISMATCH',row['run'],row['name'])
  emit(status='TRAINING_TEXT_LOCAL_FROZEN_HASH_PASS',file=i,total=len(scope['files']),run=row['run'],name=row['name'])
 u.js(M/'all_downloads_verified_v1.json',dict(status='ALL_SIX_RUN_FROZEN_TRAINING_TEXT_HASHES_VERIFIED',files=len(scope['files']),bytes=scope['total_bytes']))
elif phase=='pack':
 scope=read(M/'frozen_training_text_scope_v1.json');assert read(M/'all_downloads_verified_v1.json')['files']==len(scope['files'])
 for r in scope['files']:
  p=B/'training_outputs'/r['run']/r['name'];assert p.stat().st_size==r['bytes'] and u.sha(p)==r['sha256']
  if r['name'] in ['metrics.jsonl','SPCG_geometry.jsonl']:assert sum(1 for line in p.open(encoding='utf-8') if line.strip())==3900
  if r['name']=='resources.jsonl':assert sum(1 for line in p.open(encoding='utf-8') if line.strip())==3902
 u.put(B/'README.md',b'# SPCG complete six-run training text supplement\n\nExact frozen initialization, optimizer groups/defaults,3900-step metrics and geometry,3902 resource rows, full order/exposure/construction, completion and launch/exit evidence. Checkpoints live in the separate six-weight backup. No new server writes/model calls or deletion. All artifacts match formal per-run output-inventory hashes.\n')
 result=u.pack(B,u.inventory(B),B/'spcg_complete_training_text_20261117_v1.tar.gz');receipt=dict(status='COMPLETE_SIX_RUN_TRAINING_TEXT_ARCHIVE_ALL_MEMBERS_VERIFIED',files=len(scope['files']),bytes=scope['total_bytes'],archive=result,server_writes=0,server_deletions=0)
 u.js(B/'local_verification_receipt_v1.json',receipt);emit(**receipt)
else:raise ValueError('prepare/download/pack')
