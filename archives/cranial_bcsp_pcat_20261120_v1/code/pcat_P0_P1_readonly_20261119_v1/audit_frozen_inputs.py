"""PCAT identity and index audit only. No model imports or geometry scoring."""
import hashlib
import io
import json
import tarfile
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
ROOT = OUT.parent
NATIVE = OUT / 'spcg_native_prediction_preparation_20261117_v1/implementation_v1'
SCORE = OUT / 'spcg_score_implementation_20261117_v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def verify(record, local=None):
    path = Path(local or record['path'])
    assert path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)), path
    data = path.read_bytes()
    assert (len(data), sha(data)) == (record['bytes'],record['sha256']), path
    return data


def sentinel():
    # Model-free equivalence check of the reviewed order, inverse, interleave and
    # coordinate-parent flatten operations. Coordinates encode the two labels.
    ids = np.arange(256)
    order = (73*ids + 19) % 256
    assert not np.array_equal(order,np.argsort(order))
    inverse = np.empty_like(order)
    inverse[order] = ids
    interleaved = np.stack([-1-ids[order],ids[order]],axis=1).reshape(-1)
    restored = interleaved[1::2][inverse]
    assert np.array_equal(restored,ids)
    parent = np.stack([1000*ids,np.zeros(256,int),np.zeros(256,int)],axis=1)
    offsets = np.zeros((256,32,3),int)
    offsets[:,:,1] = restored[:,None]
    offsets[:,:,2] = np.arange(32)
    expected = np.column_stack([np.repeat(ids,32)*1000,np.repeat(ids,32),np.tile(np.arange(32),256)])
    observed = (parent[:,None,:]+offsets).reshape(-1,3)
    assert np.array_equal(observed,expected)
    offsets[[0,1]] = offsets[[1,0]]
    assert not np.array_equal((parent[:,None,:]+offsets).reshape(-1,3),expected)
    return expected[:,0]//1000


