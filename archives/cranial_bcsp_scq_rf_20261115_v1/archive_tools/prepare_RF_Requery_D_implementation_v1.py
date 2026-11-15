"""Minimal D-fold caller; model initialization provenance is separate from fold order."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1';DB=R/'outputs/scq_rf_Sref_D_implementation_20261114_v1'
O=R/'outputs/scq_rf_Requery_D_implementation_20261115_v1';O.mkdir()
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_D_training_20261115_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
old=B/'bcsp_scq_rf_Requery_C_training_entry_v1.py';s=old.read_text(encoding='utf-8');assert rec(old)['sha256']=='26be687df4a74a71d45237402e91523750d8d089409d2e372c70ebef1d3c38f1'
s=s.replace('RF-Requery Fold C isolated','RF-Requery Fold D isolated').replace('Requery-C-training-request','Requery-D-training-request').replace("q['fold']=='C'","q['fold']=='D'").replace('RF-Requery_C only','RF-Requery_D only').replace('SCQ_RF_Requery_foldC_seed0_train_','SCQ_RF_Requery_foldD_seed0_train_').replace('RF_REQUERY_C_TRAINING_ENTRY_LOCAL_P3_PASS','RF_REQUERY_D_TRAINING_ENTRY_LOCAL_P3_PASS')
s=s.replace("audit['arm']=='S-ref' and audit['fold']=='C'","audit['arm']=='S-ref' and audit['fold']=='D' and audit['check_count']==30")
s=s.replace('6370a9887893b510c95850616eb664198982131df67d5e9a06ae725f9b860a88','888ad3b1a519d26ba907b061643e602aafe42df0e0006c7d0606d242e9a5c00d')
s=s.replace("q['QC']['fold_binding'],'C',8192)","q['QC']['fold_binding'],'D',8192)").replace("pair['FoldC']","pair['FoldD']").replace("fold='C'","fold='D'")
s=s.replace("ready['payload_arrays_read']==0,'fresh readiness required'", "ready['payload_arrays_read']==0 and ready['fold']=='D' and ready['identity']==q['identity'] and ready['current_server_checked'] is False,'fresh D readiness required'")
start=s.index('def validate_static_reference(');end=s.index('\n\ndef authorize(',start)
validation='''def validate_rf_initialization_reference(q,common):
    b=q['initialization_reference']
    require(isinstance(b,dict) and set(b)=={'audit','construction','initialization','request'},'RF model-initialization reference fields')
    audit=bound(b['audit']);model=bound(b['construction']);init=bound(b['initialization']);reference=bound(b['request'])
    require(audit['status']=='FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS' and audit['arm']=='RF-Static' and audit['fold']=='C' and audit['check_count']==34 and all(audit['checks'].values()),'formal RF initial model provenance')
    require(audit['request_sha256']==b['request']['sha256']=='a3275c69e78f95d59358ba8c621c63cb053b54b97467c8583e67feedb2b1051f','exact RF reference request')
    for key,name in [('construction','model_construction.json'),('initialization','initialization.json')]:
        require(all(b[key][k]==audit['artifacts']['output/'+name][k] for k in ('bytes','sha256')),'audited RF initialization '+key)
    for key in ('science','identity','model_root','static_config','preflight_scope','dependencies','environment','initialization','rf_initialization','resources','admission'):
        require(q[key]==reference[key],'same RF model contract '+key)
    for key,r in reference['implementation'].items():
        if key not in ('entry','bridge'):require(q['implementation'][key]==r,'same RF source '+key)
    require(model['common_initial_state_SHA256']==audit['common_initial_state_SHA256']==common,'same RF reference S state')
    require(q['expected_model_initialization']=={k:init[k] for k in ('parameter_sha256','persistent_state_sha256','seed')} and init['seed']==0,'RF model fingerprints only, no C order transplant')


'''
s=s[:start]+validation+s[end:]
dp=(DB/'bcsp_scq_rf_Sref_D_training_entry_v1.py').read_text(encoding='utf-8')
continuation=dp[dp.index('def validate_continuation('):dp.index('def authorize(')]
s=s.replace('def authorize(',continuation+'def authorize(')
s=s.replace('validate_static_reference(q,common);exact', 'validate_rf_initialization_reference(q,common);validate_continuation(q,common);exact')
s=s.replace("q['expected_full_initialization']","q['expected_model_initialization']")
s=s.replace('same full Static initial parameters and buffers','same frozen RF initial parameters and buffers; D order is separate')
entry=O/'bcsp_scq_rf_Requery_D_training_entry_v1.py'
with entry.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
ast.parse(s);compile(s,str(entry),'exec')
cq=read(B/'pending_transport_v1/payload/SCQ_RF_Requery_C_training_execution_request_v1.json');dq=read(DB/'pending_transport_v1/payload/SCQ_RF_Sref_D_training_execution_request_v1.json')
mirror=read(B/'final_local_mirror_v1.json');mirror.update(read(DB/'final_local_mirror_v1.json'))
q=copy.deepcopy(cq);q.update(schema='bcsp-scq-rf-Requery-D-training-request-v1',status='DRAFT_NOT_EXECUTABLE',fold='D',run_id='SCQ_RF_Requery_foldD_seed0_train_20261115_v1')
q['output']='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/'+q['run_id'];q['implementation']['entry']=rec(entry,C+'/'+entry.name);mirror[q['implementation']['entry']['path']]=str(entry)
for key in ['QC','order_plan','data_root','pair_contract','readiness','continuation_evidence']:q[key]=copy.deepcopy(dq[key])
b={}
for key,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order_plan','order_plan.json'),('exposure','exposure.json')]:
 p=DB/'post_training_freeze_v1/output'/name;server=q['order_plan']['path'] if key=='order_plan' else dq['output']+'/'+name;b[key]=rec(p,server);mirror[server]=str(p)
p=DB/'post_training_freeze_v1/freeze_verification_v1.json';b['audit']=rec(p,C+'/Sref_D_formal_freeze_v1.json');mirror[b['audit']['path']]=str(p)
b['request']=rec(DB/'pending_transport_v1/payload/SCQ_RF_Sref_D_training_execution_request_v1.json',dq['launch_contract']['request_path']);q['paired_baseline']=b
q['initialization_reference']={k:r for k,r in cq['paired_static'].items() if k in ('audit','construction','initialization','request')}
q['expected_model_initialization']={k:cq['expected_full_initialization'][k] for k in ['parameter_sha256','persistent_state_sha256','seed']}
q.pop('paired_static');q.pop('expected_full_initialization');q.pop('training_reference',None)
q['launch_attempt']=C+'/control/attempt_claim_v1.json'
q['launch_contract'].update(tmux_session='bcsp_scq_rf_Requery_D_train_20261115_v1',request_path=C+'/SCQ_RF_Requery_D_training_execution_request_v1.json',authorization_path=C+'/control/authorization_v1.json',runtime_path=C+'/control/runtime_v1.json',launcher_path=C+'/control/launch_once_v1.sh',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
for r in q['implementation'].values():assert rec(Path(mirror[r['path']]))['sha256']==r['sha256']
emit(O/'implementation_context_v1.json',dict(status='IMPLEMENTATION_CONTEXT_NOT_EXECUTION_REQUEST',candidate=q,mirror=mirror,parent_C_request=cq,parent_Sref_D_request=dq,expected_common=read(DB/'post_training_freeze_v1/freeze_verification_v1.json')['common_initial_state_SHA256']))
emit(O/'static_review_v1.json',dict(status='REQUERY_D_ENTRY_STATIC_PASS',entry=rec(entry),parent=rec(old),bridge=dict(record=q['implementation']['bridge'],unchanged=True),model_runtime_and_formula_unchanged=True,source_read_roots_unchanged="roots=[root,entryroot,envroot,provider,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']" in s,changes=['D-only authorization/data/order/logs','Sref_D formal reference and C continuation evidence','C RF model initialization provenance only; never C data/order or prerequisite Static_D','Original RF branch, bridge, runtime and guard preserved'],CPU_tests=0,server_operations=0))
# Targeted CPU batch: preserve all proven computation/read-chain checks and adapt fold contracts.
t=(B/'test_RF_Requery_C_entry_cpu_v1.py').read_text(encoding='utf-8')
t=t.replace("F=D/'ARTIFICIAL_FIXTURES'","F=D/'ARTIFICIAL_FIXTURES';BR=R/'outputs/scq_rf_Requery_C_implementation_20261114_v1'")
t=t.replace('cpu_requery_entry_batch_v1','cpu_requery_D_entry_batch_v1').replace('bcsp_scq_rf_Requery_C_training_entry_v1.py','bcsp_scq_rf_Requery_D_training_entry_v1.py').replace('RF_REQUERY_C','RF_REQUERY_D')
t=t.replace("O/'bcsp_scq_rf_Requery_C_training_bridge_v1.py'","BR/'bcsp_scq_rf_Requery_C_training_bridge_v1.py'")
t=t.replace("('fold','D')","('fold','C')").replace("'paired_static'","'initialization_reference'").replace("'expected_full_initialization'","'expected_model_initialization'")
anchor="  script=e.render_launcher(q,'a'*64,'b'*64,'c'*64)"
extra="""  for field in ['QC','order_plan','data_root']:
   bad=copy.deepcopy(q);bad[field]=copy.deepcopy(ctx['parent_C_request'][field])
   reject('C fold asset refused '+field,lambda bad=bad:authorize(bad))
  bad=copy.deepcopy(q);bad['continuation_evidence'].pop('Requery_C');reject('C continuation evidence incomplete refused',lambda:authorize(bad))
  check('no Static_D dependency; model identity separate from order','paired_static' not in q and set(q['expected_model_initialization'])=={'parameter_sha256','persistent_state_sha256','seed'} and metadata.canonical_sha(plan)=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838')
"""
assert t.count(anchor)==1;t=t.replace(anchor,extra+anchor)
test=O/'test_RF_Requery_D_entry_cpu_v1.py';ast.parse(t);compile(t,str(test),'exec')
with test.open('x',encoding='utf-8',newline='\n') as f:f.write(t)
print('REQUERY_D_ENTRY_AND_CPU_BATCH_STATIC_PASS_NOT_EXECUTED')
