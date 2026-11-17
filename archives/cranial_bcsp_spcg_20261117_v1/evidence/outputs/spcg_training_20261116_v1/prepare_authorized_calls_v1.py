from pathlib import Path
import ast
S=Path(__file__).resolve().parent;W=S.parents[1];parent=W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3'
upload=(parent/'check_uploaded_v3.py').read_text(encoding='utf-8').replace('authorized_upload_readiness_v3','authorized_upload_readiness_v1').replace('delivery_receipt_v3.json','delivery_receipt_v1.json')
p=S/'check_uploaded_v1.py';assert not p.exists();ast.parse(upload);p.write_text(upload,encoding='utf-8')
old=(parent/'execute_authorized_cuda_v3.py').read_text(encoding='utf-8')
for a,b in {'authorized_execution_v3':'authorized_execution_v1','93ee5eb84f4e2b3b0de81e0f5b70c899c0cf2b2661f2946ffdead936c07568f6':'0f5a8aca25b1acd43c3bd258ae8ddf7ea3d06f81d020f2c38bde1ea7a944ef08','bcsp_spcg_output_policy_pending_20261116_v3.tar.gz':'bcsp_spcg_G0_C_training_pending_20261116_v1.tar.gz','7b394f97af4edbb68aefd202e90e4ac497d10d56efef4565d9fff2696228e400':'1e06b11d9c4d297f999dc64b0678174b16030f1c96dad57717cca351151c7462','SPCG_CUDA_execution_request_v3.json':'SPCG_G0_C_training_execution_request_v1.json','installation_mapping_v3.json':'installation_mapping_v1.json','INSTALLED_10_EXCLUSIVE_HASH_PASS':'INSTALLED_9_EXCLUSIVE_HASH_PASS'}.items():assert a in old,a;old=old.replace(a,b)
start=old.index("remote('01_reused_assets'");end=old.index("remote('02_targets_resources'",start)
replacement='''remote('01_reused_assets',"""rows=[v for k,v in q['implementation'].items() if k not in ['entry','bridge']]+q['dependencies']+[q[k] for k in ['native_helper','preflight_scope','static_config','order_plan']]
qc=q['QC'];rows += [qc['qualified_receipt'],qc['verification'],qc['fold_binding']]+list(qc['manifests'].values())
for r in rows:exact(r)
s=json.loads(Path(q['preflight_scope']['path']).read_bytes())
for r in s['bindings']['provider']+s['bindings']['environment_metadata']:exact(r)
sources=[dict(path=str(Path(q['model_root'])/r.get('relative_target',r.get('relative_path'))),bytes=r['bytes'],sha256=r['sha256']) for r in s['bindings']['candidate']+s['bindings']['isolated_model_project_sources']]
for r in sources:exact(r)
fold=json.loads(Path(qc['fold_binding']['path']).read_bytes())['folds']['C'];records=[json.loads(l) for l in Path(qc['manifests']['8192']['path']).read_text().splitlines()];selected=[r for r in records if r['case_id'] in fold['train_case_ids']];assert len(selected)==315
for r in selected:
 rel=Path(r['point_path']);assert not rel.is_absolute() and '..' not in rel.parts;v=Path(q['data_root'])/rel;assert not any(x.is_symlink() for x in (v,*v.parents));assert hashlib.sha256(v.read_bytes()).hexdigest()==r['sha256']
print(json.dumps(dict(status='REUSED_ASSETS_AND315_TRAIN_HASHES_PASS',sources=len(sources),reused=len(rows),train_inputs=len(selected))))
""")
'''
old=old[:start]+replacement+old[end:]
old=old.replace("q['entry']['path']","q['implementation']['entry']['path']")
needle="qh=hashlib.sha256(qraw).hexdigest();ab,rb=e.materialization(q,qh,'User authorized this exact request and11forward/3loss/3backward/0step in chat2026-11-16')"
replacement="""qh=hashlib.sha256(qraw).hexdigest();auth=dict(schema='bcsp-spcg-training-authorization-v1',request_sha256=qh,explicit_user_authorization=True,user_authorization_text='User authorized exactG0_C request3900step execution2026-11-16')
ab=(json.dumps(auth,indent=2)+'\\n').encode();rt=dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256=hashlib.sha256(ab).hexdigest());rb=(json.dumps(rt,indent=2)+'\\n').encode()
e.validate(q,qh,auth,hashlib.sha256(ab).hexdigest(),rt)"""
assert needle in old;old=old.replace(needle,replacement)
old=old.replace("control.mkdir(mode=0o700)","assert not control.parent.exists() and not any(x.is_symlink() for x in control.parents)\ncontrol.parent.mkdir(mode=0o700);control.mkdir(mode=0o700)")
p=S/'execute_authorized_G0_C_v1.py';assert not p.exists();ast.parse(old);p.write_text(old,encoding='utf-8');print('AUTHORIZED_CALLS_STATIC_READY')
