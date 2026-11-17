"""Bind proven short-call helpers to the explicitly authorized G2 request."""
from pathlib import Path
import ast,json,base64,zlib,subprocess
V=Path(__file__).resolve().parent;P=V.parent/'G1_C_implementation_v1'
d=json.loads((V/'delivery_receipt_v1.json').read_text(encoding='utf-8'))
assert d['request']['sha256']=='f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322'
body=(P/'execute_authorized_G1_C_v1.py').read_text(encoding='utf-8')
for a,b in [('2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4',d['request']['sha256']),('0e7dfa82fc484e7cb355b4513833136483989523974babcaa810099da804d43b',d['archive']['sha256']),('G1_C','G2_C'),('exactG1_C','exactG2_C'),('INSTALLED_9','INSTALLED_10')]:body=body.replace(a,b)
pre=next(ast.literal_eval(n.value) for n in ast.parse(body).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets))
lengths={}
for n in ast.parse(body).body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);code=pre+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];lengths[label]=len(subprocess.list2cmdline(args).encode());assert lengths[label]<=2048,(label,lengths[label])
for name,code in [('execute_authorized_G2_C_v1.py',body),('check_uploaded_v1.py',(P/'check_uploaded_v1.py').read_text(encoding='utf-8')),('status_G2_C_v1.py',(P/'status_G1_C_v1.py').read_text(encoding='utf-8').replace('SPCG_G1_foldC_seed0_train_20261116_v1','SPCG_G2_foldC_seed0_train_20261116_v1'))]:
 ast.parse(code)
 with (V/name).open('x',encoding='utf-8',newline='\n') as f:f.write(code)
with (V/'authorized_call_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(request_sha256=d['request']['sha256'],all_remote_scripts_compiled=True,command_bytes=lengths,server_operations=0),f,indent=2)
print(json.dumps(lengths))
