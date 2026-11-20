"""Verify the durable PCAT C prefix without rerunning geometry."""
import gzip
import hashlib
import io
import json
import math
import statistics
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'fold_C_results_v1'
REQUEST = 'c4e54f945d846c53ad54aed5c1cf6f76c21cc5b94978896e65ba6e5c3f3e76ed'
TOL = 1e-10


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def checked(rec):
    p=Path(rec['path'])
    assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),p
    raw=p.read_bytes()
    assert (len(raw),digest(raw))==(rec['bytes'],rec['sha256']),p
    return raw


def snapshot(paths):
    return {str(p.relative_to(ROOT)):dict(bytes=len(raw),sha256=digest(raw))
            for p in paths if (raw:=p.read_bytes()) is not None}


def approx(a,b,tol=TOL):
    assert math.isclose(a,b,rel_tol=0,abs_tol=tol),(a,b)


def score_metrics(saved, old, historical_coarse):
    dense,coarse=saved['dense'],saved['coarse']
    assert (dense['point_count'],coarse['point_count'])==(8192,256)
    assert dense==old['full_metrics'],'full saved dense scorer mismatch'
    assert saved['risk']==old['risk_labels']
    assert saved['risk']['severe_geometry']==(dense['primary_E_G_P95_mm']>20 or
        dense['regions']['A1']['J']['coverage']['2.0']==0)
    for region in ('E','J'):
        approx(coarse['regions']['A1'][region]['p95_mm'],historical_coarse[region],1e-9)
    far=saved['far_transition']
    assert set(far)=={f'parent_{p}_child_{c}' for p in (True,False) for c in (True,False)}
    assert all(0<=v<=1 and (8192*v).is_integer() for v in far.values())
    approx(sum(far.values()),1.)
    approx(far['parent_True_child_True']+far['parent_False_child_True'],old['metrics']['reverse_A2_outlier_20.0mm'])


def check_region(r,arm_results,region):
    shared_area=r['common_shared_area']
    assert 0<=shared_area<=1 and abs(r['delta_shared_multi'])<=shared_area+TOL
    if shared_area:
        approx(r['delta_shared_multi_conditional'],r['delta_shared_multi']/shared_area)
    else:
        assert r['delta_shared_multi_conditional'] is None
    assert 0<=r['a2_s00_area']<=1 and abs(r['a2_delta_abs00'])<=r['a2_s00_area']+TOL
    if r['a2_s00_area']>=.01:
        approx(r['a2_delta00'],r['a2_delta_abs00']/r['a2_s00_area'])
    else:
        assert r['a2_delta00'] is None
    for arm in ('G1','G2'):
        a=r[arm]
        s=a['strata']
        assert set(s)=={'S00','S01','S10','S11'}
        approx(sum(v['area'] for v in s.values()),1.)
        for v in s.values():
            for name in ('area','cover','unique','multi','zero'):
                assert 0<=v[name]<=1+TOL
            approx(v['unique']+v['multi'],v['cover'])
            approx(v['cover']+v['zero'],v['area'])
            if v['area']>=.01:approx(v['conditional_cover'],v['cover']/v['area'])
            else:assert v['conditional_cover'] is None
            share,exclusive=v['share_credit'],v['exclusive_credit']
            assert len(share)==len(exclusive)==256
            assert all(0<=e<=h+TOL and h<=1+TOL for e,h in zip(exclusive,share))
            approx(math.fsum(share),v['cover'])
            approx(math.fsum(exclusive),v['unique'])
        approx(sum(v['multi'] for v in s.values()),a['multi'])
        existing=('S10','S11') if arm=='G1' else ('S01','S11')
        missing=set(s)-set(existing)
        approx(sum(s[k]['cover'] for k in missing),a['gain'])
        approx(sum(s[k]['zero'] for k in existing),a['loss'])
        C=lambda stage:arm_results[arm][stage]['regions']['A1'][region]['coverage']['2.0']
        approx(sum(s[k]['area'] for k in existing),C('coarse'))
        approx(sum(v['cover'] for v in s.values()),C('dense'))
        approx(a['gain']-a['loss'],C('dense')-C('coarse'))
    s1,s2=(r[k]['strata']['S00'] for k in ('G1','G2'))
    for key in r['G1']['strata']:
        approx(r['G1']['strata'][key]['area'],r['G2']['strata'][key]['area'])
    approx(s2['cover']-s1['cover'],r['delta_abs00'])
    approx(r['G2']['multi']-r['G1']['multi'],r['delta_multi'])
    if s1['area']>=.01:
        approx(s2['conditional_cover']-s1['conditional_cover'],r['delta00'])
    else:
        assert s1['conditional_cover'] is s2['conditional_cover'] is r['delta00'] is None