def main():
    freeze = read(NATIVE/'post_prediction_freeze_v1/formal_freeze_result_v1.json')
    native_path = NATIVE/'pending_transport_v1/payload/SPCG_sixmodel_native_execution_request_v1.json'
    assert freeze['status']=='FORMAL_SPCG_NATIVE630_POST_PREDICTION_FREEZE_PASS' and all(freeze['checks'].values())
    assert sha(native_path.read_bytes())==freeze['request_sha256']
    q = read(native_path)
    audit = read(OUT/'spcg_score_freeze_20261117_v1/audit_verification_v1.json')
    score_path = SCORE/'SPCG_local_scoring_execution_request_v1.json'
    assert audit['status']=='FORMAL_SPCG_THREE_ARM_TWOFOLD_POST_SCORE_FREEZE_AUDIT_PASS' and all(audit['checks'].values())
    assert sha(score_path.read_bytes())==audit['request_sha256']
    score = read(score_path)
    scope = score['archive_inputs']['SPCG']
    assert scope['prediction_request_sha256']==freeze['request_sha256']
    assert all(scope['archive'][k]==freeze['archive'][k] for k in ('bytes','sha256'))
    ar = verify(scope['archive'])
    sidecars = {r['path'].rsplit('.',1)[-1]+str(i):verify(r) for i,r in enumerate(scope['sidecars'])}
    sidecar = next(v for v in sidecars.values() if b'predictions/' in v)
    contents = {}
    for line in sidecar.decode().splitlines():
        digest,name = line.split(maxsplit=1)
        assert name not in contents
        contents[name]=digest
    idx = json.loads(verify(score['score_case_index']))
    program = verify(score['implementation']['metrics'])
    compile(program,'<frozen-score-metrics>','exec')
    ni = json.loads(verify(q['input_index'],scope['prediction_index']['path']))
    roles = {'G1_C','G2_C','G1_D','G2_D'}
    byrun = {r['label']:r for r in ni['runs'] if r['label'] in roles}
    lookup = {(r['run'],r['case_id']):r for r in ni['inputs'] if r['run'] in roles}
    cases = {(r['fold'],r['case_id']):r for r in idx['cases']}
    preds = {(r['arm']+'_'+r['fold'],r['case_id']):r for r in idx['prediction_records'] if r['arm'] in ('G1','G2')}
    assert len(cases)==210 and len(preds)==len(lookup)==420 and preds.keys()==lookup.keys() and byrun.keys()==roles
    scores_raw = verify(audit['inventory']['output']['case_metrics.jsonl'],SCORE/'unified_scores_v1/case_metrics.jsonl')
    scored = {}
    for line in scores_raw.splitlines():
        row = json.loads(line)
        key = (row['arm']+'_'+row['fold'],row['case_id'])
        if key in lookup:
            assert key not in scored
            scored[key] = row
    assert scored.keys()==lookup.keys()
    sources = {}
    types = {'bilateral','frontoorbital','parietotemporal','random_1','random_2'}
    for (fold,cid),c in cases.items():
        sources.setdefault((fold,c['source_id']),set()).add(cid.split('__',2)[2])
        with np.load(io.BytesIO(verify(c['reference'])),allow_pickle=False) as ref:
            xyz,w,j,axes=(ref[k] for k in ('a_centers','a_weights','a_is_j','a_axes'))
            assert xyz.shape==(len(w),3) and w.shape==j.shape==axes.shape and j.dtype==np.bool_
            assert np.isfinite(xyz).all() and np.isfinite(w).all() and (w>0).all() and j.any() and (~j).any()
            assert ((axes>=0)&(axes<=2)).all() and ref['affine'].shape==(3,3) and np.isfinite(ref['affine']).all()
            assert ref['b_centers'].shape==(len(ref['b_weights']),3) and np.isfinite(ref['b_centers']).all() and np.isfinite(ref['b_weights']).all() and (ref['b_weights']>0).all()
        with np.load(io.BytesIO(verify(c['point_file'])),allow_pickle=False) as z:
            assert set(z.files)=={'partial','implant'}
            for k in z.files:
                array=z[k]
                assert array.shape==(8192,3) and array.dtype==np.float32 and np.isfinite(array).all()
                if k=='implant':
                    assert sha(array.tobytes())==c['target_array_sha256']
    assert len(sources)==42 and all(t==types for t in sources.values()) and Counter(f for f,_ in sources)=={'C':21,'D':21}
    assert not {s for f,s in sources if f=='C'} & {s for f,s in sources if f=='D'}
    with tarfile.open(fileobj=io.BytesIO(ar),mode='r:gz') as tar:
        members=tar.getmembers()
        assert len(members)==len(contents)==635 and {m.name for m in members}==contents.keys() and all(m.isfile() for m in members)
        manifest_raw=tar.extractfile('inference_manifest.jsonl').read()
        assert sha(manifest_raw)==contents['inference_manifest.jsonl']
        selected=[]
        for line in manifest_raw.splitlines():
            m=json.loads(line)
            if m['run'] in roles: selected.append(m)
        assert len(selected)==420 and {(r['run'],r['case_id']) for r in selected}==lookup.keys()
        for m in selected:
            key=(m['run'],m['case_id'])
            n,p,r=lookup[key],preds[key],scored[key]
            c=cases[m['fold'],m['case_id']]
            assert all(m[k]==n[k] for k in ('source_id','fold','normalization','variant','n_input','n_output'))
            assert m['normalization']==c['normalization'] and c['normalization_source']=='defective_bbox'
            assert m['input_sha256']==n['input']['sha256']==c['point_file']['sha256']
            assert m['checkpoint_sha256']==byrun[m['run']]['checkpoint']['sha256']
            assert r['source_id']==c['source_id']==m['source_id'] and r['status']=='OK'
            assert r['stage_geometry']['coarse']['tensor_saved'] and r['stage_geometry']['coarse']['points']==256 and r['stage_geometry']['dense_points']==8192
            filename=p['member']
            assert filename==m['prediction']['name']==n['prediction_filename']
            payload=tar.extractfile(filename).read()
            assert len(payload)==m['prediction']['bytes']==p['bytes']
            assert sha(payload)==p['sha256']==m['prediction']['sha256']==contents[filename]
            with np.load(io.BytesIO(payload),allow_pickle=False) as z:
                assert z.files==['prediction','coarse']
                for name, count in [('prediction',8192),('coarse',256)]:
                    a=z[name]
                    assert a.shape==(count,3) and a.dtype==np.float32 and np.isfinite(a).all()
    local_sources = {
        'mother_source':('p1pub/models/AdaPoinTr.py',q['mother_source']),
        'static_config':('p1pub/archives/cranial_bcsp_trace_20261117_v1/bound_shared_sources/86dbbb7b216a_static_training_config_v1.json',q['static_config']),
        'entry':('spcg_native_prediction_preparation_20261117_v1/implementation_v1/bcsp_spcg_sixmodel_native_predict_v1.py',q['entry']),
    }
    for key, path in {
        'encoder':'cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_mamba_encoder_v1.py',
        'factory':'cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_model_factory_v1.py',
        'head':'spcg_implementation_20261116_v1/bcsp_spcg_head_v1.py',
        'spcg_factory':'spcg_implementation_20261116_v1/bcsp_spcg_factory_v1.py',
        'lqi_factory':'cranial_bcsp_fullmamba_20261110/lqi_implementation_v1/bcsp_lqi_factory_v1.py',
        'lqi_decoder':'cranial_bcsp_fullmamba_20261110/lqi_implementation_v1/bcsp_lqi_decoder_v1.py',
    }.items():
        local_sources[key]=(path,q['implementation'][key])
    bindings={}
    for key,(name,record) in local_sources.items():
        verify(record,OUT/name)
        bindings[key]=dict(local_path=name,**record)
    config=read(OUT/local_sources['static_config'][0])['model']
    assert (config['decoder_type'],config['num_query'],config['num_points'],config['query_selection'])==('fc',256,8192,'learned_only')
    historical=OUT/'coarse_dense_full_review_20261118_v1/summary_v2.json'
    assert sha(historical.read_bytes())=='6e56776be1059133c0ba1a3a6a24f4ccd84c65e6910f99e7bc39880308545238'
    parent=sentinel()
    assert np.array_equal(parent,np.arange(8192)//32) and np.array_equal(np.bincount(parent),np.full(256,32))
    parent_bytes=json.dumps(parent.tolist(),separators=(',',':')).encode()
    result=dict(status='IDENTITY_AND_INDEX_CHECKS_COMPLETE',predictions=420,cases=210,references=210,point_sets=210,sources=42,archive_members=635,
                native_request_sha256=freeze['request_sha256'],score_request_sha256=audit['request_sha256'],
                source_bindings=bindings,reference_contract=score['implementation']['metrics'],
                checkpoint_identities={k:v['checkpoint']['sha256'] for k,v in byrun.items()},
                parent_map_sha256=sha(parent_bytes),parent_rule='saved_P_index // 32',
                sentinel='Non-involutive permutation, interleave/suffix selection, inverse, offsets, parent-major flatten and adversarial group swap',
                native_instrumentation_replayed=False,new_forward=0,new_training=0,new_scores=0)
    with (HERE/'parent_id_v1.json').open('xb') as f:f.write(parent_bytes)
    with (HERE/'audit_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_bindings','reference_contract','checkpoint_identities')}))


if __name__=='__main__':
    main()
