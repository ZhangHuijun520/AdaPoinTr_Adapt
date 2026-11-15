"""Minimal Sref_D caller + versioned fold metadata; no model/runtime/server changes."""
from pathlib import Path
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent;B=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3'
O=R/'outputs/scq_rf_Sref_D_implementation_20261114_v1';O.mkdir()
C='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1'
def read(p):return json.loads(p.read_bytes())
def rec(p,path=None):return dict(path=path or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
qc=read(B/'pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json');mirror=read(B/'local_mirror_v3.json')
D=R/'outputs/cranial_bcsp_scq_foldD_training_preparation_20261113_v1';dq=read(D/'pending_transport_v1/payload/SCQ_B_FoldD_training_execution_request_v1.json');dctx=read(D/'FoldD_context_v1.json');mirror.update(dctx['mirror'])
oldpair_path=Path(mirror[qc['pair_contract']['path']]);oldpair=read(oldpair_path);pair=copy.deepcopy(oldpair)
old_fullpair=read(R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/SCQ_BS_CD_pair_contract_v1.json')
assert all(dq[k]==old_fullpair['FoldD'][k] for k in ['QC','order_plan','data_root'])
pair['FoldD']=copy.deepcopy(old_fullpair['FoldD'])
pair['metadata_extension']=dict(version=2,scope='Add exact pre-existing FoldD bindings only; no scientific or resource change',parent_sha256=rec(oldpair_path)['sha256'])
pair_path=O/'RF_six_run_contract_v2.json';emit(pair_path,pair)
ready=dict(status='LOCAL_METADATA_VERIFIED_FRESH_SERVER_CHECK_REQUIRED',fresh_reverification_required=True,fold='D',identity=qc['identity'],payload_arrays_read=0,current_server_checked=False,counts=dict(train_sources=63,train_cases=315,dev_sources=21,dev_cases=105),provenance='RF stage FoldD exact old QC/order/data bindings; old device readiness is historical only',before_execution='Fresh exact identity/provider/source/QC/order/train315 hash and resources required. No automatic rebind.')
ready_path=O/'RF_FoldD_metadata_readiness_v1.json';emit(ready_path,ready)
old=B/'bcsp_scq_rf_Sref_C_training_entry_v3.py';s=old.read_text(encoding='utf-8');assert rec(old)['sha256']=='bc01d750489002949bd442bcd806e8340d272ce7dfe16727ede8ee54f15d4adf'
s=s.replace('S-ref Fold C isolated','S-ref Fold D isolated').replace('Sref-C-training-request','Sref-D-training-request').replace("q['fold']=='C'","q['fold']=='D'").replace('S-ref_C first run only','S-ref_D only').replace('SCQ_RF_Sref_foldC_seed0_train_','SCQ_RF_Sref_foldD_seed0_train_').replace('RF_SREF_C_TRAINING_ENTRY_LOCAL_P3_PASS','RF_SREF_D_TRAINING_ENTRY_LOCAL_P3_PASS')
s=s.replace("q['QC']['fold_binding'],'C',8192)","q['QC']['fold_binding'],'D',8192)").replace("pair['FoldC']","pair['FoldD']").replace("fold='C'","fold='D'")
s=s.replace("ready['payload_arrays_read']==0,'fresh readiness required'", "ready['payload_arrays_read']==0 and ready['fold']=='D' and ready['identity']==q['identity'] and ready['current_server_checked'] is False,'fresh D readiness required'")
continuation='''def validate_continuation(q,common):
    expected={'Sref_C':('FORMAL_SCQ_RF_SREF_POST_TRAINING_FREEZE_AUDIT_PASS','S-ref',26),'Static_C':('FORMAL_RF_STATIC_C_TRAINING_PAIR_FREEZE_AUDIT_PASS','RF-Static',34),'Requery_C':('FORMAL_RF_REQUERY_C_TRAINING_PAIR_FREEZE_AUDIT_PASS','RF-Requery',43)}
    require(set(q['continuation_evidence'])==set(expected),'all three frozen C arms')
    for key,(status,arm,count) in expected.items():
        a=bound(q['continuation_evidence'][key])
        require(a['status']==status and a['arm']==arm and a['fold']=='C' and a['identity']==q['identity'] and a['check_count']==count and all(a['checks'].values()),'formal continuation '+key)
        require((a['updates'],a['traversals'],a['exposures'],a['drops'])==(3900,100,31200,300) and a['common_initial_state_SHA256']==common and not any(a[k] for k in ('BNCal','evaluation','resume')),'complete C counts and same initialization '+key)


'''
s=s.replace('def authorize(',continuation+'def authorize(').replace('admission,common=validate_admission(q)','admission,common=validate_admission(q);validate_continuation(q,common)')
entry=O/'bcsp_scq_rf_Sref_D_training_entry_v1.py'
with entry.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
ast.parse(s);compile(s,str(entry),'exec')
q=copy.deepcopy(qc);q.update(schema='bcsp-scq-rf-Sref-D-training-request-v1',status='DRAFT_NOT_EXECUTABLE',fold='D',run_id='SCQ_RF_Sref_foldD_seed0_train_20261114_v1')
q['output']='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/'+q['run_id'];q['implementation']['entry']=rec(entry,C+'/'+entry.name)
for key in ['QC','order_plan','data_root']:q[key]=copy.deepcopy(dq[key])
q['pair_contract']=rec(pair_path,C+'/'+pair_path.name);q['readiness']=rec(ready_path,C+'/'+ready_path.name)
q['continuation_evidence']={}
for key,path in [('Sref_C',B/'post_training_freeze_v1/freeze_verification_v1.json'),('Static_C',R/'outputs/scq_rf_Static_C_implementation_20261114_v1/post_training_freeze_v1/freeze_verification_v1.json'),('Requery_C',R/'outputs/scq_rf_Requery_C_implementation_20261114_v1/post_training_freeze_v1/freeze_verification_v1.json')]:
 r=rec(path,C+'/'+key+'_formal_freeze_v1.json');q['continuation_evidence'][key]=r;mirror[r['path']]=str(path)
q['launch_attempt']=C+'/control/attempt_claim_v1.json'
q['launch_contract'].update(tmux_session='bcsp_scq_rf_Sref_D_train_20261114_v1',request_path=C+'/SCQ_RF_Sref_D_training_execution_request_v1.json',authorization_path=C+'/control/authorization_v1.json',runtime_path=C+'/control/runtime_v1.json',launcher_path=C+'/control/launch_once_v1.sh',log=q['output']+'/launch.log',PID=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
q.pop('supersedes',None);q.pop('limited_fix',None)
for r,path in [(q['implementation']['entry'],entry),(q['pair_contract'],pair_path),(q['readiness'],ready_path)]:mirror[r['path']]=str(path)
# Conflicting old/new device mirrors must not silently change identical records.
for key,r in q['implementation'].items():
 p=Path(mirror[r['path']]);assert rec(p)['sha256']==r['sha256'] and p.stat().st_size==r['bytes']
emit(O/'implementation_context_v1.json',dict(status='IMPLEMENTATION_CONTEXT_NOT_EXECUTION_REQUEST',candidate=q,mirror=mirror,expected_common=pair['expected_Sref_common_state_SHA256'],parent_C_request=qc))
emit(O/'static_review_v1.json',dict(status='SREF_D_ENTRY_METADATA_STATIC_PASS',entry=rec(entry),parent=rec(old),bridge=dict(record=q['implementation']['bridge'],unchanged=True),matrix=rec(pair_path),readiness=rec(ready_path),model_runtime_and_formula_unchanged=True,source_read_roots_unchanged="roots=[root,entryroot,envroot,provider,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']" in s,changes=['D-only selection and identifiers','Versioned matrix adds frozen FoldD only','Current frozen identity readiness explicitly server-unverified','C trio freeze evidence required'],CPU_tests=0,server_operations=0))
# Reuse the verified S-ref CPU batch, changing only stage paths and D-specific cases.
test=(B.parent/'test_scq_rf_Sref_C_startup_chain_cpu_v4.py').read_text(encoding='utf-8')
test=test.replace("D=O/'cpu_startup_chain_batch_v4'","D=O/'cpu_Sref_D_batch_v1'")
test=test.replace("F=D/'ARTIFICIAL_FIXTURES'","F=D/'ARTIFICIAL_FIXTURES';BR=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1'")
test=test.replace("O/'startup_chain_binding_v3/bcsp_scq_rf_Sref_C_training_entry_v3.py'","O/'bcsp_scq_rf_Sref_D_training_entry_v1.py'").replace("O/'bcsp_scq_rf_training_bridge_v1.py'","BR/'bcsp_scq_rf_training_bridge_v1.py'").replace("O/'context_v1.json'","O/'implementation_context_v1.json'").replace('RF_SREF_C_TRAINING_ENTRY_LOCAL_P3_PASS','RF_SREF_D_TRAINING_ENTRY_LOCAL_P3_PASS').replace("('fold','D')","('fold','C')")
test=test.replace("status='RF_SREF_TRAINING_ENTRY_ARTIFICIAL_CPU_PASS'","status='RF_SREF_D_ENTRY_ARTIFICIAL_CPU_PASS'")
anchor="  allowed=e.payload_paths(str(F/'train_root'),selected)"
assert anchor in test
test=test.replace(anchor,"""  check('D exact source identity and canonical order',fold['train_case_ids']==plan['case_ids'] and e.sha(mirror[q['order_plan']['path']])==q['order_plan']['sha256'] and metadata.canonical_sha(plan)=='2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838')
  for field in ['QC','order_plan','data_root']:
   bad=copy.deepcopy(q);bad[field]=copy.deepcopy(ctx['parent_C_request'][field])
   reject('C fold asset rejected '+field,lambda bad=bad:authorize(bad))
  bad=copy.deepcopy(q);bad['continuation_evidence'].pop('Requery_C');reject('incomplete C trio rejected',lambda:authorize(bad))
"""+anchor)
test_path=O/'test_RF_Sref_D_entry_cpu_v1.py';ast.parse(test);compile(test,str(test_path),'exec')
with test_path.open('x',encoding='utf-8',newline='\n') as f:f.write(test)
print('SREF_D_ENTRY_METADATA_CPU_BATCH_STATIC_PASS_NOT_EXECUTED')
