"""Local, bounded derivation of the isolated H2-AUX entry. No execution on server."""
import ast
from pathlib import Path

S=Path(__file__).resolve().parent
P=S.parent/'H1_implementation_v1/bcsp_p2_h1_training_entry_v1.py'
source=P.read_text(encoding='utf-8')
tree=ast.parse(source)
replacements={}
replacements['validate_static_h1']='''def validate_static_h2(static, baseline, metadata):
    import copy
    stripped=copy.deepcopy(static)
    require(stripped.pop('H2',None)==H2,'unique H2-AUX config')
    require(stripped==baseline,'only top-level H2 config changes')
    metadata.validate_static(baseline)
    require(static['counts']==COUNTS and static['resources']==RESOURCES,'counts/resources')
    require(not static['model'].get('coarse_geometry_guard',{}).get('enabled',False),'H1 off')
    return static
'''
replacements['validate_model_h1']='''def validate_model_h2(model):
    import torch
    require(model.num_query==256 and model.num_points==8192 and model.factor==32
            and model.decoder_type=='fc' and model.denoise_weight==0
            and model.fine_coverage_weight==1 and model.fine_local_weight==0,'model contract')
    b=model.base_model
    require(b.center_num==[512,256] and b.encoder_type=='graph' and b.query_selection=='learned_only'
            and not b.use_denoise and not b.encoder_adapter.enabled and not model.scqr_contract.enabled,'backbone')
    for name in ('coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled'):
        require(getattr(model,name) is False,'optional path '+name)
    require(model.h2_metadata()==H2,'actual AUX metadata')
    head=model.h2_range_head
    require(set(head.state_dict())=={'weight','bias'} and tuple(head.weight.shape)==(1,1024)
            and tuple(head.bias.shape)==(1,) and sum(p.numel() for p in head.parameters())==1025,'exact head')
    require(all(p.device.type=='cpu' and p.dtype==torch.float32 and torch.count_nonzero(p).item()==0
                for p in head.parameters()),'scratch zero head; synthetic CUDA fixture bias forbidden')
'''
replacements['authorize']='''def authorize(qr,ar,rr):
    q=json_bound(qr);base=json_bound(q['baseline_request'])
    extra={'baseline_request','baseline_audit','p3','h2_config','cuda_audit','readiness'}
    require(set(q)==set(base)|extra,'exact request fields')
    require(q['schema']=='bcsp-p2-H2-AUX-training-request-v1'
            and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'
            and q['stage']=='CRANIAL_BCSP_MAMBA_P2_H2' and q['variant']=='M0'
            and q['fold']=='C' and q['n_input']==q['n_output']==8192,'first AUX C only')
    pin=FROZEN_BASELINES['C']
    require(q['baseline_request']['sha256']==pin['request_sha256']
            and q['baseline_audit']['sha256']==pin['audit_sha256'],'frozen M0 baseline')
    audit=json_bound(q['baseline_audit'])
    require(audit['status']=='FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS'
            and audit['request_sha256']==pin['request_sha256']
            and audit['checks_passed']==len(audit['checks'])>0 and all(audit['checks'].values()),'baseline audit')
    changed={'schema','stage','run_id','static_config','implementation','output','launch_attempt',
             'launch_contract','provenance','not_authorized','identity','environment'}
    require(all(q[k]==v for k,v in base.items() if k not in changed),'original scientific pairing')
    require(base['variant']=='M0' and base['fold']=='C' and q['h2_config']==H2,'H2-only scientific delta')
    require(q['identity']==CURRENT_IDENTITY,'frozen current resource binding')
    require(set(q['environment'])==set(base['environment'])
            and all(v==base['environment'][k] for k,v in q['environment'].items() if k!='CUDA_VISIBLE_DEVICES')
            and q['environment']['CUDA_VISIBLE_DEVICES']==CURRENT_IDENTITY['gpu_uuid'],'environment pairing')
    require(set(q['implementation'])==set(base['implementation'])|{'h2_range','h2_adapter'},'implementation set')
    for k,v in base['implementation'].items():
        if k not in ('entry','runtime'):require(q['implementation'][k]==v,'reused implementation '+k)
    for k,h in H2_HASHES.items():require(q['implementation'][k]['sha256']==h,'final H2 source '+k)
    for v in q['implementation'].values():exact(v)
    require(exact(q['implementation']['entry'])==Path(__file__).absolute(),'entry origin')
    cuda=json_bound(q['cuda_audit']);require(q['cuda_audit']['sha256']==CUDA_AUDIT_SHA
            and cuda['status']=='FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS','formal CUDA evidence')
    p3=json_bound(q['p3'])
    require(p3['status']=='LOCAL_H2_AUX_TRAINING_ENTRY_P3_PASS'
            and p3['entry_sha256']==q['implementation']['entry']['sha256']
            and p3['H2_source_hashes']==H2_HASHES,'P3 final source binding')
    ready=json_bound(q['readiness'])
    require(ready['status']=='BOUNDED_H2_AUX_C_READINESS_PASS'
            and ready['identity']==CURRENT_IDENTITY and ready['training_payloads']==315,'bounded readiness')
    a,r=json_bound(ar),json_bound(rr)
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'}
            and a['schema']=='bcsp-p2-H2-training-authorization-v1' and a['request_sha256']==qr['sha256']
            and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate authorization')
    require(r==dict(schema='bcsp-p2-H2-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
    metadata=load_bound('bcsp_training_contract_v1',q['implementation']['contract'])
    static=validate_static_h2(json_bound(q['static_config']),json_bound(base['static_config']),metadata)
    selected,fold=metadata.verify_qualified_receipt(json_bound(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192)
    plan=metadata.validate_order(json_bound(q['order_plan']),fold['train_case_ids'])
    return q,static,metadata,selected,fold,plan
'''
replacements['dispatch_training']='''def dispatch_training(q,static,selected,fold,plan,*,factory,h2_adapter,model_builder,runtime,helper,budget,torch,knn_enable,expected_factory,device='cuda:0'):
    require(q['variant']=='M0' and q['fold']=='C' and static['H2']==H2,'H2-AUX C dispatch')
    model,evidence=h2_adapter.build_h2(factory,model_builder,'AUX',seed=0)
    require({k:v for k,v in evidence.items() if k not in ('H2_mode','H2_contract','common_state_after_H2_unchanged')}==expected_factory
            and not evidence['artificial_fixture'],'frozen real initialization')
    require(evidence['H2_mode']=='AUX' and dict(evidence['H2_contract'],mode='AUX')==H2
            and evidence['common_state_after_H2_unchanged'] is True,'H2 common initialization')
    validate_model_h2(model)
    dataset=runtime.BCSPDataset(q['data_root'],selected,fold['train_sources'],8192)
    budget.first_step_evidence=dict(factory=evidence,H2_head_initialization='ALL_ZERO_NO_RNG_DRAW')
    budget.run_identity=dict(stage=q['stage'],variant='M0',fold='C',seed=0,H2=H2,
        numeric_policy_sha256=q['numeric_policy']['sha256'],CUDA_audit_sha256=q['cuda_audit']['sha256'],
        checkpoint_legacy_stage='BCSP_INPUT_DENSITY_V1',legacy_stage_is_provenance_only=True,
        SSM_gradient_non_bitwise_reproducibility_disclosed=True)
    return runtime.train_lifecycle(model,lambda e:runtime.make_loader(dataset,plan,e),selected,plan,q['output'],device=device,numeric_check=helper.assert_numeric,resources=budget,knn_enable=knn_enable,state_fingerprint=helper.state_sha)
'''
lines=source.splitlines(keepends=True)
for n in sorted([n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in replacements],key=lambda n:n.lineno,reverse=True):
    lines[n.lineno-1:n.end_lineno]=[replacements[n.name]]
