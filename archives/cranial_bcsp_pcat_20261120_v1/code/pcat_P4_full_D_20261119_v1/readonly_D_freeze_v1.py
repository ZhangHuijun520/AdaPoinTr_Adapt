"""Check the complete D run and its saved geometry identities without replaying it."""
import gzip
import importlib.util
import io
import json
import math
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'fold_D_results_v1'
SHA='dc0a038f84e412c791ecd4bdceeeeebfe7adfb589c513ec0ce5535273a1edd48'


def helpers():
    path=ROOT.parent/'pcat_P4_full_C_20261119_v1/readonly_timeout_freeze_v1.py'
    spec=importlib.util.spec_from_file_location('pcat_C_audit_helpers',path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    h=helpers()
    p=ROOT/'PCAT_full_D_execution_request_v1.json'
    assert h.digest(p.read_bytes())==SHA
    q=h.load(p)
    assert q['fold']=='D' and q['counts']==dict(cases=105,predictions=210,stages=420,parent_groups=53760,new_forward=0,new_training=0)
    e=ROOT/'fold_D_exit_receipt_v1.json';exit_record=h.load(e)
    a=Path(q['launch']['authorization_receipt'])
    assert h.load(a)['request_sha256']==exit_record['request_sha256']==SHA
    assert h.load(a)['explicit_user_authorization'] is True and h.digest(a.read_bytes())==exit_record['authorization_sha256']
    assert exit_record['exit_code']==0 and not exit_record['timed_out'] and 0<=exit_record['wall_seconds']<=1800
    stdout=ROOT/'fold_D_stdout_v1.bin';stderr=ROOT/'fold_D_stderr_v1.bin'
    assert stdout.stat().st_size==stderr.stat().st_size==exit_record['stdout_bytes']==exit_record['stderr_bytes']==0
    assert {p.name for p in OUT.iterdir()}=={'cases.jsonl','claim.json','resources.jsonl','completion.json'}
    ends=[p,e,a,stdout,stderr,*sorted(OUT.iterdir())]
    before={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=h.digest(p.read_bytes())) for p in ends}
    assert h.load(OUT/'claim.json')==dict(request_sha256=SHA,authorization_sha256=exit_record['authorization_sha256'],fold='D')
    completion=h.load(OUT/'completion.json')
    assert completion['status']=='PCAT_FOLD_D_COMPUTE_COMPLETE_PENDING_FREEZE'
    assert completion['fold']=='D' and completion['counts']==q['counts'] and completion['request_sha256']==SHA
    assert completion['files']=={name:before['fold_D_results_v1\\'+name] for name in ('cases.jsonl','claim.json','resources.jsonl')}
    for key in ('entry','geometry','metric','python','protocol','p01_decision','p01_audit','parent_map','budget_freeze',
                'benchmark_request','benchmark_completion','preparation_validation','C_merge_receipt','C_merged_cases','D_budget_review'):
        h.checked(q[key])
    for x in q['packages'].values():h.checked(x)
    frozen_c=json.loads(h.checked(q['C_merge_receipt']))
    assert frozen_c['status']=='PCAT_FOLD_C_105_CASES_MERGED_AND_FROZEN'
    assert frozen_c['artifacts']['cases.jsonl']=={k:q['C_merged_cases'][k] for k in ('bytes','sha256')}
    cases=json.loads(h.checked(q['case_manifest']))['cases']
    ids=[r['case_id'] for r in cases]
    assert len(ids)==105 and ids==sorted(set(ids)) and all(r['fold']=='D' for r in cases)
    assert len({r['source_id'] for r in cases})==21 and len({p['member'] for r in cases for p in r['predictions'].values()})==210
    historical={}
    for line in h.checked(q['historical_scores']).splitlines():
        old=json.loads(line)
        if old['fold']=='D' and old['arm'] in ('G1','G2'):
            k=old['case_id'],old['arm'];assert k not in historical;historical[k]=old
    assert len(historical)==210
    lines=(OUT/'cases.jsonl').read_bytes().splitlines(keepends=True)
    logs=(OUT/'resources.jsonl').read_bytes().splitlines(keepends=True)
    assert len(lines)==105 and len(logs)==completion['resources']['samples']==3781
    assert all(line.endswith(b'\n') for line in lines+logs)
    resources=[json.loads(log) for log in logs]
    assert all(math.isfinite(r[k]) and 0<=r[k]<=q['limits'][k] for r in resources for k in q['limits'])
    assert all(x['wall_seconds']<=y['wall_seconds'] for x,y in zip(resources,resources[1:]))
    peak={k:max(r[k] for r in resources) for k in q['limits']}
    assert peak==completion['resources']['peak'] and peak['wall_seconds']<=exit_record['wall_seconds']
    offsets=[0]
    for log in logs:offsets.append(offsets[-1]+len(log))
    claim_bytes=completion['files']['claim.json']['bytes']
    with gzip.GzipFile(fileobj=io.BytesIO(h.checked(q['archive']))) as stream:
        raw=stream.read(q['max_tar_bytes']+1)
    assert len(raw)<=q['max_tar_bytes']
    end=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as archive:
        for i,(line,case) in enumerate(zip(lines,cases),1):
            row=json.loads(line)
            assert (row['fold'],row['case_id'])==('D',case['case_id'])
            assert row['reference_A1']>0 and row['reference_A2']==4*row['reference_A1']
            assert math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds']>0
            assert set(row['results'])=={'G1','G2','regions'} and set(row['results']['regions'])=={'E','J'}
            for key in ('reference','point_file'):h.checked(case[key])
            for arm,pred in case['predictions'].items():
                member=archive.getmember(pred['member']);b=archive.extractfile(member).read()
                assert member.isfile() and (len(b),member.size,h.digest(b))==(pred['bytes'],pred['bytes'],pred['sha256'])
                h.score_metrics(row['results'][arm],historical[row['case_id'],arm],case['historical_coarse_A1_P95_mm'][arm])
            for region,metrics in row['results']['regions'].items():
                h.check_region(metrics,row['results'],region)
            end+=len(line)
            post=i*36
            assert resources[post]['output_bytes']==claim_bytes+offsets[post]+end
    assert end==(OUT/'cases.jsonl').stat().st_size
    assert before=={str(p.relative_to(ROOT)):dict(bytes=p.stat().st_size,sha256=h.digest(p.read_bytes())) for p in ends}
    receipt=dict(status='PCAT_FOLD_D_FORMAL_READ_ONLY_FREEZE_PASS',request_sha256=SHA,counts=q['counts'],
                 files=before,resources=len(logs),observed_peak=peak,source_count=21,
                 verification='Saved scores and labels, area and credit conservation, post-write samples, bound input hashes, byte-preserving artifacts.',
                 geometry_recomputed=False,new_model_forward=0,new_training=0)
    with (ROOT/'fold_D_formal_freeze_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
    print(json.dumps({k:v for k,v in receipt.items() if k!='files'}))


if __name__=='__main__':main()
