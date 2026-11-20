"""Independent read-only verification of finalized PCAT pilot artifacts."""
import hashlib
import importlib.util
import io
import json
import math
import tarfile
import time
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'real_pilot_results_v1'
REQUEST_SHA = '65b0e49ab4341e44e6abc53e840b709848b461b5cd8ed004a804a2d2cb755ab4'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def checked(record):
    path = Path(record['path'])
    assert path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), path
    raw = path.read_bytes()
    assert (len(raw),sha(raw)) == (record['bytes'],record['sha256']),path
    return raw


def close(actual,saved,tol=1e-10):
    if saved is None:
        assert actual is None
    else:
        np.testing.assert_allclose(actual,saved,atol=tol,rtol=1e-12)


def nearest(tree, points):
    return tree.query(points,workers=2)[0]


def audit_case(case, saved, parent, tar, metric, historical):
    with np.load(io.BytesIO(checked(case['reference'])),allow_pickle=False) as z:
        ref={k:z[k] for k in z.files}
    with np.load(io.BytesIO(checked(case['point_file'])),allow_pickle=False) as z:
        assert sha(z['implant'].tobytes())==case['target_array_sha256']
        gt=metric.world_points(z['implant'],case['normalization'])
    xyz,w,j=ref['a_centers'],ref['a_weights'],ref['a_is_j']
    a2,w2,j2=metric.a2_reference(ref)
    assert saved['reference_A1']==len(xyz) and saved['reference_A2']==len(a2)==4*len(xyz)
    b,bw=ref['b_centers'],ref['b_weights']
    ref_tree,a2_tree,b_tree,gt_tree=map(cKDTree,(xyz,a2,b,gt))
    arms={}
    def full_stats(points,tree,d1,d2):
        groups={}
        for name,distance,weight,tag in [('A1',d1,w,j),('A2',d2,w2,j2)]:
            groups[name]={name:metric.stats(distance[mask],weight[mask])
                          for name,mask in [('all',np.ones(len(tag),bool)),('E',~tag),('J',tag)]}
        groups['B']=dict(all=metric.stats(nearest(tree,b),bw),E=None,J=None,partition_status='NO_EXACT_MC_INTERFACE_LABELS')
        reverse={}
        raw={}
        for name,rtree in [('A2',a2_tree),('B',b_tree)]:
            d=nearest(rtree,points)
            raw[name]=d
            reverse[name]=dict(**metric.stats(d),outlier_fraction={str(t):float(np.mean(d>t)) for t in metric.TAUS})
        result=dict(status='OK',point_count=len(points),duplicate_points=len(points)-len(np.unique(points,axis=0)),
                    primary_E_G_P95_mm=groups['A1']['E']['p95_mm'],regions=groups,reverse_discrete_reference=reverse,
                    CD_L1_mm=.5*(float(nearest(gt_tree,points).mean())+float(nearest(tree,gt).mean())))
        return result,raw['A2']
    for arm,rec in case['predictions'].items():
        member=tar.getmember(rec['member'])
        raw=tar.extractfile(member).read()
        assert member.isfile() and len(raw)==rec['bytes'] and sha(raw)==rec['sha256']
        with np.load(io.BytesIO(raw),allow_pickle=False) as z:
            assert z['coarse'].shape==(256,3) and z['prediction'].shape==(8192,3)
            q,p=[metric.world_points(z[k],case['normalization']) for k in ('coarse','prediction')]
        qtree,ptree=map(cKDTree,(q,p))
        dq,dp=[nearest(t,xyz) for t in (qtree,ptree)]
        dq2,dp2=[nearest(t,a2) for t in (qtree,ptree)]
        gotQ,qrev=full_stats(q,qtree,dq,dq2)
        gotP,prev=full_stats(p,ptree,dp,dp2)
        arm_saved=saved['results'][arm]
        assert gotQ==arm_saved['coarse'] and gotP==arm_saved['dense'],'historical scorer reproduction'
        old=historical[case['fold'],case['case_id'],arm]
        for name in ('E','J'):
            assert abs(gotP['regions']['A1'][name]['p95_mm']-old['metrics'][f'{name}_P95_mm'])<=1e-9
            for t in ('0.5','1.0','2.0'):
                assert abs(gotP['regions']['A1'][name]['coverage'][t]-old['metrics'][f'{name}_coverage_{t}mm'])<=1e-12
            assert abs(gotQ['regions']['A1'][name]['p95_mm']-case['historical_coarse_A1_P95_mm'][arm][name])<=1e-9
        assert abs(gotP['CD_L1_mm']-old['metrics']['CD_L1_mm'])<=1e-9
        p0,g0=p-p.mean(0),gt-gt.mean(0)
        radius=float(np.sqrt(np.square(p0).sum()/np.square(g0).sum()))
        risk=dict(placement_tail=np.linalg.norm(p.mean(0)-gt.mean(0))>20,
                  compact_distribution=radius<.9,
                  severe_geometry=gotP['regions']['A1']['E']['p95_mm']>20 or gotP['regions']['A1']['J']['coverage']['2.0']==0)
        assert risk==arm_saved['risk']==old['risk_labels']
        assert float((prev>20).mean())==old['metrics']['reverse_A2_outlier_20.0mm']
        for x in (False,True):
            for y in (False,True):
                close(float((((qrev[parent]>20)==x)&((prev>20)==y)).mean()),arm_saved['far_transition'][f'parent_{x}_child_{y}'])
        # Query all 32 children at once for each proven slot, then reduce the
        # reference-index/parent incidence rather than reusing the pilot helper.
        counts=np.zeros(len(xyz),np.int32)
        footprints=[]
        max_neighbors=0
        for slot in range(256):
            children=p[parent==slot]
            neighborhoods=ref_tree.query_ball_point(children,np.nextafter(2.,np.inf),eps=0)
            max_neighbors=max(max_neighbors,max(map(len,neighborhoods)))
            hits=np.unique(np.concatenate(neighborhoods).astype(np.intp))
            distances=cKDTree(children).query(xyz[hits])[0]
            hits=hits[distances<=2.]
            footprints.append(hits)
            counts[hits]+=1
        assert max_neighbors==arm_saved['max_neighbors_per_child']
        assert np.array_equal(counts>0,dp<=2)
        arms[arm]=dict(q=dq<=2,p=dp<=2,q2=dq2<=2,p2=dp2<=2,n=counts,foot=footprints)

    a,b=arms['G1'],arms['G2']
    for label,mask,mask2 in [('E',~j,~j2),('J',j,j2)]:
        region=saved['results']['regions'][label]
        total=w[mask].sum()
        W=lambda m:float(np.sum(w[m&mask])/total)
        W2=lambda m:float(np.sum(w2[m&mask2])/np.sum(w2[mask2]))
        strata={f'S{x}{y}':(a['q']==bool(x))&(b['q']==bool(y)) for x in (0,1) for y in (0,1)}
        assert all(np.array_equal(sum(s.astype(int) for s in strata.values()),np.ones(len(xyz),int)) for _ in (0,))
        for arm,v in arms.items():
            r=region[arm]
            close(W(~v['q']&v['p']),r['gain'])
            close(W(v['q']&~v['p']),r['loss'])
            close(W(v['n']>=2),r['multi'])
            for name,m in strata.items():
                item=r['strata'][name]
                covered,long=m&v['p'],m&(v['n']>=2)
                unique,zero=m&(v['n']==1),m&~v['p']
                for k,x in [('area',m),('cover',covered),('unique',unique),('multi',long),('zero',zero)]:
                    close(W(x),item[k])
                share=np.divide(w,v['n'],out=np.zeros_like(w),where=v['n']>0)
                share[~(m&mask)]=0
                exclusive=w*(unique&mask)
                close([share[h].sum()/total for h in v['foot']],item['share_credit'])
                close([exclusive[h].sum()/total for h in v['foot']],item['exclusive_credit'])
                close(sum(item['share_credit']),item['cover'])
                close(sum(item['exclusive_credit']),item['unique'])
                close(W(covered)/W(m) if W(m)>=.01 else None,item['conditional_cover'])
        s00=strata['S00']
        abs_diff=W(s00&b['p'])-W(s00&a['p'])
        shared=strata['S11']&a['p']&b['p']
        delta_shared=W(shared&(b['n']>=2))-W(shared&(a['n']>=2))
        s002=~a['q2']&~b['q2']
        a2diff=W2(s002&b['p2'])-W2(s002&a['p2'])
        for key,value in dict(delta00=abs_diff/W(s00) if W(s00)>=.01 else None,delta_abs00=abs_diff,
                              delta_multi=W(b['n']>=2)-W(a['n']>=2),delta_shared_multi=delta_shared,
                              delta_shared_multi_conditional=delta_shared/W(shared) if W(shared)>0 else None,
                              common_shared_area=W(shared),a2_s00_area=W2(s002),a2_delta_abs00=a2diff,
                              a2_delta00=a2diff/W2(s002) if W2(s002)>=.01 else None).items():
            close(value,region[key])


