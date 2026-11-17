from pathlib import Path
import os,socket,json,hashlib
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_native_prediction_20261117_v1');b=(r/'SPCG_sixmodel_native_execution_request_v1.json').read_bytes();assert hashlib.sha256(b).hexdigest()=='c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc';q=json.loads(b);o=Path(q['output'])
def read(p):return json.loads(p.read_bytes())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<128*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns);return dict(bytes=s.st_size,sha256=h.hexdigest())
idx=read(Path(q['input_index']['path']));assert record(Path(q['input_index']['path']))=={k:q['input_index'][k] for k in ['bytes','sha256']}
import subprocess
assert sorted(p.name for p in o.iterdir() if p.is_dir())==['predictions','tmp'] and not list((o/'tmp').iterdir())
for p in [o,o/'predictions',o/'tmp']:assert not any(x.is_symlink() for x in (p,*p.parents))
files={p.name:record(p) for p in o.iterdir() if p.is_file()};files.update({'predictions/'+p.name:record(p) for p in (o/'predictions').iterdir()})
c=read(o/'completion.json');checks=dict(exit_zero=(o/'exit_code.txt').read_text()=='0\n',worker_absent=not Path('/proc/'+(o/'worker.pid').read_text().strip()).exists(),tmux_absent=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1,completion=c['status']=='PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT' and c['forwards']==630 and c['request_sha256']==hashlib.sha256(b).hexdigest())
expected={x['prediction_filename'] for x in idx['inputs']}|{'completion.json','inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','resources.jsonl','inference_complete.json','launch.log','worker.pid','exit_code.txt','development_predictions_v1.tar.gz','development_predictions_v1.tar.gz.sha256','development_predictions_v1.tar.gz.bytes','development_predictions_v1.tar.gz.contents.sha256'}
checks['exact_output_set']=set(files)==expected
print(json.dumps(dict(files=files,checks=checks)))
