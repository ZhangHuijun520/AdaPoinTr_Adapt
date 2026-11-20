"""Bounded CPU pilot on frozen predictions. No model or checkpoint is loaded."""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tarfile
import time
from pathlib import Path

import numpy as np
import psutil
from scipy.spatial import cKDTree


def checked(record):
    path = Path(record['path'])
    assert path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), path
    data = path.read_bytes()
    assert len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['sha256'], path
    return data


def parent_footprints(ref, dense, parent_id, tick=lambda:None, dense_distance=None):
    tree = cKDTree(ref)
    counts = np.zeros(len(ref),np.uint16)
    footprints, largest, total = [], 0, 0
    for parent in np.unique(parent_id):
        sub = dense[parent_id==parent]
        # Expand candidate search by one ULP. Apply the frozen <=2 mm test
        # independently and never truncate a returned neighborhood.
        radius = np.nextafter(2.,np.inf)
        hits=[]
        for start in range(0,len(sub),8):
            block=sub[start:start+8]
            sizes=tree.query_ball_point(block,radius,eps=0,return_length=True)
            largest=max(largest,int(sizes.max()))
            assert int(sizes.sum())<=262144,'candidate-neighbor bound'
            for point, indices in zip(block,tree.query_ball_point(block,radius,eps=0)):
                indices=np.asarray(indices,dtype=np.intp)
                distances=np.linalg.norm(ref[indices]-point,axis=1)
                hits.append(indices[distances<=2.])
        passing=np.unique(np.concatenate(hits))
        total+=len(passing)
        assert total<=8_388_608,'retained footprint index bound'
        footprints.append(passing)
        counts[passing]+=1
        if len(footprints)%16==0:tick()
    direct=(cKDTree(dense).query(ref)[0] if dense_distance is None else dense_distance)<=2.
    assert np.array_equal(counts>0,direct),'parent union differs from direct dense support'
    return counts,footprints,largest


def area(w, mask):
    return float(w[mask].sum(dtype=np.float64))


def region_stats(w, region, stratum, n, footprints):
    eligible=region&stratum
    denominator=area(w,region)
    assert denominator>0
    covered=eligible&(n>0)
    unique=eligible&(n==1)
    shared=eligible&(n>=2)
    shares=np.zeros_like(w)
    shares[covered]=w[covered]/n[covered]
    exclusive=w*unique
    credits=[float(shares[h].sum()/denominator) for h in footprints]
    exclusive_credits=[float(exclusive[h].sum()/denominator) for h in footprints]
    cover=area(w,covered)/denominator
    unq=area(w,unique)/denominator
    multi=area(w,shared)/denominator
    zero=area(w,eligible&~covered)/denominator
    fraction=area(w,eligible)/denominator
    assert abs(unq+multi-cover)<1e-10 and abs(unq+multi+zero-fraction)<1e-10
    assert abs(sum(credits)-cover)<1e-10 and abs(sum(exclusive_credits)-unq)<1e-10
    return dict(area=fraction,cover=cover,unique=unq,multi=multi,zero=zero,
                conditional_cover=cover/fraction if fraction>=.01 else None,
                share_credit=credits,exclusive_credit=exclusive_credits)


def artificial():
    below=np.nextafter(2.,0.)
    above=np.nextafter(2.,np.inf)
    ref=np.array([[below,0,0],[2.,0,0],[above,0,0],[0.,5,0]],dtype=np.float64)
    p=np.array([[0.,0,0],[0.,0,0],[2.,0,0]],dtype=np.float64)
    parent=np.array([0,0,1])
    n,foot,_=parent_footprints(ref,p,parent)
    np.testing.assert_array_equal(n,[2,2,1,0])
    r=region_stats(np.ones(4),np.ones(4,bool),np.ones(4,bool),n,foot)
    assert r['cover']==.75 and r['unique']==.25 and r['multi']==.5 and r['zero']==.25
    # A valid-sized wrong map must be rejected by the bound slot indices,
    # even though union/support tests alone cannot prove its lineage.
    expected=np.arange(8192)//32
    wrong=expected.copy()
    wrong[:64]=np.roll(wrong[:64],32)
    assert np.array_equal(np.bincount(wrong),np.bincount(expected)) and not np.array_equal(wrong,expected)
    assert region_stats(np.ones(4),np.ones(4,bool),np.zeros(4,bool),n,foot)['conditional_cover'] is None
    print(json.dumps(dict(status='PASS',tests=['2mm boundary','same-parent deduplication','direct union','area and share conservation','wrong-index distinction','empty-fraction NA'],real_cases=0)))


