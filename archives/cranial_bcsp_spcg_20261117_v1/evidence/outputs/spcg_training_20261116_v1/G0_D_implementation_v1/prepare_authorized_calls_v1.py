"""Bind existing short-call installer to authorized G0_D; no changes to frozen files."""
from pathlib import Path
import json,hashlib,ast,base64,zlib,subprocess
V=Path(__file__).resolve().parent;P=V.parent/'G2_C_implementation_v1'
d=json.loads((V/'delivery_receipt_v1.json').read_text(encoding='utf-8'))
assert d['request']['sha256']=='a877093becfd3e9763da36565c9401275e2f5ddd4f6d4f223fb4964ddf1d7fea'
assert hashlib.sha256(Path(d['request']['path']).read_bytes()).hexdigest()==d['request']['sha256']
s=(P/'execute_authorized_G2_C_v1.py').read_text(encoding='utf-8')
for a,b in [('f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322',d['request']['sha256']),('c5993b324c3fcd735bdcd64df1c4ccadfa36de97476a7326dc3788eac15cc3c3',d['archive']['sha256']),('G2_C','G0_D'),('INSTALLED_10','INSTALLED_11')]:s=s.replace(a,b)
s=s.replace(",'probe_asset','head_initialization','mother_source'",'').replace("['folds']['C']","['folds']['D']")
tree=ast.parse(s);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets));lengths={}
for n in tree.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);code=pre+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];lengths[label]=len(subprocess.list2cmdline(a).encode());assert lengths[label]<=2048
for name,code in [('execute_authorized_G0_D_v1.py',s),('check_uploaded_v1.py',(P/'check_uploaded_v1.py').read_text(encoding='utf-8')),('status_G0_D_v1.py',(P/'status_G2_C_v1.py').read_text(encoding='utf-8').replace('SPCG_G2_foldC_seed0_train_20261116_v1','SPCG_G0_foldD_seed0_train_20261116_v1'))]:
 ast.parse(code)
 with (V/name).open('x',encoding='utf-8') as f:f.write(code)
with (V/'authorized_call_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(request_sha256=d['request']['sha256'],command_bytes=lengths,all_remote_compiled=True,server_operations=0),f,indent=2)
print(json.dumps(lengths))
