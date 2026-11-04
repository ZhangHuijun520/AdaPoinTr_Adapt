"""Render bounded authorized operations; no server call or model import."""
import ast,base64,hashlib,json,shlex
from pathlib import Path,PurePosixPath
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';A=O/'authorized_execution_v2'
S='4a889afad90b1a8a52fcb75691c71990d03af8b7d120a96608ac4b9b85cb7a62'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(name,raw):
 with (A/name).open('xb') as f:f.write(raw)
def main():
 scope_raw=(O/'V1_training_execution_request_v2.json').read_bytes();assert sha(scope_raw)==S
 qraw=(O/'V1_training_entry_request_v1.json').read_bytes();scope=json.loads(scope_raw);q=json.loads(qraw)
 assert sha(qraw)==scope['inner_request']['sha256']
 mapping=json.loads((O/'non_overwrite_installation_mapping_v1.json').read_text(encoding='utf-8'))
 roots=[q['implementation']['entry']['path'].split('/implementation/')[0],q['data_root'].rsplit('/',1)[0],str(PurePosixPath(scope['future_paths']['output']).parent)]
 def destination(member):
  p=PurePosixPath(member);assert not p.is_absolute() and '..' not in p.parts and '\\' not in member
  return roots[1]+'/'+member[5:] if member.startswith('data/') else roots[0]+'/'+member
 assert len(mapping['assets'])==647 and all(destination(r['member'])==r['destination'] for r in mapping['assets'])
 common='''import os,socket,json,hashlib,stat,subprocess,shutil,sys,time,base64,tarfile,io
from pathlib import Path,PurePosixPath
START=time.monotonic()
def h(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,msg):
 if not ok:raise RuntimeError(msg)
def parents(p):
 for x in (p,*p.parents):need(stat.S_ISDIR(x.lstat().st_mode),'non-directory/linked parent: '+str(x))
def regular(p):
 parents(p.parent);need(stat.S_ISREG(p.lstat().st_mode),'nonregular/linked file: '+str(p))
def exact(p,size,digest):
 p=Path(p);regular(p);a=p.stat();need(a.st_size==size,'size: '+str(p));raw=p.read_bytes();b=p.stat()
 need((a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns) and h(raw)==digest,'hash/drift: '+str(p));return raw
def absent(p):
 need(not p.exists() and not p.is_symlink(),'target exists: '+str(p))
def cmd(v):return subprocess.check_output(v,stderr=subprocess.PIPE,timeout=10).decode().strip()
def identity():
 need(socket.gethostname()==Q['identity']['hostname'] and os.getuid()==1000,'host/uid')
 project=Path(Q['identity']['project']);parents(project);os.chdir(project)
 v=[x.strip() for x in cmd(['nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']).split(',')]
 i=Q['identity'];need(v[:4]==[i['gpu_uuid'],i['gpu_name'],i['driver_version'],str(i['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
 need(not cmd(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']),'GPU compute process')
 need(shutil.disk_usage(project).free>=4294967296,'minimum free disk')
 need(str(Path(i['python_realpath']).resolve())==i['python_realpath'] and cmd([i['python_realpath'],'--version'])=='Python '+i['python_version'],'Python identity')
def destination(member):
 p=PurePosixPath(member);need(not p.is_absolute() and '..' not in p.parts and '\\\\' not in member,'member path')
 need(member.startswith(('data/','evidence/','implementation/','control_V1_v1/')),'member domain')
 return Path(ROOTS[1]+'/'+member[5:] if member.startswith('data/') else ROOTS[0]+'/'+member)
def uploaded():
 for r in SCOPE['transport']['files']:exact(Path('/home/jovyan')/r['filename'],r['bytes'],r['sha256'])
 name='bcsp_sampling_ab_foldc_seed0_v1'
 text=(Path('/home/jovyan')/(name+'.contents.sha256')).read_text(encoding='ascii')
 rows={}
 for line in text.splitlines():
  digest,member=line.split('  ',1);need(member not in rows and len(digest)==64,'manifest duplicates');destination(member);rows[member]=digest
 need(len(rows)==647,'manifest count')
 need((Path('/home/jovyan')/(name+'.bytes')).read_text().strip()==str(SCOPE['transport']['files'][0]['bytes']),'byte sidecar')
 return rows,Path('/home/jovyan')/(name+'.tar.gz')
def fresh_roots():
 for name in ROOTS:
  p=Path(name);parents(p.parent);absent(p);need(os.access(p.parent,os.W_OK),'parent not writable')
def exact_old_assets():
 report=json.loads(exact(ROOTS[0]+'/evidence/server_assets_observation_v1.json',ASSET_SIZE,ASSET_SHA))
 need(report['status']=='SELECTED30_HASH_PASS' and len(report['assets'])==30,'selected30 evidence')
 for r in report['assets']:exact(r['path'],r['bytes'],r['sha256'])
def emit(v):print(json.dumps(v,ensure_ascii=True),flush=True)
'''
 constants='SCOPE_RAW=base64.b64decode('+repr(base64.b64encode(scope_raw).decode())+')\n'
 constants+='need(h(SCOPE_RAW)=='+repr(S)+',"scope identity")\nSCOPE=json.loads(SCOPE_RAW)\n'
 constants+='Q_RAW=base64.b64decode('+repr(base64.b64encode(qraw).decode())+')\nQ=json.loads(Q_RAW)\n'
 constants+='need(h(Q_RAW)==SCOPE["inner_request"]["sha256"],"inner identity")\nROOTS='+repr(roots)+'\n'
 ar=O/'server_assets_observation_v1.json';constants+='ASSET_SIZE='+str(ar.stat().st_size)+'\nASSET_SHA='+repr(sha(ar.read_bytes()))+'\n'
 precheck='''identity();rows,archive=uploaded();fresh_roots()
need(not shutil.which('tmux') is None,'tmux unavailable')
need(subprocess.run(['tmux','has-session','-t',SCOPE['future_paths']['tmux']],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode!=0,'tmux already exists')
emit(dict(status='UPLOAD_AND_DESTINATION_READONLY_PASS',scope_sha256=h(SCOPE_RAW),upload_files=5,members=647,roots_absent=ROOTS,server_writes=0,disk_free=shutil.disk_usage(Path.cwd()).free,seconds=time.monotonic()-START))
'''
 install='''created=[];dirs=[];phase='PREWRITE'
try:
 identity();rows,archive=uploaded();fresh_roots()
 payload={}
 with tarfile.open(archive,'r:gz') as tf:
  ms=tf.getmembers();need(len(ms)==len({m.name for m in ms})==647 and {m.name for m in ms}==set(rows),'exact archive set')
  for m in ms:
   need(m.isfile() and m.size<=2000000,'member type/size');raw=tf.extractfile(m).read();need(h(raw)==rows[m.name],'member hash');payload[destination(m.name)]=raw
 need(shutil.disk_usage(Path.cwd()).free>=4294967296+sum(map(len,payload.values())),'installation disk budget')
 for p in payload:absent(p)
 emit(dict(status='ALL_647_TARGETS_PREWRITE_PASS',scope_sha256=h(SCOPE_RAW),server_writes=0))
 phase='EXCLUSIVE_INSTALLATION'
 for name in ROOTS:os.mkdir(name,0o755);dirs.append(name)
 for p,raw in payload.items():
  chain=[];cur=p.parent
  while not cur.exists():chain.append(cur);cur=cur.parent
  parents(cur)
  for d in reversed(chain):os.mkdir(d,0o755);dirs.append(str(d))
  parents(p.parent);absent(p)
  dfd=os.open(str(p.parent),os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
  try:
   fd=os.open(p.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644,dir_fd=dfd);created.append(str(p))
   with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  finally:os.close(dfd)
 for member,digest in rows.items():
  p=destination(member);exact(p,len(payload[p]),digest)
 emit(dict(status='INSTALLATION_647_HASH_PASS',scope_sha256=h(SCOPE_RAW),files=len(created),directories=len(dirs),seconds=time.monotonic()-START,training_started=False))
except BaseException as exc:
 emit(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),created_files=len(created),last_created=created[-1] if created else None,directories=dirs,training_started=False));raise
'''
 materialize='''phase='PRE_MATERIALIZATION'
try:
 identity();rows,archive=uploaded()
 for member,digest in rows.items():
  p=destination(member);regular(p);need(h(p.read_bytes())==digest,'installed hash: '+str(p))
 exact_old_assets()
 import importlib.util
 entry_path=Path(Q['implementation']['entry']['path'])
 spec=importlib.util.spec_from_file_location('authorized_sampling_metadata',entry_path);entry=importlib.util.module_from_spec(spec);sys.modules[spec.name]=entry;spec.loader.exec_module(entry)
 selected,fold=entry.verify_qualified_receipt(entry.json_bound(Q['QC']['qualified_receipt']),Q['QC']['verification'],Q['QC']['manifests'],Q['QC']['fold_binding'],Q['fold'],Q['n_input'],Q['arm'])
 entry.validate_order(entry.json_bound(Q['order_plan']),fold['train_case_ids'])
 entry.validate_rebind(Q['resource_rebind'],Q['preflight_scope'],Q['GPU_audit'])
 helper=entry.load_bound('sampling_source_guard',Q['implementation']['preflight_helper']);scope=entry.json_bound(Q['preflight_scope']);root=Path(Q['model_root'])
 for rel,r in helper.source_map(scope).items():helper.exact(root/rel,r['sha256'],r['bytes'])
 helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
 for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
 need('torch' not in sys.modules,'unexpected model import during preparation')
 future=SCOPE['future_paths'];control=Path(future['control']);parents(control)
 need({p.name for p in control.iterdir()}=={'training_entry_request_v1.json'},'fresh request-only control')
 for key in ['authorization','runtime','launcher','launch_attempt','output']:absent(Path(future[key]))
 need(subprocess.run(['tmux','has-session','-t',future['tmux']],stdout=subprocess.PIPE,stderr=subprocess.PIPE).returncode!=0,'tmux exists')
 def save(path,raw,mode=0o600):
  p=Path(path);parents(p.parent);absent(p);fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode)
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 def encode(v):return json.dumps(v,ensure_ascii=True,indent=2).encode()
 phase='AUTHORIZED_MATERIALIZATION'
 grant={'schema':'bcsp-training-authorization-v1','request_sha256':h(Q_RAW),'explicit_user_authorization':True,'user_authorization_text':USER_GRANT}
 auth=encode(grant);save(future['authorization'],auth)
 runtime=encode({'schema':'bcsp-training-runtime-v1','request_sha256':h(Q_RAW),'authorization_sha256':h(auth)});save(future['runtime'],runtime)
 def record(path,raw):return {'path':path,'bytes':len(raw),'sha256':h(raw)}
 entry.authorize(SCOPE['inner_request'],record(future['authorization'],auth),record(future['runtime'],runtime))
 env=dict(SCOPE['launcher_contract']['environment']);env['TMPDIR']=future['output']+'/tmp'
 entry.validate_environment(scope,Q['identity'],future['output'],env)
 import shlex
 argv=['env']+[k+'='+v for k,v in env.items()]+['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',SCOPE['launcher_contract']['python'],'-I','-S','-B',str(entry_path),'--request',SCOPE['inner_request']['path'],'--request-sha256',h(Q_RAW),'--authorization',future['authorization'],'--authorization-sha256',h(auth),'--runtime',future['runtime'],'--runtime-sha256',h(runtime)]
 quote=shlex.quote;command=' '.join(map(quote,argv))
 launcher='#!/bin/bash\\nset -u\\numask 077\\nmkdir -- '+quote(future['output'])+' || exit 90\\n'+command+' > '+quote(future['log'])+' 2>&1\\nrc=$?\\n(set -o noclobber; printf \\'%s\\\\n\\' "$rc" > '+quote(future['exit_code'])+') || exit 91\\nexit "$rc"\\n'
 raw_launcher=launcher.encode();save(future['launcher'],raw_launcher,0o700)
 check=subprocess.run(['/bin/bash','-n',future['launcher']],stdout=subprocess.PIPE,stderr=subprocess.PIPE);need(check.returncode==0,'launcher syntax')
 identity()
 marker=encode({'schema':'bcsp-sampling-single-launch-attempt-v1','status':'CLAIMED_BEFORE_TMUX','request_sha256':h(Q_RAW),'execution_scope_sha256':h(SCOPE_RAW),'run_id':Q['run_id'],'no_retry':True})
 phase='SINGLE_TMUX_ATTEMPT';save(future['launch_attempt'],marker)
 result=subprocess.run(['tmux','new-session','-d','-s',future['tmux'],'exec /bin/bash '+quote(future['launcher'])],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
 need(result.returncode==0,'tmux launch return code '+str(result.returncode))
 emit(dict(status='SINGLE_TMUX_LAUNCH_RETURNED_ZERO_NOT_TRAINING_PROOF',scope_sha256=h(SCOPE_RAW),request_sha256=h(Q_RAW),authorization_sha256=h(auth),runtime_sha256=h(runtime),launcher_sha256=h(raw_launcher),tmux=future['tmux'],derived_TMPDIR=env['TMPDIR'],candidate_started=False,seconds=time.monotonic()-START))
except BaseException as exc:
 emit(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),candidate_started=False));raise
'''
 grant='Exact user text: 已上传，按既定分阶段边界，再单独授权当前 **v2 request完整SHA256**\nReference resolution (not a quotation): current v2 scope SHA256 '+S+'; sole V1 inner request SHA256 '+sha(qraw)
 for name,body in [('precheck',precheck),('install',install),('materialize',materialize)]:
  source=common+constants+'USER_GRANT='+repr(grant)+'\n'+body
  ast.parse(source);save(name+'_server_v1.py',source.encode('utf-8'))
 template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8')
 for name in ['precheck','install','materialize']:
  payload=(A/(name+'_server_v1.py')).read_bytes()
  seconds=300 if name=='install' else 120
  driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',sha(payload)).replace('120s ',str(seconds)+'s ').replace("'135'",repr(str(seconds+15)))
  ast.parse(driver);save(name+'_driver_v1.py',driver.encode())
 save('operation_plan_v1.json',json.dumps({'scope_sha256':S,'phases':['precheck','install','materialize','observe'],'payloads':{n:sha((A/(n+'_server_v1.py')).read_bytes()) for n in ['precheck','install','materialize']},'only_one_training':True,'existing_short_wire_driver_reused':True,'TMPDIR_derivation':'Required explicitly by frozen entry; set to exact owned output/tmp, frozen listed environment fields unchanged'},indent=2).encode())
 print('AUTHORIZED_OPERATIONS_RENDERED_NO_SERVER_CALLS')
if __name__=='__main__':main()
