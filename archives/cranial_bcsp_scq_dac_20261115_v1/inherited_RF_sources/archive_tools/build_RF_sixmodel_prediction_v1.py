from pathlib import Path, PurePosixPath
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent
PRE=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1';S=PRE/'implementation_v1';S.mkdir()
OLD=R/'outputs/cranial_bcsp_scq_BS_CD_native_prediction_preparation_20261114_v1/implementation_v1/resource_rebind_v2'
H=R/'outputs/scq_rf_Static_D_implementation_20261115_v1/selector_diagnostic_hotfix_v2'
REMOTE='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def emit(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
t=read(H/'pending_transport_v2/payload/SCQ_RF_Static_D_training_execution_request_v2.json');ctx=read(OLD/'context_v2.json');q=copy.deepcopy(ctx['candidate']);mirror=dict(ctx['mirror']);mirror.update(read(H/'final_local_mirror_v2.json'))
index=read(PRE/'RF_sixmodel_input_index_candidate_v1.json');index.update(schema='bcsp-scq-rf-sixmodel-native-index-v1',status='FROZEN_REQUIRES_FRESH_SERVER_READINESS');folds=read(R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/fold_binding.json')['folds']
pins={};audits={}
for r in index['runs']:
 label=r['label'];audits[label]=r['training_audit']['path'];a=read(Path(audits[label]));train=read(Path(r['training_request']['path']))
 r.update(train_sources=folds[r['fold']]['train_sources'],dev_sources=folds[r['fold']]['dev_sources'])
 r['training_audit']=dict(r['training_audit'],path=REMOTE+'/frozen_'+label+'_training_audit_v1.json');r['training_request']=dict(r['training_request'],path=train['launch_contract']['request_path'])
 pins[label]=dict(fold=r['fold'],variant=r['variant'],checkpoint=r['checkpoint'],request_sha256=r['training_request']['sha256'],audit_sha256=r['training_audit']['sha256'],audit_status=a['status'],identity=a['identity'])
for row in index['inputs']:row.update(save_coarse=True,save_Qraw=True)
ip=S/'RF_sixmodel_input_index_v1.json';emit(ip,index)
protocol=dict(schema='scq-rf-native-protocol-v1',inference=dict(forward_attempt_budget=630,models=list(pins),cases_per_model=105,batch=1,backward=0,optimizer=0,BNCal=0,loss=0,warmup=0,TTA=0,GT_condition=False),outputs=dict(predictions=630,keys=['prediction','coarse','Qraw','delta','Q0','Q1','Q2','delta0','delta1'],context_caches=0,full_decoder_traces=0,frame='D-only normalized; per-input center/scale retained',RF_second_stage_applicable='False for Sref, True for RF-Static/RF-Requery'),numeric=dict(repeat_GPU_preflight=False,FP32=True,TF32=False,finite_gradient_nondeterminism_disclosed=True),comparison_qualification=t['comparison_qualification'],failure='STOP_NO_AUTOMATIC_RETRY_RESUME',resources=q['limits'])
pp=S/'RF_sixmodel_native_scope_v1.json';emit(pp,protocol)
impl={k:t['implementation'][k] for k in ['encoder','factory','lqi_decoder','lqi_factory','scq_residual','scq_factory','rf_residual','rf_factory','timezone','cuda_entry']}
source=(OLD/'bcsp_scq_fourmodel_native_predict_v2.py').read_text(encoding='utf-8');replacements={}
replacements['authorize']='''def authorize(qr,ar,rr):
 q,a,r=bound(qr),bound(ar),bound(rr)
 require(q['schema']=='bcsp-scq-rf-sixmodel-native-prediction-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'request type/status')
 require(q['forward_budget']==630 and q['batch_size']==1 and q['unique_cases']==210 and all(q[k]==0 for k in ('backward','optimizer_steps','BNCal','loss_calls','warmup','TTA')),'Native630 only')
 require(q['limits']==LIMITS and q['identity']==CURRENT_IDENTITY and q['environment']['CUDA_VISIBLE_DEVICES']==CURRENT_IDENTITY['gpu_uuid'],'current identity/resources')
 require(q['input_index']['sha256']==INDEX_SHA and q['protocol']['sha256']==PROTOCOL_SHA and q['scope_origin']=='EXACT_FROZEN_SCQ_RF_SIX_DEVELOPMENT_RUNS_NO_RESELECTION','frozen scope')
 require(q['comparison_qualification']==QUALIFICATION,'accepted D device confound disclosure')
 require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-development-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate explicit authorization')
 require(r==dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
 return q
'''
v=ast.get_source_segment(source,next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='validate_index'))
v=v.replace('bcsp-scq-fourmodel-native-index-v1','bcsp-scq-rf-sixmodel-native-index-v1').replace("['B_C','S_C','B_D','S_D']",repr(list(pins))).replace('len(rows)==420','len(rows)==630').replace("==420 and len({r['input']['path']", "==630 and len({r['input']['path']")
start=v.index(" for f in 'CD':")
v=v[:start]+''' for f in 'CD':
  parts=[[r for r in rows if r['run']==a+'_'+f] for a in ('Sref','Static','Requery')]
  require(all(all(x[k]==y[k]==z[k] for k in ('case_id','source_id','input','normalization')) for x,y,z in zip(*parts)),'three arms paired identical inputs')
 return runs,rows
'''
replacements['validate_index']=v
replacements['validate_evidence']='''def validate_evidence(q,index):
 require(set(q['training_audits'])==set(FROZEN_MODELS),'six audit records')
 for run in index['runs']:
  pin=FROZEN_MODELS[run['label']];r=q['training_audits'][run['label']]
  require(r['sha256']==pin['audit_sha256'],'audit pin');a=bound(r)
  require(a['status']==pin['audit_status'] and a['variant']==pin['variant'] and a['fold']==pin['fold'] and a['identity']==pin['identity'] and a['request_sha256']==pin['request_sha256'],'formal historical freeze identity')
  require(a['check_count']==len(a['checks'])>0 and all(a['checks'].values()),'formal audit checks')
  require(a['checkpoint']=={k:run['checkpoint'][k] for k in ('bytes','sha256')} and (a['updates'],a['traversals'],a['exposures'],a['drops'])==(3900,100,31200,300) and not any(a[k] for k in ('BNCal','evaluation','resume')),'checkpoint and counts')
 for k,h in PINS.items():require(q['implementation'][k]['sha256']==h,'implementation pin '+k)
 for r in q['implementation'].values():exact(r)
 for r in q['dependencies']:exact(r)
 require(q['initialization']==INITIALIZATION and q['rf_initialization']==RF_INITIALIZATION,'frozen initializer records')
 exact(q['initialization']);exact(q['rf_initialization']);exact(q['entry']);bound(q['numeric_policy'])
 admission=bound(q['prior_native_admission']['audit'])
 require(admission['status']=='RF_NATIVE_CUDA_FREEZE_AUDIT_PASS' and all(admission['checks'].values()),'historical admitted implementation; no current-device equivalence claim')
 p=bound(q['protocol']);require(p['inference']['forward_attempt_budget']==630 and p['numeric']['repeat_GPU_preflight'] is False and p['outputs']['context_caches']==p['outputs']['full_decoder_traces']==0 and p['comparison_qualification']==QUALIFICATION,'Native scope')
 p3=bound(q['P3']);require(p3['status']=='LOCAL_RF_NATIVE_PREDICTION_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'] and all(p3['checks'].values()),'final P3')
'''
replacements['load_scq_builder']='''def load_scq_builder(implementation):
 for name,key in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory'),('bcsp_scq_residual_v1','scq_residual')]:source_module(name,implementation[key])
 scq=source_module('bcsp_scq_factory_v1',implementation['scq_factory'])
 source_module('bcsp_scq_rf_residual_v1',implementation['rf_residual'])
 rf=source_module('bcsp_scq_rf_factory_v1',implementation['rf_factory'])
 return dict(scq=scq,rf=rf)
'''
oldvalidate=ast.get_source_segment(source,next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='validate_model')).replace('def validate_model(', 'def validate_scq_model(')
replacements['validate_model']=oldvalidate+'''

def validate_model(model,evidence,artificial_cpu=False):
 is_rf='rf' in evidence
 scq=evidence['parent'] if is_rf else evidence
 # SCQ parent records its pre-RF count; total model count is checked below.
 validate_scq_model(model,scq,True if is_rf else artificial_cpu)
 if is_rf:
  require(scq['parent']['artificial_fixture'] is artificial_cpu,'actual RF parent fixture flag')
  rf=evidence['rf'];require(rf['variant'] in ('RF-Static','RF-Requery') and rf['additional_parameters']==231171 and rf['common_state_preserved'] and rf['CPU_RNG_preserved'] and rf['initialization_sha256']==RF_INITIALIZATION['sha256'],'RF construction contract')
  require(hasattr(model.base_model,'rf') and model.base_model.rf.variant==rf['variant'],'actual RF module arm')
  if not artificial_cpu:require(rf['total_parameters']==sum(p.numel() for p in model.parameters())==40827847,'RF exact total count')
 else:require(not hasattr(model.base_model,'rf') and scq['scq']['variant']=='S','Sref unmodified S')
'''
# Validate SCQ structure without confusing RF parent evidence artificial flag.
replacements['validate_model']=replacements['validate_model'].replace("validate_scq_model(model,scq,True if is_rf else artificial_cpu)","validate_scq_model(model,scq,artificial_cpu,check_total=not is_rf)")
replacements['validate_model']=replacements['validate_model'].replace("def validate_scq_model(model,evidence,artificial_cpu=False):", "def validate_scq_model(model,evidence,artificial_cpu=False,check_total=True):").replace("if not artificial_cpu:require(s['total_parameters']", "if not artificial_cpu and check_total:require(s['total_parameters']")
replacements['build_scq_model']='''def build_scq_model(factory,legacy_builder,run,initialization,rf_initialization):
 variant=run['variant'];require(variant in ('S','RF-Static','RF-Requery'),'only Sref/Static/Requery')
 if variant=='S':return factory['scq'].build_model(legacy_builder,'S',initialization,seed=0)
 model,evidence=factory['rf'].build_model(legacy_builder,variant,initialization,rf_initialization,seed=0)
 require(evidence['rf']['variant']==variant,'RF builder variant dispatch');return model,evidence
'''
replacements['make_source_guard']='''def make_source_guard(implementation,initialization,rf_initialization):
 reader=source_module('scq_native_exact_reader',implementation['cuda_entry'])
 return reader.ExactSCQReads(ExactSourceReads(implementation),[implementation[k] for k in ('scq_residual','scq_factory','rf_residual','rf_factory')]+[initialization,rf_initialization])
'''
replacements['scq_arrays']='''def scq_arrays(torch,np,model,coarse):
 info=model.base_model._scq_last_info;require(isinstance(info,dict),'SCQ diagnostic record')
 def array(key):return info[key].detach().cpu().numpy().copy()
 q0=array('Q0');q2=array('Qused');delta=array('delta');rf=hasattr(model.base_model,'rf')
 if rf:q1=array('Q1');d0=array('delta0');d1=array('delta1')
 else:q1=q2.copy();d0=delta.copy();d1=np.zeros_like(delta)
 arrays=dict(Q0=q0,Q1=q1,Q2=q2,delta0=d0,delta1=d1)
 require(all(x.shape==(1,256,3) and x.dtype==np.float32 and np.isfinite(x).all() for x in [q0,q1,q2,delta,d0,d1]),'finite native stage arrays')
 require(np.array_equal(q2,coarse) and np.allclose(q0+d0,q1,rtol=2e-5,atol=2e-6) and np.allclose(q1+d1,q2,rtol=2e-5,atol=2e-6) and np.allclose(q0+delta,q2,rtol=2e-5,atol=2e-6),'native row aligned Q0/Q1/Q2 equations')
 model.base_model._scq_last_info=None
 return q0,delta,arrays,rf
'''
for n in sorted(ast.parse(source).body,key=lambda n:n.lineno,reverse=True):
 if isinstance(n,ast.FunctionDef) and n.name in replacements:
  lines=source.splitlines(True);lines[n.lineno-1:n.end_lineno]=[replacements[n.name]+'\n'];source=''.join(lines)
