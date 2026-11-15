"""Ten fixed SCQ S observations. Inert import; no RF head, GT, loss or updates."""
import argparse,gc,hashlib,importlib.util,json,os,random,shutil,socket,sys,time
from pathlib import Path

PARENT_SHA='c74e0da099d170dca3f4d1e002998ad0ce634aae702f0d2e6b324cc469ef5d81'
PARENT_REQUEST_SHA='ce4b4b672a299934721d0b0f1fb22ea23de1bc41fd998ff94e10368fe1ebee5a'
CASES_C=('train__013__frontoorbital','train__051__frontoorbital','train__053__frontoorbital','train__036__bilateral','train__105__frontoorbital','train__076__parietotemporal','train__042__random_1')
CASES_D=('train__046__parietotemporal','train__069__random_2','train__054__random_2')
COUNTS=dict(forward=10,extra_N1_KNN=10,backward=0,optimizer_steps=0,loss=0,BNCal=0,warmup=0,retry=0)
LIMITS=dict(wall_seconds=1800,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=2147483648,minimum_free_disk_bytes=4294967296)

def require(ok,message):
    if not ok:raise RuntimeError(message)

def clean(path):
    p=Path(path).absolute()
    require(not any(x.is_symlink() for x in (p,*p.parents)),'original path links: '+str(p))
    require(not ({'.ssh','.aws','.git','.credentials'}&set(p.parts)) and p.name not in {'.env','.netrc'},'secret path')
    return p

def exact(r):
    p=clean(r['path']);require(p.is_file() and p.stat().st_size==r['bytes'],'file size: '+str(p))
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    require(h.hexdigest()==r['sha256'],'file SHA256: '+str(p));return p

def bound(r):return json.loads(exact(r).read_bytes())

def source(name,record):
    require(name not in sys.modules,'preloaded module')
    p=exact(record);spec=importlib.util.spec_from_file_location(name,p);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    try:exec(compile(p.read_bytes(),str(p),'exec',dont_inherit=True),module.__dict__)
    except BaseException:sys.modules.pop(name,None);raise
    return module

def validate(q):
    require(q['schema']=='bcsp-scq-rf-ten-memory-capture-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'pending request only')
    require(q['counts']==COUNTS and q['limits']==LIMITS and q['batch_size']==1,'fixed ten zero-update budget')
    require(q['parent_entry']['sha256']==PARENT_SHA and q['parent_request']['sha256']==PARENT_REQUEST_SHA,'frozen parent')
    require(q['variant']=='S' and q['RF_head_installed'] is False and q['GT_access'] is False,'observation only')
    require(q['comparison_tolerance']==dict(normalized_max_abs=1e-6,world_max_abs_mm=.001),'existing trace equivalence tolerance')
    rows=q['cases'];require([(x['fold'],x['case_id']) for x in rows]==[('C',c) for c in CASES_C]+[('D',c) for c in CASES_D],'fixed ordered cases')
    require(len({x['input']['path'] for x in rows})==10 and len({x['source_id'] for x in rows})==10,'ten unique inputs/sources')
    require([x['label'] for x in q['runs']]==['S_C','S_D'] and all(x['variant']=='S' for x in q['runs']),'two S checkpoints')
    pinned={'C':'00f1ce94d219a42294c6c5a7874710edbd58431deac44c9522a9ab4f120d2f0b','D':'bd8fe23f1a276019b776b5d2cadce7aad62bd31eea440975ffd1222331f636fa'}
    for run in q['runs']:require(run['checkpoint']['sha256']==pinned[run['fold']],'wrong SCQ checkpoint')
    for row in rows:
        cid=row['case_id'];require(row['source_id']=='train:'+cid.split('__')[1] and row['n_input']==row['n_output']==8192,'case identity')
        require(row['run']=='S_'+row['fold'] and row['normalization_source']=='defective_bbox','model/frame')
        require(row['input']['path'].startswith('/home/jovyan/adapointr_work/PoinTr/data/') and row['input']['path'].endswith('/'+cid+'_8192.npz'),'input path')
        require(row['normalization']['scale']>0 and len(row['normalization']['center'])==3,'D-only normalization')
        require(row['output_filename']=='memory/'+row['run']+'__'+cid+'.npz','output member')
    root=Path('/home/jovyan/adapointr_work/PoinTr');require(Path(q['output']).parent==root/'logs/cranial_bcsp_fullmamba','output boundary')
    require(q['launch_contract']['single_attempt'] is True and q['launch_contract']['timeout_seconds']==1800,'single attempt timeout')
    for key in ('output','launch_attempt'):clean(q[key])
    for key in ('request_path','authorization','runtime','launcher','log','pid','exit_code'):clean(q['launch_contract'][key])
    return q

def authorize(qr,ar,rr):
    q,a,r=bound(qr),bound(ar),bound(rr);validate(q)
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='scq-rf-memory-authorization-v1','authorization schema')
    require(a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'explicit full hash authorization')
    require(set(r)=={'schema','request_sha256','authorization_sha256'} and r['schema']=='scq-rf-memory-runtime-v1' and r['request_sha256']==qr['sha256'] and r['authorization_sha256']==ar['sha256'],'one-way runtime binding')
    return q

