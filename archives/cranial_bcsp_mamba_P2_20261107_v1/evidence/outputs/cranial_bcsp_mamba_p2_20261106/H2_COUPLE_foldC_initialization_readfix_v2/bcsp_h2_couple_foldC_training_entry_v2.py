# Isolated P2 derivative; unchanged P1 I/O policy, monitoring, initialization and dispatch lifecycle.
"""H2-COUPLE first Fold C training entry. Import is inert; execution needs separate hash authorization."""
import argparse,hashlib,importlib.util,json,os,random,shutil,socket,sys,time
from pathlib import Path,PurePosixPath

PROJECT='/home/jovyan/adapointr_work/PoinTr'
COUNTS=dict(cases=315,sources=63,batch=8,epochs=100,batches_per_epoch=39,updates=3900,exposures=31200)
RESOURCES=dict(wall_seconds=86400,RSS_bytes=8589934592,device_MiB=22528,torch_peak_bytes=21474836480,output_bytes=2147483648,minimum_free_disk_bytes=4294967296)

def require(ok,text):
    if not ok:raise ValueError(text)

def no_links(path):
    p=Path(path).absolute();require(not any(x.is_symlink() for x in (p,*p.parents)),'linked path: '+str(p));return p

def sha(path):
    h=hashlib.sha256()
    with no_links(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def exact(r):
    require(isinstance(r,dict) and set(r)=={'path','bytes','sha256'},'binding fields')
    p=no_links(r['path']);require(p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'binding '+str(p));return p

def json_bound(r):return json.loads(exact(r).read_bytes())

def emit(p,v):
    with no_links(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())

def load_bound(name,r):
    spec=importlib.util.spec_from_file_location(name,exact(r));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

H2 = {'version': 'H2-range-soft-coupling-v1', 'feature_dim': 1024, 'coarse_points': 256, 'head_parameters': 1025, 'beta': 0.1, 'aux_weight': 0.1, 'maximum_scale': 1.25, 'minimum_radius': 1e-06, 'epsilon_added_to_radius': False, 'detach_Q_in_aux_target': True, 'detach_delta_in_coupling': True, 'mode': 'COUPLE'}
FROZEN_BASELINES = {'C': {'request_sha256':'48dedc867ce2a9c46bc1a6fdc7db3506b6f2405dbdf914de49cf561e2fe12b54','audit_sha256':'bcbfb9a65742ab7c9da4a2d01c55b5f9a78bc77da66e38cf078f3074e0968815'}}
CURRENT_IDENTITY = {'hostname': 'shu-common-25721452-notebook-1lvq9b-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-4009474d-3c21-c7a6-b03d-7b46cebafa52', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '570.190', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.'}
H2_HASHES = {'h2_range':'ffdd06efa1c4c45339eea3d3d75bcc4b39aadb3561943cec0cc1727baa00d825','h2_adapter':'130939f3bfee8e11b2fefbb26f96b644056134e4bc1b776bebf99cf56edd4330','runtime':'d39bef924e459f6509a3f9d7829317a3ddddbfd822aa838d28c30480ebcb190c'}
CUDA_AUDIT_SHA = '545a5996309fbc865beb145f4a1df4aef5e2077e4374d52a6fc930dd9080313c'

AUX_PAIR_PINS = {'request': '0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517', 'audit': '580a0b195c5730e56f260e357e135966e2ab954b9cef7582ff7298b35d33ee1c', 'initialization': 'f1622a6a792b347ebbaea21884ad3a5f89862e2662a3b95f6795bec91a2414fe'}

def validate_static_h2(static, baseline, metadata):
    import copy
    stripped=copy.deepcopy(static)
    require(stripped.pop('H2',None)==H2,'unique H2-COUPLE config')
    require(stripped==baseline,'only top-level H2 config changes')
    metadata.validate_static(baseline)
    require(static['counts']==COUNTS and static['resources']==RESOURCES,'counts/resources')
    require(not static['model'].get('coarse_geometry_guard',{}).get('enabled',False),'H1 off')
    return static

def validate_model_h2(model):
    import torch
    require(model.num_query==256 and model.num_points==8192 and model.factor==32
            and model.decoder_type=='fc' and model.denoise_weight==0
            and model.fine_coverage_weight==1 and model.fine_local_weight==0,'model contract')
    b=model.base_model
    require(b.center_num==[512,256] and b.encoder_type=='graph' and b.query_selection=='learned_only'
            and not b.use_denoise and not b.encoder_adapter.enabled and not model.scqr_contract.enabled,'backbone')
    for name in ('coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled'):
        require(getattr(model,name) is False,'optional path '+name)
    require(model.h2_metadata()==H2,'actual COUPLE metadata')
    head=model.h2_range_head
    require(set(head.state_dict())=={'weight','bias'} and tuple(head.weight.shape)==(1,1024)
            and tuple(head.bias.shape)==(1,) and sum(p.numel() for p in head.parameters())==1025,'exact head')
    require(all(p.device.type=='cpu' and p.dtype==torch.float32 and torch.count_nonzero(p).item()==0
                for p in head.parameters()),'scratch zero head; synthetic CUDA fixture bias forbidden')

def authorize(qr,ar,rr):
    q=json_bound(qr);base=json_bound(q['baseline_request'])
    extra={'baseline_request','baseline_audit','p3','h2_config','cuda_audit','readiness','aux_pairing'}
    require(set(q)==set(base)|extra,'exact request fields')
    require(q['schema']=='bcsp-p2-H2-COUPLE-training-request-v1'
            and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'
            and q['stage']=='CRANIAL_BCSP_MAMBA_P2_H2' and q['variant']=='M0'
            and q['fold']=='C' and q['n_input']==q['n_output']==8192,'COUPLE C only')
    pin=FROZEN_BASELINES['C']
    require(q['baseline_request']['sha256']==pin['request_sha256']
            and q['baseline_audit']['sha256']==pin['audit_sha256'],'frozen M0 baseline')
    audit=json_bound(q['baseline_audit'])
    require(audit['status']=='FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS'
            and audit['request_sha256']==pin['request_sha256']
            and audit['checks_passed']==len(audit['checks'])>0 and all(audit['checks'].values()),'baseline audit')
    changed={'schema','stage','run_id','static_config','implementation','output','launch_attempt',
             'launch_contract','provenance','not_authorized','identity','environment'}
    require(all(q[k]==v for k,v in base.items() if k not in changed),'original scientific pairing')
    require(base['variant']=='M0' and base['fold']=='C' and q['h2_config']==H2,'H2-only scientific delta')
    require(q['identity']==CURRENT_IDENTITY,'frozen current resource binding')
    require(set(q['environment'])==set(base['environment'])
            and all(v==base['environment'][k] for k,v in q['environment'].items() if k!='CUDA_VISIBLE_DEVICES')
            and q['environment']['CUDA_VISIBLE_DEVICES']==CURRENT_IDENTITY['gpu_uuid'],'environment pairing')
    require(set(q['implementation'])==set(base['implementation'])|{'h2_range','h2_adapter'},'implementation set')
    for k,v in base['implementation'].items():
        if k not in ('entry','runtime'):require(q['implementation'][k]==v,'reused implementation '+k)
    for k,h in H2_HASHES.items():require(q['implementation'][k]['sha256']==h,'final H2 source '+k)
    for v in q['implementation'].values():exact(v)
    require(exact(q['implementation']['entry'])==Path(__file__).absolute(),'entry origin')
    cuda=json_bound(q['cuda_audit']);require(q['cuda_audit']['sha256']==CUDA_AUDIT_SHA
            and cuda['status']=='FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS','formal CUDA evidence')
    p3=json_bound(q['p3'])
    require(p3['status']=='LOCAL_H2_COUPLE_TRAINING_ENTRY_P3_PASS'
            and p3['entry_sha256']==q['implementation']['entry']['sha256']
            and p3['H2_source_hashes']==H2_HASHES,'P3 final source binding')
    metadata=load_bound('bcsp_training_contract_v1',q['implementation']['contract'])
    static=validate_static_h2(json_bound(q['static_config']),json_bound(base['static_config']),metadata)
    ready=json_bound(q['readiness'])
    require(ready['status']=='BOUNDED_H2_AUX_C_READINESS_PASS'
            and ready['identity']==CURRENT_IDENTITY and ready['training_payloads']==315,'bounded readiness')
    pair=q['aux_pairing']
    require(set(pair)=={'request','audit','initialization'},'exact AUX pairing evidence')
    require(all(pair[k]['sha256']==h for k,h in AUX_PAIR_PINS.items()),'frozen AUX pairing pins')
    aux=json_bound(pair['request']);aux_audit=json_bound(pair['audit']);aux_initial=json_bound(pair['initialization'])
    require(aux_audit['status']=='FORMAL_H2_AUX_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS'
            and aux_audit['request_sha256']==pair['request']['sha256']
            and aux_audit['checks_passed']==len(aux_audit['checks'])>0 and all(aux_audit['checks'].values()),'AUX formal audit')
    require(aux_initial==aux_audit['initialization']['record'] and aux_initial['seed']==0,'AUX initial fingerprint evidence')
    require(aux['h2_config']==dict(H2,mode='AUX') and aux['fold']=='C' and aux['variant']=='M0','AUX pairing role')
    for key in ('identity','environment','QC','order_plan','data_root','model_root','initialization_reference','numeric_policy','numeric_protocol','pair_contract','dependencies','n_input','n_output'):
        require(q.get(key)==aux.get(key),'AUX scientific pairing '+key)
    require(all(q['implementation'][k]==v for k,v in aux['implementation'].items() if k!='entry'),'same H2 modules and inherited implementation')
    aux_static=json_bound(aux['static_config']);require(dict(static, H2=dict(H2,mode='AUX'))==aux_static,'only mode differs from AUX')
    a,r=json_bound(ar),json_bound(rr)
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'}
            and a['schema']=='bcsp-p2-H2-training-authorization-v1' and a['request_sha256']==qr['sha256']
            and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate authorization')
    require(r==dict(schema='bcsp-p2-H2-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime')
    selected,fold=metadata.verify_qualified_receipt(json_bound(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192)
    plan=metadata.validate_order(json_bound(q['order_plan']),fold['train_case_ids'])
    return q,static,metadata,selected,fold,plan



def payload_paths(root,selected):
    root=no_links(root);result={}
    for r in selected:
        rel=PurePosixPath(r['point_path'])
        require(not rel.is_absolute() and '..' not in rel.parts and '\\' not in r['point_path'] and ':' not in r['point_path'] and rel.as_posix()==r['point_path'],'canonical relative payload path')
        p=no_links(root/r['point_path']);require(root in p.parents and p.suffix=='.npz' and p not in result,'exact payload path');result[p]=r['sha256']
    require(len(result)==315,'315 payload allowlist');return result

def make_training_policy(helper,read_roots,output,allowed,utc_guard):
    class Policy(helper.FilePolicy):
        def check(self,filename,write=False):
            if isinstance(filename,int):return
            if utc_guard.allow(filename,write):return
            p=no_links(os.fsdecode(filename));require(not {'.ssh','.aws','.credentials','.git'}&set(p.parts) and p.name not in ('.env','.netrc'),'secret path')
            if p.suffix.lower()=='.npz':require(not write and p in allowed,'non-allowlisted NPZ');return
            if p.suffix.lower() in helper.PAYLOAD or p.name.lower().endswith('.nii.gz'):require(p==self.output/'ckpt-last.pth','nonfinal checkpoint/payload');return
            return super().check(filename,write)
    return Policy(read_roots,output)

class TrainingBudget:
    """Per-step monitored contract, not a cgroup or continuous-memory guarantee."""
    def __init__(self, limits, output, torch, helper):
        self.limits, self.output, self.torch, self.helper = limits, Path(output), torch, helper
        self.start, self.records = time.monotonic(), 0
        self.path = self.output / 'resources.jsonl'
        with self.path.open('x', encoding='utf-8'):
            pass
        torch.cuda.reset_peak_memory_stats(0)

    def local(self):
        require(time.monotonic() - self.start <= self.limits['wall_seconds'], 'training wall budget')
        status = Path('/proc/' + str(os.getpid()) + '/status').read_text(encoding='ascii')
        rss = int(next(x.split()[1] for x in status.splitlines() if x.startswith('VmRSS:'))) * 1024
        size = sum(p.stat().st_size for p in self.output.rglob('*') if p.is_file())
        require(rss <= self.limits['RSS_bytes'] and size <= self.limits['output_bytes'],
                'training RSS/output budget')
        require(shutil.disk_usage(self.output).free >= self.limits['minimum_free_disk_bytes'], 'free disk')
        return rss, size

    def sample(self, label, step):
        rss, size = self.local()
        self.torch.cuda.synchronize()
        allocated = self.torch.cuda.max_memory_allocated(0)
        reserved = self.torch.cuda.max_memory_reserved(0)
        used = int(self.helper.smi('memory.used')[0])
        # User-approved research-priority policy: PID telemetry is diagnostic only.
        # SMI PIDs and container PIDs have no established common namespace here.
        pids, pid_query_error = None, None
        try:
            pids = [int(p) for p in self.helper.smi('pid', True)]
        except Exception as exc:
            pid_query_error = repr(exc)[:512]
        own_pid = os.getpid()
        checks = {
            'allocated_within_limit': allocated <= self.limits['torch_peak_bytes'],
            'reserved_within_limit': reserved <= self.limits['torch_peak_bytes'],
            'device_within_limit': used <= self.limits['device_MiB'],
        }
        self.records += 1
        require(self.records <= 3902, 'fixed training resource record cap')
        event = {
            'phase': label, 'committed_step': step, 'RSS': rss, 'output_bytes': size,
            'peak_allocated': allocated, 'peak_reserved': reserved, 'device_MiB': used,
            'compute_PIDs': pids, 'own_PID': own_pid,
            'PID_policy': 'DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE',
            'PID_query_error': pid_query_error,
            'raw_PIDs_match_worker_number': (all(p == own_pid for p in pids) if pids else None),
            'PID_warning': (pid_query_error is not None or not pids
                            or any(p != own_pid for p in pids)),
            'elapsed_seconds': time.monotonic() - self.start,
            'limits': dict(self.limits), 'checks': checks,
            'failed_checks': [key for key, passed in checks.items() if not passed],
            'resource_guard_passed': all(checks.values()),
        }
        # Persist the failed sample before enforcing exactly the original assertion.
        # A logging/fsync failure propagates immediately; it never permits training to continue.
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event, allow_nan=False) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        require(allocated <= self.limits['torch_peak_bytes'] and reserved <= self.limits['torch_peak_bytes']
                and used <= self.limits['device_MiB'],
                'training GPU memory budget')

    def before_step(self, step):
        self.local()

    def after_step(self, step):
        self.sample('after_step', step)

    def before_final(self):
        self.sample('before_final', 3900)

    def after_final(self):
        self.sample('after_final', 3900)

class P1Budget(TrainingBudget):
    def before_step(self,step):
        super().before_step(step)
        if step==0:
            emit(self.output/'model_construction.json',self.first_step_evidence)
            emit(self.output/'run_identity.json',self.run_identity)

def dispatch_training(q,static,selected,fold,plan,*,factory,h2_adapter,model_builder,runtime,helper,budget,torch,knn_enable,expected_factory,device='cuda:0'):
    require(q['variant']=='M0' and q['fold']=='C' and static['H2']==H2,'H2-COUPLE C dispatch')
    model,evidence=h2_adapter.build_h2(factory,model_builder,'COUPLE',seed=0)
    require({k:v for k,v in evidence.items() if k not in ('H2_mode','H2_contract','common_state_after_H2_unchanged')}==expected_factory
            and not evidence['artificial_fixture'],'frozen real initialization')
    require(evidence['H2_mode']=='COUPLE' and dict(evidence['H2_contract'],mode='COUPLE')==H2
            and evidence['common_state_after_H2_unchanged'] is True,'H2 common initialization')
    validate_model_h2(model)
    aux_initial=json_bound(q['aux_pairing']['initialization'])
    require(helper.state_sha(model,True)==aux_initial['parameter_sha256']
            and helper.state_sha(model)==aux_initial['persistent_state_sha256'],'same full scratch initialization as AUX')
    dataset=runtime.BCSPDataset(q['data_root'],selected,fold['train_sources'],8192)
    budget.first_step_evidence=dict(factory=evidence,H2_head_initialization='ALL_ZERO_NO_RNG_DRAW',AUX_initialization_exact_match=True,AUX_initialization_sha256=q['aux_pairing']['initialization']['sha256'])
    budget.run_identity=dict(stage=q['stage'],variant='M0',fold='C',seed=0,H2=H2,
        numeric_policy_sha256=q['numeric_policy']['sha256'],CUDA_audit_sha256=q['cuda_audit']['sha256'],
        checkpoint_legacy_stage='BCSP_INPUT_DENSITY_V1',legacy_stage_is_provenance_only=True,
        SSM_gradient_non_bitwise_reproducibility_disclosed=True)
    return runtime.train_lifecycle(model,lambda e:runtime.make_loader(dataset,plan,e),selected,plan,q['output'],device=device,numeric_check=helper.assert_numeric,resources=budget,knn_enable=knn_enable,state_fingerprint=helper.state_sha)

def main():
    parser=argparse.ArgumentParser()
    for key in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):parser.add_argument('--'+key,required=True)
    args=parser.parse_args()
    def record(p,h):return dict(path=p,bytes=no_links(p).stat().st_size,sha256=h)
    qr=record(args.request,args.request_sha256)
    q,static,metadata,selected,fold,plan=authorize(qr,record(args.authorization,args.authorization_sha256),record(args.runtime,args.runtime_sha256))
    I=q['identity'];out=no_links(q['output']);root=no_links(q['model_root']);expected_factory=json_bound(q['initialization_reference'])['factory']
    require(sys.platform=='linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'Linux -I -S -B')
    require(socket.gethostname()==I['hostname'] and os.getuid()==I['uid'] and str(Path(sys.executable).resolve())==I['python_realpath'] and sys.version.split()[0]==I['python_version'],'identity')
    os.chdir(PROJECT);require(Path.cwd()==Path(PROJECT) and out.parent==Path(PROJECT+'/logs/cranial_bcsp_mamba_p2'),'project/output')
    require(exact(q['implementation']['entry'])==Path(__file__).absolute(),'entry origin')
    parent=Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    require(parent[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s'],'fixed external timeout')
    require(json.loads(no_links(q['launch_attempt']).read_bytes())==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']),'single attempt claim')
    for r in q['implementation'].values():exact(r)
    for r in q['dependencies']:exact(r)
    allowed=payload_paths(q['data_root'],selected)
    for p,h in allowed.items():require(p.is_file() and sha(p)==h,'payload drift')
    helper=load_bound('p1_training_gpu_helper',q['implementation']['preflight_helper']);helper._MONITOR=None
    scope=json_bound(q['preflight_scope']);sources=helper.source_map(scope)
    for rel,r in sources.items():helper.exact(root/rel,r['sha256'],r['bytes'])
    helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
    for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:helper.exact(r['path'],r['sha256'],r['bytes'])
    for k,v in q['environment'].items():require(os.environ.get(k)==v.replace('<owned_output>',str(out)),'environment '+k)
    gpu=[s.strip() for s in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    require(gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256,'idle GPU identity')
    require(out.is_dir() and {p.name for p in out.iterdir()}=={'launch.log'} and not (out/'launch.log').is_symlink(),'fresh launcher-only output')
    with (out/'worker.pid').open('x') as f:f.write(str(os.getpid())+'\n')
    utc_guard=None
    try:
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
        impl=Path(q['implementation']['entry']['path']).parent;factory_root=Path(q['implementation']['factory']['path']).parent
        sys.path[:0]=[str(impl),str(Path(q['implementation']['h2_range']['path']).parent),str(factory_root),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,sources))
        (out/'tmp').mkdir();require(os.environ.get('TMPDIR')==str(out/'tmp'),'TMPDIR')
        utc=load_bound('p1_training_exact_UTC',q['implementation']['timezone']);utc_guard=utc.ExactUTCReader(utc.UTC_RESOURCE)
        read_roots=[root,impl,Path(q['aux_pairing']['initialization']['path']),Path(q['implementation']['h2_range']['path']).parent,factory_root,envroot,provider,Path(q['implementation']['contract']['path']).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']
        sys.addaudithook(make_training_policy(helper,read_roots,out,allowed,utc_guard).audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
        require(torch.cuda.is_available() and torch.cuda.device_count()==1,'one CUDA device');torch.cuda.set_device(0);helper.configure_numeric(torch)
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');native=importlib.import_module('pointnet2_ops.pointnet2_utils');ext=importlib.import_module('pointnet2_ops._ext')
        require(str(Path(native.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(ext.__file__).resolve())==scope['bindings']['provider'][2]['path'],'native provider origins');helper.check_backend(chamfer,pn,native)
        model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr;transformer=importlib.import_module('models.Transformer_utils')
        require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'unchanged model config')
        load_bound('bcsp_h2_range_v1',q['implementation']['h2_range'])
        h2_adapter=load_bound('bcsp_h2_model_adapter_v1',q['implementation']['h2_adapter'])
        runtime=load_bound('p1_frozen_training_runtime',q['implementation']['runtime']);factory=load_bound('p1_frozen_model_factory',q['implementation']['factory'])
        require(Path(sys.modules['bcsp_mamba_encoder_v1'].__file__).resolve()==exact(q['implementation']['encoder']),'encoder origin')
        random.seed(0);np.random.seed(0);torch.manual_seed(0)
        budget=P1Budget(static['resources'],out,torch,helper)
        result=dispatch_training(q,static,selected,fold,plan,factory=factory,h2_adapter=h2_adapter,model_builder=lambda:model_class(EasyDict(static['model'])),runtime=runtime,helper=helper,budget=budget,torch=torch,knn_enable=transformer.enable_bcsp_knn,expected_factory=expected_factory)
        budget.local()
        files=[p for p in out.iterdir() if p.is_file() and p.name not in ('launch.log','worker.pid')]
        emit(out/'payload_manifest.json',dict(files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]));budget.local()
        return result
    except BaseException as exc:
        if not (out/'failure.json').exists() and not (out/'completion.json').exists():emit(out/'startup_failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)))
        raise
    finally:
        if utc_guard is not None:utc_guard.close()

if __name__=='__main__':main()
