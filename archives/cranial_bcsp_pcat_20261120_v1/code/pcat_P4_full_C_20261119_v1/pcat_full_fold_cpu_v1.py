"""Single-fold PCAT runner. Geometry is delegated to the frozen v2 implementation."""
import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tarfile
import time
from collections import Counter
from pathlib import Path

ARMS = ('G1', 'G2')
TYPES = {'bilateral', 'frontoorbital', 'parietotemporal', 'random_1', 'random_2'}
EXPECTED_COUNTS = dict(cases=105, predictions=210, stages=420, parent_groups=53760, new_forward=0, new_training=0)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(record):
    p = Path(record['path'])
    assert p.is_file() and not any(n.is_symlink() for n in (p,*p.parents)), str(p)
    assert p.stat().st_size == record['bytes'], str(p)
    raw = p.read_bytes()
    assert sha(raw) == record['sha256'], str(p)
    return raw


def module(name, record):
    source = checked(record)
    spec = importlib.util.spec_from_file_location(name, record['path'])
    obj = importlib.util.module_from_spec(spec)
    exec(compile(source,record['path'],'exec'),obj.__dict__)
    return obj


def validate_cases(cases):
    assert len(cases)==105
    ids=[x['case_id'] for x in cases]
    assert ids==sorted(set(ids))
    types={}
    members=set()
    for case in cases:
        assert case['fold']=='C' and set(case['predictions'])==set(ARMS)
        assert set(case['historical_coarse_A1_P95_mm'])==set(ARMS)
        code=case['case_id'].split('__',2)
        assert code[:2]==['train',case['source_id'].removeprefix('train:')]
        types.setdefault(case['source_id'],set()).add(code[2])
        for arm,p in case['predictions'].items():
            assert p['member']==f"predictions/{arm}_C__{case['case_id']}.npz"
            assert p['member'] not in members and p['bytes']>0 and len(p['sha256'])==64
            members.add(p['member'])
    assert len(members)==210 and len(types)==21 and all(v==TYPES for v in types.values())


def validate_request(q):
    assert q['schema']=='pcat-full-fold-C-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'
    assert q['execution_authorized'] is False and q['fold']=='C' and q['counts']==EXPECTED_COUNTS
    assert q['limits']==dict(wall_seconds=1200,rss_bytes=8589934592,output_bytes=1073741824)
    assert q['launch']['attempts']==1 and q['launch']['auto_retry'] is False
    assert q['launch']['foreground_timeout_seconds']==1200


def assert_authorized(auth, request_sha):
    assert auth['request_sha256']==request_sha and auth['explicit_user_authorization'] is True


def unpack_archive(raw, maximum):
    assert maximum==128*1024**2
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        tar=stream.read(maximum+1)
    assert len(tar)<=maximum,'archive expanded beyond bound'
    return tar


def emit(path, value, mode='x'):
    with path.open(mode,encoding='utf-8',newline='\n') as f:
        json.dump(value,f,allow_nan=False)
        f.write('\n')


def checksummed(path):
    raw=path.read_bytes()
    return dict(bytes=len(raw),sha256=sha(raw))


def run(args):
    import numpy as np
    import psutil

    started=time.monotonic()
    request=Path(args.request)
    raw=request.read_bytes()
    assert sha(raw)==args.request_sha256
    q=json.loads(raw)
    validate_request(q)
    assert Path(q['entry']['path']).resolve()==Path(__file__).resolve()
    assert Path(q['python']['path']).resolve()==Path(sys.executable).resolve()
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    assert Path(args.authorization).resolve()==Path(q['launch']['authorization_receipt']).resolve()
    auth_raw=Path(args.authorization).read_bytes()
    assert sha(auth_raw)==args.authorization_sha256
    assert_authorized(json.loads(auth_raw),args.request_sha256)
    for name in ('entry','python','protocol','p01_decision','p01_audit','budget_freeze',
                 'benchmark_request','benchmark_completion','preparation_validation'):
        checked(q[name])
    for r in q['packages'].values():
        checked(r)
    cases=json.loads(checked(q['case_manifest']))['cases']
    validate_cases(cases)
    parent=np.array(json.loads(checked(q['parent_map'])))
    assert np.array_equal(parent,np.arange(8192)//32)
    out=Path(q['output'])
    assert out.resolve().parent==request.resolve().parent and not any(p.is_symlink() for p in out.parents)
    assert shutil.disk_usage(out.parent).free>=q['limits']['output_bytes']
    out.mkdir(exist_ok=False)
    emit(out/'claim.json',dict(request_sha256=args.request_sha256,authorization_sha256=args.authorization_sha256,fold='C'))
    process=psutil.Process()
    samples=0
    peak=dict(wall_seconds=0.,rss_bytes=0,output_bytes=0)
    def tick():
        nonlocal samples
        record=dict(wall_seconds=time.monotonic()-started,rss_bytes=process.memory_info().rss,
                    output_bytes=sum(p.stat().st_size for p in out.iterdir() if p.is_file()))
        assert all(record[k]<=q['limits'][k] for k in record),record
        for key,value in record.items():
            peak[key]=max(peak[key],value)
        samples+=1
        emit(out/'resources.jsonl',record,'a')

    try:
        tick()
        geometry=module('pcat_bound_geometry',q['geometry'])
        metric=module('pcat_bound_historical_metric',q['metric'])
        ids={x['case_id'] for x in cases}
        history={}
        for line in checked(q['historical_scores']).splitlines():
            row=json.loads(line)
            if row['fold']=='C' and row['case_id'] in ids and row['arm'] in ARMS:
                key=('C',row['case_id'],row['arm'])
                assert key not in history and row['status']=='OK'
                history[key]=row
        assert len(history)==210
        count=0
        with tarfile.open(fileobj=io.BytesIO(unpack_archive(checked(q['archive']),q['max_tar_bytes'])),mode='r:') as tar:
            for case in cases:
                result=geometry.run_case(case,parent,metric,tar,history,tick)
                assert (result['fold'],result['case_id'])==('C',case['case_id'])
                emit(out/'cases.jsonl',result,'a')
                count+=1
                tick()
        assert count==105 and samples>105
        products=('claim.json','cases.jsonl','resources.jsonl')
        report=dict(status='PCAT_FOLD_C_COMPUTE_COMPLETE_PENDING_FREEZE',fold='C',counts=EXPECTED_COUNTS,
                    request_sha256=args.request_sha256,resources=dict(samples=samples,peak=peak),
                    files={name:checksummed(out/name) for name in products})
        serialized=(json.dumps(report,allow_nan=False)+'\n').encode('utf-8')
        assert sum((out/name).stat().st_size for name in products)+len(serialized)<=q['limits']['output_bytes']
        assert time.monotonic()-started<=q['limits']['wall_seconds']
        with (out/'completion.json').open('xb') as stream:
            stream.write(serialized)
    except BaseException as e:
        emit(out/'failure.json',dict(error=repr(e),resource_samples=samples,observed_peak=peak))
        raise


def main():
    parser=argparse.ArgumentParser()
    for name in ('request','request-sha256','authorization','authorization-sha256'):
        parser.add_argument('--'+name,required=True)
    run(parser.parse_args())


if __name__=='__main__':
    main()
