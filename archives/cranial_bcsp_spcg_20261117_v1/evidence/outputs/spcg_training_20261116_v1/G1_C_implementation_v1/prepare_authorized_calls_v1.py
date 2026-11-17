from pathlib import Path
import ast
V=Path(__file__).resolve().parent;S=V.parent;prior=S/'UTC_order_hotfix_v3'
text=(prior/'execute_authorized_G0_C_v3.py').read_text(encoding='utf-8')
for a,b in {'authorized_execution_v3':'authorized_execution_v1','871c5216815d5e479446108da979e8c77ce6ea5aec2578ac0573652e51a75d63':'2d8ef3fff5db90653d0408ac6db72911e2c84b75aa61c9f03c8033aaf56ac0e4','bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz':'bcsp_spcg_G1_C_training_pending_20261116_v1.tar.gz','0c1891dd121c5763411e9d3278e3e6b92f44409e4ce43bd3f36ad272493099bb':'0e7dfa82fc484e7cb355b4513833136483989523974babcaa810099da804d43b','SPCG_G0_C_training_execution_request_v3.json':'SPCG_G1_C_training_execution_request_v1.json','installation_mapping_v3.json':'installation_mapping_v1.json','INSTALLED_8_EXCLUSIVE_HASH_PASS':'INSTALLED_9_EXCLUSIVE_HASH_PASS'}.items():assert a in text,a;text=text.replace(a,b)
tree=ast.parse(text);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets));parts=[]
for n in tree.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':
  label=ast.literal_eval(n.value.args[0]);body=ast.literal_eval(n.value.args[1])
  if label=='01_reused_assets':
   body=body.replace("'static_config','order_plan']","'static_config','order_plan','probe_asset','head_initialization','mother_source']")
  if label=='04_materialize_launch_once':body=body.replace('exactG0_C','exactG1_C')
  compile(pre+body,label,'exec');parts.append('remote('+repr(label)+','+repr(body)+')\n')
prefix=text[:text.index("remote('01_reused_assets'")];p=V/'execute_authorized_G1_C_v1.py';assert not p.exists();p.write_text(prefix+''.join(parts),encoding='utf-8')
upload=(prior/'check_uploaded_v3.py').read_text(encoding='utf-8').replace('authorized_upload_readiness_v3','authorized_upload_readiness_v1').replace('delivery_receipt_v3.json','delivery_receipt_v1.json');p=V/'check_uploaded_v1.py';assert not p.exists();ast.parse(upload);p.write_text(upload,encoding='utf-8')
status=(prior/'status_G0_C_v3.py').read_text(encoding='utf-8').replace('authorized_execution_v3','authorized_execution_v1').replace('SPCG_G0_foldC_seed0_train_20261116_v3','SPCG_G1_foldC_seed0_train_20261116_v1').replace("glob('status_*_result.json')","glob('status_*_stdout.bin')");p=V/'status_G1_C_v1.py';assert not p.exists();ast.parse(status);p.write_text(status,encoding='utf-8');print('G1_CALLS_STATIC_COMPILE_PASS')
