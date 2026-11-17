# -*- coding: utf-8 -*-
"""Independent read-only verification of existing TRACE analysis. No scoring/model calls."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
import hashlib,io,json,math,statistics,tarfile,zipfile
from pathlib import Path
from collections import Counter
import numpy as np

V=Path(__file__).resolve().parent.parent;D=Path(__file__).resolve().parent
P=V/'CPU_analysis_preparation_v1';E=P/'authorized_execution_v1';O=V/'CPU_history_replay_analysis_v1'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=digest(p))
def verify(r):
    p=Path(r['path']);assert p.is_file() and p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],str(p)
def emit(p,value):
    with p.open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def ranks(values):
    order=sorted(range(len(values)),key=lambda i:values[i]);out=[0.]*len(values);i=0
    while i<len(order):
        j=i+1
        while j<len(order) and values[order[j]]==values[order[i]]:j+=1
        for k in range(i,j):out[order[k]]=(i+1+j)/2
        i=j
    return out
def correlation(a,b):
    a=[x-statistics.mean(a) for x in a];b=[x-statistics.mean(b) for x in b]
    denominator=math.sqrt(sum(x*x for x in a)*sum(y*y for y in b))
    return sum(x*y for x,y in zip(a,b))/denominator if denominator>0 else None
def numeric_finite(obj):
    if isinstance(obj,float):return math.isfinite(obj)
    if isinstance(obj,dict):return all(numeric_finite(v) for v in obj.values())
    if isinstance(obj,list):return all(numeric_finite(v) for v in obj)
    return True

def main():
    assert not (D/'formal_freeze_verification_v1.json').exists(),'single audit, no overwrite'
    Q=P/'TRACE_D0_CPU_analysis_execution_request_v1.json';q=read(Q)
    assert digest(Q)=='78952610006e441f49c0f84caf95134652dea133c0526974325cae86c038d5e9'
    checks={}
    for key in ['entry','analysis_implementation','scoring_source','metric_source','case_manifest','preparation_scope','historical_scores','trace_archive','prediction_archive','implementation_P3','local_download_verification']:verify(q[key])
    verify(q['trace_freeze']['evidence'])
    checks['frozen_request_all_code_input_and_freeze_bindings']=True
    rows=read(O/'case_evidence.json');summary=read(O/'summary.json');before=[rec(p) for p in O.iterdir() if p.is_file()]
    checks['exact_two_output_files']={p.name for p in O.iterdir()}=={'case_evidence.json','summary.json'}
    checks['complete80_unique_role_case_records']=len(rows)==80 and len({(r['run'],r['case_id']) for r in rows})==80
    checks['all_numeric_fields_finite']=numeric_finite(rows) and numeric_finite(summary)
    checks['fixed_model_order_20_each']=Counter(r['run'] for r in rows)==Counter({x:20 for x in ['G1_C','G2_C','G1_D','G2_D']})
    checks['all_fixed_metadata_fields_match']=all(all(r[k]==w[k] for k in ['run','fold','case_id','source_id','defect_type','selection_stratum']) for r,w in zip(rows,q['input_records']))
    historical=[json.loads(l) for l in Path(q['historical_scores']['path']).read_text(encoding='utf-8').splitlines()];old={(r['fold'],r['case_id'],r['arm']):r for r in historical}
    checks['historical_deltaE_matches_frozen_scores']=all(r['delta_E']==old[(r['fold'],r['case_id'],'G2')]['metrics']['E_P95_mm']-old[(r['fold'],r['case_id'],'G1')]['metrics']['E_P95_mm'] for r in rows)
    checks['all80_exact_QP_and_replay_labels']=all(all(r['replay'][k]['exact_bytes'] is True and r['replay'][k]['world_max_abs_mm']==0 for k in ['Q','P']) and r['replay']['score_match'] is True and r['replay']['risk_labels']==old[(r['fold'],r['case_id'],r['run'].split('_')[0])]['risk_labels'] for r in rows)
    # Independently compare saved tensors to historical Q/P, no metric.score_cloud.
    independent=[]
    with tarfile.open(q['trace_archive']['path']) as trace,tarfile.open(q['prediction_archive']['path']) as previous:
        manifest=[json.loads(l) for l in previous.extractfile('inference_manifest.jsonl').read().decode().splitlines()]
        lookup={(r['fold'],r['case_id'],r['variant']):r for r in manifest}
        for r in rows:
            arm=r['run'].split('_')[0]
            b=trace.extractfile('traces/'+r['run']+'__'+r['case_id']+'.npz').read()
            ref=lookup[(r['fold'],r['case_id'],arm)];oldblob=previous.extractfile(ref['prediction']['name']).read();assert hashlib.sha256(oldblob).hexdigest()==ref['prediction']['sha256']
            with np.load(io.BytesIO(b),allow_pickle=False) as archive:a={k:archive[k].copy() for k in archive.files}
            with np.load(io.BytesIO(oldblob),allow_pickle=False) as z:
                assert a['Q'].dtype==a['P'].dtype==np.float32
                assert a['Q'].tobytes()==z['coarse'].tobytes() and a['P'].tobytes()==z['prediction'].tobytes()
            assert all(np.isfinite(v).all() for v in a.values())
            S=a['S'].astype(np.float64);A=a['A'].astype(np.float64);dd=((A[:,None]-S[None])**2).sum(-1)
            ss=np.linalg.norm(S[:,None]-S[None],axis=-1);np.fill_diagonal(ss,np.inf);ell=float(np.median(ss.min(1)));assert ell>0
            nearest=np.sqrt(np.sort(dd,axis=1,kind='stable'));sp=r['spatial']
            assert sp['S_unique']==len(np.unique(S,axis=0)) and math.isclose(ell,sp['ell_S'],rel_tol=1e-12)
            assert math.isclose(float(np.median(nearest[:,0]/ell)),sp['R_case'],rel_tol=1e-12,abs_tol=1e-12)
            assert math.isclose(float(np.median(nearest[:,7]/ell)),sp['T_case'],rel_tol=1e-12,abs_tol=1e-12)
            assert float(np.mean(nearest[:,0]/ell>2))==sp['nu_case']
            if arm=='G2':
                assert np.array_equal(a['index'],np.argsort(a['native_d2'],axis=1,kind='stable')[:,:8])
                assert np.all(np.abs(a['native_d2'].astype(np.float64)-dd)<=64*np.finfo(np.float32).eps*np.maximum(1,np.abs(dd)))
                assert sp['consumed_neighborhood']=='NATIVE_FP32_K8'
            else:assert 'index' not in a and 'native_d2' not in a and sp['consumed_neighborhood']=='ALL256'
            independent.append(dict(run=r['run'],case_id=r['case_id'],exact_QP=True,finite=True,R_T_nu_consistent=True,native_neighborhood_consistent=True))
    checks['independent80_exact_tensor_replays_and_spatial_consistency']=len(independent)==80
    calculated={}
    for fold,n in [('C',17),('D',18)]:
        sub=[r for r in rows if r['run']=='G2_'+fold and r['selection_stratum']=='HASH_SELECTED_NONPRESSURE'];assert len(sub)==n and len({r['source_id'] for r in sub})==n
        x=ranks([r['spatial']['R_case'] for r in sub]);y=ranks([r['delta_E'] for r in sub]);raw=correlation(x,y);rx=x.copy();ry=y.copy()
        for typ in {r['defect_type'] for r in sub}:
            pos=[i for i,r in enumerate(sub) if r['defect_type']==typ];assert len(pos)>=2
            mx=statistics.mean(x[i] for i in pos);my=statistics.mean(y[i] for i in pos)
            for i in pos:rx[i]-=mx;ry[i]-=my
        adjusted=correlation(rx,ry);reported=summary['folds'][fold]
        assert math.isclose(raw,reported['spearman'],abs_tol=1e-12) and math.isclose(adjusted,reported['type_centered_rank_correlation'],abs_tol=1e-12)
        assert reported['n']==n and reported['budget_motivation']==(raw>0 and adjusted>0)
        calculated[fold]=dict(n=n,spearman=raw,type_centered_rank_correlation=adjusted,budget_motivation=raw>0 and adjusted>0)
    checks['35_nonpressure_and5_exposed_cases_separated']=sum(r['selection_stratum']=='PREVIOUSLY_EXPOSED_FIXED_CASE' for r in rows)==10
    checks['independent_average_rank_and_type_adjusted_correlations_match']=True
    eligible=all(r['spatial']['S_unique']==256 for r in rows);decision='PROVISIONAL_MOTIVATION_ONLY' if eligible and all(v['budget_motivation'] for v in calculated.values()) else 'NO_SUPPORT_OR_INCONCLUSIVE'
    checks['summary_decision_exact_protocol']=summary['status']==decision and summary['G3_unique_anchor_eligible']==eligible and summary['causal_claim'] is False and summary['automatic_training'] is False
    ex=read(E/'execution_exit_v1.json');assert ex['exit_code']==0 and ex['monitor_violation'] is None and ex['attempts']==1
    resources=[json.loads(l) for l in (E/'resources.jsonl').read_text().splitlines()]
    for row in resources:
        actual=dict(wall=row['elapsed_seconds']<=q['limits']['wall_seconds'],RSS=row['RSS_bytes']<=q['limits']['RSS_bytes'],output=row['output_bytes']<=q['limits']['output_bytes'])
        assert row['checks']==actual and all(actual.values())
    checks['process_zero_exit_and_all_resource_thresholds']=ex['status']=='PROCESS_EXIT_ZERO_PENDING_FORMAL_FREEZE' and ex['forward']==ex['training']==0 and ex['GPU'] is False
    checks['stdout_summary_and_empty_stderr']=json.loads((E/'stdout.log').read_text())==summary and (E/'stderr.log').stat().st_size==0
    auth=read(E/'TRACE_D0_CPU_analysis_authorization_v1.json');claim=read(E/'single_execution_claim_v1.json')
    checks['explicit_authorization_and_single_attempt']=auth['explicit_user_authorization'] is True and auth['request_sha256']==claim['request_sha256']==digest(Q) and claim['attempt']==1
    checks['analysis_outputs_unchanged_during_audit']=before==[rec(p) for p in O.iterdir() if p.is_file()]
    assert all(checks.values()),[k for k,v in checks.items() if not v]
    emit(D/'independent_case_verification_v1.json',independent)
    emit(D/'formal_freeze_verification_v1.json',dict(status='FORMAL_TRACE_D0_POST_CPU_ANALYSIS_FREEZE_PASS',checks=checks,check_count=len(checks),case_count=80,primary_nonpressure_sources={'C':17,'D':18},request_sha256=digest(Q),output_bindings=before,independent_fold_results=calculated,decision=decision,execution_exit=rec(E/'execution_exit_v1.json'),resource_records=len(resources),resource_summary=ex,audit_scope='Read-only existing outputs and saved prediction arrays; independent tensor replay, spatial consistency and rank summary verification only. No metric rescoring, model imports, forward, new candidates or training.',no_formal_gate_executed=True))
    print(json.dumps(dict(status='FORMAL_TRACE_D0_POST_CPU_ANALYSIS_FREEZE_PASS',checks=len(checks),case_count=80,folds=calculated,decision=decision)))

if __name__=='__main__':main()
