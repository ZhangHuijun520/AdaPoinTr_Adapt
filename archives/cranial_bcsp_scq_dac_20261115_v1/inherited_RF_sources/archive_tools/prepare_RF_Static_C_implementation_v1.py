"""Finite Static_C entry adaptation; frozen model/runtime sources remain unchanged."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent
B=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3'
O=R/'outputs/scq_rf_Static_C_implementation_20261114_v1';O.mkdir()
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_C_training_20261114_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,j):
 with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False)
old=B/'bcsp_scq_rf_Sref_C_training_entry_v3.py';src=old.read_text(encoding='utf-8')
assert rec(old)['sha256']=='bc01d750489002949bd442bcd806e8340d272ce7dfe16727ede8ee54f15d4adf'
s=src.replace('RF-stage S-ref Fold C isolated training entry','RF-Static Fold C isolated training entry')
s=s.replace("bcsp-scq-rf-Sref-C-training-request-v1","bcsp-scq-rf-Static-C-training-request-v1")
s=s.replace("q['arm']=='S-ref' and q['variant']=='S'","q['arm']=='RF-Static' and q['variant']=='RF-Static'")
s=s.replace("SCQ_RF_Sref_foldC_seed0_train_","SCQ_RF_Static_foldC_seed0_train_")
s=s.replace(" and q['paired_baseline'] is None,'scratch S-ref first without old B baseline'", ",'scratch RF-Static next after S-ref freeze'")
s=s.replace("'S-ref_C first run only'","'RF-Static_C only'")
s=s.replace('RF_SREF_C_TRAINING_ENTRY_LOCAL_P3_PASS','RF_STATIC_C_TRAINING_ENTRY_LOCAL_P3_PASS')
s=s.replace("for key in ('encoder','factory','lqi_decoder','lqi_factory','scq_residual','scq_factory','timezone'):","for key in ('encoder','factory','lqi_decoder','lqi_factory','scq_residual','scq_factory','timezone','rf_residual','rf_factory'):")
s=s.replace("require(q['static_config']==cuda['static_config'] and q['initialization']==cuda['initialization'],'original static and SCQ initialization')", "require(q['static_config']==cuda['static_config'] and q['initialization']==cuda['initialization'] and q['rf_initialization']==cuda['rf_initialization'],'original static and both frozen initializations')")
reference='''def validate_reference(q,common):
    b=q['paired_baseline']
    require(isinstance(b,dict) and set(b)=={'audit','construction','initialization','order_plan','exposure','request'},'formal S-ref reference fields')
    audit=bound(b['audit']);model=bound(b['construction']);init=bound(b['initialization']);exposure=bound(b['exposure']);reference=bound(b['request'])
    require(audit['status']=='FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS' and audit['arm']=='S-ref' and audit['fold']=='C' and all(audit['checks'].values()),'formal S-ref freeze')
    require(audit['request_sha256']==b['request']['sha256']=='6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88','exact reference request')
    require((audit['updates'],audit['traversals'],audit['exposures'],audit['drops'])==(3900,100,31200,300) and not any(audit[k] for k in ('BNCal','evaluation','resume')),'reference complete without later stages')
    for key,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order_plan','order_plan.json'),('exposure','exposure.json')]:
        require(all(b[key][k]==audit['artifacts']['output/'+name][k] for k in ('bytes','sha256')),'audited reference '+key)
    for key in ('identity','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','resources'):
        require(q[key]==reference[key],'paired reference '+key)
    require(b['order_plan']==q['order_plan'],'same order record')
    require(model['arm']=='S-ref' and model['common_initial_state_SHA256']==audit['common_initial_state_SHA256']==common,'same full S common initialization')
    require(init['seed']==0 and init['order_sha256']==audit['order_sha256']==exposure['order_sha256'],'reference seed and order')
    require(reference['paired_baseline'] is None,'reference is scratch S-ref')


'''
s=s.replace('def authorize(',reference+'def authorize(')
s=s.replace("admission,common=validate_admission(q)","admission,common=validate_admission(q);validate_reference(q,common);exact(q['rf_initialization'])")
s=s.replace("factory(model_builder,q['variant'],q['initialization'])","factory(model_builder,q['variant'],q['initialization'],q['rf_initialization'])")
s=s.replace("evidence['parent']['artificial_fixture'] is artificial_cpu","evidence['parent']['parent']['artificial_fixture'] is artificial_cpu")
s=s.replace("require(not hasattr(model.base_model,'rf'),'S-ref must not install RF second head')", "require(hasattr(model.base_model,'rf') and model.base_model.rf.variant=='RF-Static','Static second head required')")
s=s.replace("if not artificial_cpu:require(evidence['scq']['total_parameters']==40596676,'native S-ref parameter count')", "require(evidence['rf']['variant']=='RF-Static' and evidence['rf']['additional_parameters']==231171,'frozen RF head')\n    if not artificial_cpu:require(evidence['rf']['total_parameters']==40827847 and sum(p.numel() for p in model.parameters())==40827847,'native Static parameter count')")
s=s.replace("actual_new={r['name']:r['weight_decay'] for r in group_rows if r['name'].startswith('base_model.scq.')}","expected_new.update({'base_model.rf.V1.weight':.0005,'base_model.rf.V2.weight':.0005,'base_model.rf.V1.bias':0.,'base_model.rf.V2.bias':0.})\n    actual_new={r['name']:r['weight_decay'] for r in group_rows if r['name'].startswith(('base_model.scq.','base_model.rf.'))}")
s=s.replace("actual_new==(expected_new if q['variant']=='S' else {})","actual_new==expected_new")
s=s.replace("list(records.values())","list(records.values())")
s=s.replace("[*q['implementation'].values(),q['initialization']]","[*q['implementation'].values(),q['initialization'],q['rf_initialization']]")
anchor="factory=source_module('bcsp_scq_factory_v1',q['implementation']['scq_factory']);bridge=source_module('bcsp_scq_training_bridge_v1',q['implementation']['bridge']);runtime=source_module('scq_parent_training_runtime',q['implementation']['runtime'])"
assert anchor in s
s=s.replace(anchor,"source_module('bcsp_scq_factory_v1',q['implementation']['scq_factory']);source_module('bcsp_scq_rf_residual_v1',q['implementation']['rf_residual'])\n        factory=source_module('bcsp_scq_rf_factory_v1',q['implementation']['rf_factory']);bridge=source_module('bcsp_scq_training_bridge_v1',q['implementation']['bridge']);runtime=source_module('scq_parent_training_runtime',q['implementation']['runtime'])")
start=s.index('def scq_geometry(');end=s.index('\n\ndef dispatch_training(',start)
s=s[:start]+'''def scq_geometry(model,ret):
    import torch
    result=geometry_record(torch,ret);info=model.base_model._scq_last_info
    require(hasattr(model.base_model,'rf') and model.base_model.rf.variant=='RF-Static','Static logging model')
    require(torch.equal(info['Qused'],ret[0].detach()),'Q2 training return identity')
    require(torch.equal(info['N0'],info['N1']),'Static must reuse N0')
    def position(t):
        t=t.detach();center=t.mean(1)
        return dict(centroid=center.cpu().tolist(),radius=((t-center[:,None])**2).sum(-1).mean(1).sqrt().cpu().tolist())
    def delta(t):
        t=t.detach();norm=t.square().sum(-1).sqrt()
        return dict(centroid=t.mean(1).cpu().tolist(),mean_norm=norm.mean(1).cpu().tolist(),max_norm=norm.max(1).values.cpu().tolist())
    with torch.no_grad():
        result.update(Q0=position(info['Q0']),Q1=position(info['Q1']),Q2=position(info['Qused']),delta=delta(info['delta']),delta0=delta(info['delta0']),delta1=delta(info['delta1']),N0_N1_equal=True)
    return result
'''+s[end:]
entry=O/'bcsp_scq_rf_Static_C_training_entry_v1.py'
with entry.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
bridge_src=(B.parent/'bcsp_scq_rf_training_bridge_v1.py').read_text(encoding='utf-8')
bridge_src=bridge_src.replace('RF-stage S-ref caller bridge','RF-Static Fold C caller bridge')
bridge_src=bridge_src.replace("    if str(device)","    if not hasattr(model.base_model,'rf') or model.base_model.rf.variant!='RF-Static':\n        raise ValueError('RF-Static model required')\n    if str(device)")
bridge=O/'bcsp_scq_rf_Static_C_training_bridge_v1.py'
with bridge.open('x',encoding='utf-8',newline='\n') as f:f.write(bridge_src)
for file in [entry,bridge]:ast.parse(file.read_text(encoding='utf-8'));compile(file.read_text(encoding='utf-8'),str(file),'exec')
q=read(B/'pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json');mirror=read(B/'local_mirror_v3.json')
cq=read(Path(mirror[q['admission']['request']['path']]))
q=copy.deepcopy(q);q.update(schema='bcsp-scq-rf-Static-C-training-request-v1',status='DRAFT_NOT_EXECUTABLE',arm='RF-Static',variant='RF-Static',run_id='SCQ_RF_Static_foldC_seed0_train_20261114_v1')
q['output']='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/'+q['run_id']
q['implementation']['entry']=rec(entry,C+'/'+entry.name);q['implementation']['bridge']=rec(bridge,C+'/'+bridge.name)
for key in ['rf_residual','rf_factory']:q['implementation'][key]=cq['implementation'][key]
q['rf_initialization']=cq['rf_initialization']
baseline={}
for key,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order_plan','order_plan.json'),('exposure','exposure.json')]:
    local=B/'post_training_freeze_v1/output'/name
    server=q['order_plan']['path'] if key=='order_plan' else read(B/'pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json')['output']+'/'+name
    baseline[key]=rec(local,server);mirror[server]=str(local)
baseline['audit']=rec(B/'post_training_freeze_v1/freeze_verification_v1.json',C+'/Sref_C_formal_freeze_v1.json');mirror[baseline['audit']['path']]=str(B/'post_training_freeze_v1/freeze_verification_v1.json')
baseline['request']=rec(B/'pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json',read(B/'pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json')['launch_contract']['request_path'])
q['paired_baseline']=baseline;q.pop('supersedes',None);q.pop('limited_fix',None)
q['launch_attempt']=C+'/control/attempt_claim_v1.json'
q['launch_contract'].update(tmux_session='bcsp_scq_rf_Static_C_train_20261114_v1',request_path=C+'/SCQ_RF_Static_C_training_execution_request_v1.json',authorization_path=C+'/control/authorization_v1.json',runtime_path=C+'/control/runtime_v1.json',launcher_path=C+'/control/launch_once_v1.sh',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
mirror[q['implementation']['entry']['path']]=str(entry);mirror[q['implementation']['bridge']['path']]=str(bridge)
for key,local in [('rf_residual',R/'outputs/scq_rf_initialization_loader_20261114_v2/bcsp_scq_rf_residual_v2.py'),('rf_factory',R/'outputs/scq_rf_implementation_20261114_v1/bcsp_scq_rf_factory_v1.py')]:
    assert rec(local)['sha256']==q['implementation'][key]['sha256'];mirror[q['implementation'][key]['path']]=str(local)
local=R/'outputs/scq_rf_implementation_20261114_v1/initialization_v1.bin';assert rec(local)['sha256']==q['rf_initialization']['sha256'];mirror[q['rf_initialization']['path']]=str(local)
emit(O/'implementation_context_v1.json',dict(status='IMPLEMENTATION_CONTEXT_NOT_EXECUTION_REQUEST',candidate=q,mirror=mirror,expected_common='b7e5b640c1f0e709ab6697139db1267584266a51b4e0e29f2d5217bfd1236cc5'))
emit(O/'static_review_v1.json',dict(status='STATIC_C_ENTRY_BRIDGE_STATIC_PASS',entry=rec(entry),bridge=rec(bridge),parent=rec(old),model_runtime_and_formula_unchanged=True,source_read_roots_unchanged="roots=[root,entryroot,envroot,provider,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']" in s,changes=['Strict Static_C authorization and formal Sref reference binding','Admitted RF factory and both frozen initializers','Shared-S fingerprint excludes only RF; exact parameter/group contract','Qraw/Q1/Q2 and separate delta logs; Static N0 identity','Complete finite source and both initializer exact reads'],CPU_tests=0,server_operations=0))
print('STATIC_C_ENTRY_BRIDGE_AND_CONTEXT_PREPARED')
