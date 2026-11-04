# -*- coding: utf-8 -*-
"""Prepare only paired Fold C train inputs, static protocol and pending readiness."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
import hashlib,json,shutil,sys,time
from pathlib import Path
import numpy as np
B=Path(__file__).resolve().parent;O=B/'sampling_model_AB_foldC_seed0_20261103_v1';E=B/'spatial_stratified_expanded_20261103_v1'
SB=B/'real_data_qc_v1';OLD=B/'first_run_freeze_foldC_8192_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def arrsha(a):return hashlib.sha256(a.tobytes()).hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def permutation(cid):
    digest=hashlib.sha256(('BCSP_SAMPLING_AB_V1|point-order|'+cid).encode('ascii')).digest()
    return np.random.Generator(np.random.PCG64(int.from_bytes(digest[:8],'big'))).permutation(8192)
def main():
    start=time.monotonic();assert not O.exists();O.mkdir()
    for arm in ['V1','Morton_area_stratified8k']:(O/arm/'points').mkdir(parents=True)
    foldfile=B/'consolidated_binding_v1/fold_binding.json'
    fold=json.loads(foldfile.read_text(encoding='utf-8'))['folds']['C']
    ids=fold['train_case_ids'];assert len(ids)==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21
    assert not set(fold['train_sources'])&set(fold['dev_sources'])
    original={r['case_id']:r for r in map(json.loads,(SB/'manifest_8192.jsonl').read_text(encoding='utf-8').splitlines())}
    expanded={r['raw_case_id']:r for r in json.loads((E/'all_case_results.json').read_text(encoding='utf-8')) if r['dataset']=='SkullBreak'}
    plan=json.loads((OLD/'shared_order_foldC_seed0_v1.json').read_text(encoding='utf-8'));assert plan['case_ids']==ids
    assert len(plan['epochs'])==100 and all(len(e['batches'])==39 and len(e['dropped'])==3 for e in plan['epochs'])
    assert all(len(batch)==8 for e in plan['epochs'] for batch in e['batches'])
    impls=[Path(__file__),foldfile,SB/'manifest_8192.jsonl',E/'all_case_results.json',E/'completion.json',E/'artifact_manifest.json',OLD/'static_training_config_v1.json',OLD/'shared_order_foldC_seed0_v1.json',B/'spatial_stratified_pilot_v1.py']
    frozen={str(p):sha(p) for p in impls};records={a:[] for a in ['V1','Morton_area_stratified8k']};pairs=[]
    for i,cid in enumerate(ids):
        r=original[cid];x=expanded[cid];assert r['source_id'] in fold['train_sources']
        p=SB/r['point_path'];assert sha(p)==r['sha256']
        with np.load(p,allow_pickle=False) as z:base=z['partial'].copy();target=z['implant'].copy()
        assert base.shape==target.shape==(8192,3) and base.dtype==target.dtype==np.float32 and arrsha(target)==r['target_array_sha256']
        er=next(m for m in x['metrics'] if m['seed']==0 and m['method']=='Morton_area_stratified8k')
        ep=E/er['sample_path'];assert sha(ep)==er['sample_sha256']
        with np.load(ep,allow_pickle=False) as z:
            candidate=z['partial'].copy();assert np.array_equal(z['center'],np.array(r['normalization']['center'])) and float(z['scale'])==r['normalization']['scale']
            assert np.array_equal(candidate,((z['xyz']-z['center'])/z['scale']).astype(np.float32))
        perm=permutation(cid);assert np.array_equal(np.sort(perm),np.arange(8192))
        orderhash=arrsha(perm.astype('<i8'));original_hashes={}
        for arm,points in [('V1',base),('Morton_area_stratified8k',candidate)]:
            assert np.isfinite(points).all();partial=points[perm].copy()
            path=O/arm/'points'/f'{cid}_8192.npz'
            with path.open('xb') as f:np.savez_compressed(f,partial=partial,implant=target)
            with np.load(path,allow_pickle=False) as z:
                assert set(z.files)=={'partial','implant'} and np.array_equal(z['partial'],partial) and np.array_equal(z['implant'],target)
                assert np.array_equal(z['partial'][np.argsort(perm)],points)
            rec={**r,'point_path':str(path.relative_to(O/arm)).replace('\\','/'),'sha256':sha(path),
                'sampler_arm':arm,'sampling_seed':0,'common_point_order_sha256':orderhash,
                'source_point_file':str(p if arm=='V1' else ep),'source_point_sha256':r['sha256'] if arm=='V1' else er['sample_sha256']}
            records[arm].append(rec);original_hashes[arm]=arrsha(points)
        pairs.append({'case_id':cid,'source_id':r['source_id'],'target_array_sha256':r['target_array_sha256'],
            'normalization':r['normalization'],'common_permutation_sha256':orderhash,'original_partial_array_sha256':original_hashes})
        if (i+1)%50==0:print('PAIRED',i+1,flush=True)
        assert time.monotonic()-start<600
    for arm,rr in records.items():
        with (O/arm/'train_manifest_8192.jsonl').open('x',encoding='utf-8') as f:
            for r in rr:f.write(json.dumps(r,ensure_ascii=False)+'\n')
    dump(O/'paired_train_data_receipt.json',{'status':'PAIRED_315_TRAIN_INPUTS_VERIFIED_NOT_GPU_READY','cases':315,'sources':63,'arms':list(records),
        'input':8192,'target':8192,'sampling_seed':0,'target_and_frame_equal':True,'same_permutation_per_case':True,
        'permutation_algorithm':'SHA256(ASCII BCSP_SAMPLING_AB_V1|point-order|case_id) first8 bytes big-endian -> PCG64 -> permutation(8192); stored index hash uses little-endian int64',
        'point_geometry_unchanged':True,'development_payload_read_or_prepared':False,'pairs':pairs,
        'source_metadata_sha256':frozen,'seconds':time.monotonic()-start})
    config=json.loads((OLD/'static_training_config_v1.json').read_text(encoding='utf-8'))
    config['stage']='BCSP_SAMPLING_AB_V1';dump(O/'static_training_config_v1.json',config)
    with (O/'shared_order_foldC_seed0_v1.json').open('xb') as f:f.write((OLD/'shared_order_foldC_seed0_v1.json').read_bytes())
    dump(O/'comparison_protocol_v1.json',{'status':'SCIENTIFIC_SCOPE_FIXED_EXECUTION_NOT_AUTHORIZED','stage':'BCSP_SAMPLING_AB_V1',
        'design':'one Fold C, seed0, fresh matched V1 vs frozen Morton area-stratified, two training runs total',
        'historical_baseline_role':'historical reference only; not the main matched comparator because common input-order policy differs',
        'model':'unchanged B0 AdaPoinTr Transformer; not Mamba','fold':'C','seed':0,'sampling_seed':0,
        'train_sources':fold['train_sources'],'train_case_ids':ids,'development_sources':fold['dev_sources'],
        'development_case_ids':fold['dev_case_ids'],'counts':config['counts'],'model_config':config['model'],
        'training_config':config['training'],'resources_per_run':config['resources'],
        'extra_training_contract':{'LR':'max(0.9**(e/21),0.02), epoch end','BN_momentum':'max(0.9*0.5**(e/21),0.01), epoch start',
            'KNN':'all keys, query chunk256','PointNet2':'same bound native provider in both arms','loss':'same torch.cdist Chamfer branch',
            'deterministic':True,'TF32':False,'AMP':False,'augmentation':'no new augmentation',
            'initialization':'both scratch, seed0, parameter and persistent-state hashes must agree before training',
            'batch_order':'byte-identical shared order, 100 traversals x39 updates, 31200 used exposures and300 drops per arm'},
        'input_order':'same fixed per-case PCG64 permutation in both arms, never per-epoch shuffling; target order unchanged',
        'evaluation_plan':{'requires_later_separate_authorization':True,'sources':21,'cases_per_arm':105,'total_forward_calls':210,
            'model_mode':'native eval with final weights, no BNCal/voting/TTA','normalization':'D-only frame inverse to mm',
            'main_question':'does balanced input improve G unknown native surface E while preserving contact wall J?',
            'primary_endpoint':'source-mean E_G to prediction area-weighted P95, inherited A1 full native G face reference',
            'key_secondary':['J_G P95','J_G Cover@2mm','E_G Cover@2mm','same fixed GT8192 CD-L1'],
            'aggregation':'five defects then source equal; descriptive deltas; one-fold one-seed pilot, no final gate or significance claim'},
        'prohibitions':['no SkullFix/MUG training','no Fold D or extra seed','no 16k/proxy/output change','no automatic training/eval/BNCal/resume/retry'],
        'readiness':'current server identity/assets, training entry task registration and final hash-bound request still required'})
    dump(O/'readiness_gaps_v1.json',{'status':'NOT_AN_EXECUTION_REQUEST','training_authorized':False,
        'complete':['paired training data with equal targets/frames/common point permutation','fixed Fold C scientific protocol and counts','identical historical batch order'],
        'remaining':['current v2iwsa resource/source/provider read-only checks','one bounded new-stage data/authorization entry adaptation and CPU contract verification',
            'future transport scope and non-overwrite deployment binding','final execution request bound to finished implementation/current resource; separate full-hash authorization'],
        'no_runtime_authorization_or_launcher_materialized':True})
    for p,h in frozen.items():assert sha(p)==h
    files={str(p.relative_to(O)).replace('\\','/'):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file()}
    dump(O/'local_preparation_manifest.json',{'status':'LOCAL_DATA_AND_PROTOCOL_PREPARED','files':files,'excludes_future_server_evidence':True})
    print('LOCAL_AB_PREPARATION_PASS',len(files),sum(x['bytes'] for x in files.values()))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
