"""Sampling AB only; fixed paired 8k metadata, no training/import side effects."""
import hashlib,json
from pathlib import Path, PurePosixPath
STAGE='BCSP_BLUE_NOISE_AB_V1'
QC_STATUS='PAIRED_315_TRAIN_INPUTS_VERIFIED_NOT_GPU_READY'
GPU_STATUS='FORMAL_POST_PREFLIGHT_FREEZE_AUDIT_PASS'
COUNTS={'cases':315,'sources':63,'batch':8,'epochs':100,'batches_per_epoch':39,'updates':3900,'exposures':31200}
LIMITS=('Separate inner/outer plate coverage not certified','Representation QC is not prediction or clinical accuracy','Artificial GPU zero-update success is not complete training memory proof')
ARMS=('Euclidean_elimination','surface_graph')
def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def no_links(path):
    p = Path(path).absolute()
    require(not any(x.is_symlink() for x in (p, *p.parents)), 'linked path: ' + str(p))
    return p

def exact(record):
    require(isinstance(record, dict) and set(record) == {'path', 'bytes', 'sha256'}, 'exact binding fields')
    p = no_links(record['path'])
    require(p.is_file() and p.stat().st_size == record['bytes'] and sha(p) == record['sha256'],
            'bound file drift: ' + str(p))
    return p

def json_bound(record):
    return json.loads(exact(record).read_text(encoding='utf-8'))

def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode('utf-8')).hexdigest()

