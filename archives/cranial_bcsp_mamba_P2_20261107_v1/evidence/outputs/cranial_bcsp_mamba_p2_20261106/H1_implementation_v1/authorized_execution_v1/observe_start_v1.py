import json,os,pathlib,subprocess
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_h1_foldC_20261106_v1')
q=json.loads((R/'M_H1_foldC_seed0_training_execution_request_v1.json').read_bytes());out=pathlib.Path(q['output'])
result=dict(status='READONLY_START_OBSERVATION',output_exists=out.is_dir(),session=q['launch_contract']['tmux_session'])
r=subprocess.run(['tmux','has-session','-t',result['session']],capture_output=True,timeout=10);result['tmux_present']=r.returncode==0
result['files']=sorted(p.name for p in out.iterdir()) if out.is_dir() else []
for n in ['startup_failure.json','failure.json','completion.json']:
 p=out/n
 if p.is_file():result[n]=json.loads(p.read_bytes())
p=out/'worker.pid'
if p.is_file():
 pid=int(p.read_text());result['pid']=pid;result['pid_exists']=pathlib.Path('/proc/'+str(pid)).exists()
p=out/'exit_code.txt'
if p.is_file():result['exit_code']=p.read_text().strip()
p=out/'metrics.jsonl'
if p.is_file() and p.stat().st_size:
 with p.open('rb') as f:f.seek(max(0,p.stat().st_size-16384));lines=f.read().splitlines()
 row=json.loads(lines[-1]);result['last_metric']={k:row[k] for k in ['step','epoch','loss','H1_enabled','H1_raw','H1_weighted'] if k in row}
p=out/'launch.log'
if p.is_file() and (not result.get('tmux_present') or 'startup_failure.json' in result):
 with p.open('rb') as f:f.seek(max(0,p.stat().st_size-3500));result['log_tail']=f.read().decode('utf-8',errors='replace')
print(json.dumps(result),flush=True)
