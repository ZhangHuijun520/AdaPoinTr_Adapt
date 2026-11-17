"""Bounded 11F/3loss/3B/0step admission. Stdlib-only import; separate execution authorization."""
import argparse,copy,hashlib,importlib.util,json,os,random,shlex,signal,socket,sys,threading,time
from pathlib import Path,PurePosixPath

SCIENCE=dict(full_forward=11,full_loss=3,full_backward=3,optimizer_steps=0,synthetic_forward=6,real_D_forward=5)
LIMITS=dict(wall_seconds=1800,RSS_bytes=8589934592,torch_peak_bytes=21474836480,device_MiB=22528,output_bytes=1073741824,minimum_free_disk_bytes=4294967296)
FIXTURE=dict(kind='analytic_double_spherical_surface_and_cut_annulus_v1',outer_points=3072,inner_points=3072,wall_points=2048,outer_radius=.45,inner_radius=.40,cut_polar_angle=.55,input_seed=2026111603,target_seed=2026111604,batches=[1,8],points=8192,dtype='float32')
def need(v,s):
    if not v:raise ValueError(s)
def clean(p):
    p=Path(p).absolute();need(not any(x.is_symlink() for x in (p,*p.parents)),'linked path '+str(p));need(not {'.ssh','.aws','.credentials','.git'}&set(p.parts) and p.name not in ('.env','.netrc','auth.json'),'secret');return p
def exact(r):
    p=clean(r['path']);need(p.is_file() and p.stat().st_size==r['bytes'],'file size '+str(p));need(hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],'file hash '+str(p));return p
