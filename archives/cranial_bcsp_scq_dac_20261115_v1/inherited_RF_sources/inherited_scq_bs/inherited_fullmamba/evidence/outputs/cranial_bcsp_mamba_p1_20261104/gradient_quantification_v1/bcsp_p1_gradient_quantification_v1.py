"""Diagnostic only: original 12/4/0 path, quantitative gradient differences; no admission verdict."""
import argparse,ast,gc,hashlib,importlib.util,json,os,random,shutil,socket,sys,time
from pathlib import Path


QUANT=None


def require(ok,text):
    if not ok:raise RuntimeError(text)


def clean(p):
    p=Path(p).absolute()
    require(not any(x.is_symlink() for x in (p,*p.parents)),'linked path: '+str(p))
    require(not {'.ssh','.aws','.credentials','.git'}&set(p.parts) and p.name not in ('.env','.netrc'),'secret path')
    return p


def sha(p):
    h=hashlib.sha256()
    with clean(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def exact(r):
    p=clean(r['path']);require(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'binding '+str(p));return p


def bound(r):return json.loads(exact(r).read_bytes())


def emit(p,x):
    with clean(p).open('x',encoding='ascii') as f:json.dump(x,f,indent=2,allow_nan=False)


def load_module(name,record):
    spec=importlib.util.spec_from_file_location(name,exact(record));module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module


def authorize(qr,ar,rr):
    q=bound(qr);a=bound(ar);r=bound(rr)
    require(q['schema']=='bcsp-p1-gradient-quantification-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','request')
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-p1-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'authorization')
    require(r==dict(schema='bcsp-p1-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
    require(q['science']['forward_attempt_limit']==12 and q['science']['backward_attempt_limit']==4 and q['science']['optimizer_steps']==0,'frozen operation count')
    return q


def snapshot_rng(torch,np,cuda):
    return (random.getstate(),np.random.get_state(),torch.get_rng_state().clone(),torch.cuda.get_rng_state(0).clone() if cuda else None)


def restore_rng(torch,np,state):
    random.setstate(state[0]);np.random.set_state(state[1]);torch.set_rng_state(state[2])
    if state[3] is not None:torch.cuda.set_rng_state(state[3],0)


def rng_sha(torch,np,state,tensor_sha):
    return dict(python=hashlib.sha256(repr(state[0]).encode()).hexdigest(),numpy=hashlib.sha256(state[1][1].tobytes()+repr((state[1][0],state[1][2:])).encode()).hexdigest(),CPU=tensor_sha(state[2]),CUDA=None if state[3] is None else tensor_sha(state[3]))


def counters():return dict(forward_attempts=0,forward_returns=0,loss_calls=0,backward_attempts=0,backward_returns=0,optimizer_steps=0)


def outputs(torch,ret,training,batch):
    expected=[(batch,256,3),(batch,0,3),(batch,0,3),(batch,8192,3)] if training else [(batch,256,3),(batch,8192,3)]
    require(isinstance(ret,(tuple,list)) and len(ret)==len(expected),'return tuple')
    require(all(tuple(t.shape)==s and t.dtype==torch.float32 and bool(torch.isfinite(t).all()) for t,s in zip(ret,expected)),'finite FP32 outputs')
    return ret[0],ret[-1]


def compare(torch,current,reference,tensor_sha):
    difference=current.detach().cpu()-reference
    return dict(exact_equal=tensor_sha(current)==tensor_sha(reference),max_abs_normalized=float(difference.abs().max()))


def gradient_summary(torch,model,variant,tensor_sha):
    hashes={};nonzero={}
    for name,p in model.named_parameters():
        if p.grad is None:hashes[name]=None;nonzero[name]=False;continue
        require(bool(torch.isfinite(p.grad).all()),'nonfinite gradient '+name)
        hashes[name]=tensor_sha(p.grad);nonzero[name]=bool((p.grad!=0).any())
    require(any(v for n,v in nonzero.items() if n.startswith('base_model.coarse_pred.')),'no coarse head gradient')
    if variant=='M0':
        for i in range(6):
            prefix='base_model.encoder.blocks.blocks.'+str(i)+'.attn.mixer.'
            require(any(v for n,v in nonzero.items() if n.startswith(prefix)),'no active SSM gradient '+str(i))
    return dict(hashes=hashes,nonzero_parameter_names=[n for n,v in nonzero.items() if v])


def admit_model(torch,np,model,x,target,variant,counts,helper,event,sample,*,cuda=True,expected_presence=None,write_gradient=None,memory_prepare=None,memory_poll=None):
    """All actual model calls live here; CPU contracts use an explicitly artificial model."""
    initial={n:v.detach().cpu().clone() for n,v in model.state_dict().items()}
    modes=[m.training for m in model.modules()];rng=snapshot_rng(torch,np,cuda)
    bn_settings=[(m,m.momentum,m.track_running_stats) for m in model.modules() if isinstance(m,torch.nn.modules.batchnorm._BatchNorm)]
    initial_sha=helper.state_sha(model);rng_initial=rng_sha(torch,np,rng,helper.tensor_sha)
    eval_reference=None;train_reference=None;gradient_reference=None;loss_reference=None
    events=[];gradient_values=None;quantification=None
    require(QUANT is not None and expected_presence is not None and all(callable(f) for f in (write_gradient,memory_prepare,memory_poll)),'quantification callbacks')
    def restore():
        model.enable_full_instrumentation(False);model.load_state_dict(initial,strict=True)
        model.zero_grad(set_to_none=True);restore_rng(torch,np,rng)
        for m,flag in zip(model.modules(),modes):m.training=flag
        for m,momentum,tracking in bn_settings:m.momentum=momentum;m.track_running_stats=tracking
    try:
        for phase in ('eval_1','eval_2','eval_instrumented','eval_state_roundtrip','train_1','train_2'):
            restore();training=phase.startswith('train_');model.train(training)
            if training:
                for m in model.modules():
                    if isinstance(m,torch.nn.modules.batchnorm._BatchNorm):
                        require(m.track_running_stats,'ordinary train BN required');m.momentum=.9
            instrumented=phase=='eval_instrumented';model.enable_full_instrumentation(instrumented)
            if phase=='eval_state_roundtrip':
                memory_copy={n:v.clone() for n,v in initial.items()};model.load_state_dict(memory_copy,strict=True);del memory_copy
            sample(variant+':'+phase+':before',counts)
            require(counts['forward_attempts']<12,'forward cap')
            counts['forward_attempts']+=1;event(dict(kind='FORWARD_ATTEMPT',variant=variant,phase=phase,counts=dict(counts)))
            context=torch.enable_grad() if training else torch.inference_mode()
            with context:
                ret=model(x);counts['forward_returns']+=1
                coarse,dense=outputs(torch,ret,training,x.shape[0])
                record=dict(variant=variant,phase=phase,coarse_sha256=helper.tensor_sha(coarse),dense_sha256=helper.tensor_sha(dense))
                if training:
                    counts['loss_calls']+=1
                    denoise,recon=model.get_loss(ret,target,epoch=0,partial=x)
                    require(denoise.numel()==recon.numel()==1 and float(denoise.detach())==0 and bool(torch.isfinite(recon)) and recon.requires_grad,'original finite reconstruction loss')
                    total=denoise+recon;require(counts['backward_attempts']<4,'backward cap')
                    counts['backward_attempts']+=1;event(dict(kind='BACKWARD_ATTEMPT',variant=variant,phase=phase,counts=dict(counts)))
                    total.backward();counts['backward_returns']+=1
                    if cuda:torch.cuda.synchronize()
                    sample(variant+':'+phase+':after_backward_before_statistics',counts)
                    grads=gradient_summary(torch,model,variant,helper.tensor_sha)
                    record.update(loss_denoise=float(denoise.detach()),loss_reconstruction=float(recon.detach()),gradients=grads,temporary_state_sha256=helper.state_sha(model))
                    if train_reference is None:
                        gradient_values=QUANT.capture(torch,model,expected_presence,memory_prepare,memory_poll)
                        sample(variant+':'+phase+':gradient_reference_captured',counts)
                        train_reference=(coarse.detach().cpu().clone(),dense.detach().cpu().clone());gradient_reference=grads['hashes'];loss_reference=helper.tensor_sha(total)
                        event(record)
                    else:
                        record['coarse_comparison']=compare(torch,coarse,train_reference[0],helper.tensor_sha)
                        record['dense_comparison']=compare(torch,dense,train_reference[1],helper.tensor_sha)
                        record['gradient_exact_equal']=grads['hashes']==gradient_reference
                        record['loss_exact_equal']=helper.tensor_sha(total)==loss_reference
                        quantification=QUANT.quantify(torch,gradient_values,model,expected_presence,helper.tensor_sha,write_gradient,memory_poll)
                        record['gradient_quantification']=quantification
                        sample(variant+':'+phase+':gradient_statistics_complete',counts)
                        event(record)
                        require(record['coarse_comparison']['exact_equal'] and record['dense_comparison']['exact_equal'] and record['loss_exact_equal'],'training output/loss repeatability; gradient differences are diagnostic only')
                else:
                    if eval_reference is None:eval_reference=(coarse.detach().cpu().clone(),dense.detach().cpu().clone())
                    record['coarse_comparison']=compare(torch,coarse,eval_reference[0],helper.tensor_sha)
                    record['dense_comparison']=compare(torch,dense,eval_reference[1],helper.tensor_sha)
                    if instrumented:
                        trace=model.pop_full_instrumentation();require(isinstance(trace,dict) and 'backbone' in trace,'existing instrumentation record');del trace
                    record['state_unchanged']=helper.state_sha(model)==initial_sha
                    record['RNG_unchanged']=rng_sha(torch,np,snapshot_rng(torch,np,cuda),helper.tensor_sha)==rng_initial
                    event(record)
                    require(record['coarse_comparison']['exact_equal'] and record['dense_comparison']['exact_equal'] and record['state_unchanged'] and record['RNG_unchanged'],'eval/state/instrumentation repeatability')
            events.append(record)
            del ret,coarse,dense
            if training:del denoise,recon,total,grads
            restore();sample(variant+':'+phase+':restored',counts)
    finally:
        restore()
        state_ok=helper.state_sha(model)==initial_sha
        rng_ok=rng_sha(torch,np,snapshot_rng(torch,np,cuda),helper.tensor_sha)==rng_initial
        restored=dict(kind='RESTORATION',variant=variant,state_restored=state_ok,RNG_restored=rng_ok,modes_restored=[m.training for m in model.modules()]==modes)
        event(restored);require(state_ok and rng_ok and restored['modes_restored'],'final restoration failure')
    require(quantification is not None,'missing gradient statistics')
    return dict(variant=variant,phases=6,state_sha256=initial_sha,state_restored=True,RNG_restored=True,gradient_quantification=quantification,events=events)


class Budget:
    def __init__(self,q,out,torch,helper):self.q=q;self.out=out;self.t=torch;self.h=helper;self.start=time.monotonic()
    def memory_poll(self):
        status=Path('/proc/'+str(os.getpid())+'/status').read_text()
        rss=int(next(s.split()[1] for s in status.splitlines() if s.startswith('VmRSS:')))*1024
        require(rss<=self.q['limits']['RSS_bytes'] and time.monotonic()-self.start<=self.q['limits']['wall_seconds'],'gradient CPU memory/time budget')
        return rss
    def prepare_reference(self,reference_bytes,temporary_headroom):
        rss=self.memory_poll();ok=rss+reference_bytes+temporary_headroom<=self.q['limits']['RSS_bytes']
        with (self.out/'events.jsonl').open('a') as f:
            f.write(json.dumps(dict(kind='GRADIENT_REFERENCE_BUDGET',RSS_bytes=rss,reference_bytes=reference_bytes,temporary_headroom=temporary_headroom,limit=self.q['limits']['RSS_bytes'],passes=ok))+'\n');f.flush();os.fsync(f.fileno())
        require(ok,'insufficient RSS budget for CPU gradient reference')
    def sample(self,phase,counts):
        self.h.assert_numeric(self.t)
        status=Path('/proc/'+str(os.getpid())+'/status').read_text()
        rss=int(next(s.split()[1] for s in status.splitlines() if s.startswith('VmRSS:')))*1024
        used=int(self.h.smi('memory.used')[0]);L=self.q['limits']
        values=dict(RSS_bytes=rss,device_MiB=used,torch_allocated_peak=self.t.cuda.max_memory_allocated(0),torch_reserved_peak=self.t.cuda.max_memory_reserved(0),output_bytes=sum(p.stat().st_size for p in self.out.rglob('*') if p.is_file()),seconds=time.monotonic()-self.start,free_disk_bytes=shutil.disk_usage(self.out).free)
        checks=dict(RSS=rss<=L['RSS_bytes'],device=used<=L['device_MiB'],allocated=values['torch_allocated_peak']<=L['torch_peak_bytes'],reserved=values['torch_reserved_peak']<=L['torch_peak_bytes'],output=values['output_bytes']<=L['output_bytes'],wall=values['seconds']<=L['wall_seconds'],disk=values['free_disk_bytes']>=L['minimum_free_disk_bytes'])
        with (self.out/'resources.jsonl').open('a') as f:f.write(json.dumps(dict(phase=phase,counts=dict(counts),values=values,checks=checks))+'\n');f.flush();os.fsync(f.fileno())
        require(all(checks.values()),'resource failure: '+repr(checks))


def main():
    parser=argparse.ArgumentParser()
    for key in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):parser.add_argument('--'+key,required=True)
    a=parser.parse_args()
    def record(p,h):return dict(path=p,bytes=clean(p).stat().st_size,sha256=h)
    qr=record(a.request,a.request_sha256);q=authorize(qr,record(a.authorization,a.authorization_sha256),record(a.runtime,a.runtime_sha256));I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
    require(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux isolated no-site no-bytecode')
    require(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'identity')
    require(Path(__file__).resolve()==exact(q['entry']),'entry binding')
    require(Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','900s'],'fixed timeout parent')
    require(json.loads(clean(q['claim']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single attempt claim')
    for r in q['implementation']+q['dependencies']:exact(r)
    baselines={k:bound(v) if k!='events' else [json.loads(s) for s in exact(v).read_text().splitlines()] for k,v in q['diagnostic_baselines'].items()}
    baseline_presence={}
    for variant in ('T0','M0'):
        records=[r for r in baselines['events'] if r.get('variant')==variant and 'gradients' in r]
        require(len(records)==2 and {n:h is not None for n,h in records[0]['gradients']['hashes'].items()}=={n:h is not None for n,h in records[1]['gradients']['hashes'].items()},'historical gradient presence')
        baseline_presence[variant]={n:h is not None for n,h in records[0]['gradients']['hashes'].items()}
    helper=load_module('p1_frozen_helper',q['helper']);helper._MONITOR=None
    scope=bound(q['preflight_scope']);sources=helper.source_map(scope)
    for rel,r in sources.items():helper.exact(root/rel,r['sha256'],r['bytes'])
    helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
    for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
    static=bound(q['static_config']);fold=bound(q['fold_binding'])['folds']['C'];order=bound(q['order_plan'])
    require([r['case_id'] for r in q['batch']]==order['epochs'][0]['batches'][0] and len(q['batch'])==8,'fixed first training batch')
    require(all(r['case_id'] in fold['train_case_ids'] and r['source_id'] in fold['train_sources'] and r['source_id'] not in fold['dev_sources'] for r in q['batch']),'own-fold train only')
    manifest_rows=[json.loads(s) for s in exact(q['train_manifest']).read_text().splitlines()]
    manifest={r['case_id']:r for r in manifest_rows};require(len(manifest)==len(manifest_rows)==420,'original manifest identities')
    for r in q['batch']:
        original=manifest[r['case_id']]
        require(r['source_id']==original['source_id'] and r['input']['sha256']==original['sha256'] and r['input']['path']==q['data_root']+'/'+original['point_path'] and r['normalization']==original['normalization'],'batch original provenance')
    for r in q['batch']:exact(r['input'])
    for k,v in q['environment'].items():require(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
    gpu=[v.strip() for v in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    require(gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256 and not helper.smi('pid',True),'idle GPU identity')
    require(out.parent==Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1') and out.is_dir() and {p.name for p in out.iterdir()}=={'launch.log'},'fresh launcher-owned output')
    (out/'tmp').mkdir();(out/'resources.jsonl').open('x').close();(out/'events.jsonl').open('x').close()
    with (out/'worker.pid').open('x') as f:f.write(str(os.getpid()))
    counts=counters()
    timezone_guard=None
    def event(value):
        with (out/'events.jsonl').open('a') as f:f.write(json.dumps(value,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    try:
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
        sys.path[:0]=[str(Path(__file__).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,sources))
        allowed={clean(r['input']['path']) for r in q['batch']}
        global QUANT
        QUANT=load_module('p1_gradient_statistics',q['quantification_implementation'])
        utc_module=load_module('p1_exact_utc_resource',q['timezone_implementation'])
        require(q['timezone_resource']==utc_module.UTC_RESOURCE,'exact audited UTC binding')
        timezone_guard=utc_module.ExactUTCReader(q['timezone_resource'])
        class Policy(helper.FilePolicy):
            def check(self,filename,write=False):
                if isinstance(filename,int):return
                if timezone_guard.allow(filename,write):return
                p=clean(os.fsdecode(filename))
                if p.suffix.lower() in helper.PAYLOAD or p.name.lower().endswith('.nii.gz'):
                    require(not write and p in allowed,'only exact eight training NPZ payloads permitted');return
                return super().check(filename,write)
        sys.addaudithook(Policy([root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out).audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
        require(torch.cuda.is_available() and torch.cuda.device_count()==1,'one visible CUDA device');torch.cuda.set_device(0);helper.configure_numeric(torch)
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');native=importlib.import_module('pointnet2_ops.pointnet2_utils');helper.check_backend(chamfer,pn,native)
        require(str(Path(native.__file__).resolve())==scope['bindings']['provider'][1]['path'],'PointNet2 Python origin')
        extension=importlib.import_module('pointnet2_ops._ext');require(str(Path(extension.__file__).resolve())==scope['bindings']['provider'][2]['path'],'PointNet2 native origin')
        transformer=importlib.import_module('models.Transformer_utils');model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr
        require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'original B0 config');transformer.enable_bcsp_knn()
        import bcsp_p1_model_factory_v1 as factory
        require(Path(factory.__file__).resolve()==exact(q['factory']),'factory origin')
        helper.exact(Path(factory.__file__).parent/'bcsp_mamba_encoder_v1.py',q['encoder']['sha256'],q['encoder']['bytes'])
        X=[];G=[]
        for r in q['batch']:
            with np.load(exact(r['input']),allow_pickle=False) as z:x=z['partial'].copy();g=z['implant'].copy()
            require(x.shape==g.shape==(8192,3) and x.dtype==g.dtype==np.float32 and np.isfinite(x).all() and np.isfinite(g).all(),'training tensor')
            X.append(x);G.append(g)
        x=torch.from_numpy(np.stack(X)).to('cuda:0');target=torch.from_numpy(np.stack(G)).to('cuda:0');del X,G
        random.seed(0);np.random.seed(0);torch.manual_seed(0)
        budget=Budget(q,out,torch,helper);results=[];common=None
        runtime_tree=ast.parse(exact(q['training_runtime']).read_text(encoding='utf-8'))
        group_function=next(n for n in runtime_tree.body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups')
        runtime_namespace=dict(require=require);exec(compile(ast.Module(body=[group_function],type_ignores=[]),'<bound_p1_optimizer_groups>','exec'),runtime_namespace)
        for variant in ('T0','M0'):
            model,evidence=factory.build_model(lambda:model_class(EasyDict(static['model'])),variant)
            require(not evidence['artificial_fixture'],'native model only');helper.validate_model(model)
            require(evidence==baselines[variant]['factory'],'historical model initialization identity differs')
            if common is None:common=evidence['common_state']
            require(common==evidence['common_state'],'shared initial state differs')
            groups,group_records=runtime_namespace['optimizer_groups'](model);del groups
            emit(out/(variant+'_construction.json'),dict(factory=evidence,optimizer_groups=group_records))
            if variant=='M0':
                import mamba_ssm,causal_conv1d,selective_scan_cuda,causal_conv1d_cuda
                require(mamba_ssm.__version__=='2.3.1','Mamba version')
                modules=[mamba_ssm,importlib.import_module('mamba_ssm.modules.mamba_simple'),importlib.import_module('mamba_ssm.ops.selective_scan_interface'),causal_conv1d,importlib.import_module('causal_conv1d.causal_conv1d_interface'),selective_scan_cuda,causal_conv1d_cuda]
                origins=[str(Path(m.__file__).resolve()) for m in modules];require(set(origins)<=set(r['path'] for r in q['dependencies']),'SSM import origins')
                emit(out/'native_SSM_origins.json',dict(origins=origins,version=mamba_ssm.__version__))
                A=[r for r in group_records if r['name'].endswith('.A_log')];require(len(A)==6 and all(r['weight_decay']==0 for r in A),'A_log groups')
            model.eval().to('cuda:0');torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats(0)
            gradient_log=out/(variant+'_gradient_parameters.jsonl');gradient_log.open('x').close()
            def write_gradient(row):
                with gradient_log.open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
            result=admit_model(torch,np,model,x,target,variant,counts,helper,event,budget.sample,cuda=True,expected_presence=baseline_presence[variant],write_gradient=write_gradient,memory_prepare=budget.prepare_reference,memory_poll=budget.memory_poll)
            emit(out/(variant+'_gradient_summary.json'),result['gradient_quantification'])
            results.append(result)
            helper.assert_numeric(torch);del model;gc.collect();torch.cuda.empty_cache()
        require(counts==dict(forward_attempts=12,forward_returns=12,loss_calls=4,backward_attempts=4,backward_returns=4,optimizer_steps=0),'exact completion counts')
        budget.sample('all_complete',counts)
        emit(out/'completion.json',dict(status='GRADIENT_DIAGNOSTIC_COMPLETE_AWAITING_FORMAL_AUDIT',request_sha256=qr['sha256'],counts=counts,models=results,training_updates=0,BNCal=0,development_access=0,optimizer_constructed=False,training_admission_granted=False,prior_v3_status='FAILED_STOP_NO_RETRY'))
        files=[p for p in out.rglob('*') if p.is_file() and p.name not in ('launch.log','worker.pid')]
        emit(out/'payload_manifest.json',dict(files=[dict(name=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
    except BaseException as exc:
        emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',request_sha256=qr['sha256'],counts=counts,error=repr(exc),training_updates=0));raise
    finally:
        if timezone_guard is not None:timezone_guard.close()


if __name__=='__main__':main()
