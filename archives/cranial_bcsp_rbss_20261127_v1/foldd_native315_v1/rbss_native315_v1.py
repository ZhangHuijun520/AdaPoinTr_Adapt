"""Same-case R/C/S Native prediction with actual token observations."""
import argparse
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import tarfile
import time
import types

ARMS = 'RCS'
COUNTS = dict(forward=315, loss=0, backward=0, optimizer_steps=0)


def need(ok, msg):
    if not ok:raise ValueError(msg)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def schedule(ids):
    need(len(ids)==len(set(ids))==105, 'exact 105-case population')
    return [(arm,cid) for arm in ARMS for cid in ids]


def choose(lib, np, torch, arm, x, asset, pos, order, inv, geometry):
    need(tuple(pos.shape)==(1,256,3), 'actual target mixer input')
    s,o,v=(t.detach().cpu().contiguous().numpy()[0] for t in (pos,order,inv))
    need(lib.content_key(x,asset['frame'],s,o,geometry,'RBSS-v2')==asset['key'] and sha(s.tobytes())==asset['anchors_sha256']
         and o.tolist()==asset['order']['R'] and v.tolist()==asset['inverse']['R'], 'live input/anchor/order mismatch')
    a=arm if asset['active'] else 'R'
    chosen=asset['order'][a]; inverse=asset['inverse'][a]
    ids=np.arange(256)
    need(np.array_equal(np.asarray(chosen)[inverse],ids) and np.array_equal(np.asarray(inverse)[chosen],ids),'permutation inverse')
    record=dict(anchors=s,pi0=o,pi=np.asarray(chosen,dtype=np.int64),inverse=np.asarray(inverse,dtype=np.int64))
    pair=None if a=='R' else tuple(torch.tensor([z],dtype=torch.long,device=pos.device) for z in (chosen,inverse))
    return pair,record


def bound(path, digest):
    p=Path(path)
    need(p.is_file() and p.resolve()==p,str(p))
    b=p.read_bytes()
    need(sha(b)==digest,str(p))
    return b


def source(record):
    b=bound(record['path'],record['sha256']);need(len(b)==record['bytes'],'source size')
    m=types.ModuleType(Path(record['path']).stem);m.__file__=record['path']
    exec(compile(b,m.__file__,'exec'),m.__dict__)
    return m


def run(q, out, request_sha, prefix, orderlib, parent, support, started):
    import random

    native=support.source('rbss_prediction_native_loader',q['files']['native_loader'])
    torch,np,helper,_=native.prepare_models(parent,support)
    helper._MONITOR=None
    assets=json.loads(support.exact(q['files']['dev_orders']).read_bytes())['cases']
    expected=schedule(q['case_ids'])
    need(list(assets)==q['case_ids'],'cache cohort and order')
    fold=json.loads(support.exact(parent['fold']).read_bytes())['folds']['D']
    need(fold['dev_case_ids']==q['case_ids'] and not set(assets)&set(fold['train_case_ids']),'Fold D development only')
    x={}
    for cid in q['case_ids']:
        a=assets[cid]
        need(a['input']['path']==str(Path(q['development_root'])/'points'/f'{cid}_8192.npz'),'exact development input')
        with np.load(io.BytesIO(support.exact(a['input']).read_bytes()),allow_pickle=False) as z:
            p=z['partial']
        need(p.shape==(8192,3) and p.dtype==np.float32 and np.isfinite(p).all() and sha(p.tobytes())==a['input_sha256'],cid)
        x[cid]=p
    calls=0;states=[];archives=[];keys={}
    for arm in ARMS:
        model,target=prefix.build_model(parent,support,torch,helper,*q['seeds'])
        ck=torch.load(support.exact(q['checkpoints'][arm]),map_location='cpu',weights_only=True)
        need((ck['epoch'],ck['updates'],ck['scq_prime_run_identity'])==(99,3900,dict(variant=arm,fold='D',seed=q['seeds'][0])), 'checkpoint run identity')
        model.load_state_dict(ck['base_model'],strict=True);del ck
        model.eval().requires_grad_(False).to('cuda:0')
        base=model.base_model
        mixers=[block.attn.mixer for block in base.encoder.blocks.blocks]
        mixers.extend(m for block in base.decoder.blocks for m in (block.self_ssm,block.cond_ssm))
        need(len({id(m) for m in mixers})==22,'native SSM modules')
        def snapshot():
            g=np.random.get_state()
            return dict(state=helper.state_sha(model),cpu=helper.tensor_sha(torch.get_rng_state()),cuda=helper.tensor_sha(torch.cuda.get_rng_state(0)),
                        python=sha(repr(random.getstate()).encode()),numpy=sha(repr((g[0],*g[2:])).encode()+g[1].tobytes()))
        state=snapshot()
        for cid in q['case_ids']:
            need(calls<315 and expected[calls]==(arm,cid),'authorized call order')
            calls+=1
            prefix.emit(out/'attempts.jsonl',dict(index=calls,arm=arm,case=cid),'a')
            asset=assets[cid];obs=[]
            scans=0
            def count(*_):
                nonlocal scans
                scans+=1
            def select(pos,order,inv):
                need(not obs,'exactly one target mixer call')
                pair,rec=choose(orderlib,np,torch,arm,x[cid],asset,pos,order,inv,q['geometry_sha256'])
                obs.append(rec)
                return pair
            with ExitStack() as stack:
                stack.enter_context(orderlib.temporary_order(target,torch,select))
                for m in mixers:stack.callback(m.register_forward_hook(count).remove)
                payload=native.observe_once(torch,np,model,torch.from_numpy(x[cid]).unsqueeze(0).to('cuda:0'),'A')
            need(scans==36 and len(obs)==1 and np.array_equal(obs[0]['anchors'],payload['S']),'mixer calls and coarse head token identity')
            observed=sha(obs[0]['anchors'].tobytes())+':'+sha(obs[0]['pi0'].tobytes())
            need(keys.setdefault(cid,observed)==observed,'paired native anchor order')
            payload.update({k:obs[0][k] for k in ('pi0','pi','inverse')},active=np.asarray(asset['active']))
            f=out/'predictions'/f'{arm}_D__{cid}.npz'
            with f.open('xb') as stream:np.savez_compressed(stream,**payload)
            archives.append(f)
            prefix.emit(out/'manifest.jsonl',dict(index=calls,arm=arm,case=cid,active=asset['active'],k=asset['k'],
               fallback_reasons=asset['reasons'],matched_edges=asset['edges'][arm],native_anchor_order=observed,ssm_calls=scans,
               input_sha256=asset['input_sha256'],checkpoint_sha256=q['checkpoints'][arm]['sha256'],frame=asset['frame'],
               member=f.relative_to(out).as_posix(),bytes=f.stat().st_size,sha256=support.file_hash(f)), 'a')
            if calls%15==0:prefix.emit(out/'resources.jsonl',prefix.gpu_sample(q,out,started,torch),'a')
        after=snapshot();need(after==state,'model state or RNG changed')
        states.append(dict(arm=arm,before=state,after=after))
        del model,target
        torch.cuda.empty_cache()
    need(calls==len(archives)==315,'all predictions complete')
    prefix.emit(out/'completion.json',dict(request_sha256=request_sha,counts=COUNTS,states=states,paired_cases=len(keys)),'x')
    archive=out/'RBSS_FoldD_native315.tar.gz'
    with archive.open('xb') as f,tarfile.open(fileobj=f,mode='w:gz') as t:
        for p in [*archives,*(out/n for n in ('started.json','attempts.jsonl','manifest.jsonl','completion.json','resources.jsonl'))]:
            t.add(p,arcname=p.relative_to(out).as_posix(),recursive=False)
    need(sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=q['binding']['resources']['output_bytes'],'output cap')
    prefix.emit(out/'archive_receipt.json',dict(bytes=archive.stat().st_size,sha256=support.file_hash(archive),members=320),'x')