def emit(p,v):
    with clean(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
def load_source(name,r):
    need(name not in sys.modules,'preloaded '+name);p=exact(r);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def authorize(q,digest,a,ah,r):
    need(q['schema']=='bcsp-spcg-cuda-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'pending request')
    need(q['science']==SCIENCE and q['limits']==LIMITS and q['fixture']==FIXTURE,'frozen scope')
    need(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-spcg-authorization-v1' and a['request_sha256']==digest and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'explicit authorization')
    need(r==dict(schema='bcsp-spcg-runtime-v1',request_sha256=digest,authorization_sha256=ah),'one way runtime')
    need(len(q['real_inputs'])==5 and len({v['source_id'] for v in q['real_inputs']})==5,'five distinct training sources')
    return q
def materialization(q,digest,text):
    need(len(digest)==64 and all(x in '0123456789abcdef' for x in digest) and bool(text.strip()),'authorization text/hash')
    a=dict(schema='bcsp-spcg-authorization-v1',request_sha256=digest,explicit_user_authorization=True,user_authorization_text=text)
    ab=(json.dumps(a,indent=2,ensure_ascii=False)+'\n').encode();ah=hashlib.sha256(ab).hexdigest()
    r=dict(schema='bcsp-spcg-runtime-v1',request_sha256=digest,authorization_sha256=ah);rb=(json.dumps(r,indent=2)+'\n').encode()
    authorize(q,digest,a,ah,r)
    return ab,rb
def render_launcher(q,qh,ah,rh):
    for h in (qh,ah,rh):need(len(h)==64 and all(c in '0123456789abcdef' for c in h),'complete hashes')
    o=PurePosixPath(q['output']);L=q['launch_contract'];cmd=['/usr/bin/timeout','--signal=TERM','--kill-after=10s','1800s',q['identity']['python_realpath'],'-I','-S','-B',q['entry']['path']]
    for k,v in [('request',L['request_path']),('request-sha256',qh),('authorization',L['authorization_path']),('authorization-sha256',ah),('runtime',L['runtime_path']),('runtime-sha256',rh)]:cmd+=['--'+k,v]
    env='\n'.join('export '+k+'='+shlex.quote(v.replace('<owned_output>',str(o))) for k,v in q['environment'].items())
    script='#!/bin/bash\nset -eu\numask 077\ncd '+shlex.quote(q['project'])+'\n'+''.join('[ ! -L '+shlex.quote(str(p))+' ] || exit 121\n' for p in reversed((o,*o.parents)) if str(p)!='/')+'mkdir -p '+shlex.quote(str(o.parent))+'\nmkdir '+shlex.quote(str(o))+'\n'+env+'\nprintf "%s\\n" "$$" >'+shlex.quote(str(o/'launcher.pid'))+'\nset +e\n'+shlex.join(cmd)+' >'+shlex.quote(str(o/'launch.log'))+' 2>&1\nrc=$?\nset -e\nprintf "%s\\n" "$rc" >'+shlex.quote(str(o/'exit_code.txt'))+'\nexit "$rc"\n'
    need(max(len(l.encode()) for l in script.splitlines())<=2048,'short launcher lines');return script
def fixture(np):
    def make(seed,missing):
        rng=np.random.default_rng(seed);rows=[]
        for b in range(8):
            clouds=[]
            for radius,n in [(.45,3072),(.40,3072)]:
                phi=rng.uniform(0,2*np.pi,n);u=rng.uniform(np.cos(.55),1,n) if missing else rng.uniform(-1,np.cos(.55),n);v=np.sqrt(1-u*u)
                clouds.append(radius*np.stack([v*np.cos(phi),v*np.sin(phi),u],1))
            phi=rng.uniform(0,2*np.pi,2048);radius=rng.uniform(.40,.45,2048)
            clouds.append(np.stack([radius*np.sin(.55)*np.cos(phi),radius*np.sin(.55)*np.sin(phi),radius*np.cos(.55)],1))
            rows.append(np.concatenate(clouds).astype(np.float32))
        return np.stack(rows)
    return make(FIXTURE['input_seed'],False),make(FIXTURE['target_seed'],True)
def fingerprint(model,parameters=False):
    h=hashlib.sha256()
    for n,t in (model.named_parameters() if parameters else model.state_dict().items()):h.update(n.encode());h.update(t.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()
def snapshot(torch,np,m,cuda):
    return dict(state={n:t.detach().cpu().clone() for n,t in m.state_dict().items()},modes=[b.training for b in m.modules()],momenta=[(b,b.momentum) for b in m.modules() if isinstance(b,torch.nn.modules.batchnorm._BatchNorm)],rng=(random.getstate(),np.random.get_state(),torch.get_rng_state().clone(),torch.cuda.get_rng_state(0).clone() if cuda else None))
def restore(torch,np,m,s,cuda):
    m.load_state_dict(s['state'],strict=True);m.zero_grad(set_to_none=True)
    for b,mode in zip(m.modules(),s['modes']):b.training=mode
    for b,v in s['momenta']:b.momentum=v
    random.setstate(s['rng'][0]);np.random.set_state(s['rng'][1]);torch.set_rng_state(s['rng'][2])
    if cuda:torch.cuda.set_rng_state(s['rng'][3],0)
def run_checks(torch,np,runtime,build,D,G,real_inputs,read_real,event,sample,save_memory,device='cuda:0',cuda=True):
    budget=runtime.CallBudget();common=None;models={}
    for arm in ['G0','G1','G2']:
        model,evidence=build(arm);model.eval().to(device)
        shared=hashlib.sha256()
        for n,t in model.state_dict().items():
            if not n.startswith(('base_model.coarse_pred.','base_model.spcg_head.')):shared.update(n.encode());shared.update(t.detach().cpu().contiguous().numpy().tobytes())
        value=shared.hexdigest();need(common is None or common==value,'three arms common initialization');common=value
        estimate=runtime.output_estimate(model);s=snapshot(torch,np,model,cuda);initial=fingerprint(model);initial_parameters=fingerprint(model,True)
        if arm!='G0':model.base_model.spcg_head.capture=True
        rows=[]
        try:
            for training,b in [(False,1),(True,8)]:
                restore(torch,np,model,s,cuda);model.train(training)
                if training:
                    for bn,_ in s['momenta']:bn.momentum=.9
                sample(arm+':before',budget.counts['full_forward']);budget.claim('synthetic_forward',event);budget.claim('full_forward',event)
                with torch.set_grad_enabled(training):
                    ret=model(D[:b]);Q,P=ret[0],ret[-1]
                    need(Q.shape==(b,256,3) and P.shape==(b,8192,3) and bool(torch.isfinite(Q).all()) and bool(torch.isfinite(P).all()),'actual shape finite')
                    geom=runtime.geometry(Q);qgrad=None;grad={}
                    if training:
                        Q.retain_grad();budget.claim('full_loss',event);a,c=model.get_loss(ret,G[:b],0,partial=D[:b]);loss=a+c;need(bool(torch.isfinite(loss)) and loss.requires_grad,'complete loss');budget.claim('full_backward',event);loss.backward();qgrad=runtime.Q_gradient_record(Q);grad=runtime.gradients(model)
                        for prefix in [('base_model.coarse_pred.' if arm=='G0' else 'base_model.spcg_head.'),'base_model.encoder.','base_model.decoder.','decode_head.']:
                            need(any(n.startswith(prefix) and v>0 for n,v in grad.items()),'gradient path '+prefix)
                    changed=[n for n,t in model.state_dict().items() if not torch.equal(t.detach().cpu(),s['state'][n])]
                    need(fingerprint(model,True)==initial_parameters and all(n.endswith(('running_mean','running_var','num_batches_tracked')) for n in changed),'parameter or non-BN state changed')
                    need(bool(changed) if training else not changed,'BN train/eval contract')
                    rows.append(dict(training=training,batch=b,geometry=geom,Q_gradient=qgrad,gradients=grad,BN_changed=changed,parameters_unchanged=True));event(dict(kind='SYNTHETIC_PHASE',arm=arm,**rows[-1]))
                del ret,Q,P
                restore(torch,np,model,s,cuda);need(fingerprint(model)==initial,'state restoration')
            if arm=='G2':
                for i,row in enumerate(real_inputs):
                    restore(torch,np,model,s,cuda);model.eval();x=torch.from_numpy(read_real(row)).unsqueeze(0).to(device)
                    budget.claim('real_D_forward',event);budget.claim('full_forward',event)
                    with torch.inference_mode():ret=model(x)
                    need(ret[0].shape==(1,256,3) and ret[-1].shape==(1,8192,3) and all(bool(torch.isfinite(t).all()) for t in ret),'real D shape finite')
                    detail=model.base_model.spcg_head.last
                    save_memory(i,detail,ret);event(dict(kind='REAL_D_ONLY',case_id=row['case_id'],geometry=runtime.geometry(ret[0])))
                    del x,ret
                    sample('real_D_complete',budget.counts['full_forward'])
            models[arm]=dict(construction=evidence,estimate=estimate,phases=rows,initial_state_sha256=initial)
        finally:
            restore(torch,np,model,s,cuda)
            need(fingerprint(model)==initial,'finally state restoration')
            nr=np.random.get_state();saved=s['rng'][1]
            need(torch.equal(torch.get_rng_state(),s['rng'][2]) and random.getstate()==s['rng'][0] and nr[0]==saved[0] and bool(np.array_equal(nr[1],saved[1])) and nr[2:]==saved[2:],'CPU Python NumPy RNG restored')
            if cuda:need(torch.equal(torch.cuda.get_rng_state(0),s['rng'][3]),'CUDA RNG restored')
            event(dict(kind='RESTORED',arm=arm,state=True,RNG=True,modes=[b.training for b in model.modules()]==s['modes']))
        del model,s
        if cuda:torch.cuda.empty_cache()
    return dict(counts=budget.finish(),models=models,common_initialization_sha256=common)

def main():
    parser=argparse.ArgumentParser()
    for k in ['request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256']:parser.add_argument('--'+k,required=True)
    a=vars(parser.parse_args())
    def record(k):p=clean(a[k]);return dict(path=str(p),bytes=p.stat().st_size,sha256=a[k+'_sha256'])
    qr,ar,rr=[record(k) for k in ['request','authorization','runtime']]
    q=authorize(json.loads(exact(qr).read_bytes()),qr['sha256'],json.loads(exact(ar).read_bytes()),ar['sha256'],json.loads(exact(rr).read_bytes()))
    I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
    need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'isolated Linux')
    need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'identity')
    need(str(Path.cwd())==q['project'] and out.parent==Path(q['project'])/'logs/cranial_bcsp_fullmamba','project/output')
    parent_cmd=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().split(b'\0')
    need(parent_cmd[:4]==[b'/usr/bin/timeout',b'--signal=TERM',b'--kill-after=10s',b'1800s'],'external timeout')
    need(json.loads(clean(q['launch_contract']['launch_attempt_path']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single claim')
    for k,v in q['environment'].items():need(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
    for v in list(q['implementation'].values())+q['dependencies']+[q['entry'],q['P3']]:exact(v)
    need(json.loads(exact(q['P3']).read_bytes())['status']=='SPCG_LOCAL_P3_PASS','P3')
    rawU=exact(q['probe_asset']).read_bytes();rawH=exact(q['head_initialization']).read_bytes()
    helper=load_source('spcg_inherited_helper',q['helper']);parent=load_source('spcg_inherited_native',q['parent_helper']);utcmod=load_source('spcg_exact_utc',q['timezone_implementation'])
    need(q['timezone_resource']==utcmod.UTC_RESOURCE,'UTC binding');utc=utcmod.ExactUTCReader(q['timezone_resource'])
    scope=json.loads(exact(q['preflight_scope']).read_bytes());static=json.loads(exact(q['static_config']).read_bytes());records=helper.source_map(scope)
    for rel,r in records.items():helper.exact(root/rel,r['sha256'],r['bytes'])
    for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
    helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
    g=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    need(g[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(g[4])<=256,'GPU')
    need(not (out/'worker.pid').exists(),'output already used');(out/'worker.pid').write_text(str(os.getpid()),encoding='ascii')
    for n in ['tmp','cache','mplconfig','triton_cache','hf_cache']:(out/n).mkdir(exist_ok=False)
    journal=out/'events.jsonl';journal.open('x').close()
    def event(v):
        with journal.open('a',encoding='utf-8') as f:f.write(json.dumps(v,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    # Existing precise source guards, composed for four inherited and four candidate files.
    guards=[parent.ExactSourceReads(dict(encoder=q['implementation']['encoder'],factory=q['implementation']['factory'],f0_decoder=q['implementation']['lqi_decoder'],f0_factory=q['implementation']['lqi_factory'])),parent.ExactSourceReads(dict(encoder=q['implementation']['head'],factory=q['implementation']['spcg_factory'],f0_decoder=q['implementation']['runtime'],f0_factory=q['entry']))]
    class Both:
        def allow(self,p,write=False):return any(g.allow(p,write) for g in guards)
    envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
    sys.path[:0]=[str(Path(__file__).parent),str(provider),str(envroot/'lib/python3.10/site-packages')]
    helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records))
    policy=parent.make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['path'] for r in q['real_inputs']],[],[],utc,Both());sys.addaudithook(policy.audit)
    stop=threading.Event();watcher=None
    try:
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        need((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
        need(torch.cuda.is_available() and torch.cuda.device_count()==1,'one CUDA');torch.cuda.set_device(0);helper.configure_numeric(torch)
        need(torch.version.cuda==I['torch_cuda_version'],'CUDA version')
        ch=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');ext=importlib.import_module('pointnet2_ops._ext');helper.check_backend(ch,pn,pm)
        need(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(ext.__file__).resolve())==scope['bindings']['provider'][2]['path'],'provider path')
        tr=importlib.import_module('models.Transformer_utils');cls=importlib.import_module('models.AdaPoinTr').AdaPoinTr;tr.enable_bcsp_knn()
        need(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'static model')
        for n,k in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory'),('bcsp_spcg_head_v1','head'),('bcsp_spcg_factory_v1','spcg_factory'),('bcsp_spcg_runtime_v1','runtime')]:load_source(n,q['implementation'][k])
        head=sys.modules['bcsp_spcg_head_v1'];factory=sys.modules['bcsp_spcg_factory_v1'];runtime=sys.modules['bcsp_spcg_runtime_v1'];lqi=sys.modules['bcsp_lqi_factory_v1'];U=head.from_bytes(rawU,(256,3))
        budget=parent.Budget(q,out,torch,helper);lock=threading.Lock();observed=[0]
        def sample(label,n):
            observed[0]=n
            with lock:helper.assert_numeric(torch);budget.sample(label,n)
        def watch():
            while not stop.wait(2):
                try:sample('MONITOR',observed[0])
                except BaseException as e:
                    try:emit(out/'monitor_failure.json',dict(error=repr(e)))
                    finally:os.kill(os.getpid(),signal.SIGTERM)
        watcher=threading.Thread(target=watch,daemon=True);watcher.start();native_calls={};hooks=[]
        def build(arm):
            m,e=factory.build_model(lambda:cls(EasyDict(static['model'])),lqi,arm,U,rawH,q['mother_source']['path'],q['mother_source']['sha256'])
            need(not e['artificial_fixture'] and sum(p.numel() for p in m.parameters())==(39903169 if arm=='G0' else 39912132),'native model count');helper.validate_model(m)
            for name,module in m.named_modules():
                if type(module).__module__=='mamba_ssm.modules.mamba_simple':
                    key=arm+':'+name
                    def hook(mod,args,k=key):need(args[0].shape[1] in (256,512),'SSM tokens');native_calls[k]=native_calls.get(k,0)+1
                    hooks.append(module.register_forward_pre_hook(hook))
            return m,e
        names=['mamba_ssm','mamba_ssm.modules.mamba_simple','mamba_ssm.ops.selective_scan_interface','causal_conv1d','causal_conv1d.causal_conv1d_interface','selective_scan_cuda','causal_conv1d_cuda']
        origins=[str(Path(importlib.import_module(n).__file__).resolve()) for n in names];need(set(origins)<={r['path'] for r in q['dependencies']},'native origins')
        x,y=fixture(np);D=torch.from_numpy(x).to('cuda:0');G=torch.from_numpy(y).to('cuda:0');torch.cuda.reset_peak_memory_stats(0)
        def save_memory(i,detail,ret):
            arrays={k:v.cpu().numpy() for k,v in detail.items() if torch.is_tensor(v)};arrays.update(coarse=ret[0].cpu().numpy(),prediction=ret[-1].cpu().numpy())
            np.savez_compressed(out/('real_D_%02d.npz'%i),**arrays)
        from torch.utils._python_dispatch import TorchDispatchMode
        class NoAttention(TorchDispatchMode):
            def __torch_dispatch__(self,func,types,args=(),kwargs=None):
                need(not any(s in str(func).lower() for s in ('scaled_dot_product','flash_attention','efficient_attention','native_multi_head_attention')),'attention op');return func(*args,**(kwargs or {}))
        with NoAttention():result=run_checks(torch,np,runtime,build,D,G,q['real_inputs'],lambda r:runtime.read_partial(np,r),event,sample,save_memory)
        need(sum(native_calls.values())==396 and len(native_calls)==66,'396 native SSM calls')
        sample('complete',11);stop.set();watcher.join(10);need(not watcher.is_alive(),'monitor stop')
        emit(out/'completion.json',dict(status='SPCG_CUDA_COMPLETE_PENDING_FORMAL_FREEZE',request_sha256=qr['sha256'],result=result,native_calls=native_calls,native_origins=origins,training_admission=False,optimizer_constructed=False))
        emit(out/'payload_manifest.json',[dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('launch.log','worker.pid')])
    except BaseException as e:emit(out/'failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(e)));raise
    finally:
        stop.set()
        if watcher:watcher.join(10)
        for g in guards:g.close()
        utc.close()

if __name__=='__main__':main()
