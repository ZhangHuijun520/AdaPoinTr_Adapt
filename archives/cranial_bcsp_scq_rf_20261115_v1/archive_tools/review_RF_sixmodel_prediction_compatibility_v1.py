"""Finite local metadata/AST review; no imports of model code or server calls."""
from pathlib import Path, PurePosixPath
import ast, hashlib, json
R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1'
O.mkdir(exist_ok=True)
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,x):
 with (O/n).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
specs=[
 ('Sref_C','scq_rf_Sref_C_training_implementation_20261114_v1/startup_chain_binding_v3','pending_transport_v3/payload/SCQ_RF_Sref_C_training_execution_request_v3.json','post_training_freeze_v1/freeze_verification_v1.json'),
 ('Static_C','scq_rf_Static_C_implementation_20261114_v1','pending_transport_v1/payload/SCQ_RF_Static_C_training_execution_request_v1.json','post_training_freeze_v1/freeze_verification_v1.json'),
 ('Requery_C','scq_rf_Requery_C_implementation_20261114_v1','pending_transport_v1/payload/SCQ_RF_Requery_C_training_execution_request_v1.json','post_training_freeze_v1/freeze_verification_v1.json'),
 ('Sref_D','scq_rf_Sref_D_implementation_20261114_v1','pending_transport_v1/payload/SCQ_RF_Sref_D_training_execution_request_v1.json','post_training_freeze_v1/freeze_verification_v1.json'),
 ('Static_D','scq_rf_Static_D_implementation_20261115_v1/selector_diagnostic_hotfix_v2','pending_transport_v2/payload/SCQ_RF_Static_D_training_execution_request_v2.json','post_training_freeze_local_review_v2/freeze_verification_v1.json'),
 ('Requery_D','scq_rf_Requery_D_implementation_20261115_v1','pending_transport_v1/payload/SCQ_RF_Requery_D_training_execution_request_v1.json','post_training_freeze_v2/freeze_verification_v1.json')]
