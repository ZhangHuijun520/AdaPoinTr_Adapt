from pathlib import Path
import ast,base64,zlib,subprocess
V=Path(__file__).resolve().parent;S=V.parent
s=(S/'G2_C_implementation_v1/post_training_freeze_G2_C_v1.py').read_text(encoding='utf-8')
for a,b in [('lwwgl9-0','yxwd3w-0'),('bcsp_spcg_G2C_training_20261116_v1','bcsp_spcg_G2D_training_20261117_v1'),('SPCG_G2_C_training_execution_request_v1.json','SPCG_G2_D_training_execution_request_v1.json'),('f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322','2885c64fca8717e16a57bdaac2ad5bbf6290b36539d893893d4ef161a0e807b9'),('SPCG_G1_foldC_seed0_train_20261116_v1','SPCG_G1_foldD_seed0_train_20261117_v2'),('G0_C_freeze','G0_D_freeze'),('G1_C_freeze','G1_D_freeze'),('G1_C_POST_TRAINING','G1_D_POST_TRAINING'),('G2_C_POST_TRAINING','G2_D_POST_TRAINING'),("model['fold']=='C'","model['fold']=='D'"),("checks['G2C_identity']","checks['G2D_identity']"),("fold='C',arm='G2'","fold='D',arm='G2'"),('G1_C_implementation_v1/post_training_freeze_v1','G1_D_rebind_v2/post_training_freeze_v2'),("parent_dir/'formal_freeze_result_v1.json'","parent_dir/'formal_freeze_result_v2.json'"),('G1_C_implementation_v1/pending_transport_v1/payload/SPCG_G1_C_training_execution_request_v1.json','G1_D_rebind_v2/pending_transport_v1/payload/SPCG_G1_D_training_execution_request_v2.json')]:s=s.replace(a,b)
extra='''launch_g1=json.loads((S/'G1_D_rebind_v2/authorized_execution_v1/02_targets_resources_stdout.bin').read_bytes())
launch_g2=json.loads((V/'authorized_execution_v1/02_targets_resources_stdout.bin').read_bytes())
checks['same_observed_GPU_at_launch']=launch_g1['GPU'][0].strip()==launch_g2['GPU'][0].strip()==q['identity']['gpu_uuid']==parent['pairing']['G1_D_gpu_uuid']
checks['same_observed_driver_at_launch']=launch_g1['GPU'][1].strip()==launch_g2['GPU'][1].strip()==q['identity']['driver_version']
checks['G1_proof_request_binding']=q['resource_migration']['paired_G1_D_request_sha256']==parent['request_sha256']
checks['same_startup6GiB_runtime4GiB']=q['startup_free_disk_bytes']==pq['startup_free_disk_bytes']==6*1024**3 and q['resources']['minimum_free_disk_bytes']==4*1024**3
checks['G0_cross_device_disclosed']=q['resource_migration']['G0_D_same_device'] is False and q['resource_migration']['accepted'] is True
'''
s=s.replace('result=dict(status=',extra+'result=dict(status=',1)
s=s.replace("limitations=['Checkpoint", "pairing=dict(G1_D_same_device=True,G1_D_request_sha256=parent['request_sha256'],gpu_uuid=q['identity']['gpu_uuid'],G0_D_same_device=False),limitations=['G0_D remains cross-device; G1_D/G2_D share the observed device but finite gradient nondeterminism remains.','Checkpoint")
ast.parse(s);tree=ast.parse(s);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PREFIX' for t in n.targets));lengths={}
for n in tree.body:
 if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);prefix=pre.split('def record(p):')[0] if label=='03_all3900_order_numeric' else pre;code=prefix+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];lengths[label]=len(subprocess.list2cmdline(a).encode());assert lengths[label]<=2048
with (V/'post_training_freeze_G2_D_v1.py').open('x',encoding='utf-8') as f:f.write(s)
print(lengths)
