"""TRACE D0: authorized observation only; inert import; 80 full forward / zero updates."""
import argparse,gc,hashlib,importlib.util,json,os,random,socket,sys,time,traceback
from pathlib import Path,PurePosixPath

PARENT_SHA='c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc'
PREP_SHA='5271bdca720cb4e3ec8a260abddb8374006a4e9aa6ecfc494f9f5df5f001a95f'
NATIVE_SHA='223777e0dd409b58b04ab6fbcf53b71e76418fd9ff77b48a0a6e421517eaeb07'
ORDER=['G1_C','G2_C','G1_D','G2_D']
COUNTS=dict(full_forward=80,models=4,cases=40,per_model=20,batch=1,loss=0,backward=0,optimizer_step=0,warmup=0,retry=0,BNCal=0,training=0)

def need(ok,message):
    if not ok:raise ValueError(message)

def clean(path):
    p=Path(path).absolute()
    need(not any(x.is_symlink() for x in (p,*p.parents)), 'linked path: '+str(p))
    need(not {'.ssh','.aws','.credentials','.git'} & set(p.parts), 'secret directory')
    return p

def exact(record):
    p=clean(record['path']);need(p.is_file() and p.stat().st_size==record['bytes'],'file size: '+str(p))
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    need(h.hexdigest()==record['sha256'],'file SHA256: '+str(p));return p

def bound(record):return json.loads(exact(record).read_bytes())

def module(name,record):
    need(name not in sys.modules,'module already loaded: '+name)
    p=exact(record);m=importlib.util.module_from_spec(importlib.util.spec_from_file_location(name,p));sys.modules[name]=m
    try:exec(compile(p.read_bytes(),str(p),'exec',dont_inherit=True),m.__dict__)
    except BaseException:sys.modules.pop(name,None);raise
    return m

