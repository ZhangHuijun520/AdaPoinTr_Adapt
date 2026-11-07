"""Derive one-use install/call scaffolding, keep frozen science/entry bytes unchanged."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;OLD=S.parent/'condition_probe_implementation_v1'
def once(s,a,b):assert s.count(a)==1,a;return s.replace(a,b)
s=(OLD/'execute_authorized_once_20261107_v1.py').read_text(encoding='utf-8')
s=s.replace('9f2a04c381070d54d9e82cc70e800403b12ac7867124ff4b5e52043c1997549c','6e20c58d6ceee32b2f77858b9bb394535d39d999630302e0a115299e66de6e7a')
s=s.replace('934b6a011029a976f5c4c8ae868d8c7f07048e5209496387837ee5eb5535acf3','0b9a746712e100dffc22dce2706df4db3e62260d7bdc0dbfe4b3be3cdcb5b61d')
s=s.replace('bcsp_p2_condition_probe_pending_20261107_v1.tar.gz','bcsp_p2_H2_artificial_cuda_pending_20261107_v1.tar.gz').replace('bcsp_p2_condition_probe_20261107_v1','bcsp_p2_h2_cuda_admission_20261107_v1').replace('condition_probe_execution_request_v1.json','H2_artificial_cuda_execution_request_v1.json').replace('217631','173395')
s=once(s,"len(members)==6,'exact six archive members'","len(members)==10,'exact ten archive members'")
s=once(s,"need(q['prefix_budget']==1680 and all(q[k]==0 for k in ['backward','optimizer_steps','dense_forwards','BNCal']),'contract')","need(q['science']==dict(models=['AUX','COUPLE'],forward_attempt_limit=2,backward_attempt_limit=2,optimizer_steps=0,loss_calls=2,real_data_reads=0,checkpoint_loads=0,mode='eval_with_autograd',batch_size=1,n_input=8192,n_output=8192),'2F/2B/0 contract')")
s=once(s,"['entry','capture','core','input_index','P3']","['entry','h2_range','h2_adapter','h2_training_runtime','artificial_input','fixture_definition','P3','H2_implementation_P3']")
s=once(s," need(set(payload)==set(expected),'archive exact targets')"," expected[Path(L['launcher_template']['path']).name]=L['launcher_template']\n need(set(payload)==set(expected),'archive exact targets')")
start=s.index(" stage('four_checkpoint_and_exact_role_point_files')");end=s.index(" stage('all_readiness_pass_before_exclusive_install')",start)
s=s[:start]+" stage('artificial_only_scope_no_real_payload_read')\n need(q['artificial_input']['path']==str(INSTALL/'artificial_h2_input_v1.npz'),'exact synthetic payload')\n"+s[end:]
s=once(s,"exact_unique_point_paths=len(unique),unique_cases=len({r['case_id'] for r in idx['inputs']}),","artificial_payload_files=1,real_data_reads=0,checkpoint_reads=0,")
s=s.replace("'bcsp-condition-probe-authorization-v1'","'bcsp-h2-cuda-authorization-v1'").replace("'bcsp-condition-probe-runtime-v1'","'bcsp-h2-cuda-runtime-v1'")
start=s.index(" command=['/usr/bin/timeout'");end=s.index(" need(max(map(len,launch.splitlines()))",start)
s=s[:start]+" template=exact(L['launcher_template']).read_text(encoding='ascii')\n launch=template.replace('REQUEST_SHA256',QH).replace('AUTHORIZATION_SHA256',authsha).replace('RUNTIME_SHA256',runtime_sha)\n need(not any(p in launch for p in ['REQUEST_SHA256','AUTHORIZATION_SHA256','RUNTIME_SHA256']),'template placeholders')\n"+s[end:]
ast.parse(s)
with (S/'execute_H2_authorized_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
driver=(OLD/'invoke_authorized_operation_once_v1.py').read_text(encoding='utf-8')
driver=driver.replace('9f2a04c381070d54d9e82cc70e800403b12ac7867124ff4b5e52043c1997549c','6e20c58d6ceee32b2f77858b9bb394535d39d999630302e0a115299e66de6e7a').replace('condition_probe_execution_request_v1.json','H2_artificial_cuda_execution_request_v1.json').replace('execute_authorized_once_20261107_v1.py','execute_H2_authorized_once_v1.py').replace('condition_probe_authorized_once_20261107_v1.py','H2_cuda_authorized_once_20261107_v1.py')
ast.parse(driver)
with (S/'invoke_H2_authorized_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(driver)
assert 'idx[' not in s and "run['checkpoint']" not in s and 'unique.values' not in s
q=S/'H2_artificial_cuda_execution_request_v1.json';assert hashlib.sha256(q.read_bytes()).hexdigest()=='6e20c58d6ceee32b2f77858b9bb394535d39d999630302e0a115299e66de6e7a'
with (S/'authorized_scaffolding_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='STATIC_PRELAUNCH_CALL_PASS',request_sha256=hashlib.sha256(q.read_bytes()).hexdigest(),frozen_scientific_source_unchanged=True,real_data_or_checkpoint_checks_removed=True,template_exact_binding=True,source_bytes_capture=True,no_retry=True,scaffolding=[dict(path=str(S/n),bytes=(S/n).stat().st_size,sha256=hashlib.sha256((S/n).read_bytes()).hexdigest()) for n in ['execute_H2_authorized_once_v1.py','invoke_H2_authorized_once_v1.py']]),f,indent=2)
print('STATIC_PRELAUNCH_CALL_PASS')
