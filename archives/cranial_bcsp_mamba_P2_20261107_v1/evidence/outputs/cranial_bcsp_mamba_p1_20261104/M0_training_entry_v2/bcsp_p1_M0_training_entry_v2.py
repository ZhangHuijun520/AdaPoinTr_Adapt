"""P1 dedicated M0 training entry; frozen T0 pairing required. Import is inert; execution needs separate hash authorization."""
import argparse,hashlib,importlib.util,json,os,random,shutil,socket,sys,time
from pathlib import Path,PurePosixPath

PROJECT='/home/jovyan/adapointr_work/PoinTr'
COUNTS=dict(cases=315,sources=63,batch=8,epochs=100,batches_per_epoch=39,updates=3900,exposures=31200)
RESOURCES=dict(wall_seconds=86400,RSS_bytes=8589934592,device_MiB=22528,torch_peak_bytes=21474836480,output_bytes=2147483648,minimum_free_disk_bytes=4294967296)
PINNED_IMPL=dict(contract='08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499',runtime='939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee',factory='59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4',encoder='5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8',preflight_helper='7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291',timezone='038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e')
PINNED_EVIDENCE=dict(numeric_policy='132d019ea9d7a1a6994ee19bf98ea6686b343b3325762f1080d64b6adb6c7cc8',numeric_protocol='cac5596a04fe08e9f81c9ba6ac8aa7b23457cb56b9a8d32eaefab9edb0b1099c',pair_contract='7f95f3f76bed106762685bd037e89bd241e8e8db8d7e5ee6c587f8e759bf0895',quantification_audit='87ddd30d6b5d58b5ba54c2e7878d6c75ccdecd9117f30d8972ea5c5a06d9193c')
T0_AUDIT_SHA='428702c74772018d12a6f25131834e0c370c9b712c51a31f45497e3694ed5e42'
T0_REQUEST_SHA='5235e9575bb3630a48efe5f11fffaf1a710d317cdd8eeacb96e665432436ad6b'
QUANT_REQUEST_SHA='af4685321cb0418703de90de474107cb31dd50d18ba4697e2751aca6cde34278'

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

