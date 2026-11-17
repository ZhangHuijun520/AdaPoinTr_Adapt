from pathlib import Path
import ast,json,hashlib,base64,zlib,subprocess
V=Path(__file__).resolve().parent;P=V.parent/'G1_D_rebind_v2';d=json.loads((V/'delivery_receipt_v1.json').read_text(encoding='utf-8'))
assert d['request']['sha256']=='2885c64fca8717e16a57bdaac2ad5bbf6290b36539d893893d4ef161a0e807b9' and hashlib.sha256(Path(d['request']['path']).read_bytes()).hexdigest()==d['request']['sha256']
s=(P/'execute_authorized_G1_D_v2.py').read_text(encoding='utf-8')
for a,b in [('d0e171d7ef70bef996cb1e4b1fb7006bd7173cc0aecf9b580d130b25fb2d998e',d['request']['sha256']),('65a0b9e0a9295e88eb76768e7dadf58476a582c0bac6365a0823093cebeb0ebb',d['archive']['sha256']),('bcsp_spcg_G1_D_training_pending_20261117_v2.tar.gz',Path(d['archive']['path']).name),('SPCG_G1_D_training_execution_request_v2.json','SPCG_G2_D_training_execution_request_v1.json'),('exactG1_D_v2','exactG2_D_v1'),('INSTALLED_10','INSTALLED_11')]:
 assert a in s,a;s=s.replace(a,b)
tree=ast.parse(s);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets));lengths={}
for n in tree.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);code=pre+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];lengths[label]=len(subprocess.list2cmdline(a).encode());assert lengths[label]<=2048
upload=(P/'check_uploaded_v2.py').read_text(encoding='utf-8');status=(P/'status_G1_D_v2.py').read_text(encoding='utf-8').replace('SPCG_G1_foldD_seed0_train_20261117_v2','SPCG_G2_foldD_seed0_train_20261117_v1')
for name,code in [('execute_authorized_G2_D_v1.py',s),('check_uploaded_v1.py',upload),('status_G2_D_v1.py',status)]:
 ast.parse(code)
 with (V/name).open('x',encoding='utf-8') as f:f.write(code)
with (V/'authorized_call_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(request_sha256=d['request']['sha256'],command_bytes=lengths,all_remote_compiled=True,startup_GiB=6,server_operations=0),f,indent=2)
print(json.dumps(lengths))