def validate_reuse(q,p,parent):
    require(q['identity']==p.CURRENT_IDENTITY==parent['identity'],'current identity must be freshly reverified before activation')
    for k in ('model_root','static_config','preflight_scope','dependencies','helper','implementation','initialization','numeric_policy','environment'):
        require(q[k]==parent[k],'frozen inherited binding '+k)
    index=p.bound(parent['input_index']);lookup={(x['fold'],x['case_id']):x for x in index['inputs'] if x['variant']=='S'}
    for row in q['cases']:
        old=lookup[(row['fold'],row['case_id'])]
        require(all(row[k]==old[k] for k in ('input','normalization','normalization_source','source_id','run')),'inherited case binding')
    require(q['runs']==[x for x in index['runs'] if x['variant']=='S'],'exact S run records')
    p.validate_evidence(parent,index)
    scope=bound(q['capture_scope']);original={(x['fold'],x['case_id']):x for x in scope['cases']}
    for row in q['cases']:
        item=original[(row['fold'],row['case_id'])]
        require(row['reference']['bytes']==item['frozen_prediction']['bytes'] and row['reference']['sha256']==item['frozen_prediction']['sha256'],'native reference identity')

def descriptor(t,M,F,z,Q,idx):
    require(M.shape==(1,256,3) and F.shape==(1,256,384) and z.shape==(1,1024) and Q.shape==(1,256,3),'descriptor shapes')
    require(idx.shape==(1,256,8) and idx.dtype==t.int64 and idx.device==M.device and bool((idx>=0).all()) and bool((idx<256).all()),'native index contract')
    require(all(x.dtype==t.float32 and x.device==M.device and bool(t.isfinite(x).all()) for x in (M,F,z,Q)),'finite FP32 descriptor')
    batch=t.arange(1,device=M.device)[:,None,None]
    nf=t.nn.functional.layer_norm(F,(384,),eps=1e-5)[batch,idx]
    fa=nf.mean(2);fm=nf.max(2).values;d=M[batch,idx]-Q[:,:,None,:];mean=d.mean(2)
    sigma=((d-mean[:,:,None,:]).square().mean(2)+1e-6).sqrt();rho=t.linalg.vector_norm(d,dim=-1).mean(2,keepdim=True)
    g=t.cat((mean,sigma,rho),-1)
    return t.cat((z[:,None,:].expand(-1,256,-1),fa,fm,Q,g),-1),dict(fa=fa,fm=fm,g=g,rho=rho)

