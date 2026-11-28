"""Formal post-prediction read-only audit; no model imports or scoring."""
from pathlib import Path
import base64,datetime,hashlib,json,subprocess,zlib
b=Path(__file__).resolve().parent;t=b/'transport_h7vvrr_v2';e=b/'post_prediction_freeze_audit_v2';e.mkdir(exist_ok=False)
h=lambda raw:hashlib.sha256(raw).hexdigest()
qpath=b/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json';rid=h(qpath.read_bytes());assert rid=='4b9dc3dac44c4d547fb5c79826dc48346610a19ab828392c4fdbe1e98fcdec31'
q=json.loads(qpath.read_bytes());scope=json.loads((b/'EJTC_RTJ_D_native315_scope_v2.json').read_bytes());m=json.loads((t/'EJTC_RTJ_D_native315_h7vvrr_install_mapping_v2.json').read_bytes());i=q['binding']['identity'];root=q['binding']['output'];p=q['launch']
common=f'''import os,socket,stat,json,hashlib,sys
from pathlib import Path
assert (socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0])=={(i['hostname'],i['uid'],i['python_realpath'],i['python_version'])!r}
def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=536870912
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [a.st_size,h.hexdigest()]
'''
def run(code,name):
 source=common+code;compile(source,'<post-prediction-readonly>','exec');blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 command=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"';assert len(command.encode())<=2048,len(command)
 r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','50','--',command],capture_output=True,timeout=60)
 result=dict(returncode=r.returncode,stdout=r.stdout.decode('utf-8','replace'),stderr=r.stderr.decode('utf-8','replace'))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 assert r.returncode==0,result
 return json.loads(result['stdout'])
inventory=f'''import subprocess
assert subprocess.run(['tmux','has-session','-t','='+{p['session_name']!r}],capture_output=True).returncode==1
live=[]
for x in Path('/proc').iterdir():
 if x.name.isdecimal() and int(x.name)!=os.getpid():
  try:c=(x/'cmdline').read_bytes().split(b'\\0')
  except (FileNotFoundError,PermissionError,ProcessLookupError):continue
  if any(v in c for v in {[q['files']['worker']['path'].encode(),p['launcher']['path'].encode()]!r}):live.append(x.name)
assert not live
out=Path({root!r});installed=Path({q['binding']['install_root']!r})
files={{}};dirs=[]
for x in sorted(out.rglob('*')):
 assert not x.is_symlink() and x.resolve()==x
 if x.is_dir():dirs.append(x.relative_to(out).as_posix())
 else:files[x.relative_to(out).as_posix()]=read(str(x))
assert len(files)<=400
print(json.dumps(dict(files=files,dirs=dirs,installed={{x.name:read(str(x)) for x in sorted(installed.iterdir())}},session_absent=True,worker_launcher_absent=True)))
'''
first=run(inventory,'independent_inventory_before');files=first['files']
prednames=[f'predictions/{a}_D__{cid}.npz' for a in ('R','T','J') for cid in scope['case_ids']]
metadata=['started.json','attempts.jsonl','manifest.jsonl','inference_complete.json','resources.jsonl','completion.json','EJTC_RTJ_D_native315.tar.gz','EJTC_RTJ_D_native315.tar.gz.sha256','archive_members.json','archive_members.json.sha256']
assert set(files)==set(prednames+metadata) and len(files)==325
assert set(first['dirs'])=={'predictions','TMPDIR','XDG_CACHE_HOME','MPLCONFIGDIR','TRITON_CACHE_DIR','HF_HOME'}
installed={r['member']:[r['bytes'],r['sha256']] for r in m['files']}
installed_names={Path(p[k]).name for k in ('authorization_path','runtime_path','single_attempt_log','resource_log','dispatch_log','exit_code_path')}
assert set(first['installed'])==set(installed)|installed_names
assert all(first['installed'][k]==v for k,v in installed.items())
def fetch(name,remote):
 result=run(f"p=Path({remote!r});assert p.stat().st_size<=2097152\nprint(json.dumps(dict(raw=p.read_text(),fingerprint=read(str(p)))))",name)
 (e/(name+'_bytes.txt')).write_bytes(result['raw'].encode())
 assert h(result['raw'].encode())==result['fingerprint'][1]
 return result['raw']
