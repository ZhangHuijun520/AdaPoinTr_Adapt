"""SCQ-PRIME Fold C seed1 B/F/S training entry. Stdlib-only import; separate request authorization."""

import argparse

import hashlib

import importlib.util

import json

import os

from pathlib import Path, PurePosixPath

import shlex

import socket

import sys

def require(ok, text):
    if not ok:
        raise ValueError(text)

def no_links(path):
    p = Path(path).absolute()
    require(not any(x.is_symlink() for x in (p,*p.parents)), 'linked path: '+str(p))
    require(not {'.ssh','.aws','.credentials','.git'} & set(p.parts) and p.name not in ('.env','.netrc','auth.json'), 'secret path')
    return p

def sha(path):
    h = hashlib.sha256()
    with no_links(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):
            h.update(b)
    return h.hexdigest()

def exact(r):
    require(isinstance(r,dict) and set(r) == {'path','bytes','sha256'}, 'binding fields')
    p = no_links(r['path'])
    require(p.is_file() and p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], 'binding: '+str(p))
    return p

def bound(r):
    return json.loads(exact(r).read_bytes())

def emit(path, value):
    with no_links(path).open('x',encoding='ascii') as f:
        json.dump(value,f,indent=2,allow_nan=False); f.write('\n'); f.flush(); os.fsync(f.fileno())

def source_module(name, r):
    require(name not in sys.modules, 'preloaded module: '+name)
    p = exact(r); spec = importlib.util.spec_from_file_location(name,p)
    m = importlib.util.module_from_spec(spec); sys.modules[name] = m
    exec(compile(p.read_bytes(),str(p),'exec',dont_inherit=True),m.__dict__)
    return m

def payload_paths(root, selected):
    root = no_links(root); allowed = {}
    for r in selected:
        rel = PurePosixPath(r['point_path'])
        require(not rel.is_absolute() and '..' not in rel.parts and rel.as_posix() == r['point_path']
                and '\\' not in r['point_path'] and ':' not in r['point_path'] and rel.suffix == '.npz', 'relative training-only path')
        p = no_links(root/r['point_path']); require(root in p.parents and p not in allowed, 'duplicate/boundary')
        allowed[p] = r['sha256']
    require(len(allowed) == 315, '315 exact payload allowlist')
    return allowed

def geometry_record(torch, ret):
    require(len(ret) == 4 and ret[0].shape[1:] == (256,3) and ret[-1].shape[1:] == (8192,3), 'training geometry tuple')
    result = {}
    with torch.no_grad():
        for name, t in [('coarse',ret[0]),('dense',ret[-1])]:
            t = t.detach(); require(bool(torch.isfinite(t).all()), 'nonfinite geometry')
            center = t.mean(1)
            result[name] = dict(centroid=center.cpu().tolist(), radius=((t-center[:,None])**2).sum(-1).mean(1).sqrt().cpu().tolist(),
                                minimum=t.min(1).values.cpu().tolist(),maximum=t.max(1).values.cpu().tolist())
    return result

def render_launcher(q, qsha, asha, rsha):
    for h in (qsha,asha,rsha):
        require(len(h) == 64 and all(c in '0123456789abcdef' for c in h), 'full hash')
    out = PurePosixPath(q['output']); L = q['launch_contract']
    cmd = ['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',q['identity']['python_realpath'],'-I','-S','-B',
           q['implementation']['entry']['path'],'--request',L['request_path'],'--request-sha256',qsha,
           '--authorization',L['authorization_path'],'--authorization-sha256',asha,'--runtime',L['runtime_path'],'--runtime-sha256',rsha]
    env = '\n'.join('export '+k+'='+shlex.quote(v.replace('<owned_output>',str(out))) for k,v in q['environment'].items())
    return '#!/bin/bash\nset -eu\numask 077\ncd '+shlex.quote(PROJECT)+'\nmkdir -p '+shlex.quote(str(out.parent))+'\nmkdir '+shlex.quote(str(out))+'\n'+env+'\nset +e\n'+shlex.join(cmd)+' >'+shlex.quote(str(out/'launch.log'))+' 2>&1\nrc=$?\nset -e\nprintf "%s\\n" "$rc" >'+shlex.quote(str(out/'exit_code.txt'))+'\nexit "$rc"\n'

