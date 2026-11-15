from pathlib import Path,PurePosixPath
import ast,copy,hashlib,json
R=Path(__file__).resolve().parent.parent
S=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1';B=S/'pending_request_v1';V=S/'input_path_fix_v2';V.mkdir()
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(p,j):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
oldq=read(B/'payload/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json');assert rec(B/'payload/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json')['sha256']=='b503b487e2ed3a00b60400f2e71c98a2d56931dbdf25a77ff32e717b4ff1e561'
proof=B/'failed_inputs_readonly_audit_v1/remote_path_observation_v1.json';p=read(proof)
assert p['status']=='BOUNDED_INPUT_PATH_OBSERVATION_COMPLETE' and p['hostname']==oldq['identity']['hostname'] and p['uid']==1000 and p['server_writes']==p['array_reads']==p['new_forward']==0 and p['before']==p['after'] and not p['before']['tmux_live'] and all(not x['exists'] and not x['symlink'] for x in p['before']['targets'])
selected={}
for row in p['rows']:
 matches=[c for c in row['candidates'] if c['valid_match']];assert len(matches)==1 and not row['original_valid'];selected[row['fold'],row['case_id']]=matches[0]
assert len(selected)==210
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2'
index=read(B/'payload/RF_sixmodel_input_index_v1.json')
for row in index['inputs']:
 match=selected[row['fold'],row['case_id']];assert match['bytes']==row['input']['bytes'] and match['sha256']==row['input']['sha256'];row['input']['path']=match['path']
for run in index['runs']:run['training_audit']['path']=remote+'/frozen_'+run['label']+'_training_audit_v1.json'
ip=V/'RF_sixmodel_input_index_v2.json';emit(ip,index)
oldentry=S/'bcsp_scq_rf_sixmodel_native_predict_v1.py';source=oldentry.read_text(encoding='utf-8');lines=source.splitlines(True)
constants=dict(INDEX_SHA=rec(ip)['sha256'],DATA_ROOTS={f:str(PurePosixPath(next(r['input']['path'] for r in index['inputs'] if r['fold']==f)).parent) for f in 'CD'})
for n in sorted(ast.parse(source).body,key=lambda n:n.lineno,reverse=True):
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants:lines[n.lineno-1:n.end_lineno]=[n.targets[0].id+'='+repr(constants[n.targets[0].id])+'\n']
source=''.join(lines);ep=V/'bcsp_scq_rf_sixmodel_native_predict_v2.py';ast.parse(source);ep.open('x',encoding='utf-8',newline='\n').write(source)
def functions(s):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
assert functions(source)==functions(oldentry.read_text(encoding='utf-8'))
def top(s):return {n.targets[0].id:ast.dump(n,include_attributes=False) for n in ast.parse(s).body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)}
before=top(oldentry.read_text(encoding='utf-8'));after=top(source);assert set(before)==set(after) and {k for k in before if before[k]!=after[k]}=={'INDEX_SHA','DATA_ROOTS'}
q=copy.deepcopy(oldq);q['run_id']='SCQ_RF_sixmodel_native_development_20261115_v2';q['output']=q['identity']['project']+'/logs/cranial_bcsp_fullmamba/'+q['run_id'];q['launch_attempt']=remote+'/control/attempt_claim_v2.json'
q['entry']=dict(rec(ep),path=remote+'/'+ep.name);q['input_index']=dict(rec(ip),path=remote+'/'+ip.name)
for k in ['protocol','P3','numeric_policy']:q[k]['path']=remote+'/'+PurePosixPath(q[k]['path']).name
q['P3']=dict(path=remote+'/implementation_P3_v2.json',bytes=0,sha256='PENDING_FINAL_P3')
for label,r in q['training_audits'].items():r['path']=remote+'/frozen_'+label+'_training_audit_v1.json'
q['launch_contract'].update(tmux_session='bcsp_scq_rf_six_native_20261115_v2',request_path=remote+'/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json',authorization=remote+'/control/native_prediction_authorization_v2.json',runtime=remote+'/control/native_prediction_runtime_v2.json',launcher=remote+'/control/native_prediction_launch_once_v2.sh',log=q['output']+'/launch.log',pid=q['output']+'/worker.pid',exit_code=q['output']+'/exit_code.txt')
q['supersedes']=dict(request_sha256=rec(B/'payload/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json')['sha256'],status='STOPPED_INPUT_PATH_CHECK_NOT_INSTALLED_NO_FORWARD_NOT_REUSABLE')
q['provenance'].update(actual_input_paths_not_reverified_this_task=False,exact210_input_paths_and_hashes_readonly_verified=True,fresh_server_readiness_required=True)
resolution=dict(status='EXACT210_INPUT_PATHS_READONLY_RESOLVED',observation=rec(proof),unique_cases=210,prediction_rows_changed=630,case_source_fold_order_hash_size_normalization_unchanged=True,roots=constants['DATA_ROOTS'],previous_request_sha256=q['supersedes']['request_sha256'],model_changes=0,server_operations_this_implementation=0)
rp=V/'input_path_resolution_v2.json';emit(rp,resolution);q['path_resolution']=dict(rec(rp),path=remote+'/'+rp.name)
mirror=read(B/'local_mirror_v1.json')
for k,local in [('entry',ep),('input_index',ip),('path_resolution',rp)]:mirror[q[k]['path']]=str(local)
for k in ['protocol','numeric_policy']:mirror[q[k]['path']]=str(B/'payload'/PurePosixPath(q[k]['path']).name)
for label,r in q['training_audits'].items():mirror[r['path']]=str(B/'payload'/PurePosixPath(r['path']).name)
emit(V/'context_v2.json',dict(candidate=q,mirror=mirror,remote_root=remote))
emit(V/'static_review_v2.json',dict(status='STATIC_S0_S1_PASS',entry=rec(ep),index=rec(ip),only_changed_constants=['INDEX_SHA','DATA_ROOTS'],all_functions_and_classes_AST_identical=True,all_other_constants_AST_identical=True,proof=rec(proof),models_and_science_unchanged=True,server_operations=0))
print(json.dumps(dict(status='PATH_ONLY_STATIC_ADAPTATION_PASS',functions_changed=0,input_occurrences=630,unique_cases=210)))
