import pathlib,json,hashlib,os,socket
P=pathlib.Path
p=P('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1/RIVE_fourmodel_native_prediction_execution_request_v1.json');b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q=json.loads(b);I=q['identity'];assert socket.gethostname()==I['hostname'] and os.getuid()==I['uid']==1000
import subprocess
out=P(q['output']);session=q['launch_contract']['tmux_session'];r=dict(status='READONLY_PREDICTION_OBSERVATION',session_live=subprocess.run(['tmux','has-session','-t','='+session],capture_output=True).returncode==0,output_exists=out.is_dir())
if out.is_dir():
 r['files']=sorted(x.name for x in out.iterdir())
 for n in ('worker.pid','exit_code.txt','failure.json'):
  p=out/n
  if p.is_file():r[n]=p.read_text()[:8000]
 for n in ('inference_manifest.jsonl','forward_attempts.jsonl'):
  p=out/n
  if p.is_file():
   lines=p.read_text().splitlines();r[n+'_records']=len(lines)
   if lines:
    try:r[n+'_last']=json.loads(lines[-1])
    except json.JSONDecodeError:r[n+'_last_incomplete']=True
 for n in ('inference_complete.json','completion.json'):
  p=out/n
  if p.is_file():
   v=json.loads(p.read_bytes());r[n]=dict(status=v.get('status'),forwards=v.get('forwards'))
   if 'archive' in v:r[n]['archive']={k:x for k,x in v['archive'].items() if k!='members'}
 p=out/'launch.log'
 if p.is_file():
  with p.open('rb') as f:f.seek(max(0,p.stat().st_size-5000));r['log_tail']=f.read().decode('utf-8',errors='replace')
 if 'worker.pid' in r:r['worker_visible']=P('/proc/'+r['worker.pid'].strip()).exists()
print(json.dumps(r))
