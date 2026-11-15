import os,json,hashlib,socket,stat,subprocess,time,base64
from pathlib import Path
start=time.monotonic();checks={};files={};total=0
def require(ok,text):
 if not ok:raise RuntimeError(text)
def clean(p):
 p=Path(p);require(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),'link/path '+str(p));return p
def digest(p):
 h=hashlib.sha256()
 with clean(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):
 global total
 p=clean(p);st=p.stat();require(stat.S_ISREG(st.st_mode) and st.st_size<=1048576,'regular/1MiB '+str(p));total+=st.st_size;require(total<=8388608,'8MiB read budget');data=p.read_bytes();files[str(p)]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),mode=stat.S_IMODE(st.st_mode),uid=st.st_uid,gid=st.st_gid,mtime_ns=st.st_mtime_ns,content_base64=base64.b64encode(data).decode());return data
def exact(r):
 p=clean(r['path']);require(p.is_file() and p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],'bound identity '+str(p));return p
root=clean('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p1_foldC_paired_development_20261106_v1');rp=root/'FoldC_T0_M0_development_execution_request_v1.json';qh='d4e5665e7c285f0d8246e6ca3b104d6f003afd4faf35683e8170aa9ec8215418'
raw=read(rp);require(hashlib.sha256(raw).hexdigest()==qh,'request SHA');q=json.loads(raw);L=q['launch_contract'];I=q['identity'];out=clean(q['output'])
checks['hostname_uid']=socket.gethostname()==I['hostname'] and os.getuid()==I['uid'];require(checks['hostname_uid'],'identity');os.chdir(I['project'])
installed=[q['entry'],q['input_index'],q['protocol'],q['pair_receipt'],q['P3'],L['launcher_template'],*q['training_audits'].values()]
for r in installed:exact(r);read(r['path'])
checks['exact_nine_installed_files']=set(p.name for p in root.iterdir() if p.is_file())=={Path(r['path']).name for r in installed}|{rp.name}
checks['only_control_subdirectory']={p.name for p in root.iterdir() if p.is_dir()}=={'control'}
control=clean(root/'control');expected={Path(p).name for p in [L['authorization'],L['runtime'],L['launcher'],q['launch_attempt']]}
checks['exact_four_controls']={p.name for p in control.iterdir()}==expected
for p in control.iterdir():require(p.is_file() and not p.is_symlink(),'control type');read(p)
a=json.loads(files[L['authorization']]['content_base64'] and base64.b64decode(files[L['authorization']]['content_base64']));runtime=json.loads(base64.b64decode(files[L['runtime']]['content_base64']));claim=json.loads(base64.b64decode(files[q['launch_attempt']]['content_base64']))
ah=files[L['authorization']]['sha256'];rh=files[L['runtime']]['sha256']
checks['authorization_one_way']=set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-development-authorization-v1' and a['request_sha256']==qh and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip())
checks['runtime_one_way']=runtime==dict(schema='bcsp-development-runtime-v1',request_sha256=qh,authorization_sha256=ah)
checks['single_attempt_claim']=claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh)
template=base64.b64decode(files[L['launcher_template']['path']]['content_base64']).decode();rendered=template.replace('REQUEST_SHA256',qh).replace('AUTHORIZATION_SHA256',ah).replace('RUNTIME_SHA256',rh).encode()
checks['launcher_exact_rendering']=rendered==base64.b64decode(files[L['launcher']]['content_base64'])
# Bound traversal: only this failed output; reject links and unexpected special files.
paths=list(out.rglob('*'));require(len(paths)<=64,'64 entries');directories=[]
for p in paths:
 clean(p)
 if p.is_dir():directories.append(str(p.relative_to(out)))
 else:read(p)
relative={str(p.relative_to(out)) for p in paths if p.is_file()}
checks['exact_failure_output_files']=relative=={'launch.log','worker.pid','exit_code.txt','failure.json'}
checks['exact_output_directories']=set(directories)=={'tmp','predictions'}
failure=json.loads(base64.b64decode(files[str(out/'failure.json')]['content_base64']));log=base64.b64decode(files[L['log']]['content_base64']).decode(errors='replace')
checks['exit_code_one']=base64.b64decode(files[L['exit_code']]['content_base64']).strip()==b'1'
checks['failed_stop_no_retry']=failure['status']=='FAILED_STOP_NO_RETRY' and failure['training_updates']==0 and failure['BNCal']==0
checks['no_forward_or_prediction_artifacts']=not list((out/'predictions').iterdir()) and not any((out/n).exists() for n in ['forward_attempts.jsonl','inference_manifest.jsonl','geometry_summary.jsonl','resources.jsonl','inference_complete.json','completion.json','development_predictions_v1.tar.gz'])
checks['tmux_absent']=subprocess.run(['tmux','has-session','-t',L['tmux_session']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode==1
pid=int(base64.b64decode(files[L['pid']]['content_base64']).strip());proc=Path('/proc')/str(pid)/'cmdline';cmd=proc.read_bytes() if proc.exists() else b''
checks['worker_not_live']=not (q['entry']['path'].encode() in cmd or q['output'].encode() in cmd)
factory=q['implementation']['factory'];encoder=q['implementation']['encoder']
for r in [factory,encoder,q['helper']]:exact(r)
checks['factory_encoder_helper_unchanged']=True
checks['exact_factory_read_failure']=failure['error']=="RuntimeError('write/read boundary: "+factory['path']+"')" and "factory=module('p1_frozen_factory'" in log and 'write/read boundary:' in log
entry=base64.b64decode(files[q['entry']['path']]['content_base64']).decode()
checks['read_root_omission_confirmed']="str(Path(q['implementation']['factory']['path']).parent)" in entry and "[root,envroot,provider,Path(__file__).parent,'/usr/lib'" in entry and "roots.append" not in entry
index=json.loads(base64.b64decode(files[q['input_index']['path']]['content_base64']));checkpoint_records=[]
for run in index['runs']:
 exact(run['checkpoint']);checkpoint_records.append(run['checkpoint'])
checks['two_checkpoints_rehashed_unchanged']=len(checkpoint_records)==2
# Recheck all gathered content fingerprints, excluding access time.
for path,r in files.items():
 p=Path(path);st=p.stat();require((st.st_size,stat.S_IMODE(st.st_mode),st.st_uid,st.st_gid,st.st_mtime_ns,digest(p))==(r['bytes'],r['mode'],r['uid'],r['gid'],r['mtime_ns'],r['sha256']),'changed during audit '+path)
checks['evidence_content_stable_during_audit']=True
print(json.dumps(dict(status='FORMAL_FAILED_EXECUTION_FREEZE_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILED_STOP',checks=checks,request_sha256=qh,request_consumed=True,files=files,output_directories=directories,checkpoints=checkpoint_records,forward_attempts=0 if checks['no_forward_or_prediction_artifacts'] and checks['exact_factory_read_failure'] else None,successful_predictions=0,resource_peak_evidence='NOT_CREATED; no performance or CUDA equivalence conclusion',server_writes=0,forward_calls=0,bytes_read_for_text_evidence=total,seconds=time.monotonic()-start)),flush=True)