data={name:fetch(name.replace('.','_'),root+'/'+name) for name in metadata[:6]}
completion=json.loads(data['completion.json']);done=json.loads(data['inference_complete.json']);started=json.loads(data['started.json'])
for row in (completion,done,started):assert row['request_sha256']==rid and row['counts']==q['counts']
assert completion['status']=='PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT' and done['status']=='EJTC_RTJ_D_NATIVE315_COMPLETE'
assert done['paired_cases']==105 and [r['arm'] for r in done['states']]==['R','T','J']
for row in done['states']:
 assert row['forwards']==105 and row['before']==row['after'] and set(row['before'])=={'state','python','numpy','cpu','cuda'}
 assert all(isinstance(v,str) and len(v)==64 and set(v)<=set('0123456789abcdef') for v in row['before'].values())
assert len({r['before']['state'] for r in done['states']})==3
attempts=[json.loads(r) for r in data['attempts.jsonl'].splitlines()];manifest=[json.loads(r) for r in data['manifest.jsonl'].splitlines()]
assert len(attempts)==len(manifest)==315
for j,(a,r,sched) in enumerate(zip(attempts,manifest,scope['schedule']),1):
 arm=sched['arm'];cid=sched['case_id'];source=scope['inputs'][(j-1)%105]
 assert a==dict(index=j,arm=arm,case_id=cid,status='CLAIMED_BEFORE_FORWARD')
 assert (r['index'],r['arm'],r['fold'],r['case_id'],r['source_id'],r['seed'])==(j,arm,'D',cid,source['source_id'],q['seeds'][0])
 assert r['n_input']==r['n_output']==8192 and r['frame']=='native_D_only_normalized' and r['normalization']==source['normalization']
 assert r['input_sha256']==source['input']['sha256'] and r['partial_array_sha256']==source['partial_array_sha256'] and r['checkpoint_sha256']==q['checkpoints'][arm]['sha256']
 assert r['ssm_calls']==36 and r['native_fc_parent_major_verified'] is True and r['diagnostic_fields']==sorted(['coarse','prediction','S','delta','parent_index','token_index'])
 assert r['member']==prednames[j-1] and [r['bytes'],r['sha256']]==files[r['member']]
resources=[json.loads(r) for r in data['resources.jsonl'].splitlines()];limits=q['binding']['resources']
assert [r['index'] for r in resources]==list(range(15,316,15))+[315]
for r in resources:
 assert r['uuid']==i['gpu_uuid'] and r['driver']==i['driver_version'] and r['used_MiB']<=limits['device_used_MiB'] and r['peak_allocated']<=limits['torch_peak_bytes']
monitor=fetch('launcher_resource_log',p['resource_log']);rows=[json.loads(r) for r in monitor.splitlines()]
assert rows[-1]==dict(state='WORKER_COMPLETE',exit_code=0)
for r in rows[:-1]:
 assert r['elapsed_seconds']<=limits['wall_seconds'] and r['gpu_used_MiB']<=limits['device_used_MiB'] and r['RSS_bytes']<=limits['rss_bytes'] and r['disk_free_bytes']>=limits['minimum_disk_bytes'] and r['output_bytes']<=limits['output_bytes']
