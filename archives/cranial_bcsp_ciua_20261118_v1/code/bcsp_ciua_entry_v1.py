"""CIUA short entry: explicit authorization, bounded prefix / CPU analysis / Head modes."""
import argparse
import gc
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import socket
import sys
import tarfile
import time
import traceback

PROTOCOL_SHA='d268d3f72a6bb7108637bd627ce28984637262fab77bfc5dd20acf1ab7bac11e'
SCOPE_SHA='abd705213ffdf66c18a099d95502a58cd7a315689e85012515e86261dff8351e'
MANIFEST_SHA='ac1979d5bf76985d8d7eb1666342e50c0abebcc0f973853ba834986d8a586620'
NEW_SHA='17d38fb1d09e9390ec9efdfa9f07ebc1197cffa385c292f60a6e50f9b53aed1a'
REUSE_SHA='8f2a21ae4abaf354720b2d25846b7f7aacb02240d20a65c87a3b576a2a15f99d'
WEIGHTS={'G2_C':'7b0ee55071b8a4d3d916e9324fd306c5edcdea4079f3c30851591f99651376d8','G2_D':'61aec7309b20a67bb0db74dcec7a78d3148265e80fd04fff6699ca0d459ededb'}
COUNTS={'capture':dict(prefix=800,dense=0,loss=0,backward=0,step=0),
        'analysis':dict(records=840,solves=16,forward=0,backward=0,step=0),
        'shadow':dict(cases=40,head_calls=120,encoder=0,dense=0,backward=0,step=0)}


def need(ok,why):
    if not ok:raise ValueError(why)


def clean(p):
    p=Path(p).absolute()
    need(not any(x.is_symlink() for x in (p,*p.parents)), 'linked path '+str(p))
    need(not {'.ssh','.aws','.credentials','.git'} & set(p.parts),'secret path')
    return p


def sha(p):
    h=hashlib.sha256()
    with clean(p).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
    return h.hexdigest()


def exact(r):
    p=clean(r['path'])
    need(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'exact file '+str(p))
    return p


def bound(r):
    return json.loads(exact(r).read_bytes())


