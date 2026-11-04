"""Bind established candidate installer/launcher to the explicitly authorized graph scope."""
import ast,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';C=O/'graph_request_v2';A=C/'authorized_execution_v1'
S='1072fad5cbbb970fe37cf6300445d705b8dc99a38aba3fc20cb70cac6cf227d5'
assert hashlib.sha256((C/'candidate_training_execution_request_v1.json').read_bytes()).hexdigest()==S
p=B/'prepare_sampling_Morton_authorized_v1.py';source=p.read_text(encoding='utf-8')
for old,new in [
("O=B/'sampling_model_AB_foldC_seed0_20261103_v1'","O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2'"),
("C=O/'Morton_training_request_v1'","C=O/'graph_request_v2'"),
('d4a44a990c0b3f0b91522c6f9803074a34e6c3803c243bf08e8a46ace42eeae3',S),
('bcsp_sampling_ab_foldc_morton_control_v1','bcsp_graph_control_v1'),
("=='3311'","=='3328'"),
('Exact user text: 已上传，单独授权上述哈希','Exact user text: 已上传，单独授权上述完整哈希'),
('invoke_sampling_Morton_authorized_v1.py','invoke_blue_noise_graph_authorized_v1.py'),
('observe_sampling_Morton_status_v1.py','observe_blue_noise_graph_generated_status_v1.py'),
("sampling_model_AB_foldC_seed0_20261103_v1/Morton_training_request_v1/authorized_execution_v1","blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/graph_request_v2/authorized_execution_v1"),
]:
    assert old in source,old;source=source.replace(old,new)
ast.parse(source)
exec(compile(source,str(p)+'[frozen-graph-scope]','exec'),{'__file__':str(p),'__name__':'__main__'})
# Serialize launcher with the already verified real newline contract.
path=A/'materialize_server_v1.py';raw=path.read_text(encoding='utf-8')
line=next(x for x in raw.splitlines() if x.startswith(' launcher='))
baseline=(O/'authorized_execution_v1/materialize_server_v1.py').read_text(encoding='utf-8')
replacement=next(x for x in baseline.splitlines() if x.startswith(' launcher='))
raw=raw.replace(line,replacement).replace('candidate_started=False','training_completion_claimed=False')
ast.parse(raw)
node=next(n for n in ast.walk(ast.parse(raw)) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='launcher' for t in n.targets))
expr=ast.Expression(node.value);ast.fix_missing_locations(expr)
launcher=eval(compile(expr,'launcher-static','eval'),{'quote':lambda s:s,'future':{'output':'/x/out','log':'/x/out/log','exit_code':'/x/out/exit'},'command':'true'})
assert launcher.count('\n')==8 and launcher.startswith('#!/bin/bash\n') and 'rc=$?' in launcher
path.write_text(raw,encoding='utf-8',newline='')
template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8')
plan=json.loads((A/'operation_plan_v1.json').read_bytes())
for phase in ('precheck','install','materialize'):
    payload=(A/(phase+'_server_v1.py')).read_bytes();digest=hashlib.sha256(payload).hexdigest()
    driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',digest);ast.parse(driver)
    (A/(phase+'_driver_v1.py')).write_text(driver,encoding='utf-8',newline='');plan['payloads'][phase]=digest
plan['launcher_real_newlines_verified']=True
(A/'operation_plan_v1.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
with (A/'user_authorization_resolution_v1.json').open('x',encoding='utf-8') as f:json.dump({'user_text':'已上传，单独授权上述完整哈希','resolved_full_scope_sha256':S,'allowed_attempts':1,'arm':'surface_graph','server_calls_during_preparation':0},f,ensure_ascii=False,indent=2)
print('GRAPH_AUTHORIZED_OPERATIONS_STATIC_PASS_NO_SERVER_CALLS')
