"""Render the already authorized scope using the established byte-preserving driver."""
import ast,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent
O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2'
A=O/'authorized_execution_v1'
S='40a45089ed847261d9477993118b406048dadd09d15e492a402b455bddfdad74'
assert hashlib.sha256((O/'Euclidean_training_execution_request_v1.json').read_bytes()).hexdigest()==S
assert not A.exists();A.mkdir()
original=B/'prepare_sampling_AB_authorized_v2.py'
source=original.read_text(encoding='utf-8')
source=source.replace("O=B/'sampling_model_AB_foldC_seed0_20261103_v1';A=O/'authorized_execution_v2'", "O=B/'blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2';A=O/'authorized_execution_v1'")
source=source.replace('4a889afad90b1a8a52fcb75691c71990d03af8b7d120a96608ac4b9b85cb7a62',S)
source=source.replace('V1_training_execution_request_v2.json','Euclidean_training_execution_request_v1.json').replace('V1_training_entry_request_v1.json','Euclidean_training_entry_request_v1.json')
source=source.replace('647','650').replace('control_V1_v1','control_Euclidean_v1').replace('bcsp_sampling_ab_foldc_seed0_v1','bcsp_blue_noise_ab_foldc_seed0_v1')
source=source.replace("ar=O/'server_assets_observation_v1.json'", "ar=O.parent/'server_readiness_v1/assets_observation_v1.json'")
oldgrant="grant='Exact user text: 已上传，按既定分阶段边界，再单独授权当前 **v2 request完整SHA256**\\nReference resolution (not a quotation): current v2 scope SHA256 '+S+'; sole V1 inner request SHA256 '+sha(qraw)"
newgrant="grant='Exact user text: 已上传，按既定边界单独授权上述完整哈希。\\nReference resolution (not a quotation): authorized full execution scope SHA256 '+S+'; sole Euclidean inner request SHA256 '+sha(qraw)"
assert source.count(oldgrant)==1;source=source.replace(oldgrant,newgrant)
ast.parse(source)
exec(compile(source,str(original)+'[blue-noise-frozen-scope]','exec'),{'__file__':str(original),'__name__':'__main__'})
# Fix escaping at serialization time, before any payload or launcher is executed.
# This changes no frozen production implementation, scientific config or data.
p=A/'materialize_server_v1.py';raw=p.read_text(encoding='utf-8')
line=next(x for x in raw.splitlines() if x.startswith(' launcher='))
replacement=" launcher='#!/bin/bash\\nset -u\\numask 077\\nmkdir -- '+quote(future['output'])+' || exit 90\\n'+command+' > '+quote(future['log'])+' 2>&1\\nrc=$?\\n(set -o noclobber; printf \\\'%s\\\\n\\\' \"$rc\" > '+quote(future['exit_code'])+') || exit 91\\nexit \"$rc\"\\n'"
raw=raw.replace(line,replacement)
ast.parse(raw)
# Evaluate the launcher expression with harmless placeholders to verify newlines.
tree=ast.parse(raw)
assign=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='launcher' for t in n.targets))
expr=ast.Expression(assign.value);ast.fix_missing_locations(expr)
launcher=eval(compile(expr,'launcher-static','eval'),{'quote':lambda s:s,'future':{'output':'/x/out','log':'/x/out/log','exit_code':'/x/out/exit'},'command':'true'})
assert launcher.startswith('#!/bin/bash\n') and launcher.count('\n')==8 and 'rc=$?' in launcher and 'printf \'%s\\n\'' in launcher
p.write_text(raw,encoding='utf-8',newline='')
template=(B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py').read_text(encoding='utf-8')
payloads={}
for phase in ('precheck','install','materialize'):
    raw=(A/(phase+'_server_v1.py')).read_bytes();payloads[phase]=hashlib.sha256(raw).hexdigest()
    seconds=300 if phase=='install' else 120
    driver=template.replace('__DERIVED_CONTROLLER_PAYLOAD_SHA256__',payloads[phase]).replace('120s ',str(seconds)+'s ').replace("'135'",repr(str(seconds+15)))
    ast.parse(driver);(A/(phase+'_driver_v1.py')).write_text(driver,encoding='utf-8',newline='')
plan=json.loads((A/'operation_plan_v1.json').read_bytes());plan['payloads']=payloads
plan['launcher_static_newlines_verified']=True
(A/'operation_plan_v1.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
invoke=(B/'invoke_sampling_AB_authorized_v2.py').read_text(encoding='utf-8')
invoke=invoke.replace("sampling_model_AB_foldC_seed0_20261103_v1/authorized_execution_v2","blue_noise_model_pair_foldC_seed0_20261104_v1/first_training_request_v2/authorized_execution_v1").replace('647','650')
ast.parse(invoke)
(B/'invoke_blue_noise_authorized_execution_v1.py').write_text(invoke,encoding='utf-8',newline='')
with (A/'local_authorization_resolution_v1.json').open('x',encoding='utf-8') as f:json.dump({'user_text':'已上传，按既定边界单独授权上述完整哈希。','resolved_complete_scope_sha256':S,'single_Euclidean_training_only':True,'server_calls_during_preparation':0,'payloads':payloads,'launcher_linebreaks_static_verified':True},f,ensure_ascii=False,indent=2)
print('AUTHORIZED_BLUE_NOISE_OPERATIONS_STATIC_PASS_NO_SERVER_CALLS')