def main():
    start=time.monotonic()
    request_path=ROOT/'PCAT_CPU_pilot_execution_request_v1.json'
    assert sha(request_path.read_bytes())==REQUEST_SHA
    q=load(request_path)
    exit_record=load(ROOT/'pilot_exit_receipt_v1.json')
    auth=Path(q['launch']['authorization_receipt'])
    assert sha(auth.read_bytes())==exit_record['authorization_sha256']
    assert load(auth)['explicit_user_authorization'] is True
    assert load(auth)['request_sha256']==exit_record['request_sha256']==REQUEST_SHA
    assert exit_record['exit_code']==0 and not exit_record['timed_out']
    for name in ('stdout','stderr'):
        assert (ROOT/f'pilot_{name}_v1.bin').stat().st_size==exit_record[name+'_bytes']==0
    assert {p.name for p in OUT.iterdir()}=={'claim.json','cases.jsonl','completion.json'}
    assert load(OUT/'claim.json')=={'request_sha256':REQUEST_SHA}
    hashes={p.name:sha(p.read_bytes()) for p in OUT.iterdir()}
    completed=load(OUT/'completion.json')
    assert completed['status']=='CPU_PILOT_COMPLETE_PENDING_REVIEW' and completed['new_model_forward']==completed['new_training']==0
    assert completed['files'].keys()=={'claim.json','cases.jsonl'}
    for name,r in completed['files'].items():
        assert hashes[name]==r['sha256'] and (OUT/name).stat().st_size==r['bytes']
    for name in ('protocol','p01_decision','p01_audit','entry','python','artificial_result','metric','case_index','case_selection','historical_paired_csv','historical_arm_csv'):
        checked(q[name])
    for r in q['packages'].values():checked(r)
    parent=np.array(json.loads(checked(q['parent_map'])))
    assert np.array_equal(parent,np.arange(8192)//32)
    index={(r['fold'],r['case_id']):r for r in q['cases']}
    historical={}
    for raw in checked(q['historical_scores']).splitlines():
        r=json.loads(raw)
        if (r['fold'],r['case_id']) in index and r['arm'] in ('G1','G2'):
            historical[r['fold'],r['case_id'],r['arm']]=r
    assert len(historical)==16
    spec=importlib.util.spec_from_file_location('audit_frozen_geo',q['metric']['path'])
    metric=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    rows=[json.loads(r) for r in (OUT/'cases.jsonl').read_bytes().splitlines()]
    assert [(r['fold'],r['case_id']) for r in rows]==list(index) and len(rows)==8
    assert completed['cases']==[{k:r[k] for k in ('fold','case_id','reference_A1','reference_A2','elapsed_seconds')} for r in rows]
    peak={k:max(r[k] for r in completed['resources']) for k in q['limits']}
    assert all(0<=peak[k]<=q['limits'][k] and all(math.isfinite(r[k]) and r[k]>=0 for r in completed['resources']) for k in peak)
    assert all(a['wall_seconds']<=b['wall_seconds'] for a,b in zip(completed['resources'],completed['resources'][1:]))
    with tarfile.open(fileobj=io.BytesIO(checked(q['archive'])),mode='r:gz') as tar:
        for pair,saved in zip(q['cases'],rows):
            audit_case(pair,saved,parent,tar,metric,historical)
    assert hashes=={p.name:sha(p.read_bytes()) for p in OUT.iterdir()}
    total=sum(p.stat().st_size for p in OUT.iterdir())
    assert total<=q['limits']['output_bytes']
    v=dict(status='PCAT_PILOT_FORMAL_READ_ONLY_FREEZE_PASS',request_sha256=REQUEST_SHA,
           counts=dict(cases=8,predictions=16,stages=32,parent_groups=4096,sampled_resources=len(completed['resources'])),
           output_sha256=hashes,checks={'all_historical_scores_and_risk':True,'full_saved_Q_P_scoring':True,
           'all_parent_unions_area_shares_and_reverse_transitions':True,'all_matched_area_metrics':True,
           'resource_records_and_unchanged_output':True},observed_peak=peak,process_wall_seconds=exit_record['wall_seconds'],
           output_bytes=total,audit_seconds=time.monotonic()-start,new_model_forward=0,new_training=0)
    with (ROOT/'formal_pilot_freeze_v1.json').open('x',encoding='utf-8') as f:json.dump(v,f,indent=2)
    print(json.dumps(v))


if __name__=='__main__':
    main()