source=''.join(lines)
a=source.index('H1 = dict(');b=source.index('\n\ndef validate_static_h2',a)
import json
cuda=json.loads((S.parent/'H2_cuda_admission_v1/H2_artificial_cuda_execution_request_v1.json').read_bytes())
constants="H2 = "+repr(dict(version='H2-range-soft-coupling-v1',feature_dim=1024,coarse_points=256,head_parameters=1025,beta=.1,aux_weight=.1,maximum_scale=1.25,minimum_radius=1e-6,epsilon_added_to_radius=False,detach_Q_in_aux_target=True,detach_delta_in_coupling=True,mode='AUX'))+'\n'
constants+="FROZEN_BASELINES = {'C': {'request_sha256':'48dedc867ce2a9c46bc1a6fdc7db3506b6f2405dbdf914de49cf561e2fe12b54','audit_sha256':'bcbfb9a65742ab7c9da4a2d01c55b5f9a78bc77da66e38cf078f3074e0968815'}}\n"
constants+='CURRENT_IDENTITY = '+repr(cuda['identity'])+'\n'
constants+="H2_HASHES = {'h2_range':'ffdd06efa1c4c45339eea3d3d75bcc4b39aadb3561943cec0cc1727baa00d825','h2_adapter':'130939f3bfee8e11b2fefbb26f96b644056134e4bc1b776bebf99cf56edd4330','runtime':'d39bef924e459f6509a3f9d7829317a3ddddbfd822aa838d28c30480ebcb190c'}\n"
constants+="CUDA_AUDIT_SHA = '545a5996309fbc865beb145f4a1df4aef5e2077e4374d52a6fc930dd9080313c'"
source=source[:a]+constants+source[b:]
source=source.replace('P1 first T0 training entry','H2-AUX first Fold C training entry')
source=source.replace("PROJECT+'/logs/cranial_bcsp_mamba_p2_h1'","PROJECT+'/logs/cranial_bcsp_mamba_p2'")
source=source.replace(" and not helper.smi('pid',True)",'')
source=source.replace('sys.path[:0]=[str(factory_root)', 'sys.path[:0]=[str(impl),str(factory_root)')
source=source.replace("{k:v for k,v in static['model'].items() if k != 'coarse_geometry_guard'}", "static['model']")
source=source.replace("'H1-only model config delta'","'unchanged model config'")
source=source.replace("        runtime=load_bound('p1_frozen_training_runtime'", "        load_bound('bcsp_h2_range_v1',q['implementation']['h2_range'])\n        h2_adapter=load_bound('bcsp_h2_model_adapter_v1',q['implementation']['h2_adapter'])\n        runtime=load_bound('p1_frozen_training_runtime'")
source=source.replace('plan,factory=factory,model_builder=', 'plan,factory=factory,h2_adapter=h2_adapter,model_builder=')
ast.parse(source)
target=S/'bcsp_h2_aux_foldC_training_entry_v1.py'
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(source)
print(target)