def jsonable(x):
    if isinstance(x,dict):return {k:jsonable(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [jsonable(v) for v in x]
    if hasattr(x,'tolist'):return x.tolist()
    return x


def save(p,x):
    with clean(p).open('x',encoding='utf-8') as f:
        json.dump(jsonable(x),f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


def event(p,x):
    with clean(p).open('a',encoding='utf-8') as f:
        f.write(json.dumps(jsonable(x),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())


def pack(out):
    """Same four-file archive convention as the frozen Native entry."""
    files=sorted(p for p in out.rglob('*') if p.is_file())
    records=[dict(name=p.relative_to(out).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    archive=out/'ciua_results_v1.tar.gz'
    with archive.open('xb') as raw:
        with tarfile.open(fileobj=raw,mode='w:gz') as tf:
            for p in files:tf.add(p,arcname=p.relative_to(out).as_posix(),recursive=False)
    sidecars={'.sha256':sha(archive)+'  '+archive.name+'\n','.bytes':str(archive.stat().st_size)+'\n','.contents.sha256':''.join(r['sha256']+'  '+r['name']+'\n' for r in records)}
    for suffix,text in sidecars.items():
        with Path(str(archive)+suffix).open('x',encoding='ascii') as f:f.write(text)
    return dict(path=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=records)


def module(name,record):
    need(name not in sys.modules,'source module already loaded '+name)
    p=exact(record);m=importlib.util.module_from_spec(importlib.util.spec_from_file_location(name,p))
    sys.modules[name]=m
    try:exec(compile(p.read_bytes(),str(p),'exec',dont_inherit=True),m.__dict__)
    except BaseException:sys.modules.pop(name,None);raise
    return m


def authorize(qr,ar,rr):
    q,a,r=bound(qr),bound(ar),bound(rr)
    need(q['schema']=='ciua-execution-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'pending CIUA request')
    need(q['mode'] in COUNTS and q['counts']==COUNTS[q['mode']],'frozen CIUA mode/counts')
    need(q['protocol']['sha256']==PROTOCOL_SHA and q['implementation_scope']['sha256']==SCOPE_SHA,'confirmed protocol and A0 scope')
    exact(q['protocol']);scope=bound(q['implementation_scope'])
    need(scope['later_scientific_counts']['new_prefix_calls']==800,'800 fixed; no 840 fallback')
    need(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='ciua-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'explicit authorization; no reverse runtime binding')
    need(r==dict(schema='ciua-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
    for k in ('capture','analysis'):
        exact(q['implementation'][k])
    exact(q['entry'])
    need(q['limits']['wall_seconds']>0 and q['limits']['RSS_bytes']==8*1024**3 and q['limits']['output_bytes']==1024**3,'bounded limits')
    need(q['attempts']==1 and q['automatic_retry'] is False and q['resume'] is False,'one attempt no retry/resume')
    need(q['limits']['wall_seconds']<=(1800 if q['mode']=='shadow' else 7200),'fixed wall ceiling')
    if q['mode']=='capture':
        need(q['new_manifest']['sha256']==NEW_SHA,'frozen800 manifest')
        canonical_rows(q['rows'],bound(q['new_manifest'])['records'])
    if q['mode']=='analysis':
        need(q['all_manifest']['sha256']==MANIFEST_SHA and q['reuse_manifest']['sha256']==REUSE_SHA,'frozen840/40 manifests')
        canonical_rows(q['rows'],bound(q['all_manifest'])['records'])
    if q['mode']=='shadow':need(q['reuse_manifest']['sha256']==REUSE_SHA,'fixed40 shadows')
    if q['mode'] in ('capture','shadow'):
        need(set(q['checkpoints'])==set(WEIGHTS) and all(q['checkpoints'][k]['sha256']==v and q['checkpoints'][k]['bytes']==478923818 for k,v in WEIGHTS.items()),'fixed two final G2 weights')
    return q


def read_D(np,row):
    with np.load(exact(row['input']),allow_pickle=False) as z:
        D=z['partial'].copy()  # Never access implant in a prefix execution.
    need(D.shape==(8192,3) and D.dtype==np.float32 and np.isfinite(D).all(),'D8192 FP32 finite')
    return D


def canonical_rows(rows,expected):
    need(len(rows)==len(expected) and len({(r['run'],r['case_id']) for r in rows})==len(rows),'exact unique row count')
    for r,e in zip(rows,expected):
        need(all(r[k]==e[k] for k in ('run','fold','role','case_id','source_id','normalization')) and r['input']['sha256']==e['input_sha256'],'frozen ordered row binding')


def run_capture(torch,np,q,out,core,builder,load,budget,head_bytes):
    expected=bound(q['new_manifest'])['records'];canonical_rows(q['rows'],expected)
    need(len(expected)==800,'exact800')
    attempted=successful=0;files=[];states=[]
    for label in ('G2_C','G2_D'):
        model=builder(label);load(model,label);model.eval()
        device=next(model.parameters()).device
        before=core.state(torch,np,model)
        try:
            for row in [r for r in q['rows'] if r['run']==label]:
                budget.sample('before_prefix',attempted)
                D=read_D(np,row);tensor=torch.from_numpy(D).unsqueeze(0).to(device)
                need(attempted<800,'prefix cap');attempted+=1
                event(out/'attempts.jsonl',dict(index=attempted,run=label,case_id=row['case_id'],status='CLAIMED_BEFORE_PREFIX'))
                summary,_=core.capture(torch,np,model,tensor,head_bytes)
                p=out/'features'/(label+'__'+row['case_id']+'.npz')
                with p.open('xb') as f:np.savez_compressed(f,**summary)
                successful+=1
                b=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
                event(out/'features.jsonl',dict(**row,feature=b,prefix_index=attempted))
                files.append(p);budget.sample('after_prefix',attempted)
            after=core.state(torch,np,model);need(before==after,'whole-run state/RNG mismatch')
            states.append(dict(run=label,before=before,after=after))
        finally:
            del model;gc.collect()
    need(attempted==successful==800,'exact800 prefixes complete')
    return dict(status='CIUA800_PREFIX_COMPLETE_PENDING_FREEZE',attempted=attempted,successful=successful,states=states,dense=0,loss=0,backward=0,step=0)


def run_analysis(np,q,out,cap,analysis,budget):
    rows=q['rows'];analysis.validate_rows(rows)
    canonical_rows(rows,bound(q['all_manifest'])['records'])
    fresh=bound(q['fresh_feature_index'])['records'];reuse=bound(q['reuse_manifest'])['records']
    fresh={(r['run'],r['case_id']):r for r in fresh};cached={(r['run'],r['case_id']):r for r in reuse}
    keys={(r['run'],r['case_id']) for r in rows}
    need(len(fresh)==800 and len(cached)==40 and not fresh.keys()&cached.keys() and fresh.keys()|cached.keys()==keys,'800 fresh /40 cached partition')
    exact(q['trace_archive']);features={k:[] for k in analysis.FEATURES};labels=[];ql=[]
    with tarfile.open(q['trace_archive']['path'],'r:gz') as archive:
        for i,row in enumerate(rows):
            budget.sample('before_record',i);key=(row['run'],row['case_id']);D=read_D(np,row)
            if key in cached:
                c=cached[key];need(c['input_sha256']==row['input']['sha256'],'cached input binding')
                feature=cap.cached(np,D,archive,c['member'],c['trace']['sha256'])
            else:
                f=fresh[key];need(f['input']['sha256']==row['input']['sha256'] and f['normalization']==row['normalization'],'fresh input binding')
                with np.load(exact(f['feature']),allow_pickle=False) as z:feature={k:z[k].copy() for k in ('z','mF','mf','Q','D18')}
                need(np.array_equal(feature['D18'],cap.geometry18(np,D)),'fresh D18 exact source arithmetic')
            need(feature['z'].shape==(1024,) and feature['mF'].shape==feature['mf'].shape==(384,) and feature['Q'].shape==(256,3),'compact feature shapes')
            with np.load(exact(row['input']),allow_pickle=False) as z:G=z['implant'].copy()
            need(G.shape==(8192,3) and G.dtype==np.float32 and np.isfinite(G).all(),'GT8192 finite CPU labels only')
            labels.append(analysis.targets(np,G,D));ql.append(analysis.targets(np,feature['Q'],D))
            features['D18'].append(feature['D18']);features['z'].append(feature['z'])
            features['zF'].append(np.r_[feature['z'],feature['mF']]);features['zf'].append(np.r_[feature['z'],feature['mf']])
    result=analysis.analyze(np,rows,{k:np.asarray(v) for k,v in features.items()},np.asarray(labels),np.asarray(ql))
    save(out/'analysis_full.json',result);budget.sample('complete_analysis',840)
    return dict(status='CIUA_CPU_ANALYSIS_COMPLETE_PENDING_FREEZE',records=840,solves=result['solves'],decisions=result['decisions'],new_forward=0)


def run_shadow(torch,np,q,out,core,head_class,budget):
    reuse=bound(q['reuse_manifest'])['records'];need(len(reuse)==40,'40 cached shadow cases')
    exact(q['trace_archive']);calls=0;results=[]
    with tarfile.open(q['trace_archive']['path'],'r:gz') as archive:
        for label in ('G2_C','G2_D'):
            data=torch.load(exact(q['checkpoints'][label]),map_location='cpu',weights_only=True)
            need(data.get('stage')=='BCSP_INPUT_DENSITY_V1' and data.get('epoch')==99 and data.get('updates')==3900,'final3900 weights')
            prefix='base_model.spcg_head.'
            state={k[len(prefix):]:v for k,v in data['base_model'].items() if k.startswith(prefix)}
            head=head_class('G2',state['U']);head.load_state_dict(state,strict=True);head.eval();del data
            for r in [r for r in reuse if r['run']==label]:
                budget.sample('before_shadow',calls)
                m=archive.getmember(r['member']);need(m.isfile() and m.size<=2*1024**2,'bounded shadow member')
                import io
                raw=archive.extractfile(m).read();need(hashlib.sha256(raw).hexdigest()==r['trace']['sha256'],'shadow trace hash')
                with np.load(io.BytesIO(raw),allow_pickle=False) as z:x=z['x'].copy();Q=z['Q'].copy()
                need(calls+3<=120,'shadow cap')
                def on_call(arm,status):
                    nonlocal calls
                    if status=='CLAIMED_BEFORE_HEAD':calls+=1
                    event(out/'attempts.jsonl',dict(run=label,case_id=r['case_id'],arm=arm,status=status,total_claimed=calls))
                norm=q['normalizations'][r['run']+'__'+r['case_id']]
                values,responses=core.shadow(torch,np,head,x,Q,norm['scale'],on_call)
                p=out/'features'/(label+'__'+r['case_id']+'_NMR.npz')
                with p.open('xb') as f:np.savez_compressed(f,**values)
                results.append(dict(run=label,case_id=r['case_id'],responses=responses));budget.sample('after_shadow',calls)
            del head;gc.collect()
    need(calls==120,'exact120 Head calls');save(out/'shadow_responses.json',results)
    return dict(status='CIUA_SHADOW120_COMPLETE_PENDING_FREEZE',head_calls=120,encoder=0,dense=0)


class LocalBudget:
    def __init__(self,q,out):self.q=q;self.out=out;self.start=time.monotonic()
    def sample(self,phase,count):
        import psutil
        L=self.q['limits'];rss=psutil.Process().memory_info().rss
        size=sum(p.stat().st_size for p in self.out.rglob('*') if p.is_file())
        values=dict(RSS_bytes=rss,output_bytes=size,wall_seconds=time.monotonic()-self.start)
        checks=dict(RSS=rss<=L['RSS_bytes'],output=size<=L['output_bytes'],wall=values['wall_seconds']<=L['wall_seconds'])
        event(self.out/'resources.jsonl',dict(phase=phase,count=count,values=values,checks=checks))
        need(all(checks.values()),'CPU resource threshold '+repr(checks))


def gpu_context(q,out,handles):
    """Reuse frozen loaders, numerical policy, source guard and resource monitor."""
    need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
    I=q['identity'];need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'],'current resource identity')
    inherited=bound(q['inherited_request']);root=clean(inherited['model_root']);guard=None
    native=module('ciua_frozen_native',inherited['implementation']['native_reuse'])
    # Extend only the exact source list; inherit payload, UTC and source dispatch rules.
    iq=dict(inherited,implementation=dict(inherited['implementation'],ciua_capture=q['implementation']['capture'],ciua_analysis=q['implementation']['analysis']),entry=q['entry'])
    timezone=module('ciua_exact_utc',inherited['implementation']['timezone']);utc=timezone.ExactUTCReader(timezone.UTC_RESOURCE)
    helper=module('ciua_frozen_helper',inherited['helper']);helper._MONITOR=None
    scope=bound(inherited['preflight_scope']);static=bound(inherited['static_config'])
    records=helper.source_map(scope)
    for rel,r in records.items():helper.exact(root/rel,r['sha256'],r['bytes'])
    for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
    for k,v in q['environment'].items():need(os.environ.get(k)==v.replace('<owned_output>',str(out)),'frozen environment '+k)
    fields=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    need(fields[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(fields[4])<=256,'bound idle GPU')
    import shutil
    need(shutil.disk_usage(out).free>=6*1024**3,'startup disk6GiB')
    envroot=Path(I['python_realpath']).parent.parent;provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
    sys.path[:0]=[str(Path(inherited['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
    helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
    guard=native.make_source_guard(iq)
    handles['guard']=guard
    outputs=[out/'features'/(r['run']+'__'+r['case_id']+'.npz') for r in q['rows']]
    policy=native.make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in q['rows']],[r['path'] for r in q['checkpoints'].values()],outputs,utc,guard)
    sys.addaudithook(policy.audit)
    try:
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        need((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'bound packages')
        need(torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.version.cuda==I['torch_cuda_version'],'one bound CUDA')
        torch.cuda.set_device(0);helper.configure_numeric(torch)
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');ext=importlib.import_module('pointnet2_ops._ext')
        need(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(ext.__file__).resolve())==scope['bindings']['provider'][2]['path'],'actual provider')
        helper.check_backend(chamfer,pn,pm)
        transformer=importlib.import_module('models.Transformer_utils');model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr
        need(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'frozen model config')
        transformer.enable_bcsp_knn();factory=native.load_spcg_builder(inherited['implementation'])
        def builder(label):
            run=native.FROZEN_MODELS[label];model,evidence=native.build_spcg_model(factory,lambda:model_class(EasyDict(static['model'])),run,inherited)
            native.validate_model(model,evidence);return model.to('cuda:0')
        def load(model,label):native.load_checkpoint(torch,model,dict(native.FROZEN_MODELS[label],checkpoint=q['checkpoints'][label]))
        return torch,np,builder,load,native.Budget(q,out,torch,helper),guard
    except BaseException:
        # Source descriptors must remain live until the outer traceback has been persisted.
        raise


def main(argv=None):
    p=argparse.ArgumentParser()
    for k in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):p.add_argument('--'+k,required=True)
    a=p.parse_args(argv);out=None;guard=None;handles={}
    try:
        rec=lambda path,s:dict(path=path,bytes=clean(path).stat().st_size,sha256=s)
        q=authorize(rec(a.request,a.request_sha256),rec(a.authorization,a.authorization_sha256),rec(a.runtime,a.runtime_sha256))
        need(Path(__file__).resolve()==exact(q['entry']),'actual entry source')
        out=clean(q['output']);need(not out.exists() and out.parent.is_dir(),'new output under prepared parent')
        with clean(q['attempt_claim']).open('x') as f:f.write(a.request_sha256+'\n')
        out.mkdir();(out/'features').mkdir()
        event(out/'stages.jsonl',dict(stage='authorized_and_claimed',mode=q['mode']))
        if q['mode']=='capture':
            torch,np,builder,load,budget,guard=gpu_context(q,out,handles)
        else:
            need(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU only')
            need(str(Path(sys.executable).resolve())==str(exact(q['CPU_python']).resolve()),'bound CPU interpreter')
            import numpy as np
            budget=LocalBudget(q,out)
        cap=module('ciua_capture',q['implementation']['capture']);analysis=module('ciua_analysis',q['implementation']['analysis'])
        if q['mode']=='capture':result=run_capture(torch,np,q,out,cap,builder,load,budget,exact(q['head_source']).read_bytes())
        elif q['mode']=='analysis':result=run_analysis(np,q,out,cap,analysis,budget)
        else:
            import torch
            head=module('bcsp_ciua_frozen_head',q['head_source']).SPCGHead
            result=run_shadow(torch,np,q,out,cap,head,budget)
        save(out/'completion.json',result)
        budget.sample('before_manifest',q['counts'].get('prefix',q['counts'].get('records',120)))
        members=[dict(path=str(x.relative_to(out)),bytes=x.stat().st_size,sha256=sha(x)) for x in sorted(out.rglob('*')) if x.is_file()]
        save(out/'output_manifest.json',dict(files=members,request_sha256=a.request_sha256))
        save(out/'archive_receipt.json',pack(out))
        # Never mutate an already manifested resource log.
        need(sum(x.stat().st_size for x in out.rglob('*') if x.is_file())<=q['limits']['output_bytes'],'final output cap')
        return 0
    except BaseException as exc:
        detail=dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),traceback=traceback.format_exc())
        if out is not None and out.is_dir() and not (out/'failure.json').exists():save(out/'failure.json',detail)
        print(json.dumps(detail),file=sys.stderr,flush=True);return 1
    finally:
        final_guard=guard if guard is not None else handles.get('guard')
        if final_guard is not None:final_guard.close()


if __name__=='__main__':sys.exit(main())
