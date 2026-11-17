"""New user-authorized attempt after disk cleanup; original request and payload unchanged."""
from pathlib import Path
import ast,json,hashlib,base64,zlib,subprocess
V=Path(__file__).resolve().parent
q=V/'pending_transport_v1/payload/SPCG_G2_C_training_execution_request_v1.json'
assert hashlib.sha256(q.read_bytes()).hexdigest()=='f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322'
old=json.loads((V/'authorized_execution_v1/execution_stop_receipt_v1.json').read_text(encoding='utf-8'));assert old['status']=='STOPPED_BEFORE_INSTALL_INSUFFICIENT_DISK' and not old['installation_phase_called'] and not old['tmux_attempted']
files=[('execute_authorized_G2_C_v1.py','execute_authorized_G2_C_attempt_v2.py','authorized_execution_v1','authorized_execution_v2'),('check_uploaded_v1.py','check_uploaded_attempt_v2.py','authorized_upload_readiness_v1','authorized_upload_readiness_v2'),('status_G2_C_v1.py','status_G2_C_attempt_v2.py','authorized_execution_v1','authorized_execution_v2')]
for source,target,a,b in files:
 s=(V/source).read_text(encoding='utf-8').replace(a,b);ast.parse(s)
 if target.startswith('execute'):
  tree=ast.parse(s);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets))
  for n in tree.body:
   if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
    label=ast.literal_eval(n.value.args[0]);code=pre+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(args).encode())<=2048
 with (V/target).open('x',encoding='utf-8') as f:f.write(s)
print('ATTEMPT_V2_STATIC_PASS_ORIGINAL_REQUEST_UNCHANGED')