def exact_distances(tree, points):
    # Preserve the frozen scorer's exact 65536-row chunk size and query settings.
    points=np.asarray(points,np.float64)
    return np.concatenate([tree.query(points[i:i+65536],workers=2)[0]
                           for i in range(0,len(points),65536)])


def score_from_distances(points, metric, ref_sets, reference_trees, gt):
    prediction_tree=cKDTree(points)
    forward={name:exact_distances(prediction_tree,xyz) for name,(xyz,_,_) in ref_sets.items()}
    reverse={name:exact_distances(tree,points) for name,tree in reference_trees.items() if name!='GT'}
    groups={}
    for name in ('A1','A2'):
        xyz,w,j=ref_sets[name]
        groups[name]={label:metric.stats(forward[name][mask],w[mask])
                      for label,mask in [('all',np.ones(len(xyz),bool)),('E',~j),('J',j)]}
    groups['B']=dict(all=metric.stats(forward['B'],ref_sets['B'][1]),
                     E=None,J=None,partition_status='NO_EXACT_MC_INTERFACE_LABELS')
    reverse_stats={}
    for name, values in reverse.items():
        reverse_stats[name]=dict(**metric.stats(values),
                                 outlier_fraction={str(t):float(np.mean(values>t)) for t in metric.TAUS})
    cd=.5*(float(exact_distances(reference_trees['GT'],points).mean())
           +float(exact_distances(prediction_tree,gt).mean()))
    score=dict(status='OK',point_count=len(points),duplicate_points=int(len(points)-len(np.unique(points,axis=0))),
               primary_E_G_P95_mm=groups['A1']['E']['p95_mm'],regions=groups,
               reverse_discrete_reference=reverse_stats,CD_L1_mm=cd)
    return score,forward,reverse['A2']


