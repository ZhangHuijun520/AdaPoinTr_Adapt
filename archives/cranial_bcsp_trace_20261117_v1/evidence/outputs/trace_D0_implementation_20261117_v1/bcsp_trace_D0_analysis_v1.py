"""Offline TRACE geometry/replay only. Inert import; separate CPU execution grant required."""
import argparse,hashlib,io,json,tarfile,time
from pathlib import Path

def need(ok,message):
    if not ok:raise ValueError(message)

def geometry(a,arm):
    import numpy as np
    from scipy.spatial import cKDTree
    common={'D','S','F','z','A','x','f','mu','rho','tau','Q','P'}
    need(set(a)==common|({'index','native_d2'} if arm=='G2' else set()),'exact trace keys / G1 ALL256')
    dims=dict(D=(8192,3),S=(256,3),F=(256,384),z=(1024,),A=(256,3),x=(256,1416),f=(256,384),mu=(256,3),rho=(256,1),tau=(256,1),Q=(256,3),P=(8192,3))
    for k,shape in dims.items():need(a[k].shape==shape and a[k].dtype==np.float32 and np.isfinite(a[k]).all(),'trace shape/FP32 '+k)
    S,A,F=[a[k].astype(np.float64) for k in ['S','A','F']]
    d2=((A[:,None]-S[None])**2).sum(-1);dist=np.sqrt(d2);ordered=np.sort(dist,axis=1,kind='stable')
    if arm=='G2':
        native=a['native_d2'];idx=a['index']
        need(native.shape==(256,256) and native.dtype==np.float32 and np.isfinite(native).all(),'native d2')
        need(idx.shape==(256,8) and idx.dtype==np.int64 and np.array_equal(idx,np.argsort(native,axis=1,kind='stable')[:,:8]),'actual FP32 stable KNN')
        need(np.all(np.abs(native.astype(np.float64)-d2)<=64*np.finfo(np.float32).eps*np.maximum(1,np.abs(d2))),'FP32/FP64 roundoff')
    else:idx=np.broadcast_to(np.arange(256),(256,256))
    selected=S[idx]-A[:,None];mu=selected.mean(1);rho=np.linalg.norm(selected,axis=-1).mean(1,keepdims=True)
    tau=np.sqrt(((selected-mu[:,None])**2).sum(-1).mean(1,keepdims=True)+1e-6)
    normalized=(F-F.mean(-1,keepdims=True))/np.sqrt(F.var(-1,keepdims=True)+1e-5);f=normalized[idx].mean(1)
    for k,v in [('f',f),('mu',mu),('rho',rho),('tau',tau)]:need(np.allclose(a[k],v,rtol=3e-5,atol=3e-6),'descriptor '+k)
    x=np.concatenate([np.broadcast_to(a['z'],(256,1024)),a['f'],a['A'],a['mu'],a['rho'],a['tau']],-1)
    need(np.array_equal(x,a['x']),'actual concatenation')
    pair=np.linalg.norm(S[:,None]-S[None],axis=-1);np.fill_diagonal(pair,np.inf);ell=float(np.median(pair.min(1)))
    hits=np.bincount(idx.ravel(),minlength=256);prob=hits[hits>0]/hits.sum()
    cov=np.einsum('nki,nkj->nij',selected-mu[:,None],selected-mu[:,None])/idx.shape[1]
    result=dict(status='OK' if ell>0 else 'DEGENERATE_SPACING',S_unique=len(np.unique(S,axis=0)),ell_S=ell,
        R_case=float(np.median(ordered[:,0]/ell)) if ell>0 else None,T_case=float(np.median(ordered[:,7]/ell)) if ell>0 else None,
        nu_case=float(np.mean(ordered[:,0]/ell>2)) if ell>0 else None,
        probe_d1_quantiles=np.quantile(ordered[:,0],[0,.25,.5,.75,1]).tolist(),probe_d8_quantiles=np.quantile(ordered[:,7],[0,.25,.5,.75,1]).tolist(),
        probe_to_D_quantiles=np.quantile(cKDTree(a['D']).query(A)[0],[0,.25,.5,.75,1]).tolist(),
        consumed_neighborhood='NATIVE_FP32_K8' if arm=='G2' else 'ALL256',memory_hits=hits.tolist(),memory_union_fraction=float(np.mean(hits>0)),memory_hit_entropy=float(-(prob*np.log(prob)).sum()/np.log(256)),
        unique_neighborhoods=len(np.unique(np.sort(idx,axis=1),axis=0)),neighborhood_covariance_eigenvalues=np.linalg.eigvalsh(cov).tolist(),
        F_mean_channel_variance=float(F.var(0).mean()),f_mean_channel_variance=float(a['f'].astype(np.float64).var(0).mean()),Q_covariance_eigenvalues=np.linalg.eigvalsh(np.cov(a['Q'].astype(np.float64).T,bias=True)).tolist())
    return result

