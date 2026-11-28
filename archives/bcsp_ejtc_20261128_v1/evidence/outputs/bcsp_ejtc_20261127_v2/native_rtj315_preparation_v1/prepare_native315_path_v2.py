"""Only replace exact input root with independently hash-verified existing paths."""
from pathlib import Path,PurePosixPath
import copy,hashlib,json
d=Path(__file__).resolve().parent
h=lambda b:hashlib.sha256(b).hexdigest()
def put(p,b):
 with p.open('xb') as f:f.write(b)
def dump(p,q):put(p,(json.dumps(q,ensure_ascii=False,indent=2)+'\n').encode())
scope=json.loads((d/'EJTC_RTJ_D_native315_scope_v1.json').read_bytes())
actual=json.loads((d/'server_actual_paths_v1/Native315_actual_path_readonly_receipt_v1.json').read_bytes())
assert actual['verified_fixed_cases']==actual['path_mismatches']==105 and actual['all_file_and_partial_hashes_match']
root='/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1'
v=copy.deepcopy(scope);v['input_root']=root
for row,proof in zip(v['inputs'],actual['cases']):
 assert row['case_id']==proof['case_id'] and row['input']['path']==proof['frozen_path']
 a=proof['actual'];assert row['input']['bytes']==a['bytes'] and row['input']['sha256']==a['sha256'] and row['partial_array_sha256']==a['partial_array_sha256']
 assert a['path']==str(PurePosixPath(root)/'points'/PurePosixPath(row['input']['path']).name)
 row['input']['path']=a['path']
sp=d/'EJTC_RTJ_D_native315_scope_v2.json';dump(sp,v);scope_sha=h(sp.read_bytes())
old=(d/'ejtc_native_rtj315_v1.py').read_text()
needle="str(PurePosixPath(parent['data_root']) / original['point_path'])"
assert old.count(needle)==1
worker=old.replace("SCOPE_SHA = 'f61e62cf2cbaf9e81b2e60598c1e0fede3a7b058368694012df0c7fb121606d2'",f"SCOPE_SHA = '{scope_sha}'").replace(needle,"str(PurePosixPath(scope['input_root']) / original['point_path'])")
wp=d/'ejtc_native_rtj315_v2.py';put(wp,worker.encode())
q=json.loads((d/'Native315_execution_request_CPU_fixture_v1.json').read_bytes())
install=q['binding']['install_root']
q['files']['worker']=dict(path=install+'/'+wp.name,bytes=wp.stat().st_size,sha256=h(wp.read_bytes()))
q['files']['scope']=dict(path=install+'/'+sp.name,bytes=sp.stat().st_size,sha256=scope_sha)
q['scope_sha256']=scope_sha;q['launch']['request_path']=install+'/EJTC_RTJ_D_native315_execution_request_h7vvrr_v2.json'
q['path_revision']=dict(reason='Exact existing input directory binding corrected; cohort and file/array bytes unchanged',input_root=root,readonly_evidence_sha256=h((d/'server_actual_paths_v1/Native315_actual_path_readonly_receipt_v1.json').read_bytes()))
dump(d/'Native315_execution_request_CPU_fixture_v2.json',q)
test=(d/'verify_native315_cpu_v2.py').read_text(encoding='utf-8-sig').replace("cpu_validation_v2","cpu_validation_v3").replace('ejtc_native_rtj315_v1.py','ejtc_native_rtj315_v2.py').replace('EJTC_RTJ_D_native315_scope_v1.json','EJTC_RTJ_D_native315_scope_v2.json').replace('Native315_execution_request_CPU_fixture_v1.json','Native315_execution_request_CPU_fixture_v2.json')
put(d/'verify_native315_cpu_v3.py',test.encode())
startup=(d/'verify_native315_startup_cpu_v1.py').read_text().replace('cpu_startup_validation_v1','cpu_startup_validation_v2').replace('ejtc_native_rtj315_v1.py','ejtc_native_rtj315_v2.py').replace('EJTC_RTJ_D_native315_scope_v1.json','EJTC_RTJ_D_native315_scope_v2.json').replace('Native315_execution_request_CPU_fixture_v1.json','Native315_execution_request_CPU_fixture_v2.json')
put(d/'verify_native315_startup_cpu_v2.py',startup.encode())
print(json.dumps(dict(status='PATH_ONLY_V2_CANDIDATE_PREPARED',scope_sha256=scope_sha,worker_sha256=h(wp.read_bytes()))))