# Literal changes limited to the existing lifecycle and main dispatcher.
source=source.replace('attempts<420','attempts<630').replace('attempts==successful==420 and len(files)==420','attempts==successful==630 and len(files)==630').replace('exact420 Native','exact630 Native')
source=source.replace('raw,delta=scq_arrays(torch,np,model,coarse)', 'raw,delta,stages,rf_applicable=scq_arrays(torch,np,model,coarse)')
source=source.replace('Qraw=raw[0],delta=delta[0])','Qraw=raw[0],delta=delta[0],**{k:v[0] for k,v in stages.items()})')
source=source.replace("stats['coarse']['finite_count']", "stats['RF_second_stage_applicable']=rf_applicable;stats['stage_centroids']={k:v[0].mean(0).tolist() for k,v in stages.items()};stats['coarse']['finite_count']",1)
source=source.replace('del x,coarse,dense,raw,delta;', 'del x,coarse,dense,raw,delta,stages;')
source=source.replace("make_source_guard(q['implementation'],q['initialization'])", "make_source_guard(q['implementation'],q['initialization'],q['rf_initialization'])")
source=source.replace("run,q['initialization'])", "run,q['initialization'],q['rf_initialization'])")
source=source.replace('SCQ_BS_CD_420_NATIVE_FORWARD_COMPLETE','SCQ_RF_SIXMODEL_630_NATIVE_FORWARD_COMPLETE').replace('forwards=420','forwards=630').replace('exactly420','exactly630')
constants=dict(INITIALIZATION=t['initialization'],RF_INITIALIZATION=t['rf_initialization'],CURRENT_IDENTITY=t['identity'],INDEX_SHA=sha(ip),PROTOCOL_SHA=sha(pp),DATA_ROOTS={f:str(PurePosixPath(next(x['input']['path'] for x in index['inputs'] if x['fold']==f)).parent) for f in 'CD'},PINS={k:v['sha256'] for k,v in impl.items()},FROZEN_MODELS=pins,QUALIFICATION=t['comparison_qualification'])
lines=source.splitlines(True)
for n in sorted(ast.parse(source).body,key=lambda n:n.lineno,reverse=True):
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants:
  name=n.targets[0].id;lines[n.lineno-1:n.end_lineno]=[name+'='+repr(constants.pop(name))+'\n']
