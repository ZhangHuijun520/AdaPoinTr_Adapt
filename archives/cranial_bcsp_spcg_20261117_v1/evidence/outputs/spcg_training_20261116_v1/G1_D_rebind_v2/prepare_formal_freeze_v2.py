from pathlib import Path
import ast,base64,zlib,subprocess
V=Path(__file__).resolve().parent;S=V.parent
s=(S/'G1_C_implementation_v1/post_training_freeze_G1_C_v1.py').read_text(encoding='utf-8')
for a,b in [('post_training_freeze_v1','post_training_freeze_v2'),('lwwgl9-0','yxwd3w-0'),('bcsp_spcg_G1C_training_20261116_v1','bcsp_spcg_G1D_training_20261117_v2'),('SPCG_G1_C_training_execution_request_v1.json','SPCG_G1_D_training_execution_request_v2.json'),('2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4','d0e171d7ef70bef996cb1e4b1fb7006bd7173cc0aecf9b580d130b25fb2d998e'),('SPCG_G0_foldC_seed0_train_20261116_v3','SPCG_G0_foldD_seed0_train_20261116_v1'),('G0_C_freeze','G0_D_freeze'),('G0_C_POST_TRAINING','G0_D_POST_TRAINING'),('G1_C_POST_TRAINING','G1_D_POST_TRAINING'),("model['fold']=='C'","model['fold']=='D'"),("checks['G1C_identity']","checks['G1D_identity']"),("fold='C',arm='G1'","fold='D',arm='G1'"),('UTC_order_hotfix_v3/post_training_freeze_v3','G0_D_implementation_v1/post_training_freeze_v1'),("parent_dir/'formal_freeze_result_v3.json'","parent_dir/'formal_freeze_result_v1.json'"),('UTC_order_hotfix_v3/pending_transport_v3/payload/SPCG_G0_C_training_execution_request_v3.json','G0_D_implementation_v1/pending_transport_v1/payload/SPCG_G0_D_training_execution_request_v1.json'),("formal_freeze_result_v1.json').write_text","formal_freeze_result_v2.json').write_text")]:s=s.replace(a,b)
s=s.replace("['data_root','order_plan','static_config','identity','environment']","['data_root','order_plan','static_config','science','counts','resources']")
extra='''assets=remote('05_assets_and_parent_proof',"""items={k:record(Path(q[k]['path'])) for k in ['probe_asset','head_initialization','mother_source','G0_D_freeze']}
print(json.dumps(items))
""")
for k,r in assets.items():checks['asset_'+k]=r==dict(bytes=q[k]['bytes'],sha256=q[k]['sha256'])
expected_identity=dict(pq['identity'],hostname='shu-common-25721452-notebook-yxwd3w-0',gpu_uuid='GPU-4b19574a-832d-b4fe-e655-a57462954d6a')
checks['only_accepted_identity_changes']=q['identity']==expected_identity
checks['only_accepted_env_change']=q['environment']==dict(pq['environment'],CUDA_VISIBLE_DEVICES=expected_identity['gpu_uuid'])
checks['migration_disclosed']=q['resource_migration']['accepted'] is True and q['resource_migration']['G0_D_same_device'] is False and q['resource_migration']['G1_D_G2_D_same_device_required'] is True
checks['startup6_runtime4GiB_output1GiB']=q['startup_free_disk_bytes']==6*1024**3 and q['resources']['minimum_free_disk_bytes']==4*1024**3 and q['resources']['output_bytes']==1024**3
checks['launcher_new_gpu_binding']=expected_identity['gpu_uuid'] in co['launch_once_v1.sh']['text']
'''
s=s.replace('result=dict(status=',extra+'result=dict(status=',1)
s=s.replace("limitations=['Checkpoint", "pairing=dict(G0_D_same_device=False,G0_D_gpu_uuid=pq['identity']['gpu_uuid'],G1_D_gpu_uuid=q['identity']['gpu_uuid'],accepted_cross_device=True,G1_D_G2_D_same_device_required=True),limitations=['G0_D/G1_D comparison is cross-device; common contract agreement is not a strict same-device efficacy control.','Checkpoint")
ast.parse(s);tree=ast.parse(s);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PREFIX' for t in n.targets));lengths={}
for n in tree.body:
 if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);prefix=pre.split('def record(p):')[0] if label=='03_all3900_order_numeric' else pre;code=prefix+ast.literal_eval(n.value.args[1]);compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];lengths[label]=len(subprocess.list2cmdline(args).encode());assert lengths[label]<=2048
with (V/'post_training_freeze_G1_D_v2.py').open('x',encoding='utf-8') as f:f.write(s)
print(lengths)
