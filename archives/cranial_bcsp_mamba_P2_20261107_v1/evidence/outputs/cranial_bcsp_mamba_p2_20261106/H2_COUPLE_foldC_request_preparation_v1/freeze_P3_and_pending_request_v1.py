"""Local-only P3 and pending COUPLE request; no server access/materialized controls."""
import ast,copy,hashlib,importlib.util,io,json,shlex,shutil,tarfile
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;A=S.parent/'H2_AUX_foldC_training_preparation_v1';H=S.parent/'H2_implementation_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
entry=S/'bcsp_h2_couple_foldC_training_entry_v1.py';spec=importlib.util.spec_from_file_location('h2_couple_entry_freeze',entry);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
cpu=S/'artificial_cpu_batch_v2/result_v1.json';result=json.loads(cpu.read_bytes());assert result['status']=='H2_COUPLE_ENTRY_CPU_CONTRACT_PASS' and result['checks_passed']==len(result['checks'])==32
assert not (cpu.parent/'failure_v1.json').exists() and all(sha(Path(r['path']))==r['sha256'] for r in result['source_bindings'])
review=json.loads((S/'static_review_v2.json').read_bytes());assert review['status']=='STATIC_S0_S1_PASS' and all(sha(S/r['name'])==r['sha256'] for r in review['files'])
prior=json.loads((S/'artificial_cpu_batch_v1/failure_v1.json').read_bytes());assert prior['error']=="AssertionError('22 training imports bind own exact H2 modules')"
assert sha(entry)==json.loads((S/'static_review_v1.json').read_bytes())['files'][0]['sha256']
auxentry=A/'bcsp_h2_aux_foldC_training_entry_v1.py';assert sha(auxentry)==json.loads((A/'static_review_v1.json').read_bytes())['files'][0]['sha256']
names={'h2_range':'bcsp_h2_range_v1.py','h2_adapter':'bcsp_h2_model_adapter_v1.py','runtime':'bcsp_h2_training_runtime_v1.py'}
assert all(sha(H/n)==e.H2_HASHES[k] for k,n in names.items())
def funcs(p):return {n.name:n for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
parent,child=funcs(auxentry),funcs(entry)
unchanged=['require','no_links','sha','exact','json_bound','emit','load_bound','payload_paths','make_training_policy','TrainingBudget','P1Budget']
assert all(ast.dump(parent[n],include_attributes=False)==ast.dump(child[n],include_attributes=False) for n in unchanged)
auxrequest=A/'first_FoldC_request_v1/transport_payload/H2_AUX_foldC_seed0_training_execution_request_v1.json';auxaudit=A/'post_training_freeze_audit_v1/audit_report_v1.json';auxinitial=A/'post_training_freeze_audit_v1/downloads/initialization.json'
assert all(sha(p)==e.AUX_PAIR_PINS[k] for k,p in [('request',auxrequest),('audit',auxaudit),('initialization',auxinitial)])
aq=json.loads(auxrequest.read_bytes());audit=json.loads(auxaudit.read_bytes());assert audit['checks_passed']==25 and all(audit['checks'].values())
p3=dict(status='LOCAL_H2_COUPLE_TRAINING_ENTRY_P3_PASS',entry_sha256=sha(entry),H2_source_hashes=e.H2_HASHES,CPU_result=bind(cpu),CPU_contracts=32,static_review=bind(S/'static_review_v2.json'),AUX_entry_unchanged=bind(auxentry),AUX_pairing_pins=e.AUX_PAIR_PINS,
 checks=dict(full_authorize_path_with_real_metadata_validator=True,COUPLE_dispatch_five_coordinate_consumers=True,AUX_COUPLE_full_initial_state_equal_in_artificial_fixture=True,real_runtime_initial_parameter_and_persistent_fingerprint_gate=True,original_payload_and_resource_guards_AST_unchanged=True,exact_reused_H2_directory_in_import_and_read_policy=True,original_H2_modules_unchanged_since_CUDA=True,no_GPU_preflight_repeat=True,only_mode_changes_scientific_config=True),
 prior_failed_test=dict(batch='artificial_cpu_batch_v1',reason='Test22 retained the AUX-only sys.path text assertion',production_entry_changed_for_fix=False,failed_source_snapshot=bind(S/'artificial_cpu_batch_v1/failed_test_source_snapshot.py'),failure_receipt=bind(S/'artificial_cpu_batch_v1/failure_v1.json'),resolution='Only test assertion updated to exact reused-module parent; final32-check batch retained separately'),
 limitations=['Artificial CPU native-factory facade; no real Mamba model construction in this batch','Already frozen COUPLE CUDA admission reused; CPU success is not new CUDA/training proof','No current server/resource recheck in this implementation-only task; required before separate execution','Finite gradient nondeterminism and sampled resource-monitoring limitations inherited','No scientific effect conclusion'],server_operations=0,production_forward=0,production_backward=0,optimizer_steps=0)
emit(S/'implementation_P3_v1.json',p3)
O=S/'final_pending_request_v1';O.mkdir();P=O/'transport_payload';P.mkdir()
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_COUPLE_foldC_20261107_v1';output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_COUPLE_foldC_seed0_20261107_v1';mapping=[]
def stage(p,name=None):
 n=name or p.name;t=P/n;shutil.copyfile(p,t);r=dict(path=str(PurePosixPath(remote)/n),bytes=t.stat().st_size,sha256=sha(t));mapping.append(dict(local=str(t.absolute()),target=r['path'],bytes=r['bytes'],sha256=r['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'));return r
q=copy.deepcopy(aq);q.update(schema='bcsp-p2-H2-COUPLE-training-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id='H2_COUPLE_foldC_seed0_20261107_v1',output=output,launch_attempt=remote+'/control/single_attempt_claim_v1.json',h2_config=e.H2)
q['implementation']['entry']=stage(entry)
config=S/'static_H2_COUPLE_training_config_candidate_v1.json';static=json.loads(config.read_bytes());assert static['H2']==e.H2
auxstatic=json.loads((A/'first_FoldC_request_v1/transport_payload/static_H2_AUX_training_config_v1.json').read_bytes());reverted=copy.deepcopy(static);reverted['H2']['mode']='AUX';assert reverted==auxstatic
q['static_config']=stage(config,'static_H2_COUPLE_training_config_v1.json');q['p3']=stage(S/'implementation_P3_v1.json');stage(cpu,'CPU_result_v1.json')
q['aux_pairing']=dict(request=dict(path=aq['launch_contract']['request_path'],bytes=auxrequest.stat().st_size,sha256=sha(auxrequest)),audit=stage(auxaudit,'frozen_H2_AUX_C_post_training_audit_v1.json'),initialization=dict(path=aq['output']+'/initialization.json',bytes=auxinitial.stat().st_size,sha256=sha(auxinitial)))
lc=dict(tmux_session='bcsp_p2_H2_COUPLE_C_seed0_20261107_v1',authorization=remote+'/control/H2_authorization_v1.json',runtime=remote+'/control/H2_runtime_v1.json',launcher=remote+'/control/H2_launch_once_v1.sh',request_path=remote+'/H2_COUPLE_foldC_seed0_training_execution_request_v1.json',log=output+'/launch.log',pid=output+'/worker.pid',exit_code=output+'/exit_code.txt',single_attempt=True,timeout_seconds=86400,materialization_order='authorization -> hash -> runtime -> hash -> launcher; exclusive claim before unique tmux',parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True)
q['provenance']=dict(baseline='Original scratch M0 Fold C initialization plus same1025 zero-initialized head as frozen AUX; never load AUX final checkpoint',only_scientific_delta_from_AUX='COUPLE uses fixed bounded detached-delta radius scaling through all coarse consumers; labels/loss coefficients unchanged',AUX_formal_audit_sha256=sha(auxaudit),AUX_initialization_sha256=sha(auxinitial),reused_H2_modules_unchanged=True,no_hyperparameter_selection_from_AUX_loss=True,local_P3_pass=True,server_operations_this_preparation=0,current_server_rechecked=False,last_verified_identity=aq['identity'],readiness_receipt_semantics='Inherited AUX readiness snapshot and exact315 hash list, not a new COUPLE readiness/absence claim',required_before_materialization=['Exact current hostname/UID/GPU/Python and idle GPU; unchanged environment/provider','Uploaded archive and all mapped bytes/hashes; every new target and run/control path absent and safe parents','All reused assets and315 training payload byte hashes match','Frozen AUX request, formal audit and initial fingerprints match','Original resource limits; PID diagnostic policy unchanged'],legacy_baseline_references='P1 T0/quantification references retained as original provenance; H2 admission uses frozen CUDA audit',finite_Mamba_gradient_nondeterminism_disclosed=True,resource_policy='Original thresholds, sampled monitoring, no cgroup or common PID ownership guarantee',training_started=False)
q['not_authorized']=copy.deepcopy(aq['not_authorized'])
args=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',q['identity']['python_realpath'],'-I','-S','-B',q['implementation']['entry']['path'],'--request',lc['request_path'],'--request-sha256','REQUEST_SHA256','--authorization',lc['authorization'],'--authorization-sha256','AUTHORIZATION_SHA256','--runtime',lc['runtime'],'--runtime-sha256','RUNTIME_SHA256']
out=PurePosixPath(output);lines=['#!/bin/bash','set -u','umask 077','cd '+shlex.quote(e.PROJECT)+' || exit 120']
for p in reversed((out,*out.parents)):
 if str(p)!='/':lines.append('[ ! -L '+shlex.quote(str(p))+' ] || exit 121')
lines+=['mkdir -p -- '+shlex.quote(str(out.parent))+' || exit 122','mkdir -- '+shlex.quote(output)+' || exit 123','exec >>'+shlex.quote(lc['log'])+' 2>&1','env '+chr(92)]
for k,v in q['environment'].items():lines.append(shlex.quote(k+'='+v.replace('<owned_output>',output))+' '+chr(92))
lines+=[' '+(' '+chr(92)+'\n ').join(map(shlex.quote,args)),'result=$?','printf "%s\\n" "$result" > '+shlex.quote(lc['exit_code']),'exit "$result"']
t=O/'launch_once_template_v1.sh'
with t.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
assert max(map(len,t.read_text().splitlines()))<=2048 and '\\' not in str(out)
lc['launcher_template']=stage(t);q['launch_contract']=lc
request=P/'H2_COUPLE_foldC_seed0_training_execution_request_v1.json';emit(request,q)
mapping.append(dict(local=str(request.absolute()),target=lc['request_path'],bytes=request.stat().st_size,sha256=sha(request),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
emit(O/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED',remote_root=remote,files=mapping,reused_implementation={k:v for k,v in q['implementation'].items() if k!='entry'},reused_data_root=q['data_root'],reused_readiness_snapshot=q['readiness'],reused_aux_pairing=q['aux_pairing'],required_before_write=q['provenance']['required_before_materialization'],materials_not_created=[lc['authorization'],lc['runtime'],lc['launcher'],q['launch_attempt'],output]))
# Check the pending production request's scientific and source bindings without pretending to execute it.
assert set(q)==set(aq)|{'aux_pairing'} and all(q[k]==aq[k] for k in ['identity','environment','QC','order_plan','data_root','model_root','initialization_reference','numeric_policy','numeric_protocol','pair_contract','dependencies','n_input','n_output'])
assert all(q['implementation'][k]==v for k,v in aq['implementation'].items() if k!='entry') and all(q['aux_pairing'][k]['sha256']==h for k,h in e.AUX_PAIR_PINS.items())
archive=O/'bcsp_p2_H2_COUPLE_foldC_pending_20261107_v1.tar.gz';members=[(p,'payload/'+p.name) for p in sorted(P.iterdir())]+[(O/'installation_mapping_v1.json','installation_mapping_v1.json')]
with tarfile.open(archive,'w:gz') as tar:
 for p,n in members:
  b=p.read_bytes();info=tarfile.TarInfo(n);info.size=len(b);info.mode=0o600;info.mtime=0;tar.addfile(info,io.BytesIO(b))
with tarfile.open(archive,'r:gz') as tar:
 assert len(tar.getmembers())==len(members)
 for p,n in members:assert tar.extractfile(n).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+n+'\n' for p,n in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(request),archive=bind(archive),installation_files=len(mapping),CPU_contracts=32,P3_status=p3['status'],AUX_formal_audit_sha256=sha(auxaudit),current_server_rechecked=False,readiness_required_before_execution=True,server_operations=0,training_started=False)
emit(O/'pending_request_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))
