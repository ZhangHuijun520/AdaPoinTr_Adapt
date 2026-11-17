from pathlib import Path
import json,hashlib,ast,base64,zlib,subprocess
V=Path(__file__).resolve().parent;P=V.parent/'G2_C_implementation_v1'
d=json.loads((V/'delivery_receipt_v1.json').read_text(encoding='utf-8'));assert d['request']['sha256']=='d0e171d7ef70bef996cb1e4b1fb7006bd7173cc0aecf9b580d130b25fb2d998e'
assert hashlib.sha256(Path(d['request']['path']).read_bytes()).hexdigest()==d['request']['sha256']
s=(P/'execute_authorized_G2_C_v1.py').read_text(encoding='utf-8')
for a,b in [('f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322',d['request']['sha256']),('c5993b324c3fcd735bdcd64df1c4ccadfa36de97476a7326dc3788eac15cc3c3',d['archive']['sha256']),('bcsp_spcg_G2_C_training_pending_20261116_v1.tar.gz',Path(d['archive']['path']).name),('SPCG_G2_C_training_execution_request_v1.json','SPCG_G1_D_training_execution_request_v2.json'),('lwwgl9-0','yxwd3w-0'),('exactG2_C','exactG1_D_v2'),("['folds']['C']","['folds']['D']"),('int(8.5*1024**3)','int(6*1024**3)'),('execution2026-11-16','execution2026-11-17')]:
 assert a in s,a;s=s.replace(a,b)
tree=ast.parse(s);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets));lengths={}
for n in tree.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);code=pre+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];lengths[label]=len(subprocess.list2cmdline(a).encode());assert lengths[label]<=2048
upload=(P/'check_uploaded_v1.py').read_text(encoding='utf-8').replace('lwwgl9-0','yxwd3w-0')
status=(P/'status_G2_C_v1.py').read_text(encoding='utf-8').replace('SPCG_G2_foldC_seed0_train_20261116_v1','SPCG_G1_foldD_seed0_train_20261117_v2')
status=status.replace('import json,subprocess\np=',"import json,subprocess,socket,os\nassert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000\np=")
for name,code in [('execute_authorized_G1_D_v2.py',s),('check_uploaded_v2.py',upload),('status_G1_D_v2.py',status)]:
 ast.parse(code)
 with (V/name).open('x',encoding='utf-8') as f:f.write(code)
with (V/'authorized_call_static_review_v2.json').open('x',encoding='utf-8') as f:json.dump(dict(request_sha256=d['request']['sha256'],command_bytes=lengths,all_remote_compiled=True,startup_GiB=6,server_operations=0),f,indent=2)
print(json.dumps(lengths))