def main():
    p=argparse.ArgumentParser()
    for k in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):p.add_argument('--'+k,required=True)
    a=p.parse_args()
    q=json.loads(bound(a.request,a.request_sha256))
    auth=json.loads(bound(a.authorization,a.authorization_sha256));rt=json.loads(bound(a.runtime,a.runtime_sha256))
    need(q['schema']=='bcsp-rbss-native315-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'
         and not q['execution_authorized'] and q['counts']==COUNTS and q['seeds']==[2026112701,2026112703],'frozen prediction request')
    need(auth.get('schema')=='bcsp-development-authorization-v1' and auth.get('request_sha256')==a.request_sha256
         and auth.get('explicit_user_authorization') is True and bool(auth.get('user_authorization_text','').strip())
         and rt==dict(schema='bcsp-development-runtime-v1',request_sha256=a.request_sha256,authorization_sha256=a.authorization_sha256),'single-run authorization')
    b=q['binding'];i=b['identity'];out=Path(b['output'])
    need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
         and (socket.gethostname(),os.getuid(),os.environ.get('CUDA_VISIBLE_DEVICES'),str(Path(sys.executable).resolve()),sys.version.split()[0])
         ==(i['hostname'],i['uid'],i['gpu_uuid'],i['python_realpath'],i['python_version']),'bound runtime')
    need(Path(q['files']['worker']['path'])==Path(__file__).resolve(),'worker path')
    for r in q['files'].values():need(len(bound(r['path'],r['sha256']))==r['bytes'],'asset size')
    prefix=source(q['files']['prefix']);order=source(q['files']['order_adapter'])
    parent=json.loads(bound(b['historical_request'],prefix.PARENT_SHA));parent['identity'].update(i)
    support=prefix.load_support(parent)
    need(out.resolve()==out and not os.path.lexists(out),'fresh output')
    started=time.monotonic();gpu=prefix.gpu_sample(q,out,started)
    out.mkdir();(out/'predictions').mkdir()
    prefix.emit(out/'started.json',dict(request_sha256=a.request_sha256,gpu=gpu),'x')
    for k,v in parent['environment'].items():
        if k not in ('CUDA_VISIBLE_DEVICES','TMPDIR','XDG_CACHE_HOME','MPLCONFIGDIR','TRITON_CACHE_DIR','HF_HOME'):os.environ[k]=v
    for k in ('TMPDIR','XDG_CACHE_HOME','MPLCONFIGDIR','TRITON_CACHE_DIR','HF_HOME'):
        d=out/k;d.mkdir();os.environ[k]=str(d)
    run(q,out,a.request_sha256,prefix,order,parent,support,started)


if __name__=='__main__':main()
