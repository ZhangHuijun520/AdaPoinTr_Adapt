import base64,hashlib,json,os,pathlib,socket,stat,subprocess,zlib
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1')
Q='90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147'
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
q=json.loads((R/'H1_C_D_development_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def meta(p):
 s=p.lstat();assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and stat.S_IMODE(s.st_mode)==0o600 and s.st_uid==1000,str(p)
 return dict(bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,mode=stat.S_IMODE(s.st_mode),uid=s.st_uid,gid=s.st_gid)
names=set('completion.json exit_code.txt forward_attempts.jsonl geometry_summary.jsonl inference_complete.json inference_manifest.jsonl launch.log resources.jsonl worker.pid development_predictions_v1.tar.gz development_predictions_v1.tar.gz.bytes development_predictions_v1.tar.gz.sha256 development_predictions_v1.tar.gz.contents.sha256'.split())
assert {p.name for p in O.iterdir()}==names|{'predictions','tmp'} and list((O/'tmp').iterdir())==[]
assert not any(p.is_symlink() for p in (O,*O.parents,O/'tmp',O/'predictions'))
assert (O/'exit_code.txt').read_text().strip()=='0' and not pathlib.Path('/proc/'+(O/'worker.pid').read_text().strip()).exists()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=10).returncode==1
idx=json.loads(pathlib.Path(q['input_index']['path']).read_bytes())
wanted={r['run']+'__'+r['case_id']+'.npz' for r in idx['inputs']};assert len(wanted)==210 and {p.name for p in (O/'predictions').iterdir()}==wanted
records=[]
for p in sorted(list(O/n for n in names)+list((O/'predictions').iterdir())):
 a=meta(p);h=sha(p);assert a==meta(p)
 records.append(dict(name=p.relative_to(O).as_posix(),sha256=h,**a))
result=dict(status='EXACT_OUTPUT_HASH_INVENTORY_PASS',files=records,exit_code=0,worker_live=False,tmux_present=False,server_writes=0)
raw=json.dumps(result,separators=(',',':')).encode()
print(json.dumps(dict(status=result['status'],files=len(records),report_sha256=hashlib.sha256(raw).hexdigest(),report_zlib_base64=base64.b64encode(zlib.compress(raw,9)).decode())),flush=True)