def run_case(pair, parent_id, metric, tar, frozen_rows, tick):
    started=time.monotonic()
    with np.load(io.BytesIO(checked(pair['reference'])),allow_pickle=False) as z:
        ref={k:z[k] for k in z.files}
    with np.load(io.BytesIO(checked(pair['point_file'])),allow_pickle=False) as z:
        assert hashlib.sha256(z['implant'].tobytes()).hexdigest()==pair['target_array_sha256']
        gt=metric.world_points(z['implant'],pair['normalization'])
    xyz,w,j=ref['a_centers'],ref['a_weights'],ref['a_is_j']
    a2,w2,j2=metric.a2_reference(ref)
    ref_sets={'A1':(xyz,w,j),'A2':(a2,w2,j2),'B':(ref['b_centers'],ref['b_weights'],None)}
    reference_trees={'A2':cKDTree(a2),'B':cKDTree(ref['b_centers']),'GT':cKDTree(gt)}
    clouds, result={}, {}
    for arm,pred in pair['predictions'].items():
        tick()
        member=tar.getmember(pred['member'])
        assert member.isfile() and member.size==pred['bytes']
        blob=tar.extractfile(member).read()
        assert hashlib.sha256(blob).hexdigest()==pred['sha256']
        with np.load(io.BytesIO(blob),allow_pickle=False) as z:
            assert z['coarse'].shape==(256,3) and z['prediction'].shape==(8192,3)
            q,p=(metric.world_points(z[k],pair['normalization']) for k in ('coarse','prediction'))
        assert np.isfinite(q).all() and np.isfinite(p).all()
        old=frozen_rows[pair['fold'],pair['case_id'],arm]
        dense,dp,rp=score_from_distances(p,metric,ref_sets,reference_trees,gt)
        coarse,dq,rq=score_from_distances(q,metric,ref_sets,reference_trees,gt)
        for region in ('E','J'):
            for tau in ('0.5','1.0','2.0'):
                assert abs(dense['regions']['A1'][region]['coverage'][tau]-old['metrics'][f'{region}_coverage_{tau}mm'])<=1e-12
            assert abs(dense['regions']['A1'][region]['p95_mm']-old['metrics'][f'{region}_P95_mm'])<=1e-9
        assert abs(dense['CD_L1_mm']-old['metrics']['CD_L1_mm'])<=1e-9
        qfar=rq>20.
        pfar=rp>20.
        assert float(pfar.mean())==old['metrics']['reverse_A2_outlier_20.0mm']
        placement=float(np.linalg.norm(p.mean(0)-gt.mean(0)))
        radius=metric_radius_ratio(p,gt)
        assert abs(placement-old['metrics']['centroid_offset_mm'])<=1e-9
        assert abs(radius-old['metrics']['radius_gyration_ratio'])<=1e-9
        risk=dict(placement_tail=placement>20.,compact_distribution=radius<.9,
                  severe_geometry=dense['primary_E_G_P95_mm']>20. or dense['regions']['A1']['J']['coverage']['2.0']==0.)
        assert risk==old['risk_labels']
        for region,value in pair['historical_coarse_A1_P95_mm'][arm].items():
            assert abs(coarse['regions']['A1'][region]['p95_mm']-value)<=1e-9
        assert abs(np.linalg.norm(q.mean(0)-gt.mean(0))-old['stage_geometry']['coarse']['centroid_offset_mm'])<=1e-9
        n,foot,max_hits=parent_footprints(xyz,p,parent_id,tick,dense_distance=dp['A1'])
        clouds[arm]=dict(n=n,foot=foot,q=dq['A1']<=2.,q2=dq['A2']<=2.,p2=dp['A2']<=2.)
        result[arm]=dict(coarse=coarse,dense=dense,risk=risk,max_neighbors_per_child=max_hits,
            far_transition={f'parent_{a}_child_{b}':float(np.mean((qfar[parent_id]==a)&(pfar==b))) for a in (False,True) for b in (False,True)})
    a,b=(clouds[k] for k in ('G1','G2'))
    result['regions']={}
    for label,region,region2 in [('E',~j,~j2),('J',j,j2)]:
        W=area(w,region)
        stages={f'S{a0}{b0}':(a['q']==bool(a0))&(b['q']==bool(b0)) for a0 in (0,1) for b0 in (0,1)}
        output={}
        for arm in ('G1','G2'):
            v=clouds[arm]
            mask=v['n']>0
            gain=area(w,region&~v['q']&mask)/W
            loss=area(w,region&v['q']&~mask)/W
            assert abs((area(w,region&mask)-area(w,region&v['q']))/W-gain+loss)<1e-10
            strata={k:region_stats(w,region,s,v['n'],v['foot']) for k,s in stages.items()}
            assert abs(sum(x['area'] for x in strata.values())-1)<1e-10
            output[arm]=dict(gain=gain,loss=loss,strata=strata,
                multi=sum(s['multi'] for s in strata.values()))
        common=region&stages['S11']&(a['n']>0)&(b['n']>0)
        s1,s2=(output[k]['strata']['S00'] for k in ('G1','G2'))
        matched2=region2&~a['q2']&~b['q2']
        W2=area(w2,region2)
        area2=area(w2,matched2)
        delta2=area(w2,matched2&b['p2'])-area(w2,matched2&a['p2'])
        common_area=area(w,common)
        delta_shared=area(w,common&(b['n']>=2))-area(w,common&(a['n']>=2))
        output.update(delta00=(s2['conditional_cover']-s1['conditional_cover']) if s1['conditional_cover'] is not None else None,
            delta_abs00=s2['cover']-s1['cover'],
            delta_multi=output['G2']['multi']-output['G1']['multi'],
            delta_shared_multi=delta_shared/W,
            delta_shared_multi_conditional=delta_shared/common_area if common_area else None,
            common_shared_area=common_area/W,
            a2_s00_area=area2/W2,
            a2_delta00=delta2/area2 if area2/W2>=.01 else None,
            a2_delta_abs00=delta2/W2)
        result['regions'][label]=output
    tick()
    return dict(fold=pair['fold'],case_id=pair['case_id'],reference_A1=len(xyz),reference_A2=len(a2),
                elapsed_seconds=time.monotonic()-started,results=result)