def main():
    request=ROOT/'PCAT_full_C_execution_request_v1.json'
    assert digest(request.read_bytes())==REQUEST
    q=load(request)
    assert q['counts']['cases']==105 and q['limits']['wall_seconds']==1200
    exit_path=ROOT/'fold_C_exit_receipt_v1.json'
    e=load(exit_path)
    auth=Path(q['launch']['authorization_receipt'])
    assert e['request_sha256']==load(auth)['request_sha256']==REQUEST and load(auth)['explicit_user_authorization'] is True
    assert digest(auth.read_bytes())==e['authorization_sha256']
    assert e['timed_out'] is True and e['exit_code']!=0 and 1200<=e['wall_seconds']<1205
    assert {p.name for p in OUT.iterdir()}=={'claim.json','cases.jsonl','resources.jsonl'}
    claim=load(OUT/'claim.json')
    assert claim==dict(request_sha256=REQUEST,authorization_sha256=e['authorization_sha256'],fold='C')
    stdout=ROOT/'fold_C_stdout_v1.bin';stderr=ROOT/'fold_C_stderr_v1.bin'
    assert stdout.stat().st_size==e['stdout_bytes']==stderr.stat().st_size==e['stderr_bytes']==0
    endpoints=[request,auth,exit_path,stdout,stderr,*sorted(OUT.iterdir())]
    before=snapshot(endpoints)
    for name in ('entry','geometry','metric','python','protocol','p01_decision','p01_audit','parent_map','budget_freeze','benchmark_request','benchmark_completion','preparation_validation'):
        checked(q[name])
    for record in q['packages'].values():checked(record)
    cases=json.loads(checked(q['case_manifest']))['cases']
    ids=[c['case_id'] for c in cases]
    assert len(ids)==105 and ids==sorted(set(ids)) and all(c['fold']=='C' for c in cases)
    history={}
    for line in checked(q['historical_scores']).splitlines():
        v=json.loads(line)
        if v['fold']=='C' and v['arm'] in ('G1','G2'):
            assert (v['case_id'],v['arm']) not in history
            history[v['case_id'],v['arm']]=v
    assert len(history)==210
    raw_cases=(OUT/'cases.jsonl').read_bytes()
    raw_res=(OUT/'resources.jsonl').read_bytes()
    lines=raw_cases.splitlines(keepends=True)
    logs=raw_res.splitlines(keepends=True)
    assert len(lines)==100 and all(r.endswith(b'\n') for r in lines+logs)
    resources=[json.loads(x) for x in logs]
    assert len(resources)==3606 and all(x['wall_seconds']<=y['wall_seconds'] for x,y in zip(resources,resources[1:]))
    assert all(0<=v[key]<=q['limits'][key] for v in resources for key in q['limits'])
    resource_sizes=[0]
    for line in logs:resource_sizes.append(resource_sizes[-1]+len(line))
    claim_bytes=(OUT/'claim.json').stat().st_size
    commits=[]
    end=0
    with gzip.GzipFile(fileobj=io.BytesIO(checked(q['archive']))) as compressed:
        unpacked=compressed.read(q['max_tar_bytes']+1)
    assert len(unpacked)<=q['max_tar_bytes']
    with tarfile.open(fileobj=io.BytesIO(unpacked),mode='r:') as tar:
        for i,c in enumerate(cases):
            for key in ('reference','point_file'):checked(c[key])
            for record in c['predictions'].values():
                member=tar.getmember(record['member'])
                blob=tar.extractfile(member).read()
                assert member.isfile() and (member.size,len(blob),digest(blob))==(record['bytes'],record['bytes'],record['sha256'])
            if i>=len(lines):continue
            r=json.loads(lines[i])
            assert (r['fold'],r['case_id'])==('C',ids[i])
            assert r['reference_A1']>0 and r['reference_A2']==4*r['reference_A1']
            assert r['elapsed_seconds']>0 and math.isfinite(r['elapsed_seconds'])
            assert set(r['results'])=={'G1','G2','regions'} and set(r['results']['regions'])=={'E','J'}
            for arm in ('G1','G2'):
                score_metrics(r['results'][arm],history[ids[i],arm],c['historical_coarse_A1_P95_mm'][arm])
            for region,value in r['results']['regions'].items():
                check_region(value,r['results'],region)
            start=end
            end+=len(lines[i])
            # After each row, the original launcher emits a sample: initial tick
            # + 36 samples per case. Sample size excludes its own log line.
            post=(i+1)*36
            assert resources[post]['output_bytes']==claim_bytes+resource_sizes[post]+end
            commits.append(dict(case_id=ids[i],offset=start,bytes=len(lines[i]),sha256=digest(lines[i]),
                                post_write_sample=post+1,elapsed_seconds=r['elapsed_seconds']))
    assert end==len(raw_cases) and len(resources)-(1+36*len(lines))==5
    assert all(resources[k]['output_bytes']==claim_bytes+resource_sizes[k]+end for k in range(3601,len(resources)))
    assert before==snapshot(endpoints)
    record=dict(status='PCAT_FOLD_C_TIMEOUT_PREFIX_READ_ONLY_FREEZE_PASS',
        request_sha256=REQUEST,source_archive=q['archive'],files=before,completed_case_records=100,
        verified_saved_dense_scores=200,verified_complete_parent_groups=51200,
        pending_case_ids=ids[100:],per_case_output_rows=commits,extra_resource_samples_before_termination=5,
        preserved_prefix_is_merge_eligible=True,full_fold_complete=False,geometry_recomputed=False,
        elapsed_seconds=e['wall_seconds'],sampled_peak={k:max(x[k] for x in resources) for k in q['limits']},
        median_case_seconds=statistics.median(r['elapsed_seconds'] for r in commits),
        slowest_case_seconds=max(r['elapsed_seconds'] for r in commits),
        next_execution='Separate five-case tail in a new output directory. Require exact suffix identity, independently audited hashes and disjoint canonical merge. Do not resume or reuse old request.')
    with (ROOT/'fold_C_timeout_formal_freeze_v1.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    print(json.dumps({k:v for k,v in record.items() if k not in ('files','per_case_output_rows','source_archive')}))


if __name__=='__main__':
    main()
