"""Bounded read-only asset/resource/target verification. No CUDA imports or remote writes."""
from pathlib import Path,PurePosixPath
import base64,datetime,hashlib,json,subprocess,zlib
d=Path(__file__).resolve().parent;project=d.parents[2];base=d.parent
e=d/'execution_readiness_v1';e.mkdir(exist_ok=False)
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_bytes())
qp=d/'EJTC_D1_J_D_training_execution_request_h7vvrr_v1.json';rid=h(qp)
assert rid=='325c229ee04e2e32bbb65b4c75a80c3a53be7e6c0e347e09d3d0da5f77917d86'
q=load(qp);i=q['binding']['identity']
common=f'''import os,socket,stat,hashlib,json,sys
from pathlib import Path
assert (socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0])=={(i['hostname'],i['uid'],i['python_realpath'],i['python_version'])!r}
'''
def run(code,name):
 source=common+code;compile(source,'<J-D-read-only>','exec')
 blob=base64.b64encode(zlib.compress(source.encode(),9)).decode()
 command=i['python_realpath']+' -I -S -B -c "exec(__import__(\'zlib\').decompress(__import__(\'base64\').b64decode(\''+blob+'\')))"'
 assert len(command)<=2048,len(command)
 p=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','50','--',command],capture_output=True,timeout=60)
 rec=dict(returncode=p.returncode,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
 with (e/(name+'.json')).open('x',encoding='utf-8') as f:json.dump(rec,f,indent=2)
 assert p.returncode==0,rec
 return json.loads(rec['stdout'])
mapping=load(d/'transport_h7vvrr_v1/EJTC_J_D_h7vvrr_install_mapping_v1.json')
expected=sorted([[x['member'],x['bytes'],x['sha256']] for x in mapping['files']])
expected_inventory_hash=hashlib.sha256(json.dumps(expected,separators=(',',':')).encode()).hexdigest()
new=[q['binding']['output']]+[q['launch'][k] for k in ['authorization_path','runtime_path','single_attempt_log','resource_log','dispatch_log','exit_code_path']]
scan=f'''import subprocess
for name in {new!r}:assert not os.path.lexists(name)
r=Path({q['binding']['install_root']!r});assert r.resolve(strict=True)==r and r.is_dir()
installed=[];dirs=[]
for p in sorted(r.rglob('*')):
 assert p.resolve(strict=True)==p
 if p.is_dir():dirs.append(str(p.relative_to(r)));continue
 a=p.lstat();assert stat.S_ISREG(a.st_mode) and a.st_size<=262144
 raw=p.read_bytes();z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 installed.append([str(p.relative_to(r)),len(raw),hashlib.sha256(raw).hexdigest()])
assert dirs==['labels'] and len(installed)==279 and hashlib.sha256(json.dumps(sorted(installed),separators=(',',':')).encode()).hexdigest()=={expected_inventory_hash!r}
for name in {[q['binding']['install_root'],q['binding']['output']]!r}:
 p=Path(name).parent;assert p.resolve(strict=True)==p and p.is_dir() and os.access(p,os.W_OK|os.X_OK)
args=['/usr/bin/nvidia-smi','--id={i['gpu_uuid']}']
v=[x.strip() for x in subprocess.check_output(args+['--query-gpu=uuid,driver_version,name,memory.total,memory.used,memory.free','--format=csv,noheader,nounits'],text=True,timeout=8).strip().split(',')]
assert v[:4]=={[i['gpu_uuid'],i['driver_version'],i['gpu_name'],i['total_MiB']]!r}
assert int(v[4])<={q['binding']['resources']['idle_used_MiB']} and int(v[5])>={q['binding']['resources']['minimum_start_free_MiB']}
assert not subprocess.check_output(args+['--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True,timeout=8).strip()
assert subprocess.run(['tmux','has-session','-t','='+{q['launch']['session_name']!r}],capture_output=True).returncode==1
s=os.statvfs(Path({q['binding']['install_root']!r}).parent);free=s.f_bavail*s.f_frsize
assert free>={q['launch']['matrix_disk_budget_bytes']}
print(json.dumps(dict(hostname=socket.gethostname(),uid=os.getuid(),gpu=v,disk_free_bytes=free,new_paths_absent=True,parents_valid=True,session_absent=True)))
'''
first=run(scan,'identity_resources_targets_before')
prior=load(base/'p1_cuda_preparation_v1/server_readonly_h7vvrr_v1/server_readiness_receipt_v1.json')
assets={p:r['expected'] for p,r in prior['files'].items() if 'training_input' not in r['groups']}
for rec in q['files'].values():
 if not PurePosixPath(rec['path']).is_relative_to(PurePosixPath(q['binding']['install_root'])):assets[rec['path']]=[rec['bytes'],rec['sha256']]
for rec in [q['binding']['interpreter'],q['pairing']['initial_state'],q['pairing']['r_start']]:assets[rec['path']]=[rec['bytes'],rec['sha256']]
parent=load(project/'outputs/bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json')
geo=project/'outputs/cranial_bcsp_geov1_20261024'
fold=load(geo/'consolidated_binding_v1/fold_binding.json')['folds']['D']
rows={r['case_id']:r for r in map(json.loads,(geo/'real_data_qc_v1/manifest_8192.jsonl').read_bytes().splitlines())}
for cid in fold['train_case_ids']:
 rec=rows[cid];assets[str(PurePosixPath(parent['data_root'])/rec['point_path'])]=[(geo/'real_data_qc_v1'/rec['point_path']).stat().st_size,rec['sha256']]
assets[parent['order']['path']]=[parent['order']['bytes'],parent['order']['sha256']]
# Reverify all frozen R output/control evidence, including both large weight files.
ri=load(base/'d1_r_d_preparation_v3/post_training_freeze_audit_v3/remote_inventory_after.json')
inventory=json.loads(ri['stdout'])
rq=load(base/'d1_r_d_preparation_v3/EJTC_D1_R_D_training_execution_request_h7vvrr_v3.json')
for key,root in [('installed',rq['binding']['install_root']),('output',rq['binding']['output'])]:
 for row in inventory[key]:
  if len(row)==3:assets[str(PurePosixPath(root)/row[0])]=row[1:]
# Also verify frozen T evidence and all proposed existing label files.
ti=load(base/'d1_t_d_preparation_v1/post_training_freeze_audit_v1/remote_inventory_after.json')
tinventory=json.loads(ti['stdout'])
tq=load(base/'d1_t_d_preparation_v1/EJTC_D1_T_D_training_execution_request_h7vvrr_v1.json')
for key,root in [('installed',tq['binding']['install_root']),('output',tq['binding']['output'])]:
 for row in tinventory[key]:
  if len(row)==3:assets[str(PurePosixPath(root)/row[0])]=row[1:]
labels=load(d/'J_D_315_label_binding_v1.json')
reused=[r for r in labels['cases'] if r['proposed_mode'].startswith('PROPOSED_REUSE')]
fresh=[r for r in labels['cases'] if r['proposed_mode'].startswith('PROPOSED_NEW')]
assert len(reused)==40 and len(fresh)==275
for r in reused:assets[r['proposed_server_path']]=[r['bytes'],r['sha256']]
for r in fresh:assets[r['proposed_server_path']]=[r['bytes'],r['sha256']]
for rec in [*q['files'].values(),q['launch']['launcher']]:assets[rec['path']]=[rec['bytes'],rec['sha256']]
assets[q['launch']['request_path']]=[qp.stat().st_size,rid]
read='''def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=536870912
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,a.st_size,h.hexdigest()]
'''
paths=list(assets)
for j in range(0,len(paths),10):
 batch=paths[j:j+10]
 observed=run(read+'print(json.dumps([read(p) for p in '+repr(batch)+']))','asset_batch_'+str(j//10+1).zfill(2))
 assert observed==[[p,*assets[p]] for p in batch],'Frozen asset mismatch'
 print('Verified '+str(min(j+10,len(paths)))+'/'+str(len(paths)),flush=True)
last=run(scan,'identity_resources_targets_after')
receipt=dict(status='J_D_EXECUTION_READINESS_PASS',request_sha256=rid,timestamp=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),identity=i,gpu=last['gpu'],disk_free_bytes=last['disk_free_bytes'],verified_assets=len(assets),training_inputs=315,all_R_and_T_frozen_output_and_control_files_unchanged=True,proposed_reuse_labels_verified=40,installed_new_labels_verified=275,all_training_labels_verified=315,initial_state_bytes_and_R_start_evidence_verified=True,new_paths_absent=True,parents_valid=True,session_absent=True,remote_mutations=False,CUDA_imports=0,training_started=False,scope='Fresh prelaunch checks for separately authorized single J_D execution; no launch performed by this script',files={p:assets[p] for p in assets})
with (e/'J_D_execution_readiness_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k!='files'}))
