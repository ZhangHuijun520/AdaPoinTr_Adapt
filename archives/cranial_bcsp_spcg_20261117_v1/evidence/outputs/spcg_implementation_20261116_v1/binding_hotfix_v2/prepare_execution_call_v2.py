from pathlib import Path
import ast
V=Path(__file__).resolve().parent;S=V.parent
old=(S/'execute_authorized_cuda_v1.py').read_text(encoding='utf-8')
replacements={"authorized_execution_v1":"authorized_execution_v2","00a69c5cc3d42e04f4caa3c21650dd58db5d8c1b446741a1b42caf6730213d0f":"a2b1961158b58199e212130654ddd274ce617c90e24448f22ba70a0062c2343e","bcsp_spcg_cuda_pending_20261116_v2.tar.gz":"bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz","ac9dbd1007db1ec5d3824684361ce55691bb36aaa41b8f484b5b9b4f37a6a5e4":"0a6adcb5b8ad0da94b64e6d54fe63d0d1c8609296011cfb7f2a1ee7ffa337154","SPCG_CUDA_execution_request_v1.json":"SPCG_CUDA_execution_request_v2.json","installation_mapping_v1.json":"installation_mapping_v2.json","list(q['implementation'].values())[:4]":"list(q['implementation'].values())","'mother_source']]":"'mother_source','probe_asset','head_initialization']]","INSTALLED_14_EXCLUSIVE_HASH_PASS":"INSTALLED_7_EXCLUSIVE_HASH_PASS"}
for a,b in replacements.items():assert a in old,a;old=old.replace(a,b)
old=old.replace("q=json.loads(qraw);mapping=", "q=json.loads(qraw);assert q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'];mapping=")
p=V/'execute_authorized_cuda_v2.py';assert not p.exists();ast.parse(old);p.write_text(old,encoding='utf-8')
upload=(S/'check_authorized_upload_v1.py').read_text(encoding='utf-8').replace("authorized_upload_readiness_v1","authorized_upload_readiness_v2").replace("delivery_receipt_v2.json","delivery_receipt_v2.json")
# Hotfix receipt has no sidecar records: derive their immutable local byte hashes.
upload=upload.replace("rows=[dict(path=", "d['sidecars']=[dict(path=str(Path(d['archive']['path']+x)),bytes=Path(d['archive']['path']+x).stat().st_size,sha256=hashlib.sha256(Path(d['archive']['path']+x).read_bytes()).hexdigest()) for x in ['.sha256','.bytes','.contents.sha256']]\nrows=[dict(path=")
p=V/'check_uploaded_v2.py';assert not p.exists();ast.parse(upload);p.write_text(upload,encoding='utf-8')