def observe_once(t,np,p,model,x):
    require(not model.training and not any(m.training for m in model.modules()),'eval only')
    module=model.base_model.scq;seen={'pre':0,'post':0};saved={};handles=[]
    def pre(m,args):
        seen['pre']+=1;require(seen['pre']==1 and len(args)==4,'one original SCQ call')
        for key,value in zip(('M','F','z','Qraw'),args):saved[key]=value.detach().clone()
    def post(m,args,result):
        seen['post']+=1;require(seen['post']==1 and isinstance(result,tuple) and len(result)==2,'SCQ return tuple')
        Q1,info=result
        for key,value in [('Q1',Q1),('delta0',info['delta']),('N0',info['indices'])]:saved[key]=value.detach().clone()
    try:
        handles.append(module.register_forward_pre_hook(pre));handles.append(module.register_forward_hook(post))
        coarse,dense=p.predict_once(t,model,x)
    finally:
        for handle in handles:handle.remove()
    require(seen==dict(pre=1,post=1),'SCQ observation counts')
    with t.inference_mode():
        M,F,z,Q0,Q1,N0=(saved[k] for k in ('M','F','z','Qraw','Q1','N0'))
        require(np.array_equal(Q1.cpu().numpy(),coarse),'observed Q1 is returned coarse')
        require(t.allclose(Q0+saved['delta0'],Q1,rtol=2e-6,atol=2e-7),'Qraw plus delta0')
        N1=model.base_model.decoder.knn(8,M,Q1)
        h0,a0=descriptor(t,M,F,z,Q1,N0);h1,a1=descriptor(t,M,F,z,Q1,N1)
        overlap=(N0[:,:,:,None]==N1[:,:,None,:]).any(-1).float().mean(-1)
        summary=dict(neighbor_overlap_mean=float(overlap.mean()),neighbor_overlap_min=float(overlap.min()),changed_neighbor_queries=int((overlap<1).sum()),h_max_abs_difference=float((h1-h0).abs().max()),h_exactly_equal=bool(t.equal(h0,h1)),fa_L2_mean=float(t.linalg.vector_norm(a1['fa']-a0['fa'],dim=-1).mean()),geometry_L2_mean=float(t.linalg.vector_norm(a1['g']-a0['g'],dim=-1).mean()),old_neighbor_mean_distance=float(a0['rho'].mean()),new_neighbor_mean_distance=float(a1['rho'].mean()),interpretation='DISTINCTION_MEASUREMENTS_ONLY_NOT_EFFICACY_OR_ANATOMICAL_CORRESPONDENCE')
        arrays={k:v.cpu().numpy().copy()[0] for k,v in saved.items()}
        arrays.update(N1=N1.cpu().numpy().copy()[0],h_static=h0.cpu().numpy().copy()[0],h_requery=h1.cpu().numpy().copy()[0],prediction=dense[0].copy(),coarse=coarse[0].copy())
    model.base_model._scq_last_info=None
    return arrays,summary

def compare_reference(np,arrays,row):
    with np.load(exact(row['reference']),allow_pickle=False) as z:
        require(set(z.files)=={'prediction','coarse','Qraw','delta'},'Native reference keys')
        pairs=[('prediction','prediction'),('coarse','Q1'),('Qraw','Qraw'),('delta','delta0')]
        errors={}
        for old,new in pairs:
            ref=z[old];current=arrays[new]
            require(ref.shape==current.shape and ref.dtype==current.dtype==np.float32,'reference shape/dtype')
            require(np.isfinite(ref).all() and np.isfinite(current).all(),'reference finite')
            delta=float(np.max(np.abs(ref.astype(np.float64)-current.astype(np.float64))))
            require(delta<=1e-6 and delta*row['normalization']['scale']<=.001,'Native equivalence stop, not widen tolerance')
            errors[old]=dict(normalized_max_abs=delta,world_max_abs_mm=delta*row['normalization']['scale'])
        return errors