PROJECT='/home/jovyan/adapointr_work/PoinTr'
ADMISSION_SHA='bf63a5ed3562dc281ec3fa368220951348ea49008561ca37a83330a83151e0e9'
CUDA_REQUEST_SHA='adbc6721c4a92dbbe6765c22875ab7d4419d988deccf2ecc89a92dd27bbe0404'
CONSTRUCTION_SHA='e9428b1f6e8e8151173d485f8b1290f6fe002b04261022611e9d2220d1afb7aa'
COUNTS=dict(cases=315,sources=63,batch=8,epochs=100,batches_per_epoch=39,updates=3900,exposures=31200)
RESOURCES=dict(wall_seconds=86400,RSS_bytes=8589934592,device_MiB=22528,torch_peak_bytes=21474836480,output_bytes=2147483648,minimum_free_disk_bytes=4294967296)
PINS=dict(runtime='09973e15bfebe820f39bed550b809e814a4b14c022b22863946ad25f3c5dd292',contract='08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499',budget_parent='095cabb0ab9b098172840432d40699dd18279671cf650894fab9eb9b54575ebe')

def validate_admission(q):
    a=q['admission']
    require(set(a)=={'audit','construction','request'},'PRIME CUDA receipt set')
    require(a['audit']['sha256']==ADMISSION_SHA and a['request']['sha256']==CUDA_REQUEST_SHA
            and a['construction']['sha256']==CONSTRUCTION_SHA,'PRIME CUDA anchors')
    audit,cuda,construction=(bound(a[k]) for k in ('audit','request','construction'))
    require(audit['status']=='FORMAL_SCQ_PRIME_POST_CUDA_FREEZE_AUDIT_PASS' and audit['request_sha256']==CUDA_REQUEST_SHA
            and audit['counts']==dict(full_forward=6,full_loss=3,full_backward=3,decoder_forward=0,decoder_backward=0,optimizer_steps=0)
            and audit['rng_and_state_restorations']==6,'formal six-phase audit')
    for key in ('identity','fold','seed','model_root','preflight_scope','dependencies','environment'):
        require(q[key]==cuda[key],'same admitted '+key)
    require(q['initialization']==cuda['initialization'] and q['static_config']==cuda['static_config'],'admitted config and initializer')
    for key,value in cuda['implementation'].items():
        require(q['implementation'][key]==value,'admitted implementation '+key)
    rows=construction['models']
    require([x['phase'] for x in rows]==audit['phases'] and [x['variant'] for x in rows]==list('BFSBFS')
            and all(x['seed']==q['seed'] for x in rows) and len({x['shared_initial_state_SHA256'] for x in rows})==1,'same seed1 construction')
    return dict(status='SCQ_PRIME_NATIVE_CUDA_ADMISSION_PASS',audit_sha256=ADMISSION_SHA),rows[0]['shared_initial_state_SHA256']


def run_paths(project, arm):
    root = PurePosixPath(project)
    run_id = f"SCQ_PRIME_{arm}_C_seed2026112101_train_20261122_v1"
    install = root / 'third_party/bcsp_scq_prime_foldC_training_20261122_v1'
    out = root / 'logs/cranial_bcsp_fullmamba' / run_id
    control = install / f'control_{arm}_v1'
    launch = dict(
        request_path=str(install / (run_id + '_request.json')),
        authorization_path=str(control / 'authorization.json'),
        runtime_path=str(control / 'runtime.json'),
        launcher_path=str(control / 'launch_once.sh'),
        tmux_session=f'bcsp_scq_prime_{arm}_C_seed1_20261122_v1',
        log=str(out / 'launch.log'),
        PID=str(out / 'worker.pid'),
        exit_code=str(out / 'exit_code.txt'),
        exclusive_single_attempt=True,
        automatic_retry=False,
        resume=False,
    )
    return dict(run_id=run_id, output=str(out), launch_attempt=str(control / 'launch_attempt.json'),
                launch_contract=launch)