def authorize(qr,ar,rr):
    q=json_bound(qr)
    fields={'schema','status','stage','run_id','variant','fold','n_input','n_output','static_config','QC','order_plan','identity','data_root','model_root','implementation','preflight_scope','dependencies','environment','output','launch_attempt','numeric_policy','numeric_protocol','pair_contract','quantification_audit','quantification_request','initialization_reference','launch_contract','provenance','not_authorized','t0_pairing'}
    require(set(q)==fields and q['schema']=='bcsp-p1-M0-training-request-v2' and q['stage']=='CRANIAL_BCSP_MAMBA_P1' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION','pending P1 request schema')
    require(q['variant']=='M0' and q['fold']=='C' and q['n_input']==q['n_output']==8192,'dedicated M0 Fold C only')
    a=json_bound(ar);r=json_bound(rr)
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-p1-training-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate execution authorization')
    require(r==dict(schema='bcsp-p1-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way runtime binding')
    require(set(q['implementation'])==set(PINNED_IMPL)|{'entry'},'implementation set')
    for k,h in PINNED_IMPL.items():require(q['implementation'][k]['sha256']==h,'frozen implementation '+k)
    for k,h in PINNED_EVIDENCE.items():require(q[k]['sha256']==h,'frozen evidence '+k);exact(q[k])
    policy=json_bound(q['numeric_policy'])
    require(policy['schema']=='bcsp-p1-confirmed-numeric-policy-v1' and policy['status']=='CONFIRMED_USER_DECISION_NOT_EXECUTION_AUTHORIZATION' and bool(policy['user_confirmation']) and policy['protocol_sha256']==q['numeric_protocol']['sha256'] and policy['quantification_audit_sha256']==q['quantification_audit']['sha256'] and policy['prior_v3_status']=='FAILED_STOP_NO_RETRY' and policy['bitwise_gradient_equality_required_for_training_preparation'] is False and policy['numeric_tolerance_gate_added'] is False and policy['deterministic_flags_changed'] is False and policy['training_execution_authorized'] is False,'confirmed policy without hidden numeric relaxation')
    audit=json_bound(q['quantification_audit'])
    require(q['quantification_request']['sha256']==QUANT_REQUEST_SHA and audit['request_sha256']==QUANT_REQUEST_SHA and audit['status']=='FORMAL_READONLY_POST_DIAGNOSTIC_FREEZE_AUDIT_PASS' and audit['checks_passed']==len(audit['checks'])>0 and all(audit['checks'].values()) and audit['counts']==dict(forward_attempts=12,forward_returns=12,loss_calls=4,backward_attempts=4,backward_returns=4,optimizer_steps=0) and audit['new_forward_calls']==audit['new_backward_calls']==audit['server_writes']==0,'actual frozen diagnostic evidence')
    parent=json_bound(q['quantification_request'])
    require(parent['identity']==q['identity'] and parent['model_root']==q['model_root'] and parent['data_root']==q['data_root'] and parent['batch'] and parent['dependencies']==q['dependencies'] and parent['preflight_scope']==q['preflight_scope'] and parent['environment']==q['environment'],'same tested environment and assets')
    for k in ('static_config','order_plan'):require(q[k]==parent[k],'parent '+k)
    for k in ('factory','encoder'):require(q['implementation'][k]==parent[k],'parent '+k)
    require(q['implementation']['runtime']==parent['training_runtime'] and q['implementation']['preflight_helper']==parent['helper'] and q['implementation']['timezone']==parent['timezone_implementation'],'tested implementation paths')
    require(q['initialization_reference']==parent['diagnostic_baselines']['M0'],'frozen native M0 construction identity')
    metadata=load_bound('bcsp_training_contract_v1',q['implementation']['contract'])
    static=metadata.validate_static(json_bound(q['static_config']))
    require(static['counts']==COUNTS and static['resources']==RESOURCES,'unchanged exact counts/resource thresholds')
    pair=json_bound(q['pair_contract'])
    require(pair['status']=='FROZEN_PREPARATION_NOT_EXECUTABLE' and pair['fold']=='C' and pair['seed']==0 and pair['arm_order']==['T0','M0'] and pair['counts']==dict(COUNTS,drop_events=300) and pair['resources']==RESOURCES and pair['model']==static['model'] and pair['training']==static['training'] and pair['numeric_policy_sha256']==q['numeric_policy']['sha256'],'pair contract unchanged')
    selected,fold=metadata.verify_qualified_receipt(json_bound(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],'C',8192)
    require(q['QC']['fold_binding']==parent['fold_binding'] and q['QC']['manifests']['8192']==parent['train_manifest'],'same fold and V1 manifest')
    plan=metadata.validate_order(json_bound(q['order_plan']),fold['train_case_ids'])
    validate_T0_pairing(q,static,metadata,plan)
    return q,static,metadata,selected,fold,plan

def validate_T0_pairing(q,static,metadata,plan):
    pairing=q['t0_pairing']
    require(set(pairing)=={'audit','request','construction','initialization','order','completion'},'exact T0 pairing fields')
    require(pairing['audit']['sha256']==T0_AUDIT_SHA and pairing['request']['sha256']==T0_REQUEST_SHA,'frozen T0 audit/request hashes')
    audit=json_bound(pairing['audit'])
    require(audit['status']=='FORMAL_P1_T0_POST_TRAINING_FREEZE_AUDIT_PASS' and audit['request_sha256']==T0_REQUEST_SHA and audit['checks_passed']==len(audit['checks'])>0 and all(audit['checks'].values()),'T0 formal training audit required')
    require(audit['counts']==dict(updates=3900,traversals=100,case_exposures=31200,drop_events=300,metric_records=3900,resource_records=3902) and audit['new_forward_calls']==audit['new_backward_calls']==audit['server_writes']==0 and audit['checkpoint_deserialized'] is False,'T0 frozen counts and read-only audit')
    audited={r['path']:{k:r[k] for k in ('path','bytes','sha256')} for r in audit['files']}
    for key in ('request','construction','initialization','order','completion'):
        record=pairing[key];require(audited.get(record['path'])==record,'T0 audit content binding '+key);exact(record)
    t0=json_bound(pairing['request'])
    require(t0['schema']=='bcsp-p1-training-request-v1' and t0['variant']=='T0' and t0['fold']=='C' and t0['n_input']==t0['n_output']==8192,'frozen T0 arm identity')
    for key in ('static_config','QC','order_plan','identity','data_root','model_root','preflight_scope','dependencies','environment','numeric_policy','numeric_protocol','pair_contract','quantification_audit','quantification_request'):
        require(q[key]==t0[key],'paired frozen field '+key)
    require(all(q['implementation'][k]==v for k,v in t0['implementation'].items() if k!='entry'),'paired reused implementation')
    t0_factory=json_bound(pairing['construction'])['factory'];m0_factory=json_bound(q['initialization_reference'])['factory']
    require(t0_factory['variant']=='T0' and m0_factory['variant']=='M0' and t0_factory['seed']==m0_factory['seed']==0 and t0_factory['replaced_global_branches']==0 and m0_factory['replaced_global_branches']==6 and not t0_factory['artificial_fixture'] and not m0_factory['artificial_fixture'],'native T0/M0 construction identities')
    require(t0_factory['common_state_unchanged'] and m0_factory['common_state_unchanged'] and bool(t0_factory['common_state']) and t0_factory['common_state']==m0_factory['common_state'],'exact T0/M0 shared initial state')
    initial=json_bound(pairing['initialization']);complete=json_bound(pairing['completion'])
    require(audit['initialization']['persistent_state_matches_GPU_replay'] is True and audit['initialization']['shared_initialization_metadata_matches'] is True and initial==audit['initialization']['record'] and initial['seed']==0,'audited T0 initialization')
    require(json_bound(pairing['order'])==plan and audit['order']['canonical_sha256']==metadata.canonical_sha(plan)==initial['order_sha256']==complete['order_sha256'] and audit['order']['raw_frozen_sha256']==q['order_plan']['sha256'] and audit['order']['all_actual_batches_verified'] is True,'same frozen and actual T0 order')
    require(complete['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100) and complete['optimizer_updates']==3900 and complete['traversals']==100 and complete['case_exposures']==31200 and complete['checkpoint_sha256']==audit['checkpoint']['sha256'] and complete['bncal_executed'] is False and complete['evaluation_executed'] is False and complete['resume'] is False,'T0 completion pairing; no checkpoint loading')

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

def dispatch_training(q,static,selected,fold,plan,*,factory,model_builder,runtime,helper,budget,torch,knn_enable,expected_factory,device='cuda:0'):
    require(q['variant'] in ('T0','M0'),'model dispatch variant')
    model,evidence=factory.build_model(model_builder,q['variant'],seed=0)
    require(evidence==expected_factory and not evidence['artificial_fixture'],'frozen real initialization')
    helper.validate_model(model)
    dataset=runtime.BCSPDataset(q['data_root'],selected,fold['train_sources'],q['n_input'])
    budget.first_step_evidence=dict(factory=evidence)
    budget.run_identity=dict(stage=q['stage'],variant=q['variant'],fold=q['fold'],seed=0,numeric_policy_sha256=q['numeric_policy']['sha256'],quantification_audit_sha256=q['quantification_audit']['sha256'],prior_v3_status='FAILED_STOP_NO_RETRY',checkpoint_legacy_stage='BCSP_INPUT_DENSITY_V1',legacy_stage_is_provenance_only=True,SSM_gradient_non_bitwise_reproducibility_disclosed=True)
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
    os.chdir(PROJECT);require(Path.cwd()==Path(PROJECT) and out.parent==Path(PROJECT+'/logs/cranial_bcsp_mamba_p1'),'project/output')
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
    require(gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256 and not helper.smi('pid',True),'idle GPU identity')
    require(out.is_dir() and {p.name for p in out.iterdir()}=={'launch.log'} and not (out/'launch.log').is_symlink(),'fresh launcher-only output')
    with (out/'worker.pid').open('x') as f:f.write(str(os.getpid())+'\n')
    utc_guard=None
    try:
        envroot=Path('/opt/conda/envs/adapointr-mamba');provider=Path(scope['bindings']['provider'][0]['path']).parent.parent
        impl=Path(q['implementation']['entry']['path']).parent;factory_root=Path(q['implementation']['factory']['path']).parent
        sys.path[:0]=[str(factory_root),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root);sys.meta_path.insert(0,helper.FiniteProjectImports(root,sources))
        (out/'tmp').mkdir();require(os.environ.get('TMPDIR')==str(out/'tmp'),'TMPDIR')
        utc=load_bound('p1_training_exact_UTC',q['implementation']['timezone']);utc_guard=utc.ExactUTCReader(utc.UTC_RESOURCE)
        read_roots=[root,impl,factory_root,envroot,provider,Path(q['implementation']['contract']['path']).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']
        sys.addaudithook(make_training_policy(helper,read_roots,out,allowed,utc_guard).audit)
        import numpy as np
        import torch,timm,yaml,importlib
        from easydict import EasyDict
        require((torch.__version__,np.__version__,timm.__version__)==(I['torch_version'],I['numpy_version'],I['timm_version']),'versions')
        require(torch.cuda.is_available() and torch.cuda.device_count()==1,'one CUDA device');torch.cuda.set_device(0);helper.configure_numeric(torch)
        chamfer=importlib.import_module('extensions.chamfer_dist');pn=importlib.import_module('utils.pointnet2_utils');native=importlib.import_module('pointnet2_ops.pointnet2_utils');ext=importlib.import_module('pointnet2_ops._ext')
        require(str(Path(native.__file__).resolve())==scope['bindings']['provider'][1]['path'] and str(Path(ext.__file__).resolve())==scope['bindings']['provider'][2]['path'],'native provider origins');helper.check_backend(chamfer,pn,native)
        model_class=importlib.import_module('models.AdaPoinTr').AdaPoinTr;transformer=importlib.import_module('models.Transformer_utils')
        require(static['model']==yaml.safe_load((root/'base_model.yaml').read_text())['model'],'model config')
        runtime=load_bound('p1_frozen_training_runtime',q['implementation']['runtime']);factory=load_bound('p1_frozen_model_factory',q['implementation']['factory'])
        require(Path(sys.modules['bcsp_mamba_encoder_v1'].__file__).resolve()==exact(q['implementation']['encoder']),'encoder origin')
        random.seed(0);np.random.seed(0);torch.manual_seed(0)
        budget=P1Budget(static['resources'],out,torch,helper)
        result=dispatch_training(q,static,selected,fold,plan,factory=factory,model_builder=lambda:model_class(EasyDict(static['model'])),runtime=runtime,helper=helper,budget=budget,torch=torch,knn_enable=transformer.enable_bcsp_knn,expected_factory=expected_factory)
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