def association(rows):
    import numpy as np
    from scipy.stats import rankdata
    if any(r['R_case'] is None for r in rows):return dict(status='UNINFORMATIVE',reason='undefined spacing retained, no case drop',n=len(rows))
    x=rankdata([r['R_case'] for r in rows],method='average');y=rankdata([r['delta_E'] for r in rows],method='average')
    def corr(a,b):return float(np.corrcoef(a,b)[0,1]) if np.std(a)>0 and np.std(b)>0 else None
    primary=corr(x,y);xr=x.copy();yr=y.copy()
    for typ in sorted({r['defect_type'] for r in rows}):
        mask=np.array([r['defect_type']==typ for r in rows])
        if mask.sum()<2:return dict(status='UNINFORMATIVE',reason='type less than two; no substitution',n=len(rows))
        xr[mask]-=x[mask].mean();yr[mask]-=y[mask].mean()
    adjusted=corr(xr,yr)
    return dict(status='OK' if primary is not None and adjusted is not None else 'UNINFORMATIVE',n=len(rows),spearman=primary,type_centered_rank_correlation=adjusted,budget_motivation=primary is not None and adjusted is not None and primary>0 and adjusted>0,causal_claim=False)

def replay_arrays(new,old,normalization):
    import numpy as np
    out={}
    for key,oldkey in [('Q','coarse'),('P','prediction')]:
        need(new[key].shape==old[oldkey].shape and new[key].dtype==old[oldkey].dtype==np.float32,'replay shape dtype')
        diff=float(np.max(np.abs(new[key].astype(np.float64)-old[oldkey].astype(np.float64)))*normalization['scale'])
        need(np.allclose(new[key],old[oldkey],rtol=2e-5,atol=2e-6) and diff<=.01,'REPLAY_INCOMPARABLE: array')
        out[key]=dict(exact_bytes=new[key].tobytes()==old[oldkey].tobytes(),world_max_abs_mm=diff)
    return out

def score_replay(scoring,new,old,ref,gt,norm):
    import numpy as np
    metric=scoring.metric;out=[]
    for arrays,key in [(old,'prediction'),(new,'P')]:
        world=metric.world_points(arrays[key],norm);full=metric.score_cloud(world,ref,gt);values=scoring.select_metrics(full);pose=scoring.position_shape(world,gt)
        out.append((values,scoring.risk_labels(values,pose)))
    for k in ['E_P95_mm','J_P95_mm','CD_L1_mm']:need(out[0][0][k] is not None and out[1][0][k] is not None and abs(out[1][0][k]-out[0][0][k])<=.01,'REPLAY_INCOMPARABLE: score '+k)
    for k in ['E_coverage_2.0mm','J_coverage_2.0mm']:need(abs(out[1][0][k]-out[0][0][k])<=.001,'REPLAY_INCOMPARABLE: cover '+k)
    need(out[0][1]==out[1][1],'REPLAY_INCOMPARABLE: risk labels')
    return dict(score_match=True,risk_labels=out[1][1])

