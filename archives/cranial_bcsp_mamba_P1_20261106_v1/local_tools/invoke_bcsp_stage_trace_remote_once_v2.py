"""Local-only adaptation of the final hpc5000 terminal line. No client-file edits."""
import argparse,base64,hashlib,json,subprocess,sys
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('source');p.add_argument('capture');p.add_argument('--probe',action='store_true');p.add_argument('--timeout',type=int,default=60);a=p.parse_args()
 target=Path(a.capture);assert not target.exists()
 raw=Path(a.source).read_bytes();digest=hashlib.sha256(raw).hexdigest();encoded=base64.b64encode(raw).decode('ascii')
 if a.probe:
  remote="import base64,hashlib,json,socket;raw=base64.b64decode('"+encoded+"');assert hashlib.sha256(raw).hexdigest()=='"+digest+"';print(json.dumps(dict(status='TRANSPORT_BYTES_ONLY_PROBE_PASS',source_bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),hostname=socket.gethostname(),source_executed=False)))"
 else:remote="import base64;exec(base64.b64decode('"+encoded+"'))"
 command='/opt/conda/envs/adapointr-mamba/bin/python -I -B -c '+__import__('shlex').quote(remote)
 command_b64=base64.b64encode(command.encode()).decode()
 # This script runs locally in WSL. Only client.main handles normal credentials.
 shim="""import base64,hashlib,importlib.util,json,re,sys
from pathlib import Path
sys.path.insert(0,'/home/zhj/.local/share/remote-agent-toolkit/site-packages')
client=Path('/home/zhj/.local/share/remote-agent-toolkit/release/hpc5000.py')
spec=importlib.util.spec_from_file_location('hpc_stage_trace_call_v2',client)
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
original=m.build_remote_command
def final_line_adapter(command,command_id):
 outer,begin,end=original(command,command_id)
 prefix=\"printf '%s' \";suffix=' | base64 -d | bash'
 assert outer.startswith(prefix) and outer.endswith(suffix)
 token=outer[len(prefix):-len(suffix)]
 assert re.fullmatch('[A-Za-z0-9+/=]+',token)
 wrapped=prefix+'\\\\\\n'.join(token[i:i+900] for i in range(0,len(token),900))+suffix
 assert wrapped.replace('\\\\\\n','')==outer
 assert max(len(line.encode()) for line in wrapped.splitlines())<=940
 print(json.dumps(dict(local_transport='FINAL_OUTER_LINE_CONTINUATION_V2',unwrapped_bytes=len(outer.encode()),max_physical_line_bytes=max(len(line.encode()) for line in wrapped.splitlines()),client_file_sha256=hashlib.sha256(client.read_bytes()).hexdigest())),flush=True)
 return wrapped,begin,end
m.build_remote_command=final_line_adapter
command=base64.b64decode(COMMAND_B64).decode('utf-8')
raise SystemExit(m.main(['exec','--timeout',TIMEOUT,'--',command]))
""".replace('COMMAND_B64',repr(command_b64)).replace('TIMEOUT',repr(str(a.timeout)))
 # Compile locally before any WSL call; original source and remote code stay byte-bound.
 compile(shim,'<local_wsl_call_adapter_v2>','exec')
 try:
  r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','python3','-I','-B','-'],input=shim.encode(),capture_output=True,timeout=a.timeout+25)
  result=dict(returncode=r.returncode,stdout_base64=base64.b64encode(r.stdout).decode(),stderr_base64=base64.b64encode(r.stderr).decode(),source_sha256=digest,source_bytes=len(raw),probe_only=a.probe,installed_client_modified=False)
 except subprocess.TimeoutExpired as e:
  r=None;result=dict(status='TRANSPORT_TIMEOUT_INDETERMINATE_NO_RETRY',stdout_base64=base64.b64encode(e.stdout or b'').decode(),stderr_base64=base64.b64encode(e.stderr or b'').decode(),source_sha256=digest,probe_only=a.probe)
 with target.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
 print(json.dumps(result) if r is None else r.stdout.decode('utf-8',errors='replace'))
 if r is not None and r.returncode:print(r.stderr.decode('utf-8',errors='replace'),file=sys.stderr)
 return 125 if r is None else r.returncode

if __name__=='__main__':raise SystemExit(main())