def execute(t,np,p,helper,q,out,budget,builder,loader,device='cuda:0',artificial_cpu=False):
    require((device=='cpu') is artificial_cpu,'production is CUDA only')
    attempts=returned=extra_knn=0;files=[];states=[]
    journal=out/'forward_attempts.jsonl';manifest=out/'memory_manifest.jsonl';summaries=out/'neighbor_summaries.jsonl'
    for path in (journal,manifest,summaries):path.open('x').close()
    try:
        for run in q['runs']:
            random.seed(0);np.random.seed(0);t.manual_seed(0)
            model,construction=builder(run);loader(t,model,run);model.eval();model.to(device)
            if not artificial_cpu:t.cuda.synchronize();t.cuda.reset_peak_memory_stats(0)
            model.enable_full_instrumentation(False)
            before=helper.state_sha(model);rng=p.rng_state(t,np,helper,not artificial_cpu);budget.sample('model_start:'+run['label'],attempts)
            selected=[row for row in q['cases'] if row['run']==run['label']]
            for row in selected:
                budget.sample('before_forward',attempts);x=t.from_numpy(p.load_partial(np,row)).unsqueeze(0).to(device)
                require(attempts<10,'forward cap');attempts+=1
                p.append_event(journal,dict(status='CLAIMED_BEFORE_FORWARD',forward_index=attempts,case_id=row['case_id'],run=run['label']))
                arrays,summary=observe_once(t,np,p,model,x);returned+=1;extra_knn+=1
                errors=compare_reference(np,arrays,row)
                path=out/row['output_filename']
                with path.open('xb') as f:np.savez_compressed(f,**arrays)
                files.append(path)
                p.append_event(manifest,dict(run=run['label'],case_id=row['case_id'],input=row['input'],checkpoint=run['checkpoint'],normalization=row['normalization'],name=row['output_filename'],bytes=path.stat().st_size,sha256=p.sha(path),forward_index=attempts,equivalence=errors,z_definition='backbone global_feature at original SCQ input, not rebuild_global_feature'))
                p.append_event(summaries,dict(run=run['label'],case_id=row['case_id'],**summary))
                if not artificial_cpu:helper.assert_numeric(t)
                budget.sample('after_forward',attempts);del arrays,x
            after=helper.state_sha(model);rng_after=p.rng_state(t,np,helper,not artificial_cpu)
            require(before==after and rng==rng_after,'model or RNG changed')
            states.append(dict(run=run['label'],forwards=len(selected),state_before=before,state_after=after,RNG_before=rng,RNG_after=rng_after,construction=construction))
            del model;gc.collect()
            if not artificial_cpu:t.cuda.empty_cache()
        require(attempts==returned==extra_knn==len(files)==10,'exact ten captures and extra KNN')
        budget.sample('all_complete',attempts)
        return files+[journal,manifest,summaries],states
    except BaseException as exc:
        p.emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',forward_attempts=attempts,valid_returns=returned,extra_KNN=extra_knn,error=repr(exc),training=0))
        raise

def render_launcher(q,qsha,asha,rsha,parent):
    return parent.render_launcher(q,qsha,asha,rsha)