C=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload'
foldfile=C/'fold_binding.json';mf=C/'manifest_8192.jsonl';folds=read(foldfile)['folds'];manifest={v['case_id']:v for v in map(json.loads,mf.read_text(encoding='utf-8').splitlines())}
oldroot=R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2'
oldentry=oldroot/'bcsp_scq_fourmodel_native_predict_v2.py';oldindex=read(oldroot/'SCQ_BS_CD_input_index_v2.json');oldrows={(x['fold'],x['case_id']):x for x in oldindex['inputs']}
source=oldentry.read_text(encoding='utf-8');tree=ast.parse(source);nodes={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def body(name):return ast.get_source_segment(source,nodes[name])
assert "q['forward_budget']==420" in body('authorize') and 'B/S only' in body('build_scq_model')
assert 'strict=True' in body('load_checkpoint') and 'weights_only=True' in body('load_checkpoint')
assert 'attempts==successful==420' in body('execute_pair') and 'before==after' in body('execute_pair') and 'rng_before==rng_after' in body('execute_pair')
runs=[];rows=[];requests={};audits={}
for label,folder,request,audit in specs:
 h=R/'outputs'/folder;qp=h/request;ap=h/audit;q=read(qp);a=read(ap);arm,fold=label.split('_');variant={'Sref':'S','Static':'RF-Static','Requery':'RF-Requery'}[arm]
 assert a['status'].startswith('FORMAL_') and a['status'].endswith('_PASS') and a['check_count']==len(a['checks']) and all(a['checks'].values())
 assert a['variant']==q['variant']==variant and a['fold']==q['fold']==fold and a['request_sha256']==rec(qp)['sha256'] and a['identity']==q['identity']
 assert (a['updates'],a['traversals'],a['exposures'],a['drops'])==(3900,100,31200,300) and not any(a[k] for k in ['BNCal','evaluation','resume'])
 assert rec(foldfile)['sha256']==q['QC']['fold_binding']['sha256'] and rec(mf)['sha256']==q['QC']['manifests']['8192']['sha256']
 f=folds[fold];assert len(f['dev_case_ids'])==105 and len(f['dev_sources'])==21 and not set(f['train_sources'])&set(f['dev_sources'])
 checkpoint=dict(path=q['output']+'/ckpt-last.pth',**a['checkpoint'])
 runs.append(dict(label=label,variant=variant,factory_variant='S' if arm=='Sref' else variant,fold=fold,seed=0,n_input=8192,n_output=8192,checkpoint=checkpoint,training_request=rec(qp),training_audit=rec(ap),training_identity=q['identity'],dev_case_ids=f['dev_case_ids'],initialization=q['initialization'],rf_initialization=q.get('rf_initialization')))
 requests[label]=q;audits[label]=a
 for cid in f['dev_case_ids']:
  m=manifest[cid];old=oldrows[fold,cid];assert old['input']['sha256']==m['sha256'] and old['normalization']==m['normalization'] and m['normalization_source']=='defective_bbox'
  p=PurePosixPath(m['point_path']);assert not p.is_absolute() and '..' not in p.parts
  rows.append(dict(run=label,variant=variant,fold=fold,case_id=cid,source_id=m['source_id'],defect_type=cid.split('__',2)[2],input=dict(path=str(PurePosixPath(q['data_root'])/p),bytes=old['input']['bytes'],sha256=m['sha256']),normalization=m['normalization'],normalization_source='defective_bbox',prediction_filename='predictions/'+label+'__'+cid+'.npz',n_input=8192,n_output=8192,cache_context=False,save_full_decoder_trace=False))
assert len(rows)==630 and len({(x['run'],x['case_id']) for x in rows})==630 and len({(x['fold'],x['case_id']) for x in rows})==210 and len({x['input']['path'] for x in rows})==210
assert not set(folds['C']['dev_sources'])&set(folds['D']['dev_sources'])
for fold in 'CD':
 paired=[[r for r in rows if r['run']==arm+'_'+fold] for arm in ['Sref','Static','Requery']]
 assert all(all(x[k]==y[k]==z[k] for k in ['case_id','input','normalization']) for x,y,z in zip(*paired))
 assert set(x['defect_type'] for x in paired[0])=={'bilateral','frontoorbital','parietotemporal','random_1','random_2'}
latest=R/'outputs/scq_rf_Static_D_implementation_20261115_v1/selector_diagnostic_hotfix_v2';mirror={k:Path(v) for k,v in read(latest/'final_local_mirror_v2.json').items()};q=requests['Static_D']
sources={}
for key in ['rf_factory','rf_residual','scq_factory','scq_residual']:
 r=q['implementation'][key];p=mirror[r['path']];assert rec(p)['sha256']==r['sha256'] and rec(p)['bytes']==r['bytes'];ast.parse(p.read_text(encoding='utf-8'));sources[key]=rec(p)
rf=mirror[q['implementation']['rf_factory']['path']].read_text(encoding='utf-8')
assert "parent.build_model(legacy_builder, 'S'" in rf and "Q1=Q1.detach()" in rf and 'N1=second' in rf
counts=dict(forward=630,per_run=105,unique_inputs=210,unique_dev_sources=42,batch=1,backward=0,optimizer_step=0,loss=0,BNCal=0,warmup=0,TTA=0)
qualification=q['comparison_qualification']
emit('RF_sixmodel_input_index_candidate_v1.json',dict(status='LOCAL_METADATA_REVIEWED_NOT_EXECUTABLE_NOT_SERVER_VERIFIED',runs=runs,inputs=rows,counts=counts,actual_remote_paths_verified=False,real_payload_reads=0))
gaps=[
 dict(id='G1',topic='Six frozen models and strict checkpoint dispatch',required='Dedicated entry: S-ref uses admitted SCQ S factory (40596676 parameters); RF-Static/RF-Requery use exact RF factory and frozen-byte initialization (40827847). Strict checkpoint keys, final3900, all six exact audit schemas/hash pins. Historical training identities preserved; current execution identity separately verified.'),
 dict(id='G2',topic='Exact runtime source and initialization reads',required='Reuse existing exact-reader structure, explicitly bind RF factory/residual, actual SCQ factory chain, both frozen initializers and UTC dependency. No generic allowlist widening, seed regeneration or environment changes.'),
 dict(id='G3',topic='630 lifecycle accounting and inputs',required='Six runs in frozen prediction order Sref_C/Static_C/Requery_C/Sref_D/Static_D/Requery_D; 105 each, identical same-fold inputs/normalization; verify current 210 unique remote files and six checkpoints before execution. No selection, GT read, extra forward, warmup or retries.'),
 dict(id='G4',topic='Single-forward RF stage outputs',required='Save dense, coarse, Q0/Q1/Q2 and delta0/delta1/total delta from existing detached records, in native output ordering. S-ref: Q1=Q2=coarse, delta1=0, RF-stage fields explicitly not applicable. Preserve row-alignment after existing sorting. Optional N0/N1 overlap summaries from existing indices only, no new model call/full traces.'),
 dict(id='G5',topic='Targeted artificial CPU contracts and P3',required='Exercise complete authorize, both actual builder dispatches, strict loading, real exact-read policy and traceback, 630 count/stop-on-failure, output alignment and state/RNG invariance; no repeated GPU preflight. Only after final implementation hashes and P3 may an executable pending request be created.')]
emit('entry_compatibility_review_v1.json',dict(status='MINIMAL_RF_PREDICTION_ADAPTATION_REQUIRED',old_entry=rec(oldentry),bound_sources=sources,six_formal_training_audits_pass=True,metadata_pairing_pass=True,old_entry_directly_compatible=False,gaps=gaps,comparison_qualification=qualification,operations=dict(server_calls=0,model_imports=0,checkpoint_loads=0,real_payload_reads=0,forward=0,tests_executed=0,production_source_changes=0),request_created=False))
emit('pending_scope_NOT_execution_request_v1.json',dict(status='DRAFT_PENDING_IMPLEMENTATION_AUTHORIZATION_NOT_EXECUTABLE',schema='scq-rf-sixmodel-native-scope-v1',runs=[x['label'] for x in runs],counts=counts,current_identity_reference=q['identity'],execution_identity_requires_fresh_verification=True,resources=dict(wall_seconds=7200,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296),resource_basis='Retain existing Native prediction limits; six models sequentially, 630 forecasts; actual storage/headroom must pass startup readiness.',numeric='Admitted FP32 and TF32-disabled settings; disclose finite SSM non-bitwise reproducibility',inference='eval/inference_mode; D-only normalization; no GT, Oracle, outlier removal, registration, BNCal or training',diagnostics='Existing Q0/Q1/Q2/delta stage records only; no added forward or full Memory traces',comparison_qualification=qualification,failure='Stop, no automatic retry/resume; unique request and output paths',next='Separate minimal prediction entry implementation + targeted CPU validation + P3, then final pending execution request; no repeated GPU preflight',new_framework=False))
print(json.dumps(dict(status='MINIMAL_RF_PREDICTION_ADAPTATION_REQUIRED',models=6,forward_scope=630,unique_inputs=210,unique_sources=42,request_created=False,server_calls=0)))
