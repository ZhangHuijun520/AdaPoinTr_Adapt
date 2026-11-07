"""One isolated D-specific two-mode entry; all C and shared implementation bytes retained."""
import ast,json
from pathlib import Path
S=Path(__file__).resolve().parent;C=S.parent/'H2_COUPLE_foldC_initialization_readfix_v2/bcsp_h2_couple_foldC_training_entry_v2.py'
src=C.read_text(encoding='utf-8');tree=ast.parse(src)
replacements={}
replacements['validate_static_h2']='''def validate_static_h2(static,baseline,metadata,mode):
    import copy
    stripped=copy.deepcopy(static)
    require(stripped.pop('H2',None)==mode_config(mode),'exact D H2 config')
    require(stripped==baseline,'only H2 config delta')
    metadata.validate_static(baseline)
    require(static['counts']==COUNTS and static['resources']==RESOURCES,'counts/resources')
    require(not static['model'].get('coarse_geometry_guard',{}).get('enabled',False),'H1 off')
    return static
'''
model=ast.get_source_segment(src,next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_model_h2'))
replacements['validate_model_h2']=model.replace('validate_model_h2(model):','validate_model_h2(model,mode):').replace("model.h2_metadata()==H2,'actual COUPLE metadata'","model.h2_metadata()==mode_config(mode),'actual D mode metadata'")+'\n'
replacements['authorize']='''def authorize(qr,ar,rr):
    q=json_bound(qr);base=json_bound(q['baseline_request']);mode=q['h2_config'].get('mode');expected=mode_config(mode)
    extra={'baseline_request','baseline_audit','p3','h2_config','cuda_audit','readiness','aux_pairing'}
    require(set(q)==set(base)|extra,'exact request fields')
    require(q['schema']=='bcsp-p2-H2-foldD-training-request-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'
            and q['stage']=='CRANIAL_BCSP_MAMBA_P2_H2' and q['variant']=='M0' and q['fold']=='D'
            and q['n_input']==q['n_output']==8192 and q['h2_config']==expected,'fixed D two-mode request')
    pin=FROZEN_BASELINES['D']
    require(q['baseline_request']['sha256']==pin['request_sha256'] and q['baseline_audit']['sha256']==pin['audit_sha256'],'frozen M0 D baseline')
    audit=json_bound(q['baseline_audit'])
    require(audit['status']=='FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS' and audit['request_sha256']==pin['request_sha256']
            and audit['checks_passed']==len(audit['checks'])>0 and all(audit['checks'].values()),'M0 D formal audit')
    changed={'schema','stage','run_id','static_config','implementation','output','launch_attempt','launch_contract','provenance','not_authorized','identity','environment'}
    require(all(q[k]==v for k,v in base.items() if k not in changed),'D original scientific pairing')
    require(base['fold']=='D' and base['variant']=='M0','D baseline role')
    require(q['identity']==CURRENT_IDENTITY,'frozen current identity')
    require(set(q['environment'])==set(base['environment']) and all(v==base['environment'][k] for k,v in q['environment'].items() if k!='CUDA_VISIBLE_DEVICES')
            and q['environment']['CUDA_VISIBLE_DEVICES']==CURRENT_IDENTITY['gpu_uuid'],'environment pairing')
    require(set(q['implementation'])==set(base['implementation'])|{'h2_range','h2_adapter'},'implementation set')
    for k,v in base['implementation'].items():
        if k not in ('entry','runtime'):require(q['implementation'][k]==v,'inherited D implementation '+k)
    for k,h in H2_HASHES.items():require(q['implementation'][k]['sha256']==h,'unchanged H2 source '+k)
    for v in q['implementation'].values():exact(v)
    require(exact(q['implementation']['entry'])==Path(__file__).absolute(),'entry origin')
    cuda=json_bound(q['cuda_audit']);require(q['cuda_audit']['sha256']==CUDA_AUDIT_SHA and cuda['status']=='FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS','frozen H2 CUDA admission')
    p3=json_bound(q['p3']);require(p3['status']=='LOCAL_H2_FOLDD_TRAINING_ENTRY_P3_PASS' and p3['entry_sha256']==q['implementation']['entry']['sha256'] and p3['H2_source_hashes']==H2_HASHES,'final D P3')
    metadata=load_bound('bcsp_training_contract_v1',q['implementation']['contract']);static=validate_static_h2(json_bound(q['static_config']),json_bound(base['static_config']),metadata,mode)
    ready=json_bound(q['readiness']);require(ready['status']=='FOLDD_H2_NECESSARY_READONLY_READINESS_PASS' and ready['identity']==CURRENT_IDENTITY and ready['training_cases']==315 and ready['sources']==63,'bounded D readiness')
    if mode=='AUX':
        require(q['aux_pairing'] is None,'AUX D cannot bind future or C AUX pairing')
    else:
        pair=q['aux_pairing'];require(isinstance(pair,dict) and set(pair)=={'request','audit','initialization'},'COUPLE D requires exact prior AUX D evidence')
        aux=json_bound(pair['request']);aa=json_bound(pair['audit']);ai=json_bound(pair['initialization'])
        require(aa['status']=='FORMAL_H2_AUX_FOLDD_POST_TRAINING_FREEZE_AUDIT_PASS' and aa['request_sha256']==pair['request']['sha256']
                and aa['checks_passed']==len(aa['checks'])>0 and all(aa['checks'].values()),'AUX D formal audit')
        require(aux['schema']=='bcsp-p2-H2-foldD-training-request-v1' and aux['fold']=='D' and aux['variant']=='M0' and aux['h2_config']==mode_config('AUX') and aux['aux_pairing'] is None,'AUX D role')
        require(aux['baseline_request']['sha256']==pin['request_sha256'] and aux['baseline_audit']['sha256']==pin['audit_sha256'],'same M0 D baseline')
        require(ai==aa['initialization']['record'] and ai['seed']==0,'AUX D initial fingerprint evidence')
        for key in ('identity','environment','QC','order_plan','data_root','model_root','initialization_reference','numeric_policy','numeric_protocol','pair_contract','dependencies','n_input','n_output'):
            require(q.get(key)==aux.get(key),'AUX D paired '+key)
        require(q['implementation']==aux['implementation'],'same frozen D entry and modules')
        require(dict(static,H2=mode_config('AUX'))==json_bound(aux['static_config']),'D mode-only static delta')
    a,r=json_bound(ar),json_bound(rr)
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-p2-H2-training-authorization-v1'
            and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate explicit authorization')
    require(r==dict(schema='bcsp-p2-H2-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
    selected,fold=metadata.verify_qualified_receipt(json_bound(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'D',8192)
    plan=metadata.validate_order(json_bound(q['order_plan']),fold['train_case_ids'])
    return q,static,metadata,selected,fold,plan
'''
replacements['dispatch_training']='''def dispatch_training(q,static,selected,fold,plan,*,factory,h2_adapter,model_builder,runtime,helper,budget,torch,knn_enable,expected_factory,device='cuda:0'):
    mode=q['h2_config']['mode'];config=mode_config(mode)
    require(q['variant']=='M0' and q['fold']=='D' and static['H2']==config,'fixed D mode dispatch')
    model,evidence=h2_adapter.build_h2(factory,model_builder,mode,seed=0)
    require({k:v for k,v in evidence.items() if k not in ('H2_mode','H2_contract','common_state_after_H2_unchanged')}==expected_factory and not evidence['artificial_fixture'],'original real M0 initialization')
    require(evidence['H2_mode']==mode and dict(evidence['H2_contract'],mode=mode)==config and evidence['common_state_after_H2_unchanged'] is True,'common state and exact H2 mode')
    validate_model_h2(model,mode)
    if mode=='COUPLE':
        ai=json_bound(q['aux_pairing']['initialization'])
        require(helper.state_sha(model,True)==ai['parameter_sha256'] and helper.state_sha(model)==ai['persistent_state_sha256'],'same full scratch initialization as AUX D')
    else:require(q['aux_pairing'] is None,'AUX scratch without prior pairing')
    dataset=runtime.BCSPDataset(q['data_root'],selected,fold['train_sources'],8192)
    budget.first_step_evidence=dict(factory=evidence,H2_head_initialization='ALL_ZERO_NO_RNG_DRAW')
    if mode=='COUPLE':budget.first_step_evidence.update(AUX_initialization_exact_match=True,AUX_initialization_sha256=q['aux_pairing']['initialization']['sha256'])
    budget.run_identity=dict(stage=q['stage'],variant='M0',fold='D',seed=0,H2=config,numeric_policy_sha256=q['numeric_policy']['sha256'],CUDA_audit_sha256=q['cuda_audit']['sha256'],checkpoint_legacy_stage='BCSP_INPUT_DENSITY_V1',legacy_stage_is_provenance_only=True,SSM_gradient_non_bitwise_reproducibility_disclosed=True)
    return runtime.train_lifecycle(model,lambda e:runtime.make_loader(dataset,plan,e),selected,plan,q['output'],device=device,numeric_check=helper.assert_numeric,resources=budget,knn_enable=knn_enable,state_fingerprint=helper.state_sha)
'''
lines=src.splitlines(keepends=True)
for n in sorted([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in replacements],key=lambda n:n.lineno,reverse=True):lines[n.lineno-1:n.end_lineno]=[replacements[n.name]]
src=''.join(lines);src=src.replace('H2-COUPLE first Fold C training entry','H2 Fold D two-mode training entry')
a=src.index('H2 = ');b=src.index('\nFROZEN_BASELINES',a);common=ast.literal_eval(src[a+5:b]);common.pop('mode');src=src[:a]+'H2_COMMON = '+repr(common)+src[b:]
a=src.index('FROZEN_BASELINES = ');b=src.index('\nCURRENT_IDENTITY',a)
src=src[:a]+"FROZEN_BASELINES = {'D': {'request_sha256':'55793bca2fa9472d45b3cca0b9598154cdb12a84a3eb89633daa52b85a039d5f','audit_sha256':'f65c3dd7d82814f705a09f11f5fa95f2583fba71380cdd29cd8b9f4f59e5bb61'}}"+src[b:]
a=src.index('AUX_PAIR_PINS = ');b=src.index('\ndef validate_static_h2',a)
src=src[:a]+'''def mode_config(mode):
    require(mode in ('AUX','COUPLE'),'AUX or COUPLE only')
    return dict(H2_COMMON,mode=mode)

def pair_read_roots(q):
    mode=mode_config(q['h2_config']['mode'])['mode']
    if mode=='AUX':
        require(q['aux_pairing'] is None,'AUX has no initialization reference to prior AUX')
        return []
    return [exact(q['aux_pairing']['initialization'])]

'''+src[b:]
old="Path(q['aux_pairing']['initialization']['path']),Path(q['implementation']['h2_range']['path']).parent"
assert src.count(old)==1;src=src.replace(old,"*pair_read_roots(q),Path(q['implementation']['h2_range']['path']).parent")
ast.parse(src)
with (S/'bcsp_h2_foldD_training_entry_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(src)
print('FOLDD_ENTRY_STATIC_PARSE_PASS')
