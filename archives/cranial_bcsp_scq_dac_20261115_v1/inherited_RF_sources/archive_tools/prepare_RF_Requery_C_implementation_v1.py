"""Minimal Requery_C caller adaptation. Frozen RF/model/runtime remain untouched."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Static_C_implementation_20261114_v1'
O=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1';O.mkdir()
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
old=B/'bcsp_scq_rf_Static_C_training_entry_v1.py';s=old.read_text(encoding='utf-8')
assert rec(old)['sha256']=='c457800917fbecd3fd3e7c38f73cc1971806a905dd874ecad3d3f96da3f9755f'
s=s.replace('RF-Static','RF-Requery').replace('Static-C','Requery-C').replace('Static_foldC','Requery_foldC').replace('RF_STATIC_C','RF_REQUERY_C').replace('Static logging model','Requery logging model').replace('native Static parameter count','native Requery parameter count')
s=s.replace("    require(torch.equal(info['N0'],info['N1']),'Static must reuse N0')\n",'')
s=s.replace('N0_N1_equal=True','N0_N1_equal=bool(torch.equal(info[\'N0\'],info[\'N1\'])),neighbor_set_overlap=((info[\'N0\'][...,None]==info[\'N1\'][...,None,:]).any(-1).float().mean((1,2))).cpu().tolist()')
reference='''def validate_static_reference(q,common):
    b=q['paired_static']
    require(isinstance(b,dict) and set(b)=={'audit','construction','initialization','order_plan','exposure','request'},'Static pair fields')
    audit=bound(b['audit']);model=bound(b['construction']);init=bound(b['initialization']);exp=bound(b['exposure']);reference=bound(b['request'])
    require(audit['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and audit['arm']=='RF-Static' and audit['fold']=='C' and all(audit['checks'].values()),'formal Static freeze')
    require(audit['request_sha256']==b['request']['sha256']=='a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f','exact Static reference request')
    require((audit['updates'],audit['traversals'],audit['exposures'],audit['drops'])==(3900,100,31200,300) and not any(audit[k] for k in ('BNCal','evaluation','resume')),'Static complete without later stages')
    for key,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order_plan','order_plan.json'),('exposure','exposure.json')]:
        require(all(b[key][k]==audit['artifacts']['output/'+name][k] for k in ('bytes','sha256')),'audited Static '+key)
    for key in ('science','identity','data_root','model_root','QC','order_plan','static_config','preflight_scope','dependencies','environment','pair_contract','initialization','rf_initialization','resources','admission'):
        require(q[key]==reference[key],'same Static '+key)
    for key,r in reference['implementation'].items():
        if key not in ('entry','bridge'):require(q['implementation'][key]==r,'same Static source '+key)
    require(b['order_plan']==q['order_plan'] and model['common_initial_state_SHA256']==audit['common_initial_state_SHA256']==common,'same Static order and S state')
    require(audit['paired_baseline_audit_sha256']==q['paired_baseline']['audit']['sha256'],'same frozen Sref evidence')
    require(q['expected_full_initialization']==init and init['seed']==0 and init['order_sha256']==audit['order_sha256']==exp['order_sha256'],'exact full Static initialization and order')


'''
s=s.replace('def authorize(',reference+'def authorize(')
s=s.replace('validate_reference(q,common);exact(q[\'rf_initialization\'])',"validate_reference(q,common);validate_static_reference(q,common);exact(q['rf_initialization'])")
anchor="    require(common_sha==expected_common,'same admitted common initialization')"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n    if not artificial_cpu:\n        require(helper.state_sha(model,True)==q['expected_full_initialization']['parameter_sha256'] and helper.state_sha(model)==q['expected_full_initialization']['persistent_state_sha256'],'same full Static initial parameters and buffers')")
entry=O/'bcsp_scq_rf_Requery_C_training_entry_v1.py'
with entry.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
bridge=O/'bcsp_scq_rf_Requery_C_training_bridge_v1.py'
with bridge.open('x',encoding='utf-8',newline='\n') as f:f.write((B/'bcsp_scq_rf_Static_C_training_bridge_v1.py').read_text(encoding='utf-8').replace('RF-Static','RF-Requery'))
q=read(B/'pending_transport_v1/payload/SCQ_RF_Static_C_training_execution_request_v1.json');parent=copy.deepcopy(q);mirror=read(B/'final_local_mirror_v1.json')
q.update(schema='bcsp-scq-rf-Requery-C-training-request-v1',status='DRAFT_NOT_EXECUTABLE',execution_authorized=False,arm='RF-Requery',variant='RF-Requery',run_id='SCQ_RF_Requery_foldC_seed0_train_20261114_v1')
q['output']='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/'+q['run_id'];q['implementation']['entry']=rec(entry,C+'/'+entry.name);q['implementation']['bridge']=rec(bridge,C+'/'+bridge.name)
mirror[q['implementation']['entry']['path']]=str(entry);mirror[q['implementation']['bridge']['path']]=str(bridge)
b={}
for key,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order_plan','order_plan.json'),('exposure','exposure.json')]:
 p=B/'post_training_freeze_v1/output'/name;server=q['order_plan']['path'] if key=='order_plan' else parent['output']+'/'+name;b[key]=rec(p,server);mirror[server]=str(p)
b['audit']=rec(B/'post_training_freeze_v1/freeze_verification_v1.json',C+'/Static_C_formal_freeze_v1.json');mirror[b['audit']['path']]=str(B/'post_training_freeze_v1/freeze_verification_v1.json')
b['request']=rec(B/'pending_transport_v1/payload/SCQ_RF_Static_C_training_execution_request_v1.json',parent['launch_contract']['request_path'])
q['paired_static']=b;q['expected_full_initialization']=read(B/'post_training_freeze_v1/output/initialization.json')
q['launch_attempt']=C+'/control/attempt_claim_v1.json'
q['launch_contract'].update(tmux_session='bcsp_scq_rf_Requery_C_train_20261114_v1',request_path=C+'/SCQ_RF_Requery_C_training_execution_request_v1.json',authorization_path=C+'/control/authorization_v1.json',runtime_path=C+'/control/runtime_v1.json',launcher_path=C+'/control/launch_once_v1.sh',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
q.pop('training_reference',None)
emit(O/'implementation_context_v1.json',dict(status='IMPLEMENTATION_CONTEXT_NOT_EXECUTION_REQUEST',candidate=q,mirror=mirror,expected_common=read(B/'post_training_freeze_v1/freeze_verification_v1.json')['common_initial_state_SHA256']))
for file in [entry,bridge]:ast.parse(file.read_text(encoding='utf-8'));compile(file.read_text(encoding='utf-8'),str(file),'exec')
emit(O/'static_review_v1.json',dict(status='REQUERY_C_ENTRY_BRIDGE_STATIC_PASS',entry=rec(entry),bridge=rec(bridge),parent=rec(old),model_runtime_and_formula_unchanged=True,source_read_roots_unchanged="roots=[root,entryroot,envroot,provider,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']" in s,changes=['Strict Requery_C gate and bridge variant','Bind both frozen Sref and Static evidence; full initial state equality before native training','Measure neighbor equality and set overlap; no difference threshold','Keep exact source/init guard and frozen RF sole arm branch'],CPU_tests=0,server_operations=0))
print('REQUERY_C_ENTRY_BRIDGE_CONTEXT_STATIC_PASS')
