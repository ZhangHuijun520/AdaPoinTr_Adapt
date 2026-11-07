import json,pathlib,subprocess
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1')
q=json.loads((R/'H1_C_D_development_execution_request_v1.json').read_bytes());O=pathlib.Path(q['output'])
r=dict(status='READONLY_PREDICTION_OBSERVATION',output_exists=O.is_dir(),session=q['launch_contract']['tmux_session'])
t=subprocess.run(['tmux','has-session','-t',r['session']],capture_output=True,timeout=10);r['tmux_present']=t.returncode==0
if O.is_dir():
 r['files']=sorted(p.name for p in O.iterdir());p=O/'worker.pid'
 if p.is_file():r['pid']=int(p.read_text());r['worker_live']=pathlib.Path('/proc/'+str(r['pid'])).exists()
 p=O/'predictions';r['prediction_files']=len(list(p.glob('*.npz'))) if p.is_dir() else 0
 p=O/'inference_manifest.jsonl'
 if p.is_file():
  lines=p.read_text().splitlines();r['manifest_rows']=len(lines)
  if lines:
   last=json.loads(lines[-1]);r['last']={k:last[k] for k in ['run','fold','case_id','forward_index']}
 for n in ['failure.json','completion.json','exit_code.txt']:
  p=O/n
  if p.is_file():
   value=p.read_text();r[n]=value[:6000] if n=='exit_code.txt' else json.loads(value)
 if not r['tmux_present'] or 'failure.json' in r:
  p=O/'launch.log'
  if p.is_file():
   with p.open('rb') as f:f.seek(max(0,p.stat().st_size-4500));r['log_tail']=f.read().decode('utf-8',errors='replace')
print(json.dumps(r),flush=True)
