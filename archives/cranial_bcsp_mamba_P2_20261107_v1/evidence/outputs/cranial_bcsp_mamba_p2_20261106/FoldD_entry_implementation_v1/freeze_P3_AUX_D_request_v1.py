"""Local final P3 and first AUX_D pending request. No server calls or training."""
import ast,copy,hashlib,importlib.util,io,json,shlex,shutil,tarfile
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;R=S.parents[2];H=S.parent/'H2_implementation_v1';PRE=S.parent/'FoldD_pair_preparation_v1';A=S.parent/'H2_AUX_foldC_training_preparation_v1';C=S.parent/'H2_COUPLE_foldC_initialization_readfix_v2';P1=R/'outputs/cranial_bcsp_mamba_p1_20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,v):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
ep=S/'bcsp_h2_foldD_training_entry_v1.py';spec=importlib.util.spec_from_file_location('D_freeze_entry',ep);e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
cpu=S/'artificial_cpu_batch_v1/result_v1.json';res=json.loads(cpu.read_bytes());assert res['status']=='H2_FOLDD_ENTRY_CPU_CONTRACT_PASS' and res['checks_passed']==len(res['checks'])==33 and not (cpu.parent/'failure_v1.json').exists()
assert all(sha(Path(r['path']))==r['sha256'] for r in res['source_bindings'])
sr=json.loads((S/'static_review_v1.json').read_bytes());assert sr['status']=='STATIC_S0_S1_PASS' and all(sha(S/r['name'])==r['sha256'] for r in sr['files'])
policy=json.loads((cpu.parent/'policy_child_stdout.bin').read_bytes());assert all(policy.values())
def funcs(p):return {n.name:n for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
old=C/'bcsp_h2_couple_foldC_training_entry_v2.py';oldf,newf=funcs(old),funcs(ep)
unchanged=['require','no_links','sha','exact','json_bound','emit','load_bound','payload_paths','make_training_policy','TrainingBudget','P1Budget']
assert all(ast.dump(oldf[n],include_attributes=False)==ast.dump(newf[n],include_attributes=False) for n in unchanged)
hnames={'h2_range':'bcsp_h2_range_v1.py','h2_adapter':'bcsp_h2_model_adapter_v1.py','runtime':'bcsp_h2_training_runtime_v1.py'};assert all(sha(H/n)==e.H2_HASHES[k] for k,n in hnames.items())
baseline=P1/'M0_FoldD_request_v1/transport_payload/M0_foldD_seed0_training_execution_request_v1.json';ba=P1/'M0_FoldD_request_v1/post_training_freeze_audit_v1/audit_report_v1.json';base=json.loads(baseline.read_bytes())
assert sha(baseline)==e.FROZEN_BASELINES['D']['request_sha256'] and sha(ba)==e.FROZEN_BASELINES['D']['audit_sha256']
ca=C/'post_training_freeze_audit_v1/audit_report_v2.json';assert sha(ca)=='5a040e5d5903264c3658e52fb00c50a17b531394efcb804fa17af2f76b7310de'
readiness=PRE/'server_readiness_receipt_v1.json';ready=json.loads(readiness.read_bytes());assert ready['status']=='FOLDD_H2_NECESSARY_READONLY_READINESS_PASS' and ready['identity']==e.CURRENT_IDENTITY and ready['training_cases']==315 and ready['sources']==63
sc=PRE/'static_H2_AUX_foldD_candidate_v1.json';static=json.loads(sc.read_bytes());assert static['H2']==e.mode_config('AUX')
cstatic=json.loads((A/'first_FoldC_request_v1/transport_payload/static_H2_AUX_training_config_v1.json').read_bytes());assert static==cstatic
p3=dict(status='LOCAL_H2_FOLDD_TRAINING_ENTRY_P3_PASS',entry_sha256=sha(ep),H2_source_hashes=e.H2_HASHES,CPU_result=bind(cpu),CPU_contracts=33,static_review=bind(S/'static_review_v1.json'),actual_policy_hook_regression=policy,immutable_parent_entry=bind(old),original_guard_functions_AST_unchanged=unchanged,M0_D_request=bind(baseline),M0_D_audit=bind(ba),FoldC_H2_pair_audit=bind(ca),FoldD_preparation_contract=bind(PRE/'FoldD_H2_paired_training_contract_v1.json'),readiness_snapshot=bind(readiness),checks=dict(full_authorize_AUX_D_and_COUPLE_D=True,wrong_fold_and_mode_rejected=True,exact_D_metadata_order_contract=True,both_modes_shared_full_initial_state=True,COUPLE_runtime_fingerprint_gate=True,AUX_no_extra_read_root=True,COUPLE_exact_readonly_reference_under_actual_audit_hook=True,adjacent_files_and_reference_writes_rejected=True,actual_five_coordinate_consumers_and_loss=True,original_shared_H2_modules_unchanged=True,original_count_optimizer_resource_contracts_preserved=True,no_C_loss_based_tuning=True),limitations=['Artificial CPU native-factory facade; no real Mamba model constructed in this batch','Existing frozen H2 CUDA admission reused; no repeat and no new GPU proof','Historical resource snapshot is not a reservation; must recheck current exact assets/resources before execution','COUPLE_D request not created; requires actual future AUX_D frozen audit and initialization','Finite native Mamba gradient nondeterminism and sampled resource monitoring limitations inherited','No scientific effect claim'],server_operations=0,production_forward=0,production_backward=0,optimizer_steps=0)
emit(S/'implementation_P3_v1.json',p3)
O=S/'AUX_D_pending_request_v1';O.mkdir();P=O/'transport_payload';P.mkdir();mapping=[]
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H2_foldD_20261107_v1';output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2/H2_AUX_foldD_seed0_20261107_v1'
def stage(p,name=None):
 n=name or p.name;t=P/n;shutil.copyfile(p,t);r=dict(path=str(PurePosixPath(remote)/n),bytes=t.stat().st_size,sha256=sha(t));mapping.append(dict(local=str(t.absolute()),target=r['path'],bytes=r['bytes'],sha256=r['sha256'],write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'));return r
q=copy.deepcopy(base);q.update(schema='bcsp-p2-H2-foldD-training-request-v1',stage='CRANIAL_BCSP_MAMBA_P2_H2',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',run_id='H2_AUX_foldD_seed0_20261107_v1',identity=e.CURRENT_IDENTITY,output=output,launch_attempt=remote+'/control/AUX_D_single_attempt_claim_v1.json',h2_config=e.mode_config('AUX'),aux_pairing=None)
q['environment']['CUDA_VISIBLE_DEVICES']=e.CURRENT_IDENTITY['gpu_uuid'];q['implementation']['entry']=stage(ep)
cq=json.loads((C/'final_pending_request_v2/transport_payload/H2_COUPLE_foldC_seed0_training_execution_request_v2.json').read_bytes())
for k in hnames:q['implementation'][k]=copy.deepcopy(cq['implementation'][k]);assert q['implementation'][k]['sha256']==e.H2_HASHES[k]
q['static_config']=stage(sc,'static_H2_AUX_foldD_training_config_v1.json');q['baseline_request']=stage(baseline,'frozen_M0_D_request_v1.json');q['baseline_audit']=stage(ba,'frozen_M0_D_post_training_audit_v1.json');q['p3']=stage(S/'implementation_P3_v1.json');q['readiness']=stage(readiness,'FoldD_readiness_snapshot_v1.json');q['cuda_audit']=copy.deepcopy(cq['cuda_audit']);stage(cpu,'CPU_result_v1.json');stage(ca,'frozen_FoldC_H2_pair_audit_v1.json');stage(PRE/'FoldD_H2_paired_training_contract_v1.json')
lc=dict(tmux_session='bcsp_p2_H2_AUX_D_seed0_20261107_v1',authorization=remote+'/control/AUX_D_authorization_v1.json',runtime=remote+'/control/AUX_D_runtime_v1.json',launcher=remote+'/control/AUX_D_launch_once_v1.sh',request_path=remote+'/H2_AUX_foldD_seed0_training_execution_request_v1.json',log=output+'/launch.log',pid=output+'/worker.pid',exit_code=output+'/exit_code.txt',single_attempt=True,timeout_seconds=86400,materialization_order='authorization -> hash -> runtime -> hash -> launcher; exclusive claim before unique tmux',parent_directory_before_redirection=True,PowerShell_explicit_exit_LASTEXITCODE=True)
q['provenance']=dict(baseline='Frozen M0 Fold D seed0; original scratch factory plus zero H2 head, no final checkpoint resume',foldC_H2_pair_audit=next(dict(path=x['target'],bytes=x['bytes'],sha256=x['sha256']) for x in mapping if x['target'].endswith('/frozen_FoldC_H2_pair_audit_v1.json')),only_scientific_delta_from_M0_D='H2-AUX1025 parameter all-zero head and fixed.1 auxiliary; no generation coupling',same_scientific_settings_as_C=True,no_C_loss_or_development_based_tuning=True,shared_H2_modules_reused=True,local_P3_pass=True,current_server_rechecked_this_implementation=False,readiness_snapshot_semantics='Prior bounded Fold D readiness; no new resource reservation',resource_policy='Original thresholds, sampled monitoring; PID diagnostic only, no ownership or cgroup guarantee',numeric_policy='Finite native Mamba gradient nondeterminism accepted and disclosed',required_before_materialization=['Exact current identity, fixed GPU UUID and idle GPU; disk resources within original thresholds','Uploaded archive and all mappings match; all new targets/control/run paths absent and safe real parents','Exact reused implementations, provider, frozen metadata and315 D training file hashes match','Original D shared order and seed0 scratch construction reference match'],COUPLE_D_not_created=True,training_started=False)
q['not_authorized']=['Execution before separate complete request SHA256 authorization','Automatic retry/resume','COUPLE_D or any other run','BNCal or development evaluation','Changes to data, sampling,8192 point counts,3900 updates or original resources','Loss-based tuning or case filtering','Dependency download/build/install/upgrade','Loading final checkpoint for initialization','Materializing authorized controls while pending']
args=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',q['identity']['python_realpath'],'-I','-S','-B',q['implementation']['entry']['path'],'--request',lc['request_path'],'--request-sha256','REQUEST_SHA256','--authorization',lc['authorization'],'--authorization-sha256','AUTHORIZATION_SHA256','--runtime',lc['runtime'],'--runtime-sha256','RUNTIME_SHA256']
out=PurePosixPath(output);lines=['#!/bin/bash','set -u','umask 077','cd '+shlex.quote(e.PROJECT)+' || exit 120']
for p in reversed((out,*out.parents)):
 if str(p)!='/':lines.append('[ ! -L '+shlex.quote(str(p))+' ] || exit 121')
lines+=['mkdir -p -- '+shlex.quote(str(out.parent))+' || exit 122','mkdir -- '+shlex.quote(output)+' || exit 123','exec >>'+shlex.quote(lc['log'])+' 2>&1','env '+chr(92)]
for k,v in q['environment'].items():lines.append(shlex.quote(k+'='+v.replace('<owned_output>',output))+' '+chr(92))
lines+=[' '+(' '+chr(92)+'\n ').join(map(shlex.quote,args)),'result=$?','printf "%s\\n" "$result" > '+shlex.quote(lc['exit_code']),'exit "$result"']
template=O/'AUX_D_launch_once_template_v1.sh'
with template.open('x',encoding='utf-8',newline='\n') as f:f.write('\n'.join(lines)+'\n')
lc['launcher_template']=stage(template);q['launch_contract']=lc
assert max(map(len,template.read_text().splitlines()))<=2048 and '\\' not in str(out)
assert set(q)==set(base)|{'baseline_request','baseline_audit','p3','h2_config','cuda_audit','readiness','aux_pairing'}
unchanged_keys=['QC','order_plan','data_root','model_root','initialization_reference','numeric_policy','numeric_protocol','pair_contract','dependencies','n_input','n_output','fold','variant'];assert all(q[k]==base[k] for k in unchanged_keys)
assert all(q['implementation'][k]==v for k,v in base['implementation'].items() if k not in ('entry','runtime'))
request=P/'H2_AUX_foldD_seed0_training_execution_request_v1.json';emit(request,q);mapping.append(dict(local=str(request.absolute()),target=lc['request_path'],bytes=request.stat().st_size,sha256=sha(request),write_policy='EXCLUSIVE_CREATE_NO_OVERWRITE'))
emit(O/'installation_mapping_v1.json',dict(status='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED',remote_root=remote,files=mapping,reused_implementation={k:v for k,v in q['implementation'].items() if k!='entry'},reused_data_root=q['data_root'],training_payload_SHA256=ready['point_SHA256'],required_before_write=q['provenance']['required_before_materialization'],materials_not_created=[lc['authorization'],lc['runtime'],lc['launcher'],q['launch_attempt'],output],COUPLE_D_request_created=False))
archive=O/'bcsp_p2_H2_AUX_foldD_pending_20261107_v1.tar.gz';members=[(p,'payload/'+p.name) for p in sorted(P.iterdir())]+[(O/'installation_mapping_v1.json','installation_mapping_v1.json')]
with tarfile.open(archive,'w:gz') as tar:
 for p,n in members:
  b=p.read_bytes();info=tarfile.TarInfo(n);info.size=len(b);info.mode=0o600;info.mtime=0;tar.addfile(info,io.BytesIO(b))
with tarfile.open(archive,'r:gz') as tar:
 assert len(tar.getmembers())==len(members)
 for p,n in members:assert tar.extractfile(n).read()==p.read_bytes()
for suffix,text in [('.sha256',sha(archive)+'  '+archive.name+'\n'),('.bytes',str(archive.stat().st_size)+'\n'),('.contents.sha256',''.join(sha(p)+'  '+n+'\n' for p,n in members))]:
 with Path(str(archive)+suffix).open('x',encoding='ascii',newline='\n') as f:f.write(text)
receipt=dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION',request=bind(request),archive=bind(archive),installation_files=len(mapping),CPU_contracts=33,P3_status=p3['status'],COUPLE_D_request_created=False,readiness_recheck_required_before_execution=True,server_operations=0,training_started=False)
emit(O/'pending_request_receipt_v1.json',receipt);print(json.dumps(receipt,ensure_ascii=False,indent=2))
