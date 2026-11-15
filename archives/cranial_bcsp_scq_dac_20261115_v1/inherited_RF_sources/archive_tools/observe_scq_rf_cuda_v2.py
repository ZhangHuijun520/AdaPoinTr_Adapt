"""Bounded read-only RF CUDA status observation, no model import or launch."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,zlib

R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_cuda_preparation_20261114_v2';O=B/'authorized_execution_v2'
qp=B/'pending_transport_v2/payload/SCQ_RF_artificial_cuda_execution_request_v2.json'
assert hashlib.sha256(qp.read_bytes()).hexdigest()=='09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'
q=json.loads(qp.read_bytes())
source='''from pathlib import Path
import socket,subprocess,json
assert socket.gethostname()==HOST
p=Path(OUT);v=dict(output_exists=p.is_dir())
for name in ['completion.json','failure.json','monitor_failure.json']:
 if (p/name).is_file():
  assert (p/name).stat().st_size<=2097152
  j=json.loads((p/name).read_bytes());v[name]={k:j[k] for k in ['status','error','counts','training_admission','real_data_reads','checkpoint_loads','initial_common_state_equal','initial_RF_Sref_equivalence'] if k in j}
  if 'native_SSM_calls' in j:v[name]['native_Mamba_calls']=sum(j['native_SSM_calls'].values())
  if 'phases' in j:v[name]['phases']=[dict(phase=r['phase'],batch=r['batch'],loss=r['loss'],actual_Q2_consumers=r.get('actual_Q2_consumers'),heads=r.get('head_gradients')) for r in j['phases']]
v['exit_code']=(p/'exit_code.txt').read_text().strip() if (p/'exit_code.txt').is_file() else None
v['worker_pid']=(p/'worker.pid').read_text().strip() if (p/'worker.pid').is_file() else None
v['worker_live']=Path('/proc/'+v['worker_pid']).exists() if v['worker_pid'] else False
v['tmux_live']=subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==0
v['files']=[dict(name=x.name,bytes=x.stat().st_size) for x in p.iterdir() if x.is_file()] if p.is_dir() else []
for file,key in [('launch.log','log_tail'),('events.jsonl','events_tail'),('resources.jsonl','resources_tail')]:
 if (p/file).is_file():
  with (p/file).open('rb') as f:f.seek(max(0,(p/file).stat().st_size-8000));raw=f.read(8000)
  lines=raw.decode(errors='replace').splitlines();v[key]=lines[-3:] if key!='log_tail' else raw.decode(errors='replace')[-2500:]
print(json.dumps(v))
'''
values=dict(HOST=q['identity']['hostname'],OUT=q['output'],SESSION=q['launch_contract']['tmux_session'])
class Bind(ast.NodeTransformer):
    def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
code=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(source))))
compile(code,'remote_observation','exec')
blob=base64.b64encode(zlib.compress(code.encode(),9)).decode()
command=shlex.join(['/usr/bin/python3','-I','-S','-B','-c',"import zlib,base64;exec(zlib.decompress(base64.b64decode("+repr(blob)+")))"])
assert len(command.encode())<=2048
index=len(list(O.glob('observation_*.json')))
result=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',command],capture_output=True,timeout=45)
for kind,data in [('stdout',result.stdout),('stderr',result.stderr)]:
    with (O/('observation_'+str(index)+'_'+kind+'.bin')).open('xb') as f:f.write(data)
assert result.returncode==0,(result.returncode,result.stdout.decode(errors='replace')[-1500:])
j=json.loads(result.stdout)
with (O/('observation_'+str(index)+'.json')).open('x',encoding='utf-8') as f:json.dump(j,f,indent=2)
print(json.dumps(j))
