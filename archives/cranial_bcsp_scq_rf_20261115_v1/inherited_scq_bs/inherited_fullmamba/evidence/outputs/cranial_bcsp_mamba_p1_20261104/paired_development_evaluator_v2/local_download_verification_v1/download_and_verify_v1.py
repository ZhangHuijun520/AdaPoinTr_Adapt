import array,ast,base64,hashlib,io,json,math,os,struct,subprocess,sys,tarfile,time,zipfile
from pathlib import Path
R=Path(__file__).resolve().parent;B=R.parent;A=B/'post_prediction_freeze_audit_v1';handoff=json.loads((A/'manual_download_handoff_v1.json').read_bytes());audit=json.loads((A/'audit_report_v1.json').read_bytes());D=Path(handoff['suggested_local_directory']);start=time.monotonic()
def need(ok,text):
 if not ok:raise RuntimeError(text)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(p,obj):
 with Path(p).open('x',encoding='utf8') as f:json.dump(obj,f,indent=2,ensure_ascii=False)
def progress(**data):
 print(json.dumps(data),flush=True)
 with (R/'download_progress_v1.jsonl').open('a') as f:f.write(json.dumps(data)+'\n')
need(audit['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS','formal audit');need(D.is_absolute() and D.resolve().is_relative_to(Path('E:/ResearchBackups/AdaPoinTr').resolve()) and not D.exists(),'fresh precise backup directory')
need(not any(p.is_symlink() for p in D.parents),'backup link ancestor');D.mkdir(parents=True)
for rec in handoff['download_files']:
 name=Path(rec['path']).name;target=D/name;need(not target.exists(),'download target exists');need(target.drive.lower()=='e:','explicit WSL mount mapping')
 # This is the known Windows E: mount in local WSL, never a server-side path.
 wsl_local='/mnt/e/'+target.as_posix()[3:]
 args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','get',rec['path'],wsl_local,'--timeout','60']
 progress(phase='DOWNLOAD_START',file=name)
 result=subprocess.run(args,capture_output=True,timeout=85)
 (R/(name+'.download.stdout.bin')).write_bytes(result.stdout);(R/(name+'.download.stderr.bin')).write_bytes(result.stderr)
 need(result.returncode==0,'download failed '+name+': '+result.stderr.decode(errors='replace')[:1500])
 need(target.is_file() and target.stat().st_size==rec['bytes'] and sha(target)==rec['sha256'],'download exact bytes/SHA '+name)
 progress(phase='DOWNLOADED_AND_HASH_VERIFIED',file=name,bytes=rec['bytes'],sha256=rec['sha256'])
a=D/'development_predictions_v1.tar.gz';complete=json.loads((A/'frozen_metadata/completion.json').read_bytes());expected=complete['archive']['members'];expected_names=[r['name'] for r in expected];seen=[];predictions=coarse=0;model_counts={'C_T0':0,'C_M0':0}
source=(A/'readonly_audit_source_v1.py').read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='array_contract');code=ast.get_source_segment(source,node)
namespace=dict(need=need,budget=lambda n:None,zipfile=zipfile,io=io,struct=struct,ast=ast,array=array,sys=sys,math=math)
exec(compile(code,'<frozen_NPZ_integrity_validator>','exec'),namespace)
protocol=json.loads((B/'transport_payload/paired_development_protocol_v1.json').read_bytes());members=[]
with tarfile.open(a,'r:gz') as t:
 info=t.getmembers();need(len(info)==len(set(x.name for x in info))==215 and [x.name for x in info]==expected_names,'archive strict215 members/order')
 for item,rec in zip(info,expected):
  need(item.isfile() and item.size==rec['bytes'] and item.size<=4194304 and not item.name.startswith('/') and '..' not in Path(item.name).parts,'member regular/path/size')
  raw=t.extractfile(item).read();need(hashlib.sha256(raw).hexdigest()==rec['sha256'],'member hash '+item.name);seen.append(item.name);members.append(rec)
  if item.name.startswith('predictions/'):
   label,cid=Path(item.name).stem.split('__',1);keep=cid in protocol['coarse_tensor_cases'];namespace['array_contract'](raw,keep);predictions+=1;coarse+=int(keep);model_counts[label]+=1
  else:
   need(raw==(A/'frozen_metadata'/item.name).read_bytes(),'archive metadata vs frozen audit '+item.name)
need(predictions==210 and coarse==14 and model_counts=={'C_T0':105,'C_M0':105},'210 predictions/14coarse/per arm105')
need((D/(a.name+'.sha256')).read_text()==sha(a)+'  '+a.name+'\n','SHA sidecar content')
need((D/(a.name+'.bytes')).read_text()==str(a.stat().st_size)+'\n','bytes sidecar content')
need((D/(a.name+'.contents.sha256')).read_text()==''.join(x['sha256']+'  '+x['name']+'\n' for x in members),'contents sidecar full215 lines')
result=dict(status='LOCAL_DOWNLOAD_AND_ALL_MEMBER_VERIFICATION_PASS',backup_directory=str(D),download_files=[dict(path=str(D/Path(r['path']).name),bytes=r['bytes'],sha256=r['sha256']) for r in handoff['download_files']],archive_members_verified=215,predictions_verified=210,coarse_arrays_verified=14,per_model=model_counts,full_metadata_matches_formal_audit=True,formal_audit_sha256=sha(A/'audit_report_v1.json'),verification_script_sha256=sha(__file__),prediction_archive_sha256=sha(a),server_sources_deleted=False,server_writes=0,GPU_calls=0,scoring_executed=False,seconds=time.monotonic()-start)
write(R/'verification_result_v1.json',result);write(D/'local_verification_receipt_v1.json',result);progress(phase='LOCAL_VERIFICATION_COMPLETE',**result)
