"""Materialize one isolated twofold H1 prediction entry; no model/server execution."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
PREP=HERE.parent/'H1_prediction_preparation_v1'
P1=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104'
H=HERE.parent/'H1_implementation_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def emit(n,v):
 with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
idx=json.loads((PREP/'H1_C_D_input_index_candidate_v1.json').read_bytes())
idx.update(schema='bcsp-p2-H1-twofold-development-index-v1',status='FROZEN_FOR_SEPARATE_EXECUTION_AUTHORIZATION')
emit('H1_C_D_input_index_v1.json',idx)
protocol=json.loads((PREP/'H1_C_D_prediction_protocol_candidate_v1.json').read_bytes())
protocol.update(schema='bcsp-p2-H1-twofold-development-protocol-v1',status='FROZEN_PENDING_SEPARATE_EXECUTION_AUTHORIZATION')
emit('H1_C_D_prediction_protocol_v1.json',protocol)
pins={}
for f,req,audit in [('C',H/'first_FoldC_request_v1/transport_payload/M_H1_foldC_seed0_training_execution_request_v1.json',H/'post_training_freeze_audit_v1/audit_report_v1.json'),('D',H/'FoldD_request_v1/transport_payload/M_H1_foldD_seed0_training_execution_request_v1.json',H/'FoldD_request_v1/post_training_freeze_audit_v1/audit_report_v1.json')]:
 a=json.loads(audit.read_bytes());q=json.loads(req.read_bytes())
 assert a['request_sha256']==sha(req)
 pins[f]=dict(request_sha256=sha(req),audit_sha256=sha(audit),checkpoint_sha256=a['checkpoint']['sha256'],checkpoint_bytes=a['checkpoint']['bytes'],checkpoint_path=q['output']+'/ckpt-last.pth')
parent=P1/'paired_development_evaluator_v2/bcsp_p1_paired_predict_v2.py'
assert sha(parent)=='7f31ecddfed05bd49f3e42093b99477643ddce733dadbebb80f58d08f17f5d1c'
s=parent.read_text(encoding='utf-8')
def replace_fn(s,name,new):
 t=ast.parse(s);n=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
 lines=s.splitlines(keepends=True);return ''.join(lines[:n.lineno-1])+new+'\n\n'+''.join(lines[n.end_lineno:])
extra='''
H1=dict(enabled=True,mode='centroid_radius',weight=.1,smooth_l1_beta=.1,cvar_fraction=.1,eps=1e-6)
FROZEN_MODELS=__PINS__
INDEX_SHA='__INDEX_SHA__'
PROTOCOL_SHA='__PROTOCOL_SHA__'
DATA_ROOTS={'C':'/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points',
            'D':'/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points'}

def validate_static_h1(static,baseline_model):
 import copy
 original=copy.deepcopy(static['model'])
 require(original.pop('coarse_geometry_guard',None)==H1 and original==baseline_model,'H1-only model config')

def validate_model_h1(model):
 require(model.num_query==256 and model.num_points==8192 and model.factor==32 and model.decoder_type=='fc'
  and model.denoise_weight==0 and model.fine_coverage_weight==1 and model.fine_local_weight==0,'model contract')
 b=model.base_model
 require(b.center_num==[512,256] and b.encoder_type=='graph' and b.query_selection=='learned_only'
  and not b.use_denoise and not b.encoder_adapter.enabled and not model.scqr_contract.enabled,'backbone contract')
 require(all(getattr(model,k) is False for k in ['local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']),'unrelated optional objective')
 require(model.coarse_geometry_guard_enabled is True and model.coarse_geometry_guard_mode==H1['mode']
  and model.coarse_geometry_guard_weight==H1['weight'] and model.coarse_geometry_guard_beta==H1['smooth_l1_beta']
  and model.coarse_geometry_guard_cvar_fraction==H1['cvar_fraction'] and model.coarse_geometry_guard_eps==H1['eps'],'H1 attributes')
'''.replace('__PINS__',repr(pins)).replace('__INDEX_SHA__',sha(HERE/'H1_C_D_input_index_v1.json')).replace('__PROTOCOL_SHA__',sha(HERE/'H1_C_D_prediction_protocol_v1.json'))
s=s.replace("DEVELOPMENT_DATA_ROOT='/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points'",extra)
s=replace_fn(s,'authorize','''def authorize(qr,ar,rr):
 q=bound(qr);a=bound(ar);r=bound(rr)
 require(q['schema']=='bcsp-p2-H1-twofold-development-prediction-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','request type/status')
 require(q['forward_budget']==210 and q['batch_size']==1 and q['backward']==q['optimizer_steps']==q['BNCal']==q['loss_calls']==0,'prediction only budget')
 require(q['input_index']['sha256']==INDEX_SHA and q['protocol']['sha256']==PROTOCOL_SHA,'frozen input/protocol')
 require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and
  a['schema']=='bcsp-development-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate authorization')
 require(r==dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
 return q''')
s=replace_fn(s,'validate_index','''def validate_index(index,folds):
 runs=index['runs'];rows=index['inputs']
 require(index['schema']=='bcsp-p2-H1-twofold-development-index-v1' and index['status']=='FROZEN_FOR_SEPARATE_EXECUTION_AUTHORIZATION','index type')
 require(len(runs)==2 and len(rows)==210 and [r['label'] for r in runs]==['C_M_H1','D_M_H1'],'twofold210')
 for run,f in zip(runs,['C','D']):
  fold=folds['folds'][f];part=[r for r in rows if r['run']==run['label']];pin=FROZEN_MODELS[f]
  require(run['variant']=='M0' and run['fold']==f and run['seed']==0 and run['n_input']==run['n_output']==8192 and run['H1']==H1,'M-H1 model')
  require(run['checkpoint']==dict(path=pin['checkpoint_path'],bytes=pin['checkpoint_bytes'],sha256=pin['checkpoint_sha256'])
   and run['training_request_sha256']==pin['request_sha256'] and run['training_freeze_audit_sha256']==pin['audit_sha256'],'frozen trained model')
  require(len(part)==105 and [r['case_id'] for r in part]==run['dev_case_ids']==fold['dev_case_ids'],'ordered105 per fold')
  require(len(set(fold['dev_sources']))==21 and len(set(fold['train_sources']))==63 and not set(fold['dev_sources'])&set(fold['train_sources']),'source separation')
  require(run['dev_sources']==fold['dev_sources'] and run['train_sources']==fold['train_sources'],'source lists')
  from collections import Counter
  require(set(Counter(r['source_id'] for r in part).values())=={5} and set(r['source_id'] for r in part)==set(fold['dev_sources']),'five defects/source')
  for row in part:
   require(row['variant']=='M0' and row['fold']==f and row['n_input']==8192 and row['source_id']=='train:'+row['case_id'].split('__')[1],'row identity')
   require(row['input']['path']==DATA_ROOTS[f]+'/'+row['case_id']+'_8192.npz','exact original storage');clean(row['input']['path'])
   n=row['normalization'];require(row['normalization_source']=='defective_bbox' and len(n['center'])==3 and isinstance(n['scale'],(int,float)) and n['scale']>0,'D-only frame')
 require(len({r['case_id'] for r in rows})==len({r['input']['path'] for r in rows})==210,'unique210')
 require(not set(runs[0]['dev_sources'])&set(runs[1]['dev_sources']),'C/D dev disjoint')
 return runs,rows''')
s=replace_fn(s,'validate_source','''def validate_source(index,source,manifest):
 records={r['case_id']:r for r in manifest};require(len(records)==len(manifest)==420,'420 manifest')
 for f in ['C','D']:
  original=[r for r in source['inputs'] if r['run']==f+'_8192'];part=[r for r in index['inputs'] if r['fold']==f]
  require(len(original)==len(part)==105,'source105 per fold')
  for a,b in zip(part,original):
   require(all(a[k]==b[k] for k in ['case_id','source_id','input']),'original input provenance')
   m=records[a['case_id']]
   require(all(a[k]==m[k] for k in ['source_id','normalization','normalization_source','target_array_sha256']) and a['input']['sha256']==m['sha256'],'manifest frame/target')''')
s=replace_fn(s,'validate_evidence','''def validate_evidence(q,index):
 for run in index['runs']:
  f=run['fold'];pin=FROZEN_MODELS[f];rec=q['training_audits'][f];require(rec['sha256']==pin['audit_sha256'],'audit pin')
  audit=bound(rec)
  require(audit['status']=='FORMAL_P2_H1_FOLD'+f+'_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS'
   and audit['request_sha256']==pin['request_sha256'] and audit['checks_passed']==len(audit['checks'])>0 and all(audit['checks'].values()),'formal H1 audit')
  require(audit['checkpoint']['sha256']==run['checkpoint']['sha256'] and audit['checkpoint']['bytes']==run['checkpoint']['bytes'],'checkpoint audit')
  require(audit['counts']['counts']['step']==3900 and audit['counts']['traversals']==100 and audit['counts']['exposures']==31200
   and audit['order']['drops']==300 and audit['pairing']['full3900_batch_and_schedule_match'] is True,'training paired counts')
 for rec in q['implementation'].values():exact(rec)
 for rec in q['dependencies']:exact(rec)
 bound(q['numeric_policy']);protocol=bound(q['protocol']);p3=bound(q['P3'])
 require(protocol['forward_budget']==210 and protocol['models']==['C_M_H1','D_M_H1'] and protocol['BNCal']==0,'twofold protocol')
 require(p3['status']=='LOCAL_H1_TWOFOLD_PREDICTION_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'],'final P3 entry')''')
assert s.count('model,construction=builder(run);helper.validate_model(model)')==1
s=s.replace('model,construction=builder(run);helper.validate_model(model)','model,construction=builder(run);validate_model_h1(model)')
s=s.replace("if row['case_id'] in representatives:arrays['coarse']=coarse[0]","if row['case_id'] in representatives[run['fold']]:arrays['coarse']=coarse[0]")
s=s.replace("fold='C',n_input=8192","fold=run['fold'],n_input=8192")
s=s.replace("'/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1'","'/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p2_h1'")
s=s.replace("require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'unchanged model config');transformer.enable_bcsp_knn()","validate_static_h1(static,yaml.safe_load((root/'base_model.yaml').read_text())['model']);transformer.enable_bcsp_knn()")
s=s.replace("protocol['coarse_tensor_cases']","protocol['coarse_tensor_cases_by_fold']")
s=s.replace("status='P1_PAIR_210_FORWARD_COMPLETE'","status='P2_H1_TWOFOLD_210_FORWARD_COMPLETE'")
s=s.replace('P1 T0/M0 frozen final models, 210 native development predictions.','P2 H1 C/D final models, exactly105 each; no baseline re-inference.')
ast.parse(s)
with (HERE/'bcsp_p2_h1_twofold_predict_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
emit('source_derivation_v1.json',dict(parent=dict(path=str(parent),sha256=sha(parent)),entry_sha256=sha(HERE/'bcsp_p2_h1_twofold_predict_v1.py'),model_pins=pins,implemented=True,tested=False,server_operations=0))
print('H1 twofold isolated entry created; not tested or deployed.')
