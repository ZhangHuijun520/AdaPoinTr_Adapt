"""Read-only bounded status observation of the single authorized B_C run."""
from pathlib import Path
import ast,json,subprocess,hashlib,shlex,base64,zlib
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Static_D_implementation_20261115_v1';O=B/'authorized_execution_v1'
q=json.loads((B/'pending_transport_v1/payload/SCQ_RF_Static_D_training_execution_request_v1.json').read_bytes())
code="""from pathlib import Path
import socket,os,json,subprocess
assert socket.gethostname()==HOST and os.getuid()==1000
p=Path(OUT);v=dict(tmux_live=subprocess.run(['tmux','has-session','-t',SESSION],capture_output=True).returncode==0)
v['exit_code']=(p/'exit_code.txt').read_text().strip() if (p/'exit_code.txt').is_file() else None
v['worker_PID']=(p/'worker.pid').read_text().strip() if (p/'worker.pid').is_file() else None
proc=Path('/proc/'+v['worker_PID']) if v['worker_PID'] else None
v['worker_live']=proc.exists() if proc else False
v['worker_matches_entry']=ENTRY.encode() in (proc/'cmdline').read_bytes() if v['worker_live'] else False
for name in ['completion.json','failure.json','startup_failure.json']:
 if (p/name).is_file():v[name]=json.loads((p/name).read_bytes())
for name,key in [('metrics.jsonl','last_metric'),('resources.jsonl','last_resource')]:
 f=p/name
 if f.is_file() and f.stat().st_size:
  with f.open('rb') as stream:
   stream.seek(max(0,f.stat().st_size-65536));lines=stream.read().splitlines()
  for line in reversed(lines):
   try:v[key]=json.loads(line);break
   except (ValueError,UnicodeDecodeError):pass
log=p/'launch.log'
if log.is_file():
 with log.open('rb') as f:f.seek(max(0,log.stat().st_size-2500));v['log_tail']=f.read().decode(errors='replace')
v['files']=[dict(name=f.name,bytes=f.stat().st_size) for f in p.iterdir() if f.is_file()]
print(json.dumps(v))
"""
values={'HOST':q['identity']['hostname'],'OUT':q['output'],'SESSION':q['launch_contract']['tmux_session'],'ENTRY':q['implementation']['entry']['path']}
class Bind(ast.NodeTransformer):
 def visit_Name(self,n):return ast.copy_location(ast.parse(repr(values[n.id]),mode='eval').body,n) if isinstance(n.ctx,ast.Load) and n.id in values else n
code=ast.unparse(ast.fix_missing_locations(Bind().visit(ast.parse(code))));ast.parse(code,feature_version=(3,8))
blob=base64.b64encode(zlib.compress(code.encode(),9)).decode();cmd=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import zlib,base64;exec(zlib.decompress(base64.b64decode('+repr(blob)+')))']);assert len(cmd.encode())<=2048
x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',cmd],capture_output=True,timeout=45);i=0
while any(O.glob('observation_'+str(i)+'*')):i+=1
for n,b in [('stdout',x.stdout),('stderr',x.stderr)]:
 with (O/('observation_'+str(i)+'_'+n+'.bin')).open('xb') as f:f.write(b)
assert x.returncode==0,x.stdout.decode(errors='replace')[-1500:]
j=json.loads(x.stdout)
with (O/('observation_'+str(i)+'.json')).open('x',encoding='utf-8') as f:json.dump(j,f,indent=2)
print(json.dumps(j))

