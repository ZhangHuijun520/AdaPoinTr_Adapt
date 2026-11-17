from pathlib import Path
import ast
V=Path(__file__).resolve().parent;S=V.parent
text=(S/'binding_hotfix_v2/execute_authorized_cuda_v2.py').read_text(encoding='utf-8')
for a,b in {'authorized_execution_v2':'authorized_execution_v3','a2b1961158b58199e212130654ddd274ce617c90e24448f22ba70a0062c2343e':'93ee5eb84f4e2b3b0de81e0f5b70c899c0cf2b2661f2946ffdead936c07568f6','bcsp_spcg_binding_hotfix_pending_20261116_v2.tar.gz':'bcsp_spcg_output_policy_pending_20261116_v3.tar.gz','0a6adcb5b8ad0da94b64e6d54fe63d0d1c8609296011cfb7f2a1ee7ffa337154':'7b394f97af4edbb68aefd202e90e4ac497d10d56efef4565d9fff2696228e400','SPCG_CUDA_execution_request_v2.json':'SPCG_CUDA_execution_request_v3.json','installation_mapping_v2.json':'installation_mapping_v3.json','INSTALLED_7_EXCLUSIVE_HASH_PASS':'INSTALLED_10_EXCLUSIVE_HASH_PASS'}.items():assert a in text,a;text=text.replace(a,b)
p=V/'execute_authorized_cuda_v3.py';assert not p.exists();ast.parse(text);p.write_text(text,encoding='utf-8')
upload=(S/'binding_hotfix_v2/check_uploaded_v2.py').read_text(encoding='utf-8').replace('authorized_upload_readiness_v2','authorized_upload_readiness_v3').replace('delivery_receipt_v2.json','delivery_receipt_v3.json')
p=V/'check_uploaded_v3.py';assert not p.exists();ast.parse(upload);p.write_text(upload,encoding='utf-8')
status=(S/'binding_hotfix_v2/status_v2.py').read_text(encoding='utf-8').replace('authorized_execution_v2','authorized_execution_v3').replace('SPCG_G0_G1_G2_CUDA_20261116_v2','SPCG_G0_G1_G2_CUDA_20261116_v3')
p=V/'status_v3.py';assert not p.exists();ast.parse(status);p.write_text(status,encoding='utf-8')
