"""Unified CPU scoring of frozen RBSS Fold D predictions."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import time
from types import FunctionType

import numpy as np


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(b):
    return hashlib.sha256(b).hexdigest()


def exact(rec):
    p = Path(rec['path'])
    need(p.is_file() and p.resolve() == p and p.stat().st_size == rec['bytes'], str(p))
    b = p.read_bytes()
    need(digest(b) == rec['sha256'], str(p))
    return b


def module(rec):
    exact(rec)
    spec = importlib.util.spec_from_file_location(Path(rec['path']).stem, rec['path'])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def save(path, data):
    with path.open('x', encoding='utf8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def verify_payload(raw, binding, manifest, arm):
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        names = {'coarse','prediction','S','delta','parent_index','token_index','pi0','pi','inverse','active'}
        need(len(z.files)==len(names) and set(z.files)==names, 'exact fields')
        v = {k:z[k] for k in names}
    ids = np.arange(256, dtype=np.int64)
    for k in ('S','delta','coarse','prediction'):
        a=v[k];need(a.dtype==np.float32 and a.shape==((8192 if k=='prediction' else 256),3) and np.isfinite(a).all(),k)
    need(np.array_equal(v['coarse'],v['S']+v['delta']) and np.array_equal(v['parent_index'],np.repeat(ids,32))
         and np.array_equal(v['token_index'],ids), 'parent and anchor slots')
    active=binding['active']; a=arm if active else 'R'
    need(v['active'].shape==() and v['active'].dtype==np.bool_ and bool(v['active'])==active,'RBSS activation')
    for k, want in (('pi0',binding['order']['R']),('pi',binding['order'][a]),('inverse',binding['inverse'][a])):
        need(v[k].dtype==np.int64 and v[k].tolist()==want,k)
    need(np.array_equal(v['pi'][v['inverse']],ids),'inverse')
    anchors=digest(v['S'].tobytes());order=digest(v['pi0'].astype('<i8',copy=False).tobytes())
    need(anchors==binding['anchors_sha256'] and manifest['native_anchor_order']==anchors+':'+order,'actual anchors/native order')
    return v


def comparison(core, rows, sources, indices, first, second):
    aliases = {first:'A', second:'B'}
    selected = [dict(row, arm=aliases[row['arm']]) for row in rows if row['arm'] in aliases]
    fn = core.summarize
    summarize = FunctionType(fn.__code__, dict(fn.__globals__, ARMS=('B','A')), fn.__name__)
    pairs, summary = summarize(selected,sources,indices)
    summary.update(comparison=f'{first}_minus_{second}', arm_aliases={'A':first,'B':second})
    return dict(pairs=pairs,summary=summary)


def archive_members(q):
    audit = json.loads(exact(q['prediction_freeze']))
    need(audit['status']=='FORMAL_NATIVE315_READ_ONLY_FREEZE_AUDIT_PASS' and audit['request_sha256']==q['prediction_request_sha256'],'server freeze')
    raw = exact(q['archive'])
    need(digest(raw)==audit['archive']['sha256'] and len(audit['member_sha256'])==320,'archive identity')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as t:
        ms=t.getmembers()
        need([m.name for m in ms]==list(audit['member_sha256']), 'archive inventory')
        out={}
        for m in ms:
            need(m.isfile() and 0<m.size<=8*1024**2,m.name)
            blob=t.extractfile(m).read()
            need(len(blob)==m.size and digest(blob)==audit['member_sha256'][m.name],m.name)
            out[m.name]=blob
    return out


def score(q, result):
    import psutil
    import scipy
    from threadpoolctl import threadpool_limits

    started=time.monotonic(); limits=q['limits']; process=psutil.Process()
    need([np.__version__,scipy.__version__]==q['numeric_versions'],'numeric runtime')
    arc=archive_members(q)
    manifest=list(map(json.loads,arc['manifest.jsonl'].splitlines()))
    need([(x['arm'],x['case']) for x in manifest]==[(a,c) for a in 'RCS' for c in q['case_ids']],'three arm manifest')
    inputs=json.loads(exact(q['dev_cache']))['cases']
    rows=json.loads(exact(q['case_index']))['cases']
    need([r['case_id'] for r in rows]==q['case_ids']==list(inputs),'paired reference order')
    indices=np.random.Generator(np.random.PCG64(2026112707)).integers(0,21,size=(2000,21),dtype=np.int64)
    core=module(q['scorer']); metric=module(q['metrics'])
    scores=[];lookup={(x['arm'],x['case']):x for x in manifest}
    with threadpool_limits(limits=1), (result/'model_scores.jsonl').open('x',encoding='utf8',newline='\n') as log:
        for c in rows:
            cid=c['case_id'];binding=inputs[cid]
            need(c['normalization']==binding['frame'],'physical coordinates')
            with np.load(io.BytesIO(exact(c['reference'])),allow_pickle=False) as z:
                ref={k:z[k] for k in z.files}
            with np.load(io.BytesIO(exact(c['point_file'])),allow_pickle=False) as z:
                y=z['implant']
            need(y.shape==(8192,3) and y.dtype==np.float32 and np.isfinite(y).all() and digest(y.tobytes())==c['target_array_sha256'],'frozen target')
            gt=metric.world_points(y,c['normalization']);a2,_,_=metric.a2_reference(ref)
            for arm in 'RCS':
                need(time.monotonic()-started<=limits['wall_seconds'] and process.memory_info().rss<=limits['RSS_bytes']
                     and log.tell()<=limits['output_bytes'],'resource limit')
                row=lookup[arm,cid]
                name=f'predictions/{arm}_D__{cid}.npz'; raw=arc.pop(name)
                need(row['member']==name and row['sha256']==digest(raw) and row['bytes']==len(raw)
                     and row['input_sha256']==binding['input_sha256'],'manifest member binding')
                arr=verify_payload(raw,binding,row,arm)
                record=dict(arm=arm,fold='D',case_id=cid,source_id=c['source_id'],
                            **core.score_prediction(metric,arr,ref,a2,gt,c['normalization']))
                scores.append(record)
                log.write(json.dumps(record,allow_nan=False)+'\n');log.flush()
    need(len(scores)==315 and len(arc)==5,'all predictions scored')
    save(result/'paired_summary.json',{f'{a}_minus_{b}':comparison(core,scores,q['source_ids'],indices,a,b)
                                      for a,b in (('S','R'),('S','C'),('C','R'))})
    with (result/'source_bootstrap_indices.npy').open('xb') as f:
        np.save(f,indices,allow_pickle=False)
    save(result/'completion.json',dict(status='SCORED_AWAITING_READ_ONLY_FREEZE',rows=315,cases=105,comparisons=3,
                                      request_sha256=q['_request_sha256']))


def main():
    p=argparse.ArgumentParser()
    for k in ('request','request-sha256','authorization','authorization-sha256'):p.add_argument('--'+k,required=True)
    a=p.parse_args()
    q=json.loads(exact(dict(path=a.request,bytes=Path(a.request).stat().st_size,sha256=a.request_sha256)))
    auth=json.loads(exact(dict(path=a.authorization,bytes=Path(a.authorization).stat().st_size,sha256=a.authorization_sha256)))
    need(q['schema']=='bcsp-rbss-cpu-scoring-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'
         and q['execution_authorized'] is False and q['counts']==dict(rows=315,cases=105,comparisons=3), 'frozen request')
    need(auth.get('schema')=='bcsp-development-authorization-v1' and auth.get('request_sha256')==a.request_sha256
         and auth.get('explicit_user_authorization') is True and bool(auth.get('user_authorization_text','').strip()),'single-run authorization')
    need(Path(__file__).resolve()==Path(q['entry']['path']),'scoring entry identity')
    exact(q['entry']); exact(q['interpreter'])
    import sys
    need(Path(sys.executable).resolve()==Path(q['interpreter']['path']),'scoring interpreter')
    out=Path(q['output']);out.mkdir()
    q['_request_sha256']=a.request_sha256
    try:
        score(q,out)
    except BaseException as e:
        save(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(e)))
        raise


if __name__=='__main__':main()