def authorize(qr,ar,rr):
    q,a,r=bound(qr),bound(ar),bound(rr)
    need(q['schema']=='bcsp-trace-D0-execution-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'pending TRACE request')
    need(q['counts']==COUNTS and q['order']==ORDER,'fixed80 and zero updates')
    need(q['parent_native_request']['sha256']==PARENT_SHA and q['preparation_scope']['sha256']==PREP_SHA,'inherited scope pins')
    parent,prep=bound(q['parent_native_request']),bound(q['preparation_scope'])
    need(q['identity']==parent['identity'] and q['environment']==parent['environment'],'frozen identity/environment')
    need(q['limits']==dict(parent['limits'],wall_seconds=900) and q['startup_free_disk_bytes']==6*1024**3,'resource thresholds')
    need(q['input_records']==prep['input_records'] and q['checkpoints']==prep['checkpoints'],'exact80 rows / four weights')
    for key in ['model_root','mother_source','static_config','preflight_scope','helper','probe_asset','head_initialization','parent_G0_initial_state_sha256','dependencies']:
        need(q[key]==parent[key],'inherited '+key)
    for key,rec in parent['implementation'].items():need(q['implementation'][key]==rec,'inherited source '+key)
    need(q['implementation']['native_reuse']['sha256']==NATIVE_SHA,'frozen Native functions')
    need(q['output']==prep['future_paths'][1]['path'],'owned output pin')
    base=PurePosixPath(prep['future_paths'][0]['path']);L=q['launch_contract']
    need(L==dict(request_path=str(base/'TRACE_D0_execution_request_v1.json'),authorization=str(base/'TRACE_D0_authorization_v1.json'),runtime=str(base/'TRACE_D0_runtime_v1.json'),launcher=str(base/'launch_TRACE_D0_once_v1.sh'),session='TRACE_D0_memory_20261117_v1',log=q['output']+'/launch.log',exit_code=q['output']+'/exit_code'),'launch paths')
    need(q['launch_attempt']==str(base/'TRACE_D0_single_attempt_claim_v1.json'),'single attempt path')
    need(q['entry']['path']==str(base/'bcsp_trace_D0_entry_v1.py') and q['implementation']['observer']['path']==str(base/'bcsp_trace_D0_observer_v1.py'),'entry paths')
    need(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-trace-D0-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'explicit authorization')
    need(r==dict(schema='bcsp-trace-D0-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime binding')
    p3=bound(q['P3']);need(p3['status']=='TRACE_D0_LOCAL_P3_PASS' and all(p3['checks'].values()) and p3['entry_sha256']==q['entry']['sha256'] and p3['observer_sha256']==q['implementation']['observer']['sha256'],'final P3')
    return q

def write_json(path,value):
    with clean(path).open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False)

def execute(torch,np,native,helper,observer,q,out,builder,budget,*,device='cuda:0',artificial_cpu=False):
    need((device=='cpu') is artificial_cpu,'CPU only with explicit artificial fixture')
    need(q['counts']==COUNTS and q['order']==ORDER and len(q['input_records'])==80,'80 contract')
    rows=q['input_records'];need([r['run'] for r in rows]==[run for run in ORDER for _ in range(20)],'fixed model order')
    for fold in ('C','D'):
        a=[r for r in rows if r['run']=='G1_'+fold];b=[r for r in rows if r['run']=='G2_'+fold]
        need(len({r['case_id'] for r in a})==20 and len({r['source_id'] for r in a})==20,'20 sources/fold')
        need(all({k:v for k,v in x.items() if k not in ('run','arm')}=={k:v for k,v in y.items() if k not in ('run','arm')} for x,y in zip(a,b)),'paired identical inputs')
    manifest=out/'trace_manifest.jsonl';journal=out/'forward_attempts.jsonl'
    for p in (manifest,journal):p.open('x').close()
    attempts=successful=0;files=[];states=[]
    try:
        for label in ORDER:
            run=dict(native.FROZEN_MODELS[label]);need(run['checkpoint']==q['checkpoints'][label],'checkpoint role')
            random.seed(0);np.random.seed(0);torch.manual_seed(0)
            model,evidence=builder(run);native.validate_model(model,evidence,artificial_cpu);native.load_checkpoint(torch,model,run)
            model.eval();model.to(device)
            if hasattr(model,'enable_full_instrumentation'):model.enable_full_instrumentation(False)
            if not artificial_cpu:torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0)
            before=helper.state_sha(model);rng=native.rng_state(torch,np,helper,not artificial_cpu)
            with observer.Observer(model.base_model.spcg_head,q['implementation']['head']['path'],torch) as capture:
                for row in [r for r in rows if r['run']==label]:
                    helper.assert_numeric(torch);budget.sample('before_forward',attempts)
                    x=torch.from_numpy(native.load_partial(np,dict(row,n_input=8192))).unsqueeze(0).to(device)
                    capture.begin();need(attempts<80,'attempt cap');attempts+=1
                    native.append_event(journal,dict(forward_index=attempts,run=label,case_id=row['case_id'],status='CLAIMED_BEFORE_FORWARD'))
                    with torch.inference_mode():
                        result=model(x)
                        need(isinstance(result,(tuple,list)) and len(result)==2,'Native coarse/dense tuple')
                        arrays=capture.finish(x,*result)
                    successful+=1;p=out/'traces'/(label+'__'+row['case_id']+'.npz')
                    with p.open('xb') as f:np.savez_compressed(f,**arrays)
                    r=dict(path=str(p),bytes=p.stat().st_size,sha256=native.sha(p))
                    native.append_event(manifest,dict(**row,forward_index=attempts,trace=r,array_keys=list(arrays),neighborhood='ALL256' if run['arm']=='G1' else 'NATIVE_FP32_K8',checkpoint_sha256=run['checkpoint']['sha256']))
                    files.append(p);del arrays,x,result
                    helper.assert_numeric(torch);budget.sample('after_forward',attempts)
            after=helper.state_sha(model);rng_after=native.rng_state(torch,np,helper,not artificial_cpu)
            need(before==after and rng==rng_after,'model state/RNG changed')
            states.append(dict(run=label,forwards=20,state_before=before,state_after=after,RNG_before=rng,RNG_after=rng_after,construction=evidence))
            del model;gc.collect()
            if not artificial_cpu:torch.cuda.empty_cache()
        need(attempts==successful==len(files)==80,'exact80 complete')
        return files+[manifest,journal],states
    except BaseException as exc:
        write_json(out/'diagnostic_failure.json',dict(status='FAILED_STOP_NO_RETRY',attempts=attempts,successful=successful,error=repr(exc),loss=0,backward=0,optimizer_step=0))
        raise