assert fetch('exit_code',p['exit_code_path']).strip()=='0'
authraw=fetch('authorization',p['authorization_path']);rtraw=fetch('runtime',p['runtime_path']);auth=json.loads(authraw);rt=json.loads(rtraw)
assert auth['request_sha256']==rid and auth['explicit_user_authorization'] is True and rid in auth['user_authorization_text']
assert rt==dict(schema='bcsp-development-runtime-v1',request_sha256=rid,authorization_sha256=h(authraw.encode()))
archivecode=f'''import tarfile
out=Path({root!r});rows=[];seen=set()
with tarfile.open(out/'EJTC_RTJ_D_native315.tar.gz','r:gz') as a:
 for t in a:
  assert t.isfile() and t.name not in seen and len(rows)<320 and t.size<=2097152
  seen.add(t.name);b=a.extractfile(t).read();fp=[len(b),hashlib.sha256(b).hexdigest()]
  assert fp==read(str(out/t.name));rows.append(dict(name=t.name,bytes=fp[0],sha256=fp[1]))
assert len(rows)==320
listing=json.loads((out/'archive_members.json').read_bytes());assert rows==listing
for n in ('EJTC_RTJ_D_native315.tar.gz','archive_members.json'):
 assert (out/(n+'.sha256')).read_text().split()==[read(str(out/n))[1],n]
print(json.dumps(dict(rows=rows,archive=read(str(out/'EJTC_RTJ_D_native315.tar.gz')),listing=read(str(out/'archive_members.json')))))
'''
packed=run(archivecode,'independent_archive_and_members')
assert {r['name'] for r in packed['rows']}==set(prednames+metadata[:5])
assert packed['archive']==[completion['archive']['bytes'],completion['archive']['sha256']] and packed['listing'][1]==completion['archive']['member_listing_sha256']
# Independent NPY header/finite/geometry checks using stdlib only; no CUDA/NumPy imports.
payloadcode='''import array,ast,io,math,struct,zipfile
def validate(name):
 with zipfile.ZipFile(name) as z:
  assert set(z.namelist())=={k+'.npy' for k in ('coarse','prediction','S','delta','parent_index','token_index')}
  values={}
  for k,shape,typ in [('coarse',(256,3),'<f4'),('prediction',(8192,3),'<f4'),('S',(256,3),'<f4'),('delta',(256,3),'<f4'),('parent_index',(8192,),'<i8'),('token_index',(256,),'<i8')]:
   f=io.BytesIO(z.read(k+'.npy'));assert f.read(6)==b'\\x93NUMPY';v=f.read(2);assert v in (b'\\x01\\x00',b'\\x02\\x00')
   n=struct.unpack('<H' if v[0]==1 else '<I',f.read(2 if v[0]==1 else 4))[0];header=ast.literal_eval(f.read(n).decode('latin1'))
   assert header==dict(descr=typ,fortran_order=False,shape=shape)
   a=array.array('f' if typ=='<f4' else 'q');a.frombytes(f.read());assert len(a)==math.prod(shape)
   assert all(math.isfinite(x) for x in a);values[k]=a
  assert list(values['token_index'])==list(range(256)) and list(values['parent_index'])==[j//32 for j in range(8192)]
  assert values['coarse'].tobytes()==b''.join(struct.pack('<f',s+d) for s,d in zip(values['S'],values['delta']))
 return True
'''
for j in range(0,315,30):
 names=[root+'/'+n for n in prednames[j:j+30]]
 assert run(payloadcode+'print(json.dumps([validate(n) for n in '+repr(names)+']))','payload_batch_'+str(j//30+1).zfill(2))==[True]*len(names)
 print('Independently validated predictions '+str(min(j+30,315))+'/315',flush=True)
# Rehash all 167 reused files, including three weights and 105 inputs, after prediction.
assets=m['reused_assets'];paths=list(assets)
for j in range(0,len(paths),8):
 names=paths[j:j+8];got=run('print(json.dumps({p:read(p) for p in '+repr(names)+'}))','reuse_'+str(j//8+1).zfill(2))
 assert got=={p:[assets[p]['bytes'],assets[p]['sha256']] for p in names}
last=run(inventory,'independent_inventory_after');assert first==last
receipt=dict(status='FORMAL_READ_ONLY_EJTC_NATIVE315_V2_POST_PREDICTION_FREEZE_AUDIT_PASS',timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),request_sha256=rid,identity=i,counts=q['counts'],predictions=315,paired_cases=105,sources=21,arms=['R','T','J'],output_files=325,archive_members=320,archive=dict(path=root+'/EJTC_RTJ_D_native315.tar.gz',bytes=packed['archive'][0],sha256=packed['archive'][1]),listing_sha256=packed['listing'][1],all_member_hashes_independently_recomputed=True,all_prediction_payloads_validated=True,all_case_pairing_verified=True,state_and_all_RNG_streams_unchanged=True,reused_file_hashes_verified=167,monitor_resource_samples=len(rows)-1,resource_records=len(resources),all_recorded_resources_pass=True,exit_code=0,session_worker_launcher_absent=True,stable_inventory_before_after=True,remote_mutations=False,CUDA_imports=0,new_forward_calls=0,scoring_started=False,evidence_sha256={p.name:h(p.read_bytes()) for p in sorted(e.iterdir()) if p.is_file()})
with (e/'formal_post_prediction_freeze_audit_v2.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k!='evidence_sha256'},ensure_ascii=False))