source=''.join(lines);i=source.index('def authorize(');source=source[:i]+''.join(k+'='+repr(v)+'\n' for k,v in constants.items())+'\n'+source[i:]
ep=S/'bcsp_scq_rf_sixmodel_native_predict_v1.py';ast.parse(source);ep.open('x',encoding='utf-8',newline='\n').write(source)
for key in ['training_identity','resource_rebind']:q.pop(key,None)
q.update(schema='bcsp-scq-rf-sixmodel-native-prediction-v1',stage='CRANIAL_BCSP_SCQ_RF',run_id='SCQ_RF_sixmodel_native_development_20261115_v1',variant='Sref_Static_Requery',forward_budget=630,unique_cases=210,identity=t['identity'],environment=t['environment'],dependencies=t['dependencies'],implementation=impl,initialization=t['initialization'],rf_initialization=t['rf_initialization'],scope_origin='EXACT_FROZEN_SCQ_RF_SIX_DEVELOPMENT_RUNS_NO_RESELECTION',comparison_qualification=t['comparison_qualification'],prior_native_admission=t['admission'],execution_authorized=False)
q['output']=t['identity']['project']+'/logs/cranial_bcsp_fullmamba/'+q['run_id'];q['launch_attempt']=REMOTE+'/control/attempt_claim_v1.json'
q['entry']=dict(rec(ep),path=REMOTE+'/'+ep.name);q['input_index']=dict(rec(ip),path=REMOTE+'/'+ip.name);q['protocol']=dict(rec(pp),path=REMOTE+'/'+pp.name)
q['training_audits']={r['label']:r['training_audit'] for r in index['runs']}
q['P3']=dict(path=REMOTE+'/implementation_P3_v1.json',bytes=0,sha256='PENDING_FINAL_P3')
q['launch_contract'].update(tmux_session='bcsp_scq_rf_six_native_20261115_v1',request_path=REMOTE+'/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json',authorization=REMOTE+'/control/native_prediction_authorization_v1.json',runtime=REMOTE+'/control/native_prediction_runtime_v1.json',launcher=REMOTE+'/control/native_prediction_launch_once_v1.sh',log=q['output']+'/launch.log',pid=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
q['expected_artifacts']=['630 prediction NPZ with dense/coarse/Qraw/Q0/Q1/Q2/delta/delta0/delta1','inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','resources.jsonl','inference_complete.json','development_predictions_v1.tar.gz plus three sidecars','completion.json','worker.pid','launch.log','exit_code.txt']
q['provenance']=dict(six_formal_training_freezes=True,fresh_server_readiness_required=True,CPU_not_CUDA_or_efficacy=True,actual_input_paths_not_reverified_this_task=True,historical_admission_not_current_device_preflight=True)
q['installation_prerequisites']=['Separate full request SHA256 authorization before any installation/materialization/launch','Fresh hostname/UID/Python/GPU selector/driver and idle checks; mismatch stops','Upload hashes and every new install/control/output target absent, reject links and overwrite','Reverify exact reused sources/providers/environment, six checkpoint hashes, 210 unique input hashes and free disk>=4GiB; no guessed path substitution','Receipt hash -> runtime -> launcher -> unique claim -> one tmux; no retry/resume','No scoring, training, BNCal, extra forward, GT access, download, compile or upgrade']
q['not_authorized']=['Execution before full request hash authorization','Training/BNCal/scoring/loss/backward/optimizer/warmup/TTA','GT alignment/registration/outlier filtering/case selection','Extra forward or repeated GPU preflight','Automatic retries/resume','Dependency downloads/builds/upgrades']
mirror.update({q[k]['path']:str(p) for k,p in [('entry',ep),('input_index',ip),('protocol',pp)]})
for label,p in audits.items():mirror[q['training_audits'][label]['path']]=p
emit(S/'context_v1.json',dict(candidate=q,remote_root=REMOTE,mirror=mirror,audit_local_files=audits))
oldnodes={n.name:ast.dump(n,include_attributes=False) for n in ast.parse((OLD/'bcsp_scq_fourmodel_native_predict_v2.py').read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};newnodes={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(source).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
inherited=['load_partial','predict_once','ExactSourceReads','source_module','make_policy','Budget','pack','rng_state','geometry_summary','load_checkpoint','render_launcher','validate_source','validate_lqi_model']
assert all(oldnodes[n]==newnodes[n] for n in inherited)
emit(S/'static_review_v1.json',dict(status='STATIC_S0_S1_PASS',entry=rec(ep),checks=dict(AST_compiles=True,inherited_read_numeric_resource_checkpoint_launcher_unchanged=True,no_model_source_changes=True,no_server_operations=True),inherited_AST_unchanged=inherited,changed_functions=[n for n in newnodes if oldnodes.get(n)!=newnodes[n]],candidate_not_execution_request=True))
print(json.dumps(dict(status='ISOLATED_ENTRY_AND_STATIC_CONTEXT_CREATED',entry=str(ep),inherited=len(inherited),server_calls=0)))
