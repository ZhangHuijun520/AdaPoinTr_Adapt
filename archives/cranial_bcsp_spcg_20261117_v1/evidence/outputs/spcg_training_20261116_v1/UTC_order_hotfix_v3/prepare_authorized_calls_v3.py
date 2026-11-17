from pathlib import Path
import ast
V=Path(__file__).resolve().parent;S=V.parent;old=S/'startup_chain_hotfix_v2'
text=(old/'execute_authorized_G0_C_v2.py').read_text(encoding='utf-8')
replacements={'authorized_execution_v2':'authorized_execution_v3','6a1ff266ff9eae8db51b5809b7db3aa87b72900625d267a4ee3b0a5a9a489f42':'871c5216815d5e479446108da979e8c77ce6ea5aec2578ac0573652e51a75d63','bcsp_spcg_G0_C_startup_hotfix_pending_20261116_v2.tar.gz':'bcsp_spcg_G0_C_UTC_order_pending_20261116_v3.tar.gz','6179475556febed2323fe99d3269a6c625d49bf54336c1b55542a1cc1d4bf1c2':'0c1891dd121c5763411e9d3278e3e6b92f44409e4ce43bd3f36ad272493099bb','SPCG_G0_C_training_execution_request_v2.json':'SPCG_G0_C_training_execution_request_v3.json','installation_mapping_v2.json':'installation_mapping_v3.json','INSTALLED_10_EXCLUSIVE_HASH_PASS':'INSTALLED_8_EXCLUSIVE_HASH_PASS'}
for a,b in replacements.items():assert a in text,a;text=text.replace(a,b)
tree=ast.parse(text);pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets))
for n in tree.body:
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote':compile(pre+ast.literal_eval(n.value.args[1]),ast.literal_eval(n.value.args[0]),'exec')
p=V/'execute_authorized_G0_C_v3.py';assert not p.exists();p.write_text(text,encoding='utf-8')
text=(old/'check_uploaded_v2.py').read_text(encoding='utf-8').replace('authorized_upload_readiness_v2','authorized_upload_readiness_v3').replace('delivery_receipt_v2.json','delivery_receipt_v3.json');p=V/'check_uploaded_v3.py';assert not p.exists();ast.parse(text);p.write_text(text,encoding='utf-8')
text=(old/'status_G0_C_v2.py').read_text(encoding='utf-8').replace('authorized_execution_v2','authorized_execution_v3').replace('SPCG_G0_foldC_seed0_train_20261116_v2','SPCG_G0_foldC_seed0_train_20261116_v3');p=V/'status_G0_C_v3.py';assert not p.exists();ast.parse(text);p.write_text(text,encoding='utf-8');print('ALL_REMOTE_SCRIPTS_STATIC_COMPILE_PASS')
