"""Isolated H2 four-model native evaluator derivative; no model/dependency changes."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;P=S.parent/'H2_fourmodel_prediction_preparation_v1';H=S.parent/'H1_prediction_implementation_v1'
src=(H/'bcsp_p2_h1_twofold_predict_v1.py').read_text(encoding='utf-8');tree=ast.parse(src);repl={}
index=json.loads((P/'H2_C_D_fourmodel_input_index_v1.json').read_bytes());protocol=json.loads((P/'H2_fourmodel_native_prediction_protocol_v1.json').read_bytes());pins={}
for run in index['runs']:
 a=json.loads(Path(index['training_audit_evidence'][run['label']]['formal_audit']['path']).read_bytes())
 pins[run['label']]=dict(fold=run['fold'],mode=run['mode'],checkpoint=run['checkpoint'],request_sha256=run['training_request_sha256'],audit_sha256=run['training_freeze_audit_sha256'],audit_status=a['status'])
repl['validate_static_h1']='''def validate_static_h2(static,baseline_model):
 require(static['model']==baseline_model and static['H2']==dict(H2_COMMON,mode='AUX'),'original model, frozen H2 AUX template')
 require(not static['model'].get('coarse_geometry_guard',{}).get('enabled',False),'H1 off')
'''
repl['validate_model_h1']='''def validate_model_h2(model,mode):
 require(mode in ('AUX','COUPLE') and model.h2_metadata()==dict(H2_COMMON,mode=mode),'exact H2 mode/constants')
 require(model.num_query==256 and model.num_points==8192 and model.factor==32 and model.decoder_type=='fc'
  and model.denoise_weight==0 and model.fine_coverage_weight==1 and model.fine_local_weight==0,'model contract')
 b=model.base_model
 require(b.center_num==[512,256] and b.encoder_type=='graph' and b.query_selection=='learned_only' and not b.use_denoise and not b.encoder_adapter.enabled and not model.scqr_contract.enabled,'backbone contract')
 require(all(getattr(model,k) is False for k in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']),'H1 and optional objectives off')
 require(sum(p.numel() for p in model.h2_range_head.parameters())==1025 and model._h2_controller.mode==mode and model._h2_controller.override is None,'native H2 head and no intervention')
'''
repl['validate_index']='''def validate_index(index,folds):
 runs,rows=index['runs'],index['inputs']
 require(index['schema']=='bcsp-p2-H2-fourmodel-development-index-v1' and len(runs)==4 and len(rows)==420 and [r['label'] for r in runs]==list(FROZEN_MODELS),'four model420')
 for run in runs:
  pin=FROZEN_MODELS[run['label']];f=pin['fold'];fold=folds['folds'][f];part=[r for r in rows if r['run']==run['label']]
  require(run['variant']=='M0' and run['fold']==f and run['mode']==pin['mode'] and run['H2']==dict(H2_COMMON,mode=pin['mode']) and run['seed']==0 and run['n_input']==run['n_output']==8192,'frozen H2 model')
  require(run['checkpoint']==pin['checkpoint'] and run['training_request_sha256']==pin['request_sha256'] and run['training_freeze_audit_sha256']==pin['audit_sha256'],'trained model pins')
  require(len(part)==105 and [r['case_id'] for r in part]==run['dev_case_ids']==fold['dev_case_ids'],'ordered105')
  require(len(fold['dev_sources'])==len(set(fold['dev_sources']))==21 and len(fold['train_sources'])==63 and not set(fold['train_sources'])&set(fold['dev_sources']),'source disjoint')
  require(run['dev_sources']==fold['dev_sources'] and run['train_sources']==fold['train_sources'],'source lists')
  from collections import Counter
  require(set(Counter(r['source_id'] for r in part).values())=={5} and set(r['source_id'] for r in part)==set(fold['dev_sources']),'five defects each source')
  for row in part:
   require(row['variant']=='M0' and row['fold']==f and row['H2_mode']==pin['mode'] and row['n_input']==8192 and row['source_id']=='train:'+row['case_id'].split('__')[1],'row identity')
   require(row['input']['path']==DATA_ROOTS[f]+'/'+row['case_id']+'_8192.npz','frozen storage');clean(row['input']['path'])
   n=row['normalization'];require(row['normalization_source']=='defective_bbox' and len(n['center'])==3 and n['scale']>0,'D-only frame')
 for f in ['C','D']:
  paired=[[{k:v for k,v in r.items() if k not in ('run','H2_mode')} for r in rows if r['run']==f+'_'+mode] for mode in ['AUX','COUPLE']]
  require(paired[0]==paired[1],'same-fold two-arm identical input rows')
 require(len({r['case_id'] for r in rows})==len({r['input']['path'] for r in rows})==210,'210 unique cases shared across arms')
 require(len({(r['run'],r['case_id']) for r in rows})==420 and not set(folds['folds']['C']['dev_sources'])&set(folds['folds']['D']['dev_sources']),'unique420 identities/C-D source disjoint')
 return runs,rows
'''
repl['validate_source']='''def validate_source(index,source,manifest):
 records={r['case_id']:r for r in manifest};require(len(records)==len(manifest)==420,'420 original manifest')
 for run in index['runs']:
  original=[r for r in source['inputs'] if r['run']==run['fold']+'_8192'];part=[r for r in index['inputs'] if r['run']==run['label']]
  require(len(part)==len(original)==105,'source105')
  for a,b in zip(part,original):
   require(all(a[k]==b[k] for k in ['case_id','source_id','input']),'original input provenance')
   m=records[a['case_id']];require(all(a[k]==m[k] for k in ['source_id','normalization','normalization_source','target_array_sha256']) and a['input']['sha256']==m['sha256'],'manifest frame/target')
'''
repl['validate_evidence']='''def validate_evidence(q,index):
 for run in index['runs']:
  pin=FROZEN_MODELS[run['label']];record=q['training_audits'][run['label']];require(record['sha256']==pin['audit_sha256'],'audit pin')
  a=bound(record);require(a['status']==pin['audit_status'] and a['request_sha256']==pin['request_sha256'] and a['checks_passed']==len(a['checks'])>0 and all(a['checks'].values()),'formal training audit')
  require(a['checkpoint']['sha256']==run['checkpoint']['sha256'] and a['checkpoint']['bytes']==run['checkpoint']['bytes'] and a['counts']==dict(updates=3900,traversals=100,case_exposures=31200,drops=300,metrics=3900,resources=3902),'frozen checkpoint/counts')
 for rec in q['implementation'].values():exact(rec)
 for rec in q['dependencies']:exact(rec)
 bound(q['numeric_policy']);p=bound(q['protocol']);p3=bound(q['P3'])
 require(p['forward_budget']==420 and p['model_order']==list(FROZEN_MODELS) and p['BNCal']==p['loss_calls']==p['backward']==p['optimizer_steps']==0,'native protocol')
 require(p3['status']=='LOCAL_H2_FOURMODEL_PREDICTION_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'],'final P3')
'''
repl['load_checkpoint']='''def load_checkpoint(torch,model,run):
 data=torch.load(exact(run['checkpoint']),map_location='cpu',weights_only=True)
 require(isinstance(data,dict) and data.get('stage')=='BCSP_INPUT_DENSITY_V1' and data.get('epoch')==99 and data.get('updates')==3900,'final frozen checkpoint metadata')
 require(data.get('H2')==dict(H2_COMMON,mode=run['mode'])==model.h2_metadata(),'checkpoint H2 mode/constants')
 require(isinstance(data.get('base_model'),dict),'checkpoint state dictionary')
 model.load_state_dict(data['base_model'],strict=True)
 del data;gc.collect()
'''
repl['load_p1_factory']='''def load_h2_builder(implementation):
 source_module('bcsp_mamba_encoder_v1',implementation['encoder'])
 factory=source_module('p1_frozen_factory',implementation['factory'])
 source_module('bcsp_h2_range_v1',implementation['h2_range'])
 adapter=source_module('bcsp_h2_model_adapter_v1',implementation['h2_adapter'])
 return factory,adapter
'''
lines=src.splitlines(keepends=True)
for n in sorted([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in repl],key=lambda n:n.lineno,reverse=True):lines[n.lineno-1:n.end_lineno]=[repl[n.name]]
src=''.join(lines);a=src.index('H1=dict(');b=src.index('DATA_ROOTS=',a)
constants='H2_COMMON='+repr(protocol['H2_common'])+'\nFROZEN_MODELS='+repr(pins)+'\nINDEX_SHA='+repr(hashlib.sha256((P/'H2_C_D_fourmodel_input_index_v1.json').read_bytes()).hexdigest())+'\nPROTOCOL_SHA='+repr(hashlib.sha256((P/'H2_fourmodel_native_prediction_protocol_v1.json').read_bytes()).hexdigest())+'\n'
src=src[:a]+constants+src[b:]
src=src.replace('bcsp-p2-H1-twofold-development-prediction-v1','bcsp-p2-H2-fourmodel-native-prediction-v1').replace("q['forward_budget']==210","q['forward_budget']==420").replace("for key in ('factory','encoder'):","for key in ('factory','encoder','h2_range','h2_adapter'):")
src=src.replace('validate_model_h1(model)','validate_model_h2(model,run[\'mode\'])').replace("load_checkpoint(torch,model,run['checkpoint'])","load_checkpoint(torch,model,run)")
src=src.replace("attempts<210","attempts<420").replace("attempts==successful==210","attempts==successful==420").replace('exact210 forwards','exact420 forwards')
old="append_event(geometry,dict(run=run['label'],case_id=row['case_id'],**geometry_summary(np,coarse,dense)))"
assert src.count(old)==1;src=src.replace(old,"append_event(geometry,dict(run=run['label'],case_id=row['case_id'],H2=native_h2_summary(np,model,run['mode']),**geometry_summary(np,coarse,dense)))")
src=src.replace("protocol['forward_budget']==210","protocol['forward_budget']==420").replace("logs/cranial_bcsp_mamba_p2_h1","logs/cranial_bcsp_mamba_p2")
src=src.replace("validate_static_h1(static,","validate_static_h2(static,").replace("factory=load_p1_factory(q['implementation'])","factory,adapter=load_h2_builder(q['implementation'])")
src=src.replace("def builder(run):return factory.build_model(lambda:model_class(EasyDict(static['model'])),run['variant'],seed=0)","def builder(run):return adapter.build_h2(factory,lambda:model_class(EasyDict(static['model'])),run['mode'],seed=0)")
src=src.replace("forwards=210","forwards=420").replace('P2_H1_TWOFOLD_210_FORWARD_COMPLETE','P2_H2_FOURMODEL_420_NATIVE_FORWARD_COMPLETE')
summary='''def native_h2_summary(np,model,mode):
 c=model._h2_controller.context
 require(model._h2_controller.override is None and c is not None and c['training'] is False and not c['consumed'] and c['log'] is None,'native eval context, no GT loss or intervention')
 def array(v):return v.detach().cpu().numpy().astype('float64')
 raw,used=array(c['raw'])[0],array(c['used'])[0];delta=array(c['delta']).flatten();scale=array(c['scale']).flatten()
 require(delta.shape==scale.shape==(1,) and np.isfinite(delta).all() and np.isfinite(scale).all(),'native one-condition record')
 def moments(x):
  mean=x.mean(0);return dict(centroid=mean.tolist(),radius=float(np.sqrt(((x-mean)**2).sum(1).mean())))
 return dict(mode=mode,delta=delta.tolist(),scale=scale.tolist(),raw=moments(raw),used=moments(used),condition_override=None,GT_read=False,loss_calls=0)

'''
assert src.count('def execute_pair(')==1;src=src.replace('def execute_pair(',summary+'def execute_pair(')
src=src.replace('P2 H1 C/D final models, exactly105 each; no baseline re-inference.','H2 AUX/COUPLE C/D, exactly4x105 Native forwards; no intervention or baseline re-inference.')
ast.parse(src)
with (S/'bcsp_h2_fourmodel_native_predict_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(src)
with (S/'source_derivation_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(parent= str((H/'bcsp_p2_h1_twofold_predict_v1.py').absolute()),parent_sha256=hashlib.sha256((H/'bcsp_p2_h1_twofold_predict_v1.py').read_bytes()).hexdigest(),entry_sha256=hashlib.sha256(src.encode()).hexdigest(),exact_source_reader_keys=['factory','encoder','h2_range','h2_adapter'],new_GPU_preflight=False,models=4,forwards=420),f,indent=2)
print('H2_FOURMODEL_ENTRY_PARSE_PASS')