def run(plan,entry):
    """Invoked only by a separately authorized local analysis request, never by GPU entry."""
    import numpy as np
    start=time.monotonic();out=Path(plan['output']);need(not out.exists(),'no output overwrite');out.mkdir()
    need(plan['preparation_scope']['sha256']==entry.PREP_SHA,'CPU scope pin')
    prep=entry.bound(plan['preparation_scope']);need(plan['input_records']==prep['input_records'],'fixed CPU analysis rows')
    scorer=entry.module('TRACE_offline_frozen_scoring',plan['scoring_source'])
    cases=entry.bound(plan['case_manifest'])['cases'];lookup={(c['fold'],c['case_id']):c for c in cases}
    wanted=plan['input_records'];need(len(wanted)==80,'80 trace rows')
    historical=[json.loads(l) for l in entry.exact(plan['historical_scores']).read_text(encoding='utf-8').splitlines()]
    oldE={(r['fold'],r['case_id'],r['arm']):r['metrics']['E_P95_mm'] for r in historical}
    records=[]
    try:
        with tarfile.open(entry.exact(plan['trace_archive'])) as traces,tarfile.open(entry.exact(plan['prediction_archive'])) as previous:
            need(all(m.isfile() for m in traces.getmembers()),'trace archive regular members only')
            expected_names={'traces/'+r['run']+'__'+r['case_id']+'.npz' for r in wanted}
            members=traces.getmembers();need(len({m.name for m in members})==len(members) and {m.name for m in members if m.name.endswith('.npz')}==expected_names,'exact80 trace member set')
            prev={ (r['fold'],r['case_id'],r['variant']):r for r in [json.loads(l) for l in previous.extractfile('inference_manifest.jsonl').read().decode().splitlines()] }
            for row in wanted:
                need(time.monotonic()-start<=1800,'CPU wall budget')
                cid=row['case_id'];fold=row['fold'];arm=row['arm'];c=lookup[(fold,cid)]
                blob=traces.extractfile('traces/'+row['run']+'__'+cid+'.npz').read()
                with np.load(io.BytesIO(blob),allow_pickle=False) as z:a={k:z[k].copy() for k in z.files}
                previous_row=prev[(fold,cid,arm)];ob=previous.extractfile(previous_row['prediction']['name']).read()
                need(hashlib.sha256(ob).hexdigest()==previous_row['prediction']['sha256'],'old prediction binding')
                with np.load(io.BytesIO(ob),allow_pickle=False) as z:old={k:z[k].copy() for k in z.files}
                replay=replay_arrays(a,old,row['normalization'])
                with np.load(entry.exact(c['reference']),allow_pickle=False) as z:ref={k:z[k] for k in z.files}
                with np.load(entry.exact(c['point_file']),allow_pickle=False) as z:target=z['implant'].copy()
                need(hashlib.sha256(target.tobytes()).hexdigest()==c['target_array_sha256'],'GT array binding, offline only')
                gt=scorer.metric.world_points(target,row['normalization']);replay.update(score_replay(scorer,a,old,ref,gt,row['normalization']))
                spatial=geometry(a,arm);delta=oldE[(fold,cid,'G2')]-oldE[(fold,cid,'G1')]
                records.append(dict(run=row['run'],fold=fold,case_id=cid,source_id=row['source_id'],defect_type=row['defect_type'],selection_stratum=row['selection_stratum'],spatial=spatial,replay=replay,delta_E=delta))
        folds={}
        for fold in ('C','D'):
            subset=[dict(R_case=r['spatial']['R_case'],delta_E=r['delta_E'],defect_type=r['defect_type']) for r in records if r['fold']==fold and r['run']=='G2_'+fold and r['selection_stratum']=='HASH_SELECTED_NONPRESSURE']
            need(len(subset)==(17 if fold=='C' else 18),'fixed nonpressure set')
            folds[fold]=association(subset)
        eligible=all(r['spatial']['S_unique']==256 for r in records)
        result=dict(status='PROVISIONAL_MOTIVATION_ONLY' if eligible and all(r.get('budget_motivation',False) for r in folds.values()) else 'NO_SUPPORT_OR_INCONCLUSIVE',folds=folds,G3_unique_anchor_eligible=eligible,causal_claim=False,automatic_training=False)
        (out/'case_evidence.json').write_text(json.dumps(records,indent=2,allow_nan=False),encoding='utf-8')
        (out/'summary.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
        return result
    except BaseException as exc:
        (out/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),completed_rows=len(records))),encoding='utf-8')
        raise

def main():
    p=argparse.ArgumentParser()
    for k in ['entry','entry-sha256','request','request-sha256','authorization','authorization-sha256']:p.add_argument('--'+k,required=True)
    a=p.parse_args();import importlib.util
    path=Path(a.entry);need(hashlib.sha256(path.read_bytes()).hexdigest()==a.entry_sha256,'analysis entry source')
    spec=importlib.util.spec_from_file_location('trace_cpu_entry',path);entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
    rec=lambda path,h:dict(path=path,bytes=Path(path).stat().st_size,sha256=h)
    q=entry.bound(rec(a.request,a.request_sha256));auth=entry.bound(rec(a.authorization,a.authorization_sha256))
    need(q['schema']=='bcsp-trace-D0-CPU-analysis-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','separate analysis request')
    need(auth['schema']=='bcsp-trace-D0-analysis-authorization-v1' and auth['request_sha256']==a.request_sha256 and auth['explicit_user_authorization'] is True,'separate analysis grant')
    need(q['trace_freeze']['status']=='FORMAL_TRACE_D0_POST_DIAGNOSTIC_FREEZE_PASS','formal GPU freeze first')
    print(json.dumps(run(q,entry)))

if __name__=='__main__':main()
