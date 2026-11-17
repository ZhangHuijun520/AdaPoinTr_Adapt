from pathlib import Path
import json,subprocess,base64,zlib,hashlib
S=Path(__file__).resolve().parent;O=S/'rendering_fix_v2'
code="""from pathlib import Path
import socket,os,json,hashlib,tarfile,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
a=Path('/home/jovyan/bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz');assert hashlib.sha256(a.read_bytes()).hexdigest()=='1e06b11d9c4d297f999dc64b0678174b16030f1c96dad57717cca351151c7462'
t=tarfile.open(a);m=json.load(t.extractfile('installation_mapping_v1.json'));r=Path(m['remote_root']);rows=[]
for x in m['files']:
 p=Path(x['target']);assert not any(v.is_symlink() for v in (p,*p.parents));b=p.read_bytes();assert len(b)==x['bytes'] and hashlib.sha256(b).hexdigest()==x['sha256'];rows.append(dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
assert {p.name for p in r.iterdir()}=={Path(x['target']).name for x in m['files']}
q=json.load(t.extractfile('payload/SPCG_G0_C_training_execution_request_v1.json'));L=q['launch_contract'];out=Path(q['output']);assert not (r/'control').exists() and not out.exists()
session=subprocess.run(['tmux','has-session','-t',L['tmux_session']],capture_output=True,timeout=5);assert session.returncode==1
print(json.dumps(dict(status='EXISTING9_HASHES_PASS_CONTROL_OUTPUT_TMUX_ABSENT',files=rows,control_exists=False,output_exists=False,tmux_live=False,request_sha256=m['request_sha256'])))
"""
b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(args).encode())<=2048
r=subprocess.run(args,capture_output=True,timeout=30);(O/'readonly_stdout.bin').write_bytes(r.stdout);(O/'readonly_stderr.bin').write_bytes(r.stderr);assert r.returncode==0
d=json.loads(r.stdout);(O/'existing_installation_readback_v2.json').write_text(json.dumps(d,indent=2),encoding='utf-8');print(json.dumps(dict(status=d['status'],files=len(d['files']),control_exists=False,output_exists=False,tmux_live=False)))
