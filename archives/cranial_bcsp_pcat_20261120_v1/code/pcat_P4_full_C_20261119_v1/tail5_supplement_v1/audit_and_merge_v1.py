"""Verify the five-case supplement independently, then publish a new C merge."""
import gzip
import hashlib
import importlib.util
import io
import json
import math
import tarfile
from pathlib import Path

import numpy as np

TAIL = Path(__file__).resolve().parent
C = TAIL.parent
AUDIT = C.parent / 'pcat_P2_P3_pilot_20261119_v1/readonly_freeze_audit.py'
OUT = TAIL / 'tail5_results_v1'
TAIL_SHA = '03d3a087108b303eaa5b333cc11a02e175a0307042ef6ee17762f996a74809a8'


def load(path):
    return json.loads(Path(path).read_bytes())


def fingerprint(raw):
    return dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


def read_exact(path, record):
    path=Path(path)
    assert path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)),path
    raw=path.read_bytes()
    assert fingerprint(raw)=={k:record[k] for k in ('bytes','sha256')},path
    return raw


def bound(record):
    return read_exact(record['path'],record)


def save(path, payload):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(payload,stream,indent=2,allow_nan=False)
        stream.write('\n')


def importer(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    request=TAIL/'PCAT_fold_C_tail5_execution_request_v1.json'
    assert fingerprint(request.read_bytes())['sha256']==TAIL_SHA
    q=load(request)
    assert q['schema']=='pcat-fold-C-tail5-v1'
    assert q['counts']==dict(cases=5,predictions=10,stages=20,parent_groups=2560,new_forward=0,new_training=0)
    auth=Path(q['launch']['authorization_receipt'])
    exit_path=TAIL/'exit_receipt_v1.json'
    exit_record=load(exit_path);a=load(auth)
    assert exit_record['exit_code']==0 and exit_record['timed_out'] is False
    assert 0<exit_record['wall_seconds']<=300
    assert a['explicit_user_authorization'] is True
    assert a['request_sha256']==exit_record['request_sha256']==TAIL_SHA
    assert fingerprint(auth.read_bytes())['sha256']==exit_record['authorization_sha256']
    assert {p.name for p in OUT.iterdir()}=={'claim.json','cases.jsonl','resources.jsonl','completion.json'}
    stdout=TAIL/'stdout_v1.bin';stderr=TAIL/'stderr_v1.bin'
    assert stdout.stat().st_size==stderr.stat().st_size==0
    monitored=[request,auth,exit_path,stdout,stderr,*sorted(OUT.iterdir())]
    before={str(p.relative_to(TAIL)):fingerprint(p.read_bytes()) for p in monitored}
    claim=load(OUT/'claim.json')
    assert claim==dict(request_sha256=TAIL_SHA,authorization_sha256=exit_record['authorization_sha256'],fold='C')
    complete=load(OUT/'completion.json')
    assert complete['status']=='PCAT_FOLD_C_TAIL5_COMPLETE_PENDING_FREEZE'
    assert complete['request_sha256']==TAIL_SHA and complete['counts']==q['counts']
    assert set(complete['files'])=={'claim.json','cases.jsonl','resources.jsonl'}
    for name,record in complete['files'].items():read_exact(OUT/name,record)
    for key in ('entry','geometry','metric','python','protocol','p01_decision','p01_audit','budget_freeze',
                'benchmark_request','benchmark_completion','preparation_validation','original_request'):
        bound(q[key])
    for record in q['packages'].values():bound(record)
    prefix_freeze=json.loads(bound(q['prefix_freeze']))
    assert prefix_freeze['status']=='PCAT_FOLD_C_TIMEOUT_PREFIX_READ_ONLY_FREEZE_PASS'
    assert prefix_freeze['preserved_prefix_is_merge_eligible'] and prefix_freeze['completed_case_records']==100
    assert prefix_freeze['request_sha256']==q['original_request']['sha256']
    for name,record in prefix_freeze['files'].items():read_exact(C/name,record)
    manifest=json.loads(bound(q['original_case_manifest']))['cases']
    cases=json.loads(bound(q['case_manifest']))['cases']
    assert len(manifest)==105 and cases==manifest[100:]
    assert [r['case_id'] for r in cases]==prefix_freeze['pending_case_ids']
    prefix=bound(q['frozen_prefix'])
    prefix_lines=prefix.splitlines(keepends=True)
    assert len(prefix_lines)==len(prefix_freeze['per_case_output_rows'])==100
    offset=0
    for line,record,case in zip(prefix_lines,prefix_freeze['per_case_output_rows'],manifest):
        assert record['offset']==offset and fingerprint(line)=={k:record[k] for k in ('bytes','sha256')}
        saved=json.loads(line)
        assert (saved['fold'],saved['case_id'])==('C',record['case_id'])==('C',case['case_id'])
        offset+=len(line)
    tail=(OUT/'cases.jsonl').read_bytes()
    lines=tail.splitlines(keepends=True)
    assert len(lines)==5 and all(line.endswith(b'\n') for line in prefix_lines+lines)
    rows=[json.loads(line) for line in lines]
    assert [(r['fold'],r['case_id']) for r in rows]==[(r['fold'],r['case_id']) for r in cases]
    res_lines=(OUT/'resources.jsonl').read_bytes().splitlines(keepends=True)
    samples=[json.loads(line) for line in res_lines]
    assert len(samples)==complete['resources']['samples']==181
    peak={k:max(x[k] for x in samples) for k in q['limits']}
    assert peak==complete['resources']['peak']
    assert all(math.isfinite(row[k]) and 0<=row[k]<=q['limits'][k] for row in samples for k in q['limits'])
    assert all(x['wall_seconds']<=y['wall_seconds'] for x,y in zip(samples,samples[1:]))
    res_offsets=[0]
    for line in res_lines:res_offsets.append(res_offsets[-1]+len(line))
    offset=0
    commits=[]
    for i,(row,line) in enumerate(zip(rows,lines),1):
        start=offset;offset+=len(line)
        sample=i*36
        assert samples[sample]['output_bytes']==(OUT/'claim.json').stat().st_size+res_offsets[sample]+offset
        commits.append(dict(case_id=row['case_id'],offset=start,post_write_sample=sample+1,**fingerprint(line)))
    parent=np.array(json.loads(bound(q['parent_map'])))
    assert np.array_equal(parent,np.arange(8192)//32)
    historical={}
    ids={r['case_id'] for r in cases}
    for line in bound(q['historical_scores']).splitlines():
        old=json.loads(line)
        if old['fold']=='C' and old['case_id'] in ids and old['arm'] in ('G1','G2'):
            key=('C',old['case_id'],old['arm'])
            assert key not in historical
            historical[key]=old
    assert len(historical)==10
    audit=importer('pcat_independent_pilot_auditor',AUDIT)
    metric=importer('pcat_frozen_metric',q['metric']['path'])
    with gzip.GzipFile(fileobj=io.BytesIO(bound(q['archive']))) as stream:
        tar_bytes=stream.read(q['max_tar_bytes']+1)
    assert len(tar_bytes)<=q['max_tar_bytes']
    with tarfile.open(fileobj=io.BytesIO(tar_bytes),mode='r:') as tar:
        for case,row in zip(cases,rows):
            audit.audit_case(case,row,parent,tar,metric,historical)
    assert before=={str(p.relative_to(TAIL)):fingerprint(p.read_bytes()) for p in monitored}
    for name,record in prefix_freeze['files'].items():read_exact(C/name,record)
    audit_path=TAIL/'tail5_formal_freeze_v1.json'
    save(audit_path,dict(status='PCAT_FOLD_C_TAIL5_FORMAL_READ_ONLY_FREEZE_PASS',request_sha256=TAIL_SHA,
         counts=q['counts'],files=before,resource_records=len(samples),observed_peak=peak,rows=commits,
         checks=['full Q/P scores and historical labels','parent union and credits','A1 and A2 matched coverage',
                 '20 mm transitions','exact suffix, durable writes and unchanged prefix']))
    merged=prefix+tail
    merged_lines=merged.splitlines(keepends=True)
    identities=[(x['fold'],x['case_id']) for x in map(json.loads,merged_lines)]
    assert len(identities)==len(set(identities))==105 and identities==[(r['fold'],r['case_id']) for r in manifest]
    assert len({r['source_id'] for r in manifest})==21
    assert len({v['member'] for r in manifest for v in r['predictions'].values()})==210
    output=C/'fold_C_merged_v1'
    output.mkdir(exist_ok=False)
    path=output/'cases.jsonl'
    with path.open('xb') as f:f.write(merged)
    assert path.read_bytes()==prefix+tail
    receipt=dict(status='PCAT_FOLD_C_105_CASES_MERGED_AND_FROZEN',cases=105,predictions=210,sources=21,
        stages=420,parent_groups=53760,exact_original_manifest_order=True,duplicate_cases=0,
        artifacts={'cases.jsonl':fingerprint(path.read_bytes())},
        bindings=dict(original_manifest=q['original_case_manifest'],prefix_file=q['frozen_prefix'],
                      prefix_freeze=q['prefix_freeze'],tail_cases=fingerprint(tail),
                      tail_freeze=fingerprint(audit_path.read_bytes())),new_model_forward=0,new_training=0)
    save(output/'merge_receipt_v1.json',receipt)
    print(json.dumps(receipt))


if __name__=='__main__':
    main()
