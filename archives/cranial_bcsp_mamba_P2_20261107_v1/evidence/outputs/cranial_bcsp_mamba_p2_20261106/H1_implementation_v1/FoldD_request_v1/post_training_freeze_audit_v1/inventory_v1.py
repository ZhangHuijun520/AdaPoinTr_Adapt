import hashlib,json,os,pathlib,socket,stat,subprocess
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldD_20261106_v1')
Q='305ce3380ae7b951c7180907f63842abc51eae5d9dec817e2a5ad89718fdd390'
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
q=json.loads((R/'M_H1_foldD_seed0_training_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def meta(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1,str(p)
 return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,mode=stat.S_IMODE(s.st_mode),uid=s.st_uid,gid=s.st_gid)
expected=set('ckpt-last.pth completion.json exit_code.txt exposure.json initialization.json launch.log metrics.jsonl model_construction.json optimizer_actual_defaults.json optimizer_parameter_groups.json order_plan.json payload_manifest.json resources.jsonl run_identity.json worker.pid'.split())
assert {p.name for p in O.iterdir()}==expected|{'tmp'}
assert not any(p.is_symlink() for p in (O,*O.parents)) and (O/'tmp').is_dir()
assert list((O/'tmp').iterdir())==[],'unexpected temporary artifacts'
assert (O/'exit_code.txt').read_text().strip()=='0'
assert not pathlib.Path('/proc/'+(O/'worker.pid').read_text().strip()).exists()
tm=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=10);assert tm.returncode==1
records=[]
for name in sorted(expected):
 p=O/name;a=meta(p);h=sha(p);assert a==meta(p),name
 records.append(dict(name=name,sha256=h,**a))
complete=json.loads((O/'completion.json').read_bytes());ck=next(x for x in records if x['name']=='ckpt-last.pth')
assert ck['sha256']==complete['checkpoint_sha256']=='6a76aa7dc156c0e2eeef29d4e03b253f624373ced8a48abebe1af4c99d7e789d'
manifest=json.loads((O/'payload_manifest.json').read_bytes())['files']
actual={x['name']:x for x in records};wanted=expected-{'launch.log','worker.pid','exit_code.txt','payload_manifest.json'}
assert len(manifest)==len(wanted) and {x['name'] for x in manifest}==wanted
assert all(all(x[k]==actual[x['name']][k] for k in ('bytes','sha256')) for x in manifest)
print(json.dumps(dict(status='INVENTORY_CHECKPOINT_MANIFEST_PASS',files=records,exit_code=0,worker_live=False,tmux_present=False,tmp_empty=True,checkpoint=ck,server_writes=0,checkpoint_loaded=False)),flush=True)