def protocol(q, pair, predecessor_receipts, common):
    arm=q['variant']
    require(q['schema']=='bcsp-scq-prime-foldC-training-request-v1'
            and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
            and q['stage']=='CRANIAL_BCSP_SCQ_PRIME'
            and arm in ('B','F','S') and q['fold']=='C' and type(q['seed']) is int and q['seed']==2026112101
            and q['n_input']==q['n_output']==8192,'fixed PRIME Fold C seed1')
    require(all(q[k]==value for k,value in run_paths(PROJECT,arm).items()),'fresh run and control paths')
    require(pair['status']=='FROZEN_PRIME_C_SEED1_NOT_AUTHORIZATION' and pair['arm_order']==['B','F','S']
            and pair['counts']==COUNTS and pair['resources']==RESOURCES and pair['drop_events']==300
            and pair['pair_common_sha256']==common and pair['audit_sha256']==ADMISSION_SHA,'pair contract')
    for key in ('fold','seed','identity','static_config','QC','order_plan','data_root','initialization','implementation',
                'admission','preflight_scope','dependencies','environment','model_root'):
        require(pair[key]==q[key],'pair identity '+key)
    expected={'B':(), 'F':('B',), 'S':('B','F')}[arm]
    require(tuple(predecessor_receipts)==expected,'formal predecessors in B/F/S order')
    for name,receipt in predecessor_receipts.items():
        require(receipt['status']=='FORMAL_SCQ_PRIME_POST_TRAINING_FREEZE_AUDIT_PASS'
                and receipt['run_identity']==dict(variant=name,fold='C',seed=q['seed'])
                and receipt['pair_contract_sha256']==q['pair_contract']['sha256']
                and receipt['common_initial_state_SHA256']==common and receipt['updates']==3900
                and receipt['exposures']==31200 and receipt['drop_events']==300,'paired predecessor '+name)


