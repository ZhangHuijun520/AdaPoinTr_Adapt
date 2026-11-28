from pathlib import Path,PurePosixPath
from collections import Counter
import base64,datetime,hashlib,json,math,subprocess,zlib
b=Path(__file__).resolve().parent
d=b/'post_training_freeze_audit_v3';d.mkdir(exist_ok=False)
h=lambda raw:hashlib.sha256(raw).hexdigest()
qraw=(b/'EJTC_D1_R_D_training_execution_request_h7vvrr_v3.json').read_bytes();rid=h(qraw)
assert rid=='91522ab958d4294327256ef4113be9ff9206995c44d264611ce27bda5afa07fc'
q=json.loads(qraw);root=q['binding']['install_root'];output=q['binding']['output'];launch=q['launch']
w=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000']
def save(name,value):
 with (d/name).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)
def remote(source,name):
 compile(source,'<read-only-training-audit>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 cmd=q['binding']['identity']['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(cmd)<=2048,len(cmd)
 p=subprocess.run(w+['exec','--timeout','55','--',cmd],capture_output=True,timeout=65)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 save(name+'.json',rec);assert p.returncode==0,rec
 return json.loads(rec['stdout'])
inventory=f'''import os,socket,stat,json,hashlib,subprocess
from pathlib import Path
assert socket.gethostname()=={q['binding']['identity']['hostname']!r} and os.getuid()==1000
def tree(name):
 root=Path(name);assert root.resolve(strict=True)==root and root.is_dir()
 rows=[]
 for p in sorted(root.rglob('*')):
  a=p.lstat();assert p.resolve(strict=True)==p
  if stat.S_ISDIR(a.st_mode):rows.append([str(p.relative_to(root)),'dir']);continue
  assert stat.S_ISREG(a.st_mode) and a.st_size<=536870912
  h=hashlib.sha256()
  with p.open('rb') as f:
   for raw in iter(lambda:f.read(4194304),b''):h.update(raw)
  z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
  rows.append([str(p.relative_to(root)),a.st_size,h.hexdigest()])
 return rows
live=[]
for p in Path('/proc').iterdir():
 if not p.name.isdigit():continue
 try:c=(p/'cmdline').read_bytes().replace(b'\\0',b' ').decode('utf-8','replace')
 except (FileNotFoundError,PermissionError,ProcessLookupError):continue
 if {root!r} in c:live.append([p.name,c])
v=subprocess.run(['tmux','has-session','-t','='+{launch['session_name']!r}],capture_output=True)
assert v.returncode in (0,1)
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),installed=tree({root!r}),output=tree({output!r}),live=live,session_absent=v.returncode==1)))
'''
before=remote(inventory,'remote_inventory_before')
assert not before['live'] and before['session_absent']
output_rows={r[0]:r[1:] for r in before['output'] if len(r)==3}
install_rows={r[0]:r[1:] for r in before['installed'] if len(r)==3}
expected_output={'common_initial_state.pth','ckpt-last.pth','ejtc_start.json','initialization.json','metrics.jsonl','optimizer_actual_defaults.json','optimizer_parameter_groups.json','order_plan.json','p3_resources.jsonl','completion.json','exposure.json'}
assert {k for k in output_rows if '/' not in k}==expected_output
assert {r[0] for r in before['output'] if len(r)==2 and '/' not in r[0]}=={'tmp','cache','mpl','triton','hf'}
assert all('/' not in k or k.split('/')[0] in {'tmp','cache','mpl','triton','hf'} for k in output_rows)
mapping=json.loads((b/'transport_h7vvrr_v3/EJTC_R_D_h7vvrr_request_install_mapping_v3.json').read_bytes())
expected_installed={PurePosixPath(x['path']).name:x['sha256'] for x in mapping['preserve_existing_files']}
expected_installed[PurePosixPath(launch['request_path']).name]=rid
new_control_names={PurePosixPath(launch[k]).name for k in ['authorization_path','runtime_path','single_attempt_log','resource_log','dispatch_log','exit_code_path']}
assert set(install_rows)==set(expected_installed)|new_control_names
assert not any(len(r)==2 for r in before['installed'])
assert all(install_rows[k][1]==v for k,v in expected_installed.items())
copies=d/'evidence';copies.mkdir()
def get(path,expected):
 name=PurePosixPath(path).name;local=copies/name
 assert not local.exists()
 target='/mnt/'+str(local.resolve())[0].lower()+str(local.resolve())[2:].replace('\\','/')
 p=subprocess.run(w+['get',path,target,'--timeout','40'],capture_output=True,timeout=55)
 assert p.returncode==0,(path,p.stdout,p.stderr)
 assert [local.stat().st_size,h(local.read_bytes())]==expected,name
for name in sorted(expected_output-{'common_initial_state.pth','ckpt-last.pth'}):get(str(PurePosixPath(output)/name),output_rows[name])
for name in sorted(new_control_names):get(str(PurePosixPath(root)/name),install_rows[name])
def obj(name):return json.loads((copies/name).read_bytes())
def lines(name):return [json.loads(x) for x in (copies/name).read_bytes().splitlines()]
done=obj('completion.json');start=obj('ejtc_start.json');init=obj('initialization.json');plan=obj('order_plan.json');exposure=obj('exposure.json')
contract=json.loads((b.parent/'d1_r_d_preparation_v1/EJTC_D1_common_contract_v1.json').read_bytes())
assert output_rows['order_plan.json'][1]==q['order_file_sha256']
canon=h(json.dumps(plan,sort_keys=True,separators=(',',':')).encode())
assert canon==contract['order_canonical_sha256']==done['order_sha256']==init['order_sha256']==exposure['order_sha256']
assert start['state_sha256']==init['persistent_state_sha256']==q['initial_state_sha256']
assert start['serialized_initial_state_sha256']==output_rows['common_initial_state.pth'][1]
assert start['request_sha256']==rid and start['arm']=='R' and start['common_sha256']==q['files']['common']['sha256']
assert init['seed']==q['seeds'][0] and len(init['parameter_sha256'])==64
assert set(start['rng'])=={'python','numpy','cpu','cuda'} and all(len(v)==64 for v in start['rng'].values())
metrics=lines('metrics.jsonl');assert len(metrics)==3900
case=Counter();source=Counter();drops=Counter()
all_ids=set(plan['case_ids']);assert len(all_ids)==315
for epoch,row in enumerate(plan['epochs']):
 assert row['epoch']==epoch and len(row['batches'])==39 and len(row['dropped'])==3
 assert set(sum(row['batches'],[])+row['dropped'])==all_ids and len(sum(row['batches'],[])+row['dropped'])==315
 drops.update(row['dropped'])
 for bi,batch in enumerate(row['batches']):
  index=epoch*39+bi;m=metrics[index]
  assert m['step']==index+1 and m['epoch']==epoch and m['batch']==bi and m['case_ids']==batch and len(batch)==8
  assert m['source_ids']==['train:'+cid.split('__')[1] for cid in batch]
  assert m['optimizer_step_committed'] is True and m['clip_max_norm']==10
  assert m['ejtc_auxiliary'] is None and m['ejtc_applied_lambda'] is None
  assert all(math.isfinite(m[k]) for k in ['loss_sparse','loss_dense','loss_denoise','loss_reconstruction','loss','grad_norm_before_clip'])
  assert m['loss_sparse']==m['loss_denoise']==0 and m['loss']==m['loss_reconstruction']==m['loss_dense']
  assert all(math.isclose(v,.0001*max(.9**(epoch/21),.02),rel_tol=1e-12) for v in m['LR']) and len(m['LR'])==2
  assert math.isclose(m['BN_momentum'],max(.9*.5**(epoch/21),.01),rel_tol=1e-12)
  case.update(batch);source.update(m['source_ids'])
assert dict(case)==exposure['case'] and dict(source)==exposure['source'] and dict(drops)==exposure['dropped_case']
assert len(case)==315 and len(source)==63 and sum(case.values())==sum(source.values())==31200 and sum(drops.values())==300
assert done['optimizer_updates']==3900 and done['traversals']==100 and done['case_exposures']==31200
assert done['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100)
assert all(done[k] is False for k in ['bncal_executed','evaluation_executed','resume'])
assert done['scq_prime_run_identity']==dict(variant='R',fold='D',seed=q['seeds'][0])
assert done['checkpoint_sha256']==output_rows['ckpt-last.pth'][1]
auth_raw=(copies/'R_D_authorization_v3.json').read_bytes();auth=json.loads(auth_raw)
assert auth==json.loads((b/'R_D_user_execution_authorization_v3.json').read_bytes()) and rid in auth['user_authorization_text']
assert obj('R_D_runtime_v3.json')==dict(schema='bcsp-development-runtime-v1',request_sha256=rid,authorization_sha256=h(auth_raw))
assert (copies/'R_D_exit_code_v3.txt').read_bytes().strip()==b'0'
mon=lines('R_D_resource_v3.jsonl');assert mon[-1]==dict(state='WORKER_COMPLETE',exit_code=0)
for row in mon[:-1]:
 r=q['binding']['resources']
 assert row['gpu_used_MiB']<=r['device_used_MiB'] and row['RSS_bytes']<=r['rss_bytes'] and row['disk_free_bytes']>=r['minimum_disk_bytes'] and row['output_bytes']<=r['output_bytes'] and row['elapsed_seconds']<=r['wall_seconds']
resources=lines('p3_resources.jsonl')
save('independent_recomputed_counts.json',dict(case=dict(case),source=dict(source),drops=dict(drops),metrics=len(metrics),order_canonical_sha256=canon,resource_records=len(resources),monitor_records=len(mon)))
after=remote(inventory,'remote_inventory_after');assert before==after
receipt=dict(status='FORMAL_READ_ONLY_R_D_V3_POST_TRAINING_FREEZE_AUDIT_PASS',request_sha256=rid,timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),checkpoint=dict(path=str(PurePosixPath(output)/'ckpt-last.pth'),bytes=output_rows['ckpt-last.pth'][0],sha256=output_rows['ckpt-last.pth'][1],independently_hashed_twice=True),initial_state=dict(recorded_tensor_fingerprint=init['persistent_state_sha256'],parameter_fingerprint=init['parameter_sha256'],serialized_sha256=output_rows['common_initial_state.pth'][1],serialized_independently_hashed_twice=True,rng=start['rng'],limitation='Tensor fingerprints are verified against frozen runtime records and P1 contract; no model rebuild or checkpoint deserialization was performed.'),counts=dict(steps=3900,epochs=100,exposures=31200,drops=300,cases=315,sources=63),full_batch_order_verified=True,all_metric_numeric_LR_BN_checks=True,recorded_R_auxiliary_absent=True,full_inventory_stable=True,output_files=len(output_rows),old_failed_files_preserved=True,worker_and_session_absent=True,resource_monitor_pass=True,elapsed_training_seconds=done['elapsed_seconds'],training_or_forward_run_during_audit=False,remote_mutations=False,BNCal=False,evaluation=False,evidence_sha256={p.name:h(p.read_bytes()) for p in sorted(copies.iterdir())})
save('formal_post_training_freeze_audit_v3.json',receipt)
print(json.dumps(receipt))