def emit(path, value):
    with no_links(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')

def validate_static(config):
    require(set(config) == {'schema', 'stage', 'counts', 'model', 'training', 'resources'}, 'static fields')
    require(config['schema'] == 'bcsp-training-static-v1' and config['stage'] == STAGE
            and config['counts'] == COUNTS and all(type(v) is int for v in config['counts'].values()),
            'stage/count contract')
    t = config['training']
    require(t == {'seed': 0, 'precision': 'FP32', 'optimizer': 'AdamW', 'lr': .0001,
                  'weight_decay': .0005, 'clip': 10, 'step_per_update': 1, 'drop_last': True,
                  'checkpoint': 'scratch_final_only', 'BNCal': False, 'evaluation': False,
                  'resume': False}, 'training scientific contract')
    m = config['model']
    require(m.get('num_query') == 256 and m.get('num_points') == 8192 and m.get('center_num') == [512, 256]
            and m.get('encoder_type') == 'graph' and m.get('decoder_type') == 'fc'
            and m.get('query_selection') == 'learned_only' and m.get('denoise_weight') == 0,
            'B0 model contract')
    r = config['resources']
    require(set(r) == {'wall_seconds', 'RSS_bytes', 'device_MiB', 'torch_peak_bytes', 'output_bytes',
                       'minimum_free_disk_bytes'}, 'training resource fields')
    require(all(type(v) is int and v > 0 for v in r.values()), 'explicit positive integer budgets required')
    require(r['RSS_bytes'] == 8 * 1024**3 and r['device_MiB'] == 22528
            and r['torch_peak_bytes'] == 20 * 1024**3
            and r['minimum_free_disk_bytes'] >= 2 * 1024**3, 'unchanged memory ceilings/minimum disk')
    require(r['output_bytes'] >= 1048576, 'output budget must be explicit and usable')
    return config

def validate_order(plan, ids):
    require(set(plan) == {'schema', 'case_ids', 'epochs'} and plan['schema'] == 'bcsp-shared-order-v1'
            and plan['case_ids'] == ids and len(ids) == len(set(ids)) == 315
            and len(plan['epochs']) == 100, 'shared order schema')
    for epoch, row in enumerate(plan['epochs']):
        require(set(row) == {'epoch', 'batches', 'dropped'} and row['epoch'] == epoch
                and len(row['batches']) == 39 and all(len(b) == 8 for b in row['batches'])
                and len(row['dropped']) == 3, 'epoch order counts')
        flat = [i for batch in row['batches'] for i in batch] + row['dropped']
        require(len(flat) == len(set(flat)) == 315 and set(flat) == set(ids), 'order case set/duplicates')
    return plan


def metadata_values(qc,records,folds,fold,n_input,arm):
    require(fold=='C' and n_input==8192 and arm in ARMS,'sampling stage fold/arm/count')
    require(qc['status']==QC_STATUS and qc['cases']==315 and qc['sources']==63 and qc['same_permutation_per_case'] is True,'paired QC')
    require(set(records)==set(ARMS),'exact two sampler arms')
    require(qc.get('stage')==STAGE and qc.get('comparison_split')=='train','new-stage training receipt only')
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
            require(r.get('comparison_stage')==STAGE and r.get('comparison_split')=='train','new-stage train records only')
            rel=PurePosixPath(r['point_path']);require(not rel.is_absolute() and '..' not in rel.parts and '\\' not in r['point_path'],'safe relative point path')
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
    receipt={'schema':'bcsp-blue-noise-qualified-v1','stage':STAGE,'arm':arm,'verification':verification,'manifests':manifests,'fold_binding':fold_binding,'fold':fold,'n_input':n_input,'train_allowlist_sha256':spec['train_allowlist_sha256'],'limitations':list(LIMITS)}
    return receipt,selected,spec

def verify_qualified_receipt(receipt,verification,manifests,fold_binding,fold,n_input,arm):
    expected,selected,spec=bind_metadata(verification,manifests,fold_binding,fold,n_input,arm)
    require(receipt==expected,'qualified sampler receipt binding');return selected,spec

def validate_rebind(record,scope_record,gpu_record):
    value=IMMUTABLE['resource_binding']
    require(isinstance(value,str) and len(value)==64 and set(value)<=set('0123456789abcdef'),'current server resource binding not finalized')
    require(record['sha256']==IMMUTABLE['resource_binding'],'current sampling resource binding')
    r=json_bound(record);scope=json_bound(scope_record);gpu=json_bound(gpu_record)
    require(r['schema']=='bcsp-blue-noise-resource-v1' and r['stage']==STAGE and r['historical_GPU_only'] is True,'resource semantics')
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
    fields={'schema','stage','status','run_id','fold','n_input','arm','paired_initialization','static_config','QC','order_plan','GPU_audit','preflight_request_sha256','preflight_scope','identity','data_root','model_root','implementation','output','launch_attempt','resource_rebind'}
    require(set(q)==fields and q['schema']=='bcsp-blue-noise-training-request-v1' and q['stage']==STAGE and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','only new pending sampler task')
    require(q['arm'] in ARMS and q['fold']=='C' and q['n_input']==8192,'fixed two arms and fold')
    require((q['arm']==ARMS[0] and q['paired_initialization'] is None) or (q['arm']==ARMS[1] and isinstance(q['paired_initialization'],dict)),'candidate requires separately frozen baseline initialization evidence')
    config=validate_static(json_bound(q['static_config']))
    auth=json_bound(authorization_record)
    require(set(auth)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and auth['schema']=='bcsp-training-authorization-v1' and auth['request_sha256']==request_record['sha256'] and auth['explicit_user_authorization'] is True and bool(auth['user_authorization_text'].strip()),'separate exact-hash authorization; no reverse runtime binding')
    require(json_bound(runtime_record)=={'schema':'bcsp-training-runtime-v1','request_sha256':request_record['sha256'],'authorization_sha256':authorization_record['sha256']},'one-way runtime binding')
    r=validate_rebind(q['resource_rebind'],q['preflight_scope'],q['GPU_audit']);require(q['identity']==r['new_identity'],'bound current identity')
    for k,record in [('static_config',q['static_config']),('order_plan',q['order_plan']),('training_runtime',q['implementation']['runtime'])]:require(record['sha256']==IMMUTABLE[k],'unchanged paired science '+k)
    return q,config

def validate_pair_initialization(value,q,parameter_sha,state_sha,order_canonical_sha):
    if q['arm']==ARMS[0]:
        require(value is None,'baseline must start fresh without parent weights');return
    require(isinstance(value,dict) and value.get('schema')=='bcsp-blue-noise-paired-initialization-v1' and value.get('stage')==STAGE,'audited baseline initialization required')
    require(value.get('verified_updates')==3900 and value.get('baseline_run_id')=='bcsp_blue_noise_foldC_Euclidean_elimination_in8192_out8192_seed0_train_v1','completed exact baseline required')
    require(value.get('identity')==q['identity'] and value.get('static_config_sha256')==q['static_config']['sha256'] and value.get('runtime_sha256')==q['implementation']['runtime']['sha256'],'same environment and science')
    require(value.get('order_plan_sha256')==q['order_plan']['sha256'] and value.get('order_canonical_sha256')==order_canonical_sha,'same exact batch order')
    require(value.get('parameter_sha256')==parameter_sha and value.get('persistent_state_sha256')==state_sha,'scratch initialization mismatch before first update')

IMMUTABLE = {'static_config': '18aa3d941ca8957fc1ecafbcd1a054b4e6ea326d3641cb6955ba204736c4d713', 'order_plan': '6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d', 'training_runtime': '84bdf882ead11282b01556d6ed302ab46b7112dc3445e6cd3e6cde24d09aa9dc', 'resource_binding': 'UNBOUND_PENDING_CURRENT_SERVER_READINESS'}
