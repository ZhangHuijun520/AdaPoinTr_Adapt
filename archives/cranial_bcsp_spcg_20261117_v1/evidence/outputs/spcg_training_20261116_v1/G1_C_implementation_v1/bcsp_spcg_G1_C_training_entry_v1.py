"""G1_C only; scratch3900. Stdlib import; no execution before separate hash authorization."""
import traceback
import argparse,hashlib,importlib.util,json,os,random,shlex,shutil,socket,sys
from pathlib import Path,PurePosixPath
COUNTS=dict(cases=315,sources=63,batch=8,epochs=100,batches_per_epoch=39,updates=3900,exposures=31200)
RESOURCES=dict(wall_seconds=3600,RSS_bytes=8589934592,device_MiB=22528,torch_peak_bytes=21474836480,output_bytes=1073741824,minimum_free_disk_bytes=4294967296)
def need(v,s):
    if not v:raise ValueError(s)
def clean(p):
    p=Path(p).absolute();need(not any(x.is_symlink() for x in (p,*p.parents)),'linked path');need(not {'.ssh','.aws','.git','.credentials'}&set(p.parts) and p.name not in ('.env','.netrc','auth.json'),'secret');return p
def sha(p):return hashlib.sha256(clean(p).read_bytes()).hexdigest()
def exact(r):
    p=clean(r['path']);need(p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'binding '+str(p));return p
