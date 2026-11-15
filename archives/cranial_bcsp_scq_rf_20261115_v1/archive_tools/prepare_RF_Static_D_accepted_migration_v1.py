"""Specific accepted device migration + final Static_D caller; no general identity framework."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Requery_D_implementation_20261115_v1';SB=R/'outputs/scq_rf_Static_C_implementation_20261114_v1'
O=R/'outputs/scq_rf_Static_D_implementation_20261115_v1';O.mkdir()
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False)
rq=read(B/'pending_transport_v1/payload/SCQ_RF_Requery_D_training_execution_request_v1.json');mirror=read(B/'final_local_mirror_v1.json')
resource_path=R/'outputs/scq_rf_Static_D_request_preparation_20261115_v1/current_resource_identity_v1.json';resource=read(resource_path)
historical=copy.deepcopy(rq['identity']);current=copy.deepcopy(historical)
current.update(hostname=resource['hostname'],gpu_uuid=resource['GPU'][0],gpu_name=resource['GPU'][1],driver_version=resource['GPU'][2],nvidia_smi_memory_total_MiB=int(resource['GPU'][3]),python_realpath=resource['python_realpath'],python_version=resource['python_version'])
changed={k for k in historical if historical[k]!=current[k]};assert changed=={'hostname','gpu_uuid','driver_version'}
migration=dict(status='USER_ACCEPTED_STATIC_D_CROSS_DEVICE_CONTINUATION_NOT_EXECUTION_AUTHORIZATION',historical_identity=historical,current_identity=current,allowed_changed_fields=sorted(changed),user_acceptance='接受上述跨设备延续限制，并授权Static_D最小入口与身份适配、CPU验证及P3，通过后创建待授权request',acceptance_date='2026-11-15',execution_authorized=False,resource_observation=rec(resource_path),model_or_science_changes=False,
 interpretation=dict(C_pair='SAME_DEVICE_PRIMARY_MECHANISM_EVIDENCE',D_Static_vs_Requery='DEVICE_AND_DRIVER_CONFOUNDED_SUPPLEMENTARY_EVIDENCE',strict_same_device_D_pair=False,do_not_attribute_all_differences_to_requery=True),
 restrictions=['Only this Static_D run and these exact old/new identities; no automatic rebind','All other source/initializer/data/order/numeric/software-version/resource guards preserved','Historical CUDA result supports model implementation only; current hardware CUDA compatibility has not been retested','No automatic retry/resume or matching retraining; final full-hash execution authorization still required'])
mp=O/'Static_D_accepted_device_migration_v1.json';emit(mp,migration);mh=rec(mp)['sha256']
old=B/'bcsp_scq_rf_Requery_D_training_entry_v1.py';s=old.read_text(encoding='utf-8');assert rec(old)['sha256']==rq['implementation']['entry']['sha256']
s=s.replace('RF-Requery Fold D isolated','RF-Static Fold D isolated').replace('Requery-D-training-request','Static-D-training-request').replace('RF-REQUERY','RF-STATIC').replace('RF_REQUERY_D','RF_STATIC_D').replace("q['arm']=='RF-Requery'","q['arm']=='RF-Static'").replace("q['variant']=='RF-Requery'","q['variant']=='RF-Static'").replace('RF-Requery_D only','RF-Static_D only').replace('SCQ_RF_Requery_foldD_seed0_train_','SCQ_RF_Static_foldD_seed0_train_').replace("model.base_model.rf.variant=='RF-Requery'","model.base_model.rf.variant=='RF-Static'").replace("evidence['rf']['variant']=='RF-Requery'","evidence['rf']['variant']=='RF-Static'")
# Historical artifacts retain their original identity; current identity is pinned separately.
s=s.replace("for key in ('identity','model_root','preflight_scope','dependencies','environment'):","require(q['historical_identity']==cuda['identity'],'historical CUDA identity')\n    for key in ('model_root','preflight_scope','dependencies','environment'):")
s=s.replace("audit['identity']==q['identity']", "audit['identity']==q['historical_identity']").replace("a['identity']==q['identity']", "a['identity']==q['historical_identity']")
s=s.replace("('identity','data_root'","('data_root'")
s=s.replace("pair['identity']==q['identity']","pair['identity']==q['historical_identity']")
s=s.replace('validate_rf_initialization_reference(q,common);','validate_requery_reference(q,common);')
start=s.index('def validate_rf_initialization_reference(');end=s.index('def validate_continuation(',start)
s=s[:start]+'''def validate_requery_reference(q,common):
    b=q['paired_requery']
    require(isinstance(b,dict) and set(b)=={'audit','construction','initialization','order_plan','exposure','request'},'Requery D pair fields')
    audit=bound(b['audit']);model=bound(b['construction']);init=bound(b['initialization']);exp=bound(b['exposure']);reference=bound(b['request'])
    require(audit['status']=='FORMAL_RF_REQUERY_D_TRAINING_PAIR_FREEZE_AUDIT_PASS' and audit['arm']=='RF-Requery' and audit['fold']=='D' and audit['check_count']==43 and all(audit['checks'].values()),'formal Requery D freeze')
    require(audit['request_sha256']==b['request']['sha256']=='4a79f67d7ce29b453343d9bedc27841030d4c6223eb7bfe02d3af1d1bed9f6ed' and audit['identity']==q['historical_identity'],'exact historical Requery D request and identity')
    require((audit['updates'],audit['traversals'],audit['exposures'],audit['drops'])==(3900,100,31200,300) and not any(audit[k] for k in ('BNCal','evaluation','resume')),'complete Requery D')
    for key,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order_plan','order_plan.json'),('exposure','exposure.json')]:
        require(all(b[key][k]==audit['artifacts']['output/'+name][k] for k in ('bytes','sha256')),'audited Requery D '+key)
    for key in ('science','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','rf_initialization','resources','admission'):
        require(q[key]==reference[key],'same Requery D science '+key)
    for key,r in reference['implementation'].items():
        if key not in ('entry','bridge'):require(q['implementation'][key]==r,'same Requery model source '+key)
    require(model['common_initial_state_SHA256']==audit['common_initial_state_SHA256']==common,'same Requery common S state')
    require(q['expected_model_initialization']=={k:init[k] for k in ('parameter_sha256','persistent_state_sha256','seed')} and init['order_sha256']==audit['order_sha256']==exp['order_sha256'],'same full Requery model initialization and D order')


'''+s[end:]
identity_fn='''def validate_execution_identity(q):
    require(q['accepted_device_migration']['sha256']==MIGRATION_SHA,'exact accepted migration supplement')
    m=bound(q['accepted_device_migration'])
    require(m['status']=='USER_ACCEPTED_STATIC_D_CROSS_DEVICE_CONTINUATION_NOT_EXECUTION_AUTHORIZATION' and m['execution_authorized'] is False and bool(m['user_acceptance']),'migration acceptance is not execution approval')
    require(q['historical_identity']==m['historical_identity'] and q['identity']==m['current_identity'],'exact old/new execution identities')
    changed=sorted(k for k in q['identity'] if q['identity'][k]!=q['historical_identity'][k])
    require(set(q['identity'])==set(q['historical_identity']) and changed==m['allowed_changed_fields']==['driver_version','gpu_uuid','hostname'],'only accepted hardware identity fields differ')
    require(q['comparison_qualification']==m['interpretation'] and not q['comparison_qualification']['strict_same_device_D_pair'],'disclose confounded D comparison')


'''
s=s.replace('def authorize(',identity_fn+'def authorize(').replace("q=bound(qr);a=bound(ar);runtime=bound(rr)","q=bound(qr);a=bound(ar);runtime=bound(rr);validate_execution_identity(q)")
s=s.replace("ADMISSION_SHA=", "MIGRATION_SHA="+repr(mh)+"\nADMISSION_SHA=",1)
s=s.replace("require(torch.equal(info['Qused'],ret[0].detach()),'Q2 training return identity')", "require(torch.equal(info['Qused'],ret[0].detach()),'Q2 training return identity')\n    require(torch.equal(info['N0'],info['N1']),'Static must reuse N0')")
s=s.replace("SSM_gradient_non_bitwise_reproducibility_disclosed=True)","SSM_gradient_non_bitwise_reproducibility_disclosed=True,cross_device_confounded_D_comparison=True,execution_identity=q['identity'],historical_pair_identity=q['historical_identity'])")
entry=O/'bcsp_scq_rf_Static_D_training_entry_v1.py'
with entry.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
ast.parse(s);compile(s,str(entry),'exec')
q=copy.deepcopy(rq);q.update(schema='bcsp-scq-rf-Static-D-training-request-v1',status='DRAFT_NOT_EXECUTABLE',arm='RF-Static',variant='RF-Static',identity=current,historical_identity=historical,run_id='SCQ_RF_Static_foldD_seed0_train_20261115_v1')
q['output']='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/'+q['run_id'];q['implementation']['entry']=rec(entry,C+'/'+entry.name);mirror[q['implementation']['entry']['path']]=str(entry)
sq=read(SB/'pending_transport_v1/payload/SCQ_RF_Static_C_training_execution_request_v1.json');q['implementation']['bridge']=sq['implementation']['bridge'];bridge=SB/'bcsp_scq_rf_Static_C_training_bridge_v1.py';assert rec(bridge)['sha256']==q['implementation']['bridge']['sha256'];mirror[q['implementation']['bridge']['path']]=str(bridge)
q['accepted_device_migration']=rec(mp,C+'/'+mp.name);mirror[q['accepted_device_migration']['path']]=str(mp);q['comparison_qualification']=migration['interpretation']
ready=read(Path(mirror[q['readiness']['path']]));ready.update(identity=current,provenance='Static_D user-accepted exact device migration; historical training identities preserved',current_server_checked=False)
ready_path=O/'Static_D_current_identity_readiness_v1.json';emit(ready_path,ready);q['readiness']=rec(ready_path,C+'/'+ready_path.name);mirror[q['readiness']['path']]=str(ready_path)
ref={}
for key,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order_plan','order_plan.json'),('exposure','exposure.json')]:
 p=B/'post_training_freeze_v2/output'/name;server=q['order_plan']['path'] if key=='order_plan' else rq['output']+'/'+name;ref[key]=rec(p,server);mirror[server]=str(p)
p=B/'post_training_freeze_v2/freeze_verification_v1.json';ref['audit']=rec(p,C+'/Requery_D_formal_freeze_v1.json');mirror[ref['audit']['path']]=str(p)
ref['request']=rec(B/'pending_transport_v1/payload/SCQ_RF_Requery_D_training_execution_request_v1.json',rq['launch_contract']['request_path']);q['paired_requery']=ref
q.pop('initialization_reference',None);q.pop('training_reference',None)
q['launch_attempt']=C+'/control/attempt_claim_v1.json'
q['launch_contract'].update(tmux_session='bcsp_scq_rf_Static_D_train_20261115_v1',request_path=C+'/SCQ_RF_Static_D_training_execution_request_v1.json',authorization_path=C+'/control/authorization_v1.json',runtime_path=C+'/control/runtime_v1.json',launcher_path=C+'/control/launch_once_v1.sh',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
for r in q['implementation'].values():assert rec(Path(mirror[r['path']]))['sha256']==r['sha256']
emit(O/'implementation_context_v1.json',dict(status='IMPLEMENTATION_CONTEXT_NOT_EXECUTION_REQUEST',candidate=q,mirror=mirror,parent_Requery_D_request=rq,expected_common=read(B/'post_training_freeze_v2/freeze_verification_v1.json')['common_initial_state_SHA256']))
emit(O/'static_review_v1.json',dict(status='STATIC_D_ENTRY_ACCEPTED_MIGRATION_STATIC_PASS',entry=rec(entry),parent=rec(old),bridge=dict(record=q['implementation']['bridge'],unchanged=True),accepted_migration=rec(mp),model_runtime_and_formula_unchanged=True,source_read_roots_unchanged="roots=[root,entryroot,envroot,provider,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']" in s,CPU_tests=0,server_operations=0))
print('STATIC_D_ENTRY_ACCEPTED_MIGRATION_STATIC_PASS')
