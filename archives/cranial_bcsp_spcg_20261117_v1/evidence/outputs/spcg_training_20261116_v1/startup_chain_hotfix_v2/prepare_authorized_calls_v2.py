from pathlib import Path
import ast
V=Path(__file__).resolve().parent;S=V.parent
original=(S/'execute_authorized_G0_C_v1.py').read_text(encoding='utf-8');tree=ast.parse(original);start=ast.parse((S/'start_existing_installation_attempt_v2.py').read_text(encoding='utf-8'))
def calls(t):return [(ast.literal_eval(n.value.args[0]),ast.literal_eval(n.value.args[1])) for n in t.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote']
correct=dict(calls(start))['04_materialize_launch_once'];parts=calls(tree);prefix=original[:original.index("remote('01_reused_assets'")].replace('authorized_execution_v1','authorized_execution_v2')
allsource=prefix+''.join('remote('+repr(label)+','+repr(correct if label=='04_materialize_launch_once' else body)+')\n' for label,body in parts)
for a,b in {'0f5a8aca25b1acd43c3bd258ae8ddf7ea3d06f81d020f2c38bde1ea7a944ef08':'6a1ff266ff9eae8db51b5809b7db3aa87b72900625d267a4ee3b0a5a9a489f42','bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz':'bcsp_spcg_G0_C_startup_hotfix_pending_20261116_v2.tar.gz','1e06b11d9c4d297f999dc64b0678174b16030f1c96dad57717cca351151c7462':'6179475556febed2323fe99d3269a6c625d49bf54336c1b55542a1cc1d4bf1c2','SPCG_G0_C_training_execution_request_v1.json':'SPCG_G0_C_training_execution_request_v2.json','installation_mapping_v1.json':'installation_mapping_v2.json','INSTALLED_9_EXCLUSIVE_HASH_PASS':'INSTALLED_10_EXCLUSIVE_HASH_PASS'}.items():assert a in allsource,a;allsource=allsource.replace(a,b)
newtree=ast.parse(allsource);pre=next(ast.literal_eval(n.value) for n in newtree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets))
for label,body in calls(newtree):compile(pre+body,label,'exec')
p=V/'execute_authorized_G0_C_v2.py';assert not p.exists();p.write_text(allsource,encoding='utf-8')
upload=(S/'check_uploaded_after_supplement_v2.py').read_text(encoding='utf-8').replace('authorized_upload_readiness_after_supplement_v2','authorized_upload_readiness_v2').replace('delivery_receipt_v1.json','delivery_receipt_v2.json');p=V/'check_uploaded_v2.py';assert not p.exists();ast.parse(upload);p.write_text(upload,encoding='utf-8')
status=(S/'status_G0_C_v1.py').read_text(encoding='utf-8').replace('authorized_start_attempt_v2','authorized_execution_v2').replace('SPCG_G0_foldC_seed0_train_20261116_v1','SPCG_G0_foldC_seed0_train_20261116_v2');p=V/'status_G0_C_v2.py';assert not p.exists();ast.parse(status);p.write_text(status,encoding='utf-8');print('ALL_RENDERED_REMOTE_SCRIPTS_COMPILE')