def bound(r):return json.loads(exact(r).read_bytes())
def emit(p,v):
    with clean(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
def source(name,r):
    need(name not in sys.modules,'preloaded '+name);p=exact(r);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def validate(q,digest,a,ah,r):
    need(q['schema']=='bcsp-spcg-G1C-training-v1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'pending')
    need((q['arm'],q['fold'],q['seed'],q['n_input'],q['n_output'])==('G1','C',0,8192,8192) and q['counts']==COUNTS and q['resources']==RESOURCES,'fixed scientific run')
    need(q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'],'GPU binding')
    need(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-spcg-training-authorization-v1' and a['request_sha256']==digest and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'explicit authorization')
    need(r==dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=digest,authorization_sha256=ah),'one-way runtime')
    need(q['science']==dict(updates=3900,traversals=100,exposures=31200,drops=300,from_scratch=True,BNCal=False,evaluation=False,resume=False,retry=False),'science scope')
    audit=bound(q['CUDA_freeze']);need(audit['status']=='FORMAL_POST_CUDA_FREEZE_PASS' and all(audit['checks'].values()),'formal CUDA freeze')
    p3=bound(q['P3']);need(p3['status']=='SPCG_G1C_TRAINING_LOCAL_P3_PASS' and p3['entry_sha256']==q['implementation']['entry']['sha256'] and p3['bridge_sha256']==q['implementation']['bridge']['sha256'],'final P3')
    pair=bound(q['G0_C_freeze'])
    need(pair['status']=='FORMAL_SPCG_G0_C_POST_TRAINING_FREEZE_PASS' and all(pair['checks'].values()),'G0 freeze')
    need((pair['arm'],pair['fold'],pair['seed'],pair['updates'],pair['traversals'],pair['exposures'],pair['drops'])==('G0','C',0,3900,100,31200,300),'G0 pairing')
    need(pair['order_plan']==q['order_plan'] and pair['initialization_raw_tensor_fingerprint']==q['parent_G0_initial_state_sha256'],'same order and untrained mother')
    for r in [q['probe_asset'],q['head_initialization'],q['mother_source']]:exact(r)
    return q
def authorize(qr,ar,rr):
    q=validate(bound(qr),qr['sha256'],bound(ar),ar['sha256'],bound(rr))
    for r in q['implementation'].values():exact(r)
    metadata=source('bcsp_training_contract_v1',q['implementation']['contract'])
    static=metadata.validate_static(bound(q['static_config']));need(static['counts']==COUNTS,'static counts')
    selected,fold=metadata.verify_qualified_receipt(bound(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192)
    plan=metadata.validate_order(bound(q['order_plan']),fold['train_case_ids'])
    need(PurePosixPath(q['output']).parent==PurePosixPath(q['project'])/'logs/cranial_bcsp_fullmamba' and PurePosixPath(q['output']).name==q['run_id'],'output')
    return q,static,selected,fold,plan
def render_launcher(q,qh,ah,rh):
    need(q['environment']['CUDA_VISIBLE_DEVICES']==q['identity']['gpu_uuid'],'GPU binding')
    for h in [qh,ah,rh]:need(len(h)==64 and all(c in '0123456789abcdef' for c in h),'full SHA')
    L=q['launch_contract'];o=PurePosixPath(q['output']);cmd=['/usr/bin/timeout','--signal=TERM','--kill-after=5s','3600s',q['identity']['python_realpath'],'-I','-S','-B',q['implementation']['entry']['path']]
    for k,v in [('request',L['request_path']),('request-sha256',qh),('authorization',L['authorization_path']),('authorization-sha256',ah),('runtime',L['runtime_path']),('runtime-sha256',rh)]:cmd+=['--'+k,v]
    env='\n'.join('export '+k+'='+shlex.quote(v.replace('<owned_output>',str(o))) for k,v in q['environment'].items())
    return '#!/bin/bash\nset -eu\numask 077\ncd '+shlex.quote(q['project'])+'\n'+''.join('[ ! -L '+shlex.quote(str(p))+' ] || exit 121\n' for p in reversed((o,*o.parents)) if str(p)!='/')+'mkdir -p '+shlex.quote(str(o.parent))+'\nmkdir '+shlex.quote(str(o))+'\n'+env+'\nset +e\n'+shlex.join(cmd)+' >'+shlex.quote(str(o/'launch.log'))+' 2>&1\nrc=$?\nset -e\nprintf "%s\\n" "$rc" >'+shlex.quote(str(o/'exit_code.txt'))+'\nexit "$rc"\n'
def load_training_chain(q):
    bridge=source('spcg_training_bridge',q['implementation']['bridge'])
    source('bcsp_spcg_head_v1',q['implementation']['head'])
    observe=source('bcsp_spcg_runtime_v1',q['implementation']['observe'])
    runtime=source('spcg_frozen_training_runtime',q['implementation']['training_runtime'])
    return bridge,observe,runtime

def fail_with_traceback(out,exc):
    # Called before finally closes the exact-source FDs; SystemExit suppresses late excepthook.
    formatted=''.join(traceback.format_exception(type(exc),exc,exc.__traceback__))
    emit(out/'training_error_traceback.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),traceback=formatted,phase='GUARD_ACTIVE_BEFORE_CLEANUP'))
    if not (out/'failure.json').exists() and not (out/'startup_failure.json').exists():
        emit(out/'startup_failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)))
    raise SystemExit(1) from None


def raw_state_fingerprint(model):
    h=hashlib.sha256()
    for n,t in model.state_dict().items():h.update(n.encode());h.update(t.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()

def build_G1(q,legacy_builder):
    # Uses same LQI constructor first; never load G0's trained checkpoint.
    model,parent=sys.modules['bcsp_lqi_factory_v1'].build_model(legacy_builder,seed=0)
    need(raw_state_fingerprint(model)==q['parent_G0_initial_state_sha256'],'G0 shared scratch identity')
    factory=source('bcsp_spcg_factory_v1',q['implementation']['spcg_factory'])
    head=sys.modules['bcsp_spcg_head_v1'];U=head.from_bytes(exact(q['probe_asset']).read_bytes(),(256,3));H=exact(q['head_initialization']).read_bytes()
    model,change=factory.install(model,'G1',U,H,q['mother_source']['path'],q['mother_source']['sha256'])
    need(raw_state_fingerprint(model)==q['expected_initial_state_sha256'],'CUDA admitted G1 initial state')
    return model,dict(parent=parent,change=change,artificial_fixture=parent['artificial_fixture'])


def main():
    ap=argparse.ArgumentParser()
    for k in ['request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256']:ap.add_argument('--'+k,required=True)
    args=vars(ap.parse_args())
    def record(k):p=clean(args[k]);return dict(path=str(p),bytes=p.stat().st_size,sha256=args[k+'_sha256'])
    qr=record('request');q,static,selected,fold,plan=authorize(qr,record('authorization'),record('runtime'));I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])
    need(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux isolated')
    need(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'identity')
    need(Path.cwd()==Path(q['project']),'cwd')
    need(Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().split(b'\0')[:4]==[b'/usr/bin/timeout',b'--signal=TERM',b'--kill-after=5s',b'3600s'],'timeout')
    need(json.loads(clean(q['launch_contract']['launch_attempt_path']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'claim')
    need({p.name for p in out.iterdir()}=={'launch.log'},'new output');(out/'worker.pid').write_text(str(os.getpid()),encoding='ascii')
    helper=source('spcg_training_helper',q['implementation']['preflight_helper']);parent=source('spcg_budget_parent',q['implementation']['budget_parent']);native=source('spcg_native_policy',q['native_helper']);utcmod=source('spcg_training_utc',q['implementation']['timezone']);utc=utcmod.ExactUTCReader(utcmod.UTC_RESOURCE)
    try:
        for k,v in q['environment'].items():need(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
        for r in q['dependencies']:exact(r)
        scope=bound(q['preflight_scope']);records=helper.source_map(scope)
        for rel,r in records.items():helper.exact(root/rel,r['sha256'],r['bytes'])
        helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
        for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
        try:g=[x.strip() for x in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
        except Exception as ex:emit(out/'startup_monitor_failure.json',dict(error=repr(ex),details=getattr(ex,'details',None)));raise
        need(g[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(g[4])<=256,'GPU')
        need(shutil.disk_usage(out).free>=int(8.5*1024**3),'foldblock disk')
        allowed={}
        for r in selected:
            rel=PurePosixPath(r['point_path']);need(not rel.is_absolute() and '..' not in rel.parts and '\\' not in str(rel),'input relpath');p=clean(Path(q['data_root'])/r['point_path']);need(sha(p)==r['sha256'],'input hash');allowed[p]=r['sha256']
        need(len(allowed)==315,'315 inputs')
        guard=native.ExactSourceReads(dict(encoder=q['implementation']['encoder'],factory=q['implementation']['factory'],f0_decoder=q['implementation']['lqi_decoder'],f0_factory=q['implementation']['lqi_factory']))
        read_records=[*q['implementation'].values(),q['native_helper'],q['probe_asset'],q['head_initialization']]
        for r in read_records:
            p=clean(r['path'])
            if p not in guard.records:guard.records[p]=r;guard.fds[p]=os.open(p,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0));guard.verify(p)
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
        sys.path[:0]=[str(Path(__file__).parent),str(provider),str(envroot/'lib/python3.10/site-packages')];helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,records));(out/'tmp').mkdir()
        roots=[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'];base=parent.make_training_policy(helper,roots,out,allowed,utc)
        class Policy(type(base)):
            def check(self,filename,write=False):
                if isinstance(filename,int):return
                if utc.allow(filename,write):return
                if guard.allow(filename,write):return
                return super().check(filename,write)
        sys.addaudithook(Policy(roots,out).audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        need((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions');need(torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.version.cuda==I['torch_cuda_version'],'CUDA');torch.cuda.set_device(0);helper.configure_numeric(torch)
        ch=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');ext=importlib.import_module('pointnet2_ops._ext');helper.check_backend(ch,pn,pm)
        need(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(ext.__file__).resolve())==scope['bindings']['provider'][2]['path'],'provider');tr=importlib.import_module('models.Transformer_utils');cls=importlib.import_module('models.AdaPoinTr').AdaPoinTr;need(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'model config')
        for n,k in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory')]:source(n,q['implementation'][k])
        bridge,observe,runtime=load_training_chain(q)
        random.seed(0);np.random.seed(0);torch.manual_seed(0);model,evidence=build_G1(q,lambda:cls(EasyDict(static['model'])));helper.validate_model(model)
        need(not evidence['artificial_fixture'] and sum(p.numel() for p in model.parameters())==39912132,'G1 LQI')
        class Budget(parent.TrainingBudget):
            def before_step(self,step):
                super().before_step(step)
                if step==0:emit(out/'model_construction.json',dict(factory=evidence,arm='G1',fold='C',CUDA_freeze=q['CUDA_freeze'],expected_initial_state_sha256=q['expected_initial_state_sha256']))
        budget=Budget(RESOURCES,out,torch,helper)
        result=bridge.dispatch(q,model,runtime,selected,fold,plan,helper,budget,observe,device='cuda:0',knn_enable=tr.enable_bcsp_knn)
        budget.local();emit(out/'payload_manifest.json',dict(files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('launch.log','worker.pid')]))
        return result
    except BaseException as ex:
        fail_with_traceback(out,ex)
    finally:
        if 'guard' in locals():guard.close()
        utc.close()
if __name__=='__main__':main()
