import ast,hashlib,json,os,socket,subprocess,sys
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-o9mz8z-0' and os.getuid()==1000
p=Path('/opt/conda/envs/adapointr-mamba/lib/python3.10/subprocess.py')
assert p.is_file() and not p.is_symlink() and p.stat().st_size<131072
text=p.read_text(encoding='utf-8');tree=ast.parse(text);functions={}
for n in ast.walk(tree):
 if isinstance(n,ast.FunctionDef) and n.name in {'run','_check_timeout'}:
  functions[n.name]={'first_line':n.lineno,'source':ast.get_source_segment(text,n)}
root=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v1')
entry=root/'bcsp_artificial_gpu_preflight_v1.py';source=entry.read_text(encoding='utf-8')
relevant={}
for n in ast.walk(ast.parse(source)):
 if isinstance(n,ast.FunctionDef) and n.name in {'smi','watch','sample','main'}:
  relevant[n.name]={'first_line':n.lineno,'source':ast.get_source_segment(source,n)}
paths=['/proc/loadavg','/proc/uptime','/proc/meminfo','/proc/driver/nvidia/version','/sys/fs/cgroup/memory.events','/sys/fs/cgroup/cpu.stat','/sys/fs/cgroup/memory.current','/sys/fs/cgroup/memory.max']
metrics={}
for name in paths:
 f=Path(name)
 if f.is_file():
  with f.open('r',encoding='ascii') as stream:value=stream.read(16385)
  assert len(value)<=16384
  metrics[name]=value
 else:metrics[name]=None
cp=subprocess.run(['ps','-eo','pid,ppid,stat,comm'],capture_output=True,text=True,timeout=5,check=True)
processes=[line for line in cp.stdout.splitlines() if any(x in line.split()[-1] for x in ('nvidia-smi','python','timeout','tmux'))]
print(json.dumps({'status':'READONLY_SOURCE_EVIDENCE','python':sys.version,'subprocess_path':str(p),'subprocess_sha256':hashlib.sha256(text.encode()).hexdigest(),'stdlib_functions':functions,'entry_functions':relevant,'current_metrics_not_incident_telemetry':metrics,'matching_process_names_only':processes,'new_nvidia_smi_calls':0,'server_writes':0}))
