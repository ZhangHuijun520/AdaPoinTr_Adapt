"""Derive a finite new-task adapter; parent training arithmetic stays unchanged."""
import ast,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';I=O/'implementation'
P=B/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False)
def write(p,s):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(s)
def main():
 I.mkdir(exist_ok=False)
 old=(P/'bcsp_training_contract_01dt08_v3.py').read_text(encoding='utf-8');tree=ast.parse(old)
 def function(name):return ast.get_source_segment(old,next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name))+'\n\n'
 source='''"""Sampling AB only; fixed paired 8k metadata, no training/import side effects."""
import hashlib,json
from pathlib import Path, PurePosixPath
STAGE='BCSP_SAMPLING_AB_V1'
QC_STATUS='PAIRED_315_TRAIN_INPUTS_VERIFIED_NOT_GPU_READY'
GPU_STATUS='FORMAL_POST_PREFLIGHT_FREEZE_AUDIT_PASS'
COUNTS={'cases':315,'sources':63,'batch':8,'epochs':100,'batches_per_epoch':39,'updates':3900,'exposures':31200}
LIMITS=('Separate inner/outer plate coverage not certified','Representation QC is not prediction or clinical accuracy','Artificial GPU zero-update success is not complete training memory proof')
ARMS=('V1','Morton_area_stratified8k')
'''
 for name in ['require','sha','no_links','exact','json_bound','canonical_sha','emit','validate_static','validate_order']:source+=function(name)
 source+='''
def metadata_values(qc,records,folds,fold,n_input,arm):
    require(fold=='C' and n_input==8192 and arm in ARMS,'sampling stage fold/arm/count')
    require(qc['status']==QC_STATUS and qc['cases']==315 and qc['sources']==63 and qc['same_permutation_per_case'] is True,'paired QC')
    require(set(records)==set(ARMS),'exact two sampler arms')
    spec=folds['folds']['C'];ids=spec['train_case_ids'];sources=spec['train_sources']
    require(len(ids)==len(set(ids))==315 and len(sources)==len(set(sources))==63 and len(spec['dev_sources'])==21 and not set(sources)&set(spec['dev_sources']),'fold boundary')
    require(folds['confirmation_count_excluded']==20,'sealed source exclusion')
    pairs={r['case_id']:r for r in qc['pairs']};require(len(pairs)==len(qc['pairs'])==315 and set(pairs)==set(ids),'pair QC IDs')
    values={}
    for a in ARMS:
        rr=records[a];require(len(rr)==315 and [r['case_id'] for r in rr]==ids,'ordered exact training allowlist')
        values[a]={r['case_id']:r for r in rr};counts={s:0 for s in sources}
        for r in rr:
            require(r['source_id'] in counts,'train sources only');counts[r['source_id']]+=1
            require(r['schema']=='BCSP-normalized-v1' and r['normalization_source']=='defective_bbox' and r['n_input']==r['n_target']==8192,'frame and point count')
            require(r['sampler_arm']==a and r['sampling_seed']==0,'fixed sampler identity')
            rel=PurePosixPath(r['point_path']);require(not rel.is_absolute() and '..' not in rel.parts and '\\\\' not in r['point_path'],'safe relative point path')
        require(set(counts.values())=={5},'five defects per source')
    for cid in ids:
        a,b=values[ARMS[0]][cid],values[ARMS[1]][cid];p=pairs[cid]
        require(a['source_id']==b['source_id']==p['source_id'],'paired source')
        require(a['target_array_sha256']==b['target_array_sha256']==p['target_array_sha256'],'paired GT content')
        require(a['normalization']==b['normalization']==p['normalization'],'paired D frame')
        require(a['common_point_order_sha256']==b['common_point_order_sha256']==p['common_permutation_sha256'],'common point-order policy')
    return [values[arm][cid] for cid in ids],spec

def bind_metadata(verification,manifests,fold_binding,fold,n_input,arm):
    qc=json_bound(verification);folds=json_bound(fold_binding)
    records={a:[json.loads(s) for s in exact(manifests[a]).read_text(encoding='utf-8').splitlines() if s] for a in ARMS}
    selected,spec=metadata_values(qc,records,folds,fold,n_input,arm)
    receipt={'schema':'bcsp-sampling-qualified-v1','stage':STAGE,'arm':arm,'verification':verification,'manifests':manifests,'fold_binding':fold_binding,'fold':fold,'n_input':n_input,'train_allowlist_sha256':spec['train_allowlist_sha256'],'limitations':list(LIMITS)}
    return receipt,selected,spec

def verify_qualified_receipt(receipt,verification,manifests,fold_binding,fold,n_input,arm):
    expected,selected,spec=bind_metadata(verification,manifests,fold_binding,fold,n_input,arm)
    require(receipt==expected,'qualified sampler receipt binding');return selected,spec

def validate_rebind(record,scope_record,gpu_record):
    require(record['sha256']==IMMUTABLE['resource_binding'],'current sampling resource binding')
    r=json_bound(record);scope=json_bound(scope_record);gpu=json_bound(gpu_record)
    require(r['schema']=='bcsp-sampling-resource-v1' and r['stage']==STAGE and r['historical_GPU_only'] is True,'resource semantics')
    require(r['old_scope_sha256']==scope_record['sha256'] and r['historical_GPU_audit_sha256']==gpu_record['sha256'] and gpu['status']==GPU_STATUS,'historical CUDA evidence')
    observed=json_bound(r['readonly_identity']);assets=json_bound(r['readonly_assets'])
    gpu_fields=[x.strip() for x in observed['gpu'].split(',')]
    identity=r['new_identity']
    require(observed['hostname']==identity['hostname'] and observed['uid']==1000 and observed['project']==identity['project'],'current identity evidence')
    require(gpu_fields[:3]==[identity['gpu_uuid'],identity['gpu_name'],identity['driver_version']],'current GPU evidence')
    require(assets['status']=='SELECTED30_HASH_PASS' and len(assets['assets'])==30,'unchanged selected source/provider evidence')
    return r

def expected_environment(scope,identity,output):
    values={k:v.replace('<owned_output>',str(output)) for k,v in scope['environment'].items()};values['CUDA_VISIBLE_DEVICES']=identity['gpu_uuid'];return values
def validate_environment(scope,identity,output,observed):
    for k,v in expected_environment(scope,identity,output).items():require(observed.get(k)==v,'environment: '+k)
def validate_live_identity(identity,observed):
    require(set(observed)=={'hostname','gpu_uuid','driver_version'} and all(identity[k]==v for k,v in observed.items()),'live device identity')

def authorize(request_record,authorization_record,runtime_record):
    q=json_bound(request_record)
    fields={'schema','stage','status','run_id','fold','n_input','arm','static_config','QC','order_plan','GPU_audit','preflight_request_sha256','preflight_scope','identity','data_root','model_root','implementation','output','launch_attempt','resource_rebind'}
    require(set(q)==fields and q['schema']=='bcsp-sampling-training-request-v1' and q['stage']==STAGE and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','only new pending sampler task')
    require(q['arm'] in ARMS and q['fold']=='C' and q['n_input']==8192,'fixed two arms and fold')
    config=validate_static(json_bound(q['static_config']))
    auth=json_bound(authorization_record)
    require(set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-training-authorization-v1' and auth['request_sha256']==request_record['sha256'] and auth['explicit_user_authorization'] is True and bool(auth['user_authorization_text'].strip()),'separate exact-hash authorization; no reverse runtime binding')
    require(json_bound(runtime_record)=={'schema':'bcsp-training-runtime-v1','request_sha256':request_record['sha256'],'authorization_sha256':authorization_record['sha256']},'one-way runtime binding')
    r=validate_rebind(q['resource_rebind'],q['preflight_scope'],q['GPU_audit']);require(q['identity']==r['new_identity'],'bound current identity')
    for k,record in [('static_config',q['static_config']),('order_plan',q['order_plan']),('training_runtime',q['implementation']['runtime'])]:require(record['sha256']==IMMUTABLE[k],'unchanged paired science '+k)
    return q,config
'''
 # The reusable counter remains the exact historical 3900-step guard. Only the
 # public task identity in checkpoint/completion is translated in this new file.
 runtime=(B/'training_closure_v5/bcsp_training_runtime_v5.py').read_text(encoding='utf-8')
 runtime=runtime.replace('state = guard.finish()','state = guard.finish()\n        state[\'stage\'] = \'BCSP_SAMPLING_AB_V1\'')
 runtime=runtime.replace("'stage': 'BCSP_INPUT_DENSITY_V1'","'stage': 'BCSP_SAMPLING_AB_V1'")
 write(I/'bcsp_sampling_training_runtime_v1.py',runtime)
 ROOT='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_sampling_ab_foldc_seed0_v1'
 scopefile=B/'gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json'
 scope=json.loads(scopefile.read_text(encoding='utf-8'));identity=dict(scope['identity'])
 obs=json.loads((O/'server_readonly_observation_v1.json').read_text(encoding='utf-8'));fields=[v.strip() for v in obs['gpu'].split(',')]
 identity.update(hostname=obs['hostname'],gpu_uuid=fields[0],gpu_name=fields[1],driver_version=fields[2],nvidia_smi_memory_total_MiB=int(fields[3].split()[0]))
 identity['python_realpath']=obs['python_realpath'];identity['python_version']=obs['python_version'].split()[-1]
 def remote_record(local,name):return {'path':ROOT+'/evidence/'+name,'bytes':Path(local).stat().st_size,'sha256':sha(local)}
 resource={'schema':'bcsp-sampling-resource-v1','stage':'BCSP_SAMPLING_AB_V1','new_identity':identity,
    'old_scope_sha256':sha(scopefile),'historical_GPU_audit_sha256':'af3c3053be96a443d203c486ccede4d2bf2f0799ae753294ee946618726cf000',
    'readonly_identity':remote_record(O/'server_readonly_observation_v1.json','server_readonly_observation_v1.json'),
    'readonly_assets':remote_record(O/'server_assets_observation_v1.json','server_assets_observation_v1.json'),
    'historical_GPU_only':True,'limitations':['Read-only source match does not certify present CUDA execution','Both new arms must use this same frozen environment; startup recheck required','Monitored resources; no PID ownership or dedicated cgroup guarantee']}
 dump(O/'resource_binding_v1.json',resource)
 immutable={'static_config':sha(O/'static_training_config_v1.json'),'order_plan':sha(O/'shared_order_foldC_seed0_v1.json'),
   'training_runtime':sha(I/'bcsp_sampling_training_runtime_v1.py'),'resource_binding':sha(O/'resource_binding_v1.json')}
 source+='\nIMMUTABLE = '+repr(immutable)+'\n';write(I/'bcsp_sampling_training_contract_v1.py',source)
 entry=(P/'bcsp_training_entry_research_v5.py').read_text(encoding='utf-8')
 entry=entry.replace('bcsp_training_contract_01dt08_v3.py','bcsp_sampling_training_contract_v1.py')
 entry=entry.replace('08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499',sha(I/'bcsp_sampling_training_contract_v1.py'))
 entry=entry.replace('54fcd0018f9a51f04b8408b3842b6d5c4243777979a0e0add31541e04fa3c55b',sha(O/'paired_train_data_receipt.json'))
 entry=entry.replace("q['QC']['fold_binding'], q['fold'], q['n_input'])","q['QC']['fold_binding'], q['fold'], q['n_input'], q['arm'])")
 write(I/'bcsp_sampling_training_entry_v1.py',entry)
 for p in I.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 dump(O/'implementation_derivation_v1.json',{'status':'IMPLEMENTED_STATIC_NOT_TESTED_NOT_DEPLOYED','runtime_changes':['checkpoint stage metadata','completion stage metadata, old exact count guard retained internally'],
   'entry_changes':['new exact-hash metadata contract bootstrap','sampling QC receipt hash','explicit same-count sampler-arm dispatch'],
   'unchanged':['model files','KNN/loss/provider','training arithmetic/order/optimizer/schedulers/resource policy'],
   'parents':{str(P/'bcsp_training_contract_01dt08_v3.py'):sha(P/'bcsp_training_contract_01dt08_v3.py'),str(P/'bcsp_training_entry_research_v5.py'):sha(P/'bcsp_training_entry_research_v5.py'),str(B/'training_closure_v5/bcsp_training_runtime_v5.py'):sha(B/'training_closure_v5/bcsp_training_runtime_v5.py')},
   'candidate_files':{p.name:sha(p) for p in I.glob('*.py')}})
 print('IMPLEMENTATION_STATIC_PASS')
if __name__=='__main__':main()