def authorize(qr,ar,rr):
    q=bound(qr);a=bound(ar);runtime=bound(rr)
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'}
            and a['schema']=='bcsp-scq-prime-training-authorization-v1' and a['request_sha256']==qr['sha256']
            and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate execution authorization')
    require(runtime==dict(schema='bcsp-scq-prime-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
    for key,r in q['implementation'].items():
        if key in PINS:require(r['sha256']==PINS[key],'exact '+key)
        exact(r)
    exact({k:q['initialization'][k] for k in ('path','bytes','sha256')})
    admission,common=validate_admission(q)
    protocol(q,bound(q['pair_contract']),{k:bound(v) for k,v in q['predecessors'].items()},common)
    p3=bound(q['P3'])
    require(p3['status']=='SCQ_PRIME_TRAIN_ENTRY_LOCAL_P3_PASS' and p3['entry_sha256']==q['implementation']['entry']['sha256']
            and p3['runtime_sha256']==q['implementation']['runtime']['sha256'],'PRIME local P3')
    metadata=source_module('bcsp_training_contract_v1',q['implementation']['contract'])
    static=metadata.validate_static(bound(q['static_config']))
    require(static['counts']==COUNTS and static['resources']==RESOURCES,'unchanged3900 and resources')
    selected,fold=metadata.verify_qualified_receipt(bound(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192)
    plan=metadata.validate_order(bound(q['order_plan']),fold['train_case_ids'])
    return q,static,metadata,selected,fold,plan,admission,common


def scq_geometry(model,ret):
    result=geometry_record(__import__('torch'),ret)
    if hasattr(model.base_model,'scq'):
        info=model.base_model._scq_last_info;raw=info['Q0'];used=info['Qused'];delta=info['delta']
        require(__import__('torch').equal(used,ret[0].detach()),'Qused training return identity')
    else:
        raw=ret[0].detach();used=raw;delta=raw.new_zeros(raw.shape)
    import torch
    with torch.no_grad():
        center=raw.mean(1);norm=delta.square().sum(-1).sqrt()
        result.update(Q0=dict(centroid=center.cpu().tolist(),radius=((raw-center[:,None])**2).sum(-1).mean(1).sqrt().cpu().tolist()),delta=dict(mean_norm=norm.mean(1).cpu().tolist(),max_norm=norm.max(1).values.cpu().tolist(),centroid=delta.mean(1).cpu().tolist()))
    return result

def dispatch_training(q,selected,fold,plan,*,factory,model_builder,runtime,prime,seeded,admission,expected_common,helper,budget,torch,np,knn_enable):
    run=prime.identity(q['variant'],q['fold'],q['seed'])
    model,evidence=prime.construct(run,model_builder,None if q['variant']=='B' else q['initialization'],
                                   torch=torch,np=np,parent=seeded,lqi=factory.parent,scq=factory)
    helper.validate_model(model)
    budget.first_step_evidence={**evidence,'pair_contract_sha256':q['pair_contract']['sha256']}
    dataset=runtime.BCSPDataset(q['data_root'],selected,fold['train_sources'],8192)
    budget.pending_geometry=None;budget.pending_losses={};budget.logged_geometry=0
    def geometry(module,args,ret):
        require(module.training and len(args)==1 and budget.pending_geometry is None,'one D-only model forward')
        budget.pending_geometry=scq_geometry(module,ret)
    def loss_capture(name):
        def hook(module,args,value):
            require(name not in budget.pending_losses,'single original loss component')
            budget.pending_losses[name]=float(value.detach())
        return hook
    hooks=[model.register_forward_hook(geometry),model.loss_func.register_forward_hook(loss_capture('coarse_CD')),model.fine_loss_func.register_forward_hook(loss_capture('dense_CD'))]
    try:
        return prime.train_admitted(run,model,evidence,runtime,q['implementation']['runtime']['sha256'],expected_common,admission,'cuda:0',lambda epoch:runtime.make_loader(dataset,plan,epoch),selected,plan,q['output'],numeric_check=helper.assert_numeric,resources=budget,knn_enable=knn_enable,state_fingerprint=helper.state_sha)
    finally:
        for h in hooks:h.remove()

def make_budget(parent,limits,out,torch,helper,q,plan):
    class SCQBudget(parent.TrainingBudget):
        def before_step(self,step):
            super().before_step(step)
            if step==0:
                emit(self.output/'model_construction.json',self.first_step_evidence)
                emit(self.output/'run_identity.json',dict(stage=q['stage'],variant=q['variant'],fold=q['fold'],seed=q['seed'],native_admission_sha256=ADMISSION_SHA,checkpoint_legacy_stage='BCSP_INPUT_DENSITY_V1',legacy_stage_is_provenance_only=True,SSM_gradient_non_bitwise_reproducibility_disclosed=True))
        def after_step(self,step):
            require(self.pending_geometry is not None and self.logged_geometry==step-1 and set(self.pending_losses)=={'coarse_CD','dense_CD'},'one geometry and both original losses per step')
            epoch,batch=divmod(step-1,39)
            row=dict(step=step,epoch=epoch,batch=batch,case_ids=plan['epochs'][epoch]['batches'][batch],frame='D-only normalized',geometry=self.pending_geometry,loss_components=self.pending_losses,reconstruction_sum=self.pending_losses['coarse_CD']+self.pending_losses['dense_CD'])
            with (self.output/'SCQ_geometry.jsonl').open('x' if step==1 else 'a',encoding='ascii') as f:f.write(json.dumps(row,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
            self.pending_geometry=None;self.pending_losses={};self.logged_geometry+=1
            super().after_step(step)
        def before_final(self):
            require(self.logged_geometry==3900 and self.pending_geometry is None and self.pending_losses=={},'exact3900 geometry/loss logs')
            super().before_final()
    return SCQBudget(limits,out,torch,helper)

def main():
    parser=argparse.ArgumentParser()
    for key in ['request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256']:parser.add_argument('--'+key,required=True)
    args=vars(parser.parse_args())
    def record(key):
        p=no_links(args[key]);return dict(path=str(p),bytes=p.stat().st_size,sha256=args[key+'_sha256'])
    qr=record('request');q,static,metadata,selected,fold,plan,admission,common=authorize(qr,record('authorization'),record('runtime'))
    I=q['identity'];out=no_links(q['output']);root=no_links(q['model_root'])
    require(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
    require(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'current identity')
    require(Path.cwd().resolve()==Path(PROJECT) and out.parent==Path(PROJECT)/'logs/cranial_bcsp_fullmamba','cwd and output')
    require(exact(q['implementation']['entry'])==Path(__file__).absolute(),'entry origin')
    parent_args=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    require(parent_args[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s'],'external timeout')
    require(json.loads(no_links(q['launch_attempt']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single launch claim')
    for r in q['dependencies']:exact(r)
    allowed=payload_paths(q['data_root'],selected)
    for p,h in allowed.items():require(p.is_file() and sha(p)==h,'315 training payload exact hash '+str(p))
    helper=source_module('scq_training_helper',q['implementation']['preflight_helper']);helper._MONITOR=None
    parent=source_module('scq_training_budget_parent',q['implementation']['budget_parent'])
    native=source_module('scq_native_read_helper',q['implementation']['native_helper'])
    cuda_entry=source_module('scq_read_guard_module',q['implementation']['cuda_entry'])
    scope=bound(q['preflight_scope']);sources=helper.source_map(scope)
    for rel,r in sources.items():helper.exact(root/rel,r['sha256'],r['bytes'])
    helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
    for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
    for k,v in q['environment'].items():require(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
    gpu=[s.strip() for s in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    require(gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])]
            and int(gpu[4])<=256 and not helper.smi('pid',True),'GPU identity and idle')
    require(out.is_dir() and {p.name for p in out.iterdir()}=={'launch.log'},'fresh output')
    with (out/'worker.pid').open('x') as f:f.write(str(os.getpid())+'\n')
    timezone=source_module('scq_training_timezone',q['implementation']['timezone']);utc=timezone.ExactUTCReader(timezone.UTC_RESOURCE)
    init_file={k:q['initialization'][k] for k in ('path','bytes','sha256')}
    guard=cuda_entry.ExactSCQReads(native.ExactSourceReads(q['implementation']),[q['implementation'][k] for k in ('scq_residual','scq_factory','prime_entry','prime_seeded_parent','runtime')]+[init_file])
    try:
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent;entryroot=Path(__file__).parent
        sys.path[:0]=[str(entryroot),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,sources));(out/'tmp').mkdir()
        roots=[root,entryroot,envroot,provider,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']
        base_policy=parent.make_training_policy(helper,roots,out,allowed,utc)
        class Policy(type(base_policy)):
            def check(self,filename,write=False):
                if isinstance(filename,int):return
                if utc.allow(filename,write):return
                if guard.allow(filename,write):return
                return super().check(filename,write)
        sys.addaudithook(Policy(roots,out).audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
        require(torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.version.cuda==I['torch_cuda_version'],'native CUDA device');torch.cuda.set_device(0);helper.configure_numeric(torch)
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');pm=importlib.import_module('pointnet2_ops.pointnet2_utils');ext=importlib.import_module('pointnet2_ops._ext');helper.check_backend(chamfer,pn,pm)
        require(str(Path(pm.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(ext.__file__).resolve())==scope['bindings']['provider'][2]['path'],'provider origin')
        transformer=importlib.import_module('models.Transformer_utils');cls=importlib.import_module('models.AdaPoinTr').AdaPoinTr
        require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'same model config')
        for name,key in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory'),('bcsp_scq_residual_v1','scq_residual')]:source_module(name,q['implementation'][key])
        factory=source_module('bcsp_scq_factory_v1',q['implementation']['scq_factory'])
        prime=source_module('bcsp_scq_prime_entry_v1',q['implementation']['prime_entry'])
        seeded=source_module('bcsp_scq_prime_seeded_parent_v1',q['implementation']['prime_seeded_parent'])
        runtime=source_module('scq_prime_training_runtime',q['implementation']['runtime'])
        budget=make_budget(parent,static['resources'],out,torch,helper,q,plan)
        result=dispatch_training(q,selected,fold,plan,factory=factory,model_builder=lambda:cls(EasyDict(static['model'])),runtime=runtime,prime=prime,seeded=seeded,admission=admission,expected_common=common,helper=helper,budget=budget,torch=torch,np=np,knn_enable=transformer.enable_bcsp_knn)
        budget.local();emit(out/'payload_manifest.json',dict(files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('launch.log','worker.pid')]))
        return result
    except BaseException as exc:
        if not (out/'failure.json').exists() and not (out/'completion.json').exists():emit(out/'startup_failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)))
        raise
    finally:guard.close();utc.close()

if __name__=='__main__':main()