def metric_radius_ratio(p,gt):
    p0=p-p.mean(0)
    g0=gt-gt.mean(0)
    return float(np.sqrt(np.linalg.eigvalsh(p0.T@p0/len(p)).sum()/np.linalg.eigvalsh(g0.T@g0/len(gt)).sum()))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--artificial',action='store_true')
    parser.add_argument('--request')
    parser.add_argument('--request-sha256')
    parser.add_argument('--authorization')
    args=parser.parse_args()
    if args.artificial:
        return artificial()
    raw=Path(args.request).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==args.request_sha256
    spec=json.loads(raw)
    auth=json.loads(Path(args.authorization).read_bytes())
    assert spec['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'
    assert auth['request_sha256']==args.request_sha256 and auth['explicit_user_authorization'] is True
    assert Path(spec['entry']['path']).resolve()==Path(__file__).resolve()
    assert Path(spec['python']['path']).resolve()==Path(sys.executable).resolve()
    assert 0<len(spec['cases'])<=8 and {x['fold'] for x in spec['cases']}=={'C','D'}
    assert len({(x['fold'],x['case_id']) for x in spec['cases']})==len(spec['cases'])
    assert all(sum(x['fold']==f for x in spec['cases'])<=4 for f in 'CD')
    for name in ('entry','python','protocol','p01_decision','artificial_result','metric'):
        checked(spec[name])
    for rec in spec['packages'].values():checked(rec)
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    out=Path(spec['output'])
    assert shutil.disk_usage(out.parent).free>=spec['limits']['output_bytes']
    out.mkdir(exist_ok=False)
    with (out/'claim.json').open('x',encoding='utf-8') as f:json.dump(dict(request_sha256=args.request_sha256),f)
    t0=time.monotonic()
    process=psutil.Process()
    resources=[]
    def tick():
        r=dict(wall_seconds=time.monotonic()-t0,rss_bytes=process.memory_info().rss,
               output_bytes=sum(p.stat().st_size for p in out.iterdir() if p.is_file()))
        resources.append(r)
        assert all(r[k]<=spec['limits'][k] for k in r),r
    try:
        parent_id=np.asarray(json.loads(checked(spec['parent_map'])))
        assert np.array_equal(parent_id,np.arange(8192)//32)
        module=importlib.util.spec_from_file_location('bound_pcat_geometry',spec['metric']['path'])
        metric=importlib.util.module_from_spec(module)
        module.loader.exec_module(metric)
        hist={}
        identities={(p['fold'],p['case_id']) for p in spec['cases']}
        for line in checked(spec['historical_scores']).splitlines():
            row=json.loads(line)
            if (row['fold'],row['case_id']) in identities and row['arm'] in ('G1','G2'):
                key=(row['fold'],row['case_id'],row['arm'])
                assert key not in hist
                hist[key]=row
        assert len(hist)==2*len(spec['cases'])
        summary=[]
        with tarfile.open(fileobj=io.BytesIO(checked(spec['archive'])),mode='r:gz') as tar:
            for pair in spec['cases']:
                result=run_case(pair,parent_id,metric,tar,hist,tick)
                with (out/'cases.jsonl').open('a',encoding='utf-8') as f:json.dump(result,f,allow_nan=False);f.write('\n')
                summary.append({k:result[k] for k in ('fold','case_id','reference_A1','reference_A2','elapsed_seconds')})
        tick()
        evidence=dict(status='CPU_PILOT_COMPLETE_PENDING_REVIEW',cases=summary,resources=resources,
                      projected_full_seconds_conservative=210*max(r['elapsed_seconds'] for r in summary),
                      new_model_forward=0,new_training=0)
        products=('claim.json','cases.jsonl')
        evidence['files']={n:dict(bytes=(out/n).stat().st_size,sha256=hashlib.sha256((out/n).read_bytes()).hexdigest()) for n in products}
        with (out/'completion.json').open('x',encoding='utf-8') as f:json.dump(evidence,f,allow_nan=False)
        tick()
    except Exception as error:
        import traceback
        with (out/'failure.json').open('x',encoding='utf-8') as f:
            json.dump(dict(error=str(error),traceback=traceback.format_exc(),resources=resources),f)
        raise


if __name__=='__main__':
    main()