def main():
    parser=argparse.ArgumentParser()
    for key in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):parser.add_argument('--'+key,required=True)
    args=parser.parse_args()
    def r(path,digest):return dict(path=path,bytes=clean(path).stat().st_size,sha256=digest)
    qr=r(args.request,args.request_sha256);q=authorize(qr,r(args.authorization,args.authorization_sha256),r(args.runtime,args.runtime_sha256))
    p=source('scq_rf_frozen_native_parent',q['parent_entry']);parent=bound(q['parent_request']);validate_reuse(q,p,parent)
    I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
    require(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
    require(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'current container/Python')
    require(Path.cwd().resolve()==Path(I['project']) and Path(__file__).resolve()==exact(q['entry']),'project and entry')
    cmdline=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    require(cmdline[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','1800s'],'external timeout')
    require(json.loads(clean(q['launch_attempt']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'one-shot claim')
    p3=bound(q['P3']);require(p3['status']=='SCQ_RF_OBSERVER_LOCAL_P3_PASS' and p3['entry_sha256']==q['entry']['sha256'] and all(p3['checks'].values()),'P3 exact final entry')
    timezone=p.source_module('scq_rf_exact_utc',q['implementation']['timezone']);utc=timezone.ExactUTCReader(timezone.UTC_RESOURCE);guard=None
    try:
        static=bound(q['static_config']);scope=bound(q['preflight_scope']);helper=p.source_module('scq_rf_reused_helper',q['helper']);helper._MONITOR=None
        records=helper.source_map(scope)
        for rel,record in records.items():helper.exact(root/rel,record['sha256'],record['bytes'])
        helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
        for record in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(record['path'],record['sha256'],record['bytes'])
        for row in q['cases']:exact(row['input']);exact(row['reference'])
        for run in q['runs']:exact(run['checkpoint'])
        for key,value in q['environment'].items():require(os.environ.get(key)==value.replace('<owned_output>',str(out)),'environment '+key)
        smi=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
        require(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256,'GPU identity and idle')
        require(out.is_dir() and {x.name for x in out.iterdir()}=={'launch.log'},'fresh output')
        for name in ('memory','tmp'):(out/name).mkdir()
        with (out/'worker.pid').open('x') as f:f.write(str(os.getpid()))
        guard=p.make_source_guard(q['implementation'],q['initialization'])
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
        sys.path[:0]=[str(Path(q['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
        outputs=[out/row['output_filename'] for row in q['cases']]
        policy=p.make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[row['input']['path'] for row in q['cases']]+[row['reference']['path'] for row in q['cases']],[x['checkpoint']['path'] for x in q['runs']],outputs,utc,guard)
        sys.addaudithook(policy.audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
        require(torch.cuda.is_available() and torch.cuda.device_count()==1,'one CUDA device');torch.cuda.set_device(0);helper.configure_numeric(torch)
        require(torch.version.cuda==I['torch_cuda_version'],'torch CUDA')
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');native=importlib.import_module('pointnet2_ops._ext')
        require(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(native.__file__).resolve())==scope['bindings']['provider'][2]['path'],'PointNet2 origins');helper.check_backend(chamfer,pn,pm)
        transformer=importlib.import_module('models.Transformer_utils');model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr
        require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'model config');transformer.enable_bcsp_knn()
        factory=p.load_scq_builder(q['implementation'])
        def builder(run):
            model,evidence=p.build_scq_model(factory,lambda:model_class(EasyDict(static['model'])),run,q['initialization']);p.validate_model(model,evidence);return model,evidence
        budget=p.Budget(q,out,torch,helper)
        files,states=execute(torch,np,p,helper,q,out,budget,builder,p.load_checkpoint)
        done=out/'capture_complete.json';p.emit(done,dict(status='TEN_MEMORY_CAPTURES_AWAITING_FORMAL_FREEZE',counts=COUNTS,models=states,request_sha256=qr['sha256'],scientific_efficacy_claim=False))
        archive=p.pack(out,files+[done,budget.path])
        require(sum(x.stat().st_size for x in out.rglob('*') if x.is_file())<=q['limits']['output_bytes'] and time.monotonic()-budget.start<=q['limits']['wall_seconds'] and shutil.disk_usage(out).free>=q['limits']['minimum_free_disk_bytes'],'post-archive resource bounds')
        p.emit(out/'completion.json',dict(status='CAPTURE_ARCHIVED_AWAITING_FORMAL_FREEZE',counts=COUNTS,archive=archive,request_sha256=qr['sha256']))
    except BaseException as exc:
        if out.exists() and not (out/'failure.json').exists():p.emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),training=0))
        raise
    finally:
        if guard is not None:guard.close()
        utc.close()

if __name__=='__main__':main()
