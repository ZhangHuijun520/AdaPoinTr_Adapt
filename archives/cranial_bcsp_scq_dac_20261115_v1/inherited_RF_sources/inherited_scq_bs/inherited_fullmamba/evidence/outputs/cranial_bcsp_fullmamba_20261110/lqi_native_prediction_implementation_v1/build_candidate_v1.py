"""Bounded local adaptation of the frozen F0 Native entry and artificial tests."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent
B=S.parent
PRE=B/'lqi_native_prediction_preparation_v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,s):
 with (S/name).open('x',encoding='utf-8',newline='\n') as f:f.write(s)
index=read(PRE/'LQI_CD_Native_input_index_candidate_v1.json')
scope=PRE/'LQI_CD_210_Native_prediction_scope_v1.json'
pins={r['label']:dict(fold=r['fold'],checkpoint_sha256=r['checkpoint']['sha256'],request_sha256=r['training_request']['sha256'],audit_sha256=r['training_audit']['sha256'],audit_status='FORMAL_LQI_FOLD'+r['fold']+'_POST_TRAINING_FREEZE_AUDIT_PASS') for r in index['runs']}
source=B/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py'
s=source.read_text(encoding='utf-8')
for a,b in [('f0_decoder','lqi_decoder'),('f0_factory','lqi_factory'),('load_f0_builder','load_lqi_builder'),('bcsp-f0-twofold-native-prediction-v1','bcsp-lqi-twofold-native-prediction-v1'),('bcsp-f0-native-development-index-candidate-v1','bcsp-lqi-native-development-index-candidate-v1'),('F0-P-v2-implementation-v1','F0-LQI-implementation-v1'),('F0-P-v2','F0-LQI-v1'),('C_F0','C_LQI'),('D_F0','D_LQI'),('LOCAL_F0_NATIVE_PREDICTION_P3_PASS','LOCAL_LQI_NATIVE_PREDICTION_P3_PASS'),('F0_CD_210_NATIVE_FORWARD_COMPLETE','LQI_CD_210_NATIVE_FORWARD_COMPLETE')]:s=s.replace(a,b)
s=s.replace("INDEX_SHA='874f0c7b8e0a4dfc6d1c98682ba5302080b9e6853d69703c1035c708f1395e84'",'INDEX_SHA='+repr(sha(PRE/'LQI_CD_Native_input_index_candidate_v1.json')))
s=s.replace("PROTOCOL_SHA='0672b1fe5e0b81859613c2973d666ff4ef7dda5ec2d430c6d190d4245b054348'",'PROTOCOL_SHA='+repr(sha(scope)))
s=s.replace(" and q['selection']['sha256']==SELECTION_SHA",'')
s=s.replace("require(q['selection_registration_timing']=='RULE_PRETRAINING_LITERAL_IDS_PRE_NATIVE_NOT_PRETRAINING','honest registration timing')","require(q['scope_origin']=='EXACT_FROZEN_F0_DEVELOPMENT_CASES_NO_RESELECTION','scope provenance')")
start=s.index('FROZEN_MODELS=');end=s.index('\nLIMITS=',start)
s=s[:start]+'FROZEN_MODELS='+repr(pins)+s[end:]
s=s.replace("'1f06524683e952e72c28c13f8cc7c3feb2102cd7092ade17b0509346e0407f5c'",repr(sha(B/'lqi_implementation_v1/bcsp_lqi_decoder_v1.py')))
s=s.replace("'25336d7745386c56a23347b5c40a78f3c046ca297fbfd66574d2807bca76992f'",repr(sha(B/'lqi_implementation_v1/bcsp_lqi_factory_v1.py')))
start=s.index('def validate_index(');end=s.index('\ndef validate_source',start)
validator='''def validate_index(index,folds,selection=None):
 runs,rows=index['runs'],index['inputs']
 require(index['schema']=='bcsp-lqi-native-development-index-candidate-v1' and [r['label'] for r in runs]==['C_LQI','D_LQI'] and len(rows)==210,'twofold210 index')
 categories={'bilateral','frontoorbital','parietotemporal','random_1','random_2'}
 for run in runs:
  pin=FROZEN_MODELS[run['label']];f=pin['fold'];fold=folds['folds'][f];part=[r for r in rows if r['run']==run['label']]
  require(run['variant']=='F0-LQI-v1' and run['fold']==f and run['seed']==0 and run['n_input']==run['n_output']==8192,'LQI identity')
  suffix={'C':'20261111_v1','D':'20261111_v2'}[f]
  require(run['checkpoint']==dict(path='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_fold'+f+'_seed0_train_'+suffix+'/ckpt-last.pth',bytes=478810419,sha256=pin['checkpoint_sha256']),'frozen final LQI checkpoint')
  require(run['training_request']['sha256']==pin['request_sha256'] and run['training_audit']['sha256']==pin['audit_sha256'],'formal audit pins')
  require(len(part)==105 and [r['case_id'] for r in part]==run['dev_case_ids']==fold['dev_case_ids'],'ordered105')
  require(run['train_sources']==fold['train_sources'] and run['dev_sources']==fold['dev_sources'] and len(set(fold['dev_sources']))==21 and len(set(fold['train_sources']))==63 and not set(fold['dev_sources'])&set(fold['train_sources']),'source partition')
  require(set(Counter(r['source_id'] for r in part).values())=={5} and set(r['source_id'] for r in part)==set(fold['dev_sources']),'five defects/source')
  for row in part:
   require(row['variant']=='F0-LQI-v1' and row['fold']==f and row['n_input']==8192 and row['source_id']=='train:'+row['case_id'].split('__')[1] and row['defect_type']=='__'.join(row['case_id'].split('__')[2:]) and row['defect_type'] in categories,'row identity')
   require(row['input']['path']==DATA_ROOTS[f]+'/'+row['case_id']+'_8192.npz' and row['prediction_filename']=='predictions/'+run['label']+'__'+row['case_id']+'.npz' and row['save_coarse'] is True,'exact paths and all coarse')
   require(row['cache_context'] is False and row['save_full_decoder_trace'] is False,'Native only no mechanism caches')
   clean(row['input']['path']);n=row['normalization']
   require(row['normalization_source']=='defective_bbox' and len(n['center'])==3 and all(isinstance(v,(float,int)) and abs(v)<1e6 for v in n['center']) and 0<n['scale']<1e6,'D-only normalization')
 require(len({r['input']['path'] for r in rows})==len({(r['run'],r['case_id']) for r in rows})==210,'unique210')
 require(not set(runs[0]['dev_sources'])&set(runs[1]['dev_sources']),'disjoint C/D dev sources')
 return runs,rows
'''
s=s[:start]+validator+s[end:]
s=s.replace("require(p['forwards']==210 and p['no_repeat_GPU_preflight'] and p['separate_mechanism']['executed_in_this_scope'] is False,'Native scope')","require(p['inference']['forward_attempt_budget']==210 and p['numeric']['repeat_GPU_preflight'] is False and p['outputs']['context_caches']==p['outputs']['full_decoder_traces']==0,'Native scope')")
s=s.replace(" require(evidence['parent']['variant']=='M0'", " require(evidence['variant']=='F0-LQI-v1' and evidence['conditional_sequence']=='query_aligned_local_memory_interleaving' and evidence['trace_prefix_suffix_semantics']=='interleaved conditional query-position output' and evidence['additional_learned_parameters']==0,'LQI semantics')\n require(evidence['parent']['variant']=='M0'")
s=s.replace("len(files)==240,'exact210 predictions20 context10 traces'","len(files)==210,'exact210 Native predictions no caches'")
s=s.replace("validate_index(index,bound(q['fold_binding']),bound(q['selection']))","validate_index(index,bound(q['fold_binding']))")
s=s.replace('context_cases=20,trace_cases=10','context_cases=0,trace_cases=0')
s=s.replace('F0 C/D: exactly210','LQI C/D: exactly210')
put('bcsp_lqi_twofold_native_predict_v1.py',s)

t=(B/'Native_prediction_implementation_v1/test_f0_native_prediction_cpu_v1.py').read_text(encoding='utf-8')
for a,b in [('Native_prediction_preparation_v1','lqi_native_prediction_preparation_v1'),('bcsp_f0_twofold_native_predict_v1.py','bcsp_lqi_twofold_native_predict_v1.py'),('F0_CD_Native_input_index_candidate_v1.json','LQI_CD_Native_input_index_candidate_v1.json'),('F0_CD_210_Native_prediction_scope_draft_v1.json','LQI_CD_210_Native_prediction_scope_v1.json'),('f0_decoder','lqi_decoder'),('f0_factory','lqi_factory'),('load_f0_builder','load_lqi_builder'),('F0-P-v2-implementation-v1','F0-LQI-implementation-v1'),('F0-P-v2','F0-LQI-v1'),('bcsp-f0-twofold-native-prediction-v1','bcsp-lqi-twofold-native-prediction-v1'),('C_F0','C_LQI'),('D_F0','D_LQI'),('LOCAL_F0_NATIVE_PREDICTION_P3_PASS','LOCAL_LQI_NATIVE_PREDICTION_P3_PASS'),('F0_NATIVE_CPU_CONTRACT_PASS','LQI_NATIVE_CPU_CONTRACT_PASS')]:t=t.replace(a,b)
t=t.replace("O=S/'artificial_cpu_batch_v1'","O=S/'artificial_cpu_batch_v1'")
t=t.replace("selection=json.loads((PRE/'recipient_donor_registration_addendum_v1.json').read_bytes())","selection=None")
t=t.replace("bad=copy.deepcopy(selection);bad['literal_table_proven_frozen_before_training']=True;reject('09 no backdated registration',lambda:p.validate_index(index,folds,bad))", "bad=copy.deepcopy(index);bad['inputs'][0]['save_full_decoder_trace']=True;reject('09 extra trace denied',lambda:p.validate_index(bad,folds))")
t=t.replace(",selection=rec(PRE/'recipient_donor_registration_addendum_v1.json'),selection_registration_timing='RULE_PRETRAINING_LITERAL_IDS_PRE_NATIVE_NOT_PRETRAINING'",",scope_origin='EXACT_FROZEN_F0_DEVELOPMENT_CASES_NO_RESELECTION'")
t=t.replace("S.parent/'implementation_v1'/n","S.parent/'lqi_implementation_v1'/n")
t=t.replace("factory.F0Decoder.__module__=='bcsp_lqi_decoder_v1'","factory.F0Decoder.__module__=='bcsp_lqi_decoder_v1'")
t=t.replace('len(files)==240 and len(set(files))==240','len(files)==210 and len(set(files))==210')
t=t.replace("==20 and len(list((out/'traces').glob('*.npz')))==10","==0 and len(list((out/'traces').glob('*.npz')))==0")
t=t.replace("len(archive['members'])==244","len(archive['members'])==214")
t=t.replace('exact210 forward calls and240 npz','exact210 forward calls and210 npz').replace('exact20 context10 traces no extra forward','no context or trace caches no extra forward')
put('test_lqi_native_prediction_cpu_v1.py',t)
for n in ['bcsp_lqi_twofold_native_predict_v1.py','test_lqi_native_prediction_cpu_v1.py']:ast.parse((S/n).read_text(encoding='utf-8'))
put('static_review_v1.json',json.dumps(dict(status='STATIC_S0_S1_PASS',files=[dict(name=n,sha256=sha(S/n)) for n in ['bcsp_lqi_twofold_native_predict_v1.py','test_lqi_native_prediction_cpu_v1.py']],checks=dict(AST_parse=True,inert_main_guard=True,exact_LQI_source_loads=True,unchanged_210_and_resource_limits=True,no_server_operations=True)),indent=2)+'\n')
print('CANDIDATE_AND_STATIC_REVIEW_CREATED_NO_TEST_EXECUTED')