def main():
    parser=argparse.ArgumentParser()
    for k in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):parser.add_argument('--'+k,required=True)
    a=parser.parse_args()
    rec=lambda p,s:dict(path=p,bytes=clean(p).stat().st_size,sha256=s)
    qr=rec(a.request,a.request_sha256);q=authorize(qr,rec(a.authorization,a.authorization_sha256),rec(a.runtime,a.runtime_sha256))
    I=q['identity'];out=clean(q['output']);root=clean(q['model_root']);guard=None
    try:
        need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
        need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'current identity')
        need(Path.cwd().resolve()==Path(I['project']) and Path(__file__).resolve()==exact(q['entry']),'project and entry')
        parent=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
        need(parent[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','900s'],'outer timeout')
        need(bound(dict(path=q['launch_attempt'],bytes=clean(q['launch_attempt']).stat().st_size,sha256=hashlib.sha256(clean(q['launch_attempt']).read_bytes()).hexdigest()))==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single attempt claim')
        need(out.is_dir() and {p.name for p in out.iterdir()}=={'launch.log'},'fresh launcher-only output')
        native=module('trace_frozen_native',q['implementation']['native_reuse'])
        for r in [*q['implementation'].values(),*q['dependencies'],q['mother_source'],q['probe_asset'],q['head_initialization']]:exact(r)
        for r in q['input_records']:exact(r['input'])
        for r in q['checkpoints'].values():exact(r)
        scope=bound(q['preflight_scope']);static=bound(q['static_config'])
        timezone=module('trace_exact_utc',q['implementation']['timezone']);utc=timezone.ExactUTCReader(timezone.UTC_RESOURCE)
        helper=module('trace_frozen_helper',q['helper']);helper._MONITOR=None
        records=helper.source_map(scope)
        for rel,r in records.items():helper.exact(root/rel,r['sha256'],r['bytes'])
        helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
        for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
        for k,v in q['environment'].items():need(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
        smi=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
        need(smi[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(smi[4])<=256,'bound GPU idle')
        import shutil
        need(shutil.disk_usage(out).free>=q['startup_free_disk_bytes'],'startup disk6GiB')
        for name in ('traces','tmp'):(out/name).mkdir()
        (out/'worker.pid').write_text(str(os.getpid()),encoding='ascii')
        guard=native.make_source_guard(q)
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
        sys.path[:0]=[str(Path(q['implementation']['factory']['path']).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
        outputs=[out/'traces'/(r['run']+'__'+r['case_id']+'.npz') for r in q['input_records']]
        policy=native.make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in q['input_records']],[r['path'] for r in q['checkpoints'].values()],outputs,utc,guard)
        sys.addaudithook(policy.audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        need((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'bound package versions')
        need(torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.version.cuda==I['torch_cuda_version'],'one actual CUDA device')
        torch.cuda.set_device(0);helper.configure_numeric(torch)
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');extension=importlib.import_module('pointnet2_ops._ext')
        need(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(extension.__file__).resolve())==scope['bindings']['provider'][2]['path'],'actual provider')
        helper.check_backend(chamfer,pn,pm)
        transformer=importlib.import_module('models.Transformer_utils');model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr
        need(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'model config')
        transformer.enable_bcsp_knn();factory=native.load_spcg_builder(q['implementation']);observer=module('trace_observer',q['implementation']['observer'])
        builder=lambda run:native.build_spcg_model(factory,lambda:model_class(EasyDict(static['model'])),run,q)
        budget=native.Budget(q,out,torch,helper)
        files,states=execute(torch,np,native,helper,observer,q,out,builder,budget)
        done=out/'diagnostic_complete.json';write_json(done,dict(status='TRACE_D0_80_FORWARD_COMPLETE_PENDING_FORMAL_FREEZE',counts=COUNTS,states=states,request_sha256=qr['sha256']))
        budget.sample('complete',80);archive=native.pack(out,files+[done,budget.path])
        # Do not append to the already archived resources.jsonl after packaging.
        need(sum(p.stat().st_size for p in out.rglob('*') if p.is_file())<=q['limits']['output_bytes'],'archive included in output cap')
        need(shutil.disk_usage(out).free>=q['limits']['minimum_free_disk_bytes'] and time.monotonic()-budget.start<=900,'post-archive disk/wall')
        write_json(out/'archive_receipt.json',archive)
    except BaseException as exc:
        # Persist traceback while exact source descriptors remain open. Exit nonzero.
        detail=dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),traceback=traceback.format_exc(),guard_lifecycle='GUARD_ACTIVE_BEFORE_CLEANUP')
        if out.is_dir() and not (out/'startup_failure.json').exists():write_json(out/'startup_failure.json',detail)
        print(json.dumps(detail),file=sys.stderr,flush=True)
        return 1
    finally:
        if guard is not None:guard.close()
    return 0

if __name__=='__main__':sys.exit(main())
