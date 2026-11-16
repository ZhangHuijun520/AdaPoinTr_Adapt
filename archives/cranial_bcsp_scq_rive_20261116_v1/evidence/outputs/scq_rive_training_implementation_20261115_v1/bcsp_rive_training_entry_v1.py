"""RIVE mode A training caller. Inert stdlib import; no model/runtime modification."""
import argparse,hashlib,importlib.util,json,os,random,shlex,shutil,socket,sys
from pathlib import Path,PurePosixPath



PROJECT='/home/jovyan/adapointr_work/PoinTr'
COUNTS={'cases': 315, 'sources': 63, 'batch': 8, 'epochs': 100, 'batches_per_epoch': 39, 'updates': 3900, 'exposures': 31200}
LEGACY_RESOURCES={'wall_seconds': 86400, 'RSS_bytes': 8589934592, 'device_MiB': 22528, 'torch_peak_bytes': 21474836480, 'output_bytes': 2147483648, 'minimum_free_disk_bytes': 4294967296}
RESOURCES={'wall_seconds': 3600, 'RSS_bytes': 8589934592, 'device_MiB': 22528, 'torch_peak_bytes': 21474836480, 'output_bytes': 2147483648, 'minimum_free_disk_bytes': 4294967296}
PINS={'encoder': '5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8', 'factory': '59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4', 'lqi_decoder': '92a52949ec037edd13bac7bfae7395bfafad84c5ffc204e1d178ea1f68507ea8', 'lqi_factory': '56d4cbe89660106f255a0d58e28c7cbaf38374c7788219d5a21779bd97aaf106', 'scq_residual': '2f3a86c5daf7ad00c01dc405b4a3b7011faae06f5766da3dcfe72d645b730404', 'scq_factory': 'fe5f7229aa40ba2b7e599c2bea32982f6bb33cf5f1db115b222a581c1d4af1c5', 'timezone': '038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e', 'runtime': '939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee', 'contract': '08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499', 'budget_parent': '095cabb0ab9b098172840432d40699dd18279671cf650894fab9eb9b54575ebe', 'preflight_helper': '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291', 'native_helper': 'b1c4bee971e73c297ce1a9e22a21ef5da69cc6891fba110a6fc2544819362309', 'cuda_entry': 'b78485c06dd94ca6e54b918f6c5b3ea055f6feebf5d935920d6da9dae4497999', 'rf_residual': 'c50cbdb0986fafe3ff2309ef8c02d74fdc5e651218c71f4bb13a87bacefc726a', 'rf_factory': '6e243f7a6463241f6c24c6feb6928bde9499ffd3a17afe1442eca54fd6738570'}
IDENTITY={'hostname': 'shu-common-25721452-notebook-qx2k0r-0', 'uid': 1000, 'project': '/home/jovyan/adapointr_work/PoinTr', 'gpu_uuid': 'GPU-383d118a-368c-94e3-166a-cad3efab8fd7', 'gpu_name': 'NVIDIA GeForce RTX 4090 D', 'driver_version': '570.190', 'nvidia_smi_memory_total_MiB': 24564, 'python_realpath': '/opt/conda/envs/adapointr-mamba/bin/python3.10', 'python_version': '3.10.20', 'torch_version': '2.4.1+cu118', 'numpy_version': '2.2.6', 'timm_version': '1.0.27', 'memory_query_semantics': 'SMI physical UUID/rounded memory separate from torch logical cuda:0/properties. Do not demand byte equality between the two interfaces; require one visible logical device mapped via the fixed UUID and record torch capacity.', 'torch_cuda_version': '11.8'}
COMMON_SHA='b7e5b640c1f0e709ab6697139db1267584266a51b4e0e29f2d5217bfd1236cc5'
INITIAL_STATE={'parameter_sha256': '8697bfc3b9d7dfd2c0003ec54253cf77cd146f2926a41138ffeacc1ec4f7d255', 'persistent_state_sha256': 'd0f4c3699fe66a2ba2b4879c1bd41ba363a325fa152d79a4055773be3e0f4167', 'seed': 0}
NATIVE_AUDIT_SHA='100770541377b1473c9cb8610375c9e2de336cb702e60189cb0ffb68194f2697'


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
    cmd = ['/usr/bin/timeout','--signal=TERM','--kill-after=5s','3600s',q['identity']['python_realpath'],'-I','-S','-B',
           q['implementation']['entry']['path'],'--request',L['request_path'],'--request-sha256',qsha,
           '--authorization',L['authorization_path'],'--authorization-sha256',asha,'--runtime',L['runtime_path'],'--runtime-sha256',rsha]
    env = '\n'.join('export '+k+'='+shlex.quote(v.replace('<owned_output>',str(out))) for k,v in q['environment'].items())
    return '#!/bin/bash\nset -eu\numask 077\ncd '+shlex.quote(PROJECT)+'\nmkdir -p '+shlex.quote(str(out.parent))+'\nmkdir '+shlex.quote(str(out))+'\n'+env+'\nset +e\n'+shlex.join(cmd)+' >'+shlex.quote(str(out/'launch.log'))+' 2>&1\nrc=$?\nset -e\nprintf "%s\\n" "$rc" >'+shlex.quote(str(out/'exit_code.txt'))+'\nexit "$rc"\n'

def startup_smi_identity_query(helper,q,out):
    out=no_links(out)
    require(out==no_links(q['output']) and out.is_dir(),'owned startup monitor output')
    try:
        return helper.smi('uuid,name,driver_version,memory.total,memory.used')
    except helper.MonitorQueryFailure as exc:
        details=exc.details
        require(len(json.dumps(details,allow_nan=False).encode('utf-8'))<=16384,'bounded monitor diagnostic details')
        emit(out/'startup_monitor_failure.json',dict(status='FAILED_STOP_NO_RETRY',stage='startup_smi_identity',run_id=q['run_id'],current_gpu_uuid=q['identity']['gpu_uuid'],CUDA_VISIBLE_DEVICES=q['environment']['CUDA_VISIBLE_DEVICES'],details=details))
        raise


def validate_reuse(q):
    require(q['identity']==IDENTITY,'exact current resource binding')
    require(q['environment']['CUDA_VISIBLE_DEVICES']==IDENTITY['gpu_uuid'],'exact current GPU selector')
    audit=bound(q['native_reference'])
    require(q['native_reference']['sha256']==NATIVE_AUDIT_SHA and audit['status']=='FORMAL_RF_STATIC_D_TRAINING_PAIR_FREEZE_AUDIT_PASS' and audit['identity']==IDENTITY,'reuse exact successful current-device native training')
    require(audit['check_count']==56 and all(audit['checks'].values()) and (audit['updates'],audit['traversals'],audit['exposures'],audit['drops'])==(3900,100,31200,300),'complete native evidence')
    require(not any(audit[k] for k in ('BNCal','evaluation','resume')),'native evidence boundaries')
    require(q['expected_model_initialization']==INITIAL_STATE=={k:audit['initialization'][k] for k in INITIAL_STATE} and audit['common_initial_state_SHA256']==COMMON_SHA,'frozen full initialization')
    ready=bound(q['reuse_evidence'])
    require(ready['status']=='READONLY_R01_REVIEW_COMPLETE_MINIMAL_ENTRY_ADAPTATION_AND_MATRIX_CAPACITY_PENDING' and ready['mode']=='A_4_RUN_ONLY','finite R01 evidence')
    require(ready['historical_CUDA_reference']['sha256']==NATIVE_AUDIT_SHA and ready['bindings']['verified_records']==60 and ready['bindings']['all_match'] is True,'bound native and source evidence')
    records={r['path']:r for r in ready['bindings']['records']}
    for key,r in q['implementation'].items():
        if key not in ('entry','bridge'):
            require(key in PINS and r['sha256']==PINS[key],'unchanged implementation '+key)
            require(all(records[r['path']][k]==r[k] for k in ('bytes','sha256')),'R01 source '+key)
    for key in ('initialization','rf_initialization','static_config','preflight_scope'):
        r=q[key];require(all(records[r['path']][k]==r[k] for k in ('bytes','sha256')),'R01 frozen '+key)
    for r in q['dependencies']:
        require(all(records[r['path']][k]==r[k] for k in ('bytes','sha256')),'R01 exact dependency')
    return dict(status='RIVE_FROZEN_NATIVE_EVIDENCE_REUSED',arm=q['arm'],fold=q['fold'],seed=0,native_reference_sha256=NATIVE_AUDIT_SHA,new_preflight_performed=False),COMMON_SHA


def validate_pair(q):
    pair=bound(q['pair_contract'])
    require(pair['status']=='FROZEN_RIVE_MODE_A_PAIRING_NOT_EXECUTION_AUTHORIZATION' and pair['execution_authorized'] is False,'pair scope not execution')
    require(pair['arm_order']==['Static_C','Requery_C','Static_D','Requery_D'] and pair['seed']==0 and pair['mode']=='A' and pair['counts']==COUNTS and pair['resources']==RESOURCES,'four-run same3900 contract')
    for k in ('identity','environment','model_root','implementation_core','initialization','rf_initialization','expected_model_initialization','static_config','preflight_scope','dependencies'):
        actual={n:r for n,r in q['implementation'].items() if n not in ('entry','bridge')} if k=='implementation_core' else q[k]
        require(pair[k]==actual,'pair immutable '+k)
    assets=pair['Fold'+q['fold']]
    require(all(q[k]==assets[k] for k in ('QC','order_plan','data_root')),'exact fold assets')
    if q['arm']=='RF-Static':
        require(q['paired_baseline'] is None,'Static starts an independent scratch pair')
    else:
        r=q['paired_baseline'];require(isinstance(r,dict) and set(r)=={'freeze'},'Requery requires own RIVE Static freeze')
        a=bound(r['freeze'])
        require(a['status']=='FORMAL_RIVE_POST_TRAINING_FREEZE_AUDIT_PASS' and all(a['checks'].values()),'RIVE paired audit')
        require(a['arm']=='RF-Static' and a['fold']==q['fold'] and a['seed']==0 and a['identity']==q['identity'],'same fold device baseline')
        require(a['pair_contract_sha256']==q['pair_contract']['sha256'] and a['expected_model_initialization']==INITIAL_STATE and a['order_plan']==q['order_plan'] and a['resources']==RESOURCES,'paired init order budget')
        require((a['updates'],a['traversals'],a['exposures'],a['drops'])==(3900,100,31200,300) and not any(a[k] for k in ('BNCal','evaluation','resume')),'paired counts')
    return pair


def authorize(qr,ar,rr):
    q=bound(qr);a=bound(ar);runtime=bound(rr)
    fields={'schema','status','execution_authorized','stage','mode','run_id','arm','variant','fold','seed','n_input','n_output','static_config','QC','order_plan','identity','data_root','model_root','implementation','preflight_scope','dependencies','environment','output','launch_attempt','launch_contract','reuse_evidence','native_reference','pair_contract','initialization','rf_initialization','expected_model_initialization','P3','resources','science','paired_baseline','capacity'}
    require(set(q)==fields,'RIVE request exact fields')
    require(q['schema']=='bcsp-rive-training-request-v1' and q['stage']=='CRANIAL_BCSP_SCQ_RIVE' and q['mode']=='A' and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False,'new pending RIVE request')
    require(q['arm']==q['variant'] and q['arm'] in ('RF-Static','RF-Requery') and q['fold'] in ('C','D') and q['seed']==0 and q['n_input']==q['n_output']==8192,'modeA scientific arm')
    tag='Static' if q['arm']=='RF-Static' else 'Requery'
    require(q['run_id'].startswith('SCQ_RIVE_'+tag+'_fold'+q['fold']+'_seed0_train_') and PurePosixPath(q['output']).name==q['run_id'],'new RIVE run only')
    require(set(a)=={'schema','request_sha256','explicit_user_authorization','user_authorization_text'} and a['schema']=='bcsp-rive-training-authorization-v1' and a['request_sha256']==qr['sha256'] and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()),'separate full hash authorization')
    require(runtime==dict(schema='bcsp-rive-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']),'one-way authorization runtime')
    require(set(q['implementation'])==set(PINS)|{'entry','bridge'},'finite source set')
    for k,r in q['implementation'].items():
        if k in PINS:require(r['sha256']==PINS[k],'frozen source '+k)
        exact(r)
    p3=bound(q['P3'])
    require(p3['status']=='RIVE_TRAINING_ENTRY_LOCAL_P3_PASS' and p3['entry_sha256']==q['implementation']['entry']['sha256'] and p3['bridge_sha256']==q['implementation']['bridge']['sha256'] and all(p3['checks'].values()),'RIVE local P3')
    admission,common=validate_reuse(q);validate_pair(q)
    exact(q['initialization']);exact(q['rf_initialization'])
    metadata=source_module('bcsp_training_contract_v1',q['implementation']['contract'])
    static=metadata.validate_static(bound(q['static_config']))
    require(static['counts']==COUNTS and static['resources']==LEGACY_RESOURCES and q['resources']==RESOURCES,'legacy unchanged, effective3600 distinct')
    require(q['science']==dict(folds=['C','D'],arms=['RF-Static','RF-Requery'],input=8192,output=8192,seed=0,updates=3900,traversals=100,exposures=31200,drops=300,from_scratch=True,BNCal=False,evaluation=False,resume=False,retry=False),'frozen RIVE science')
    require(q['capacity']['scope']=='FIRST_SINGLE_RUN_ONLY' and q['capacity']['matrix_capacity_certified'] is False,'no false matrix capacity approval')
    selected,fold=metadata.verify_qualified_receipt(bound(q['QC']['qualified_receipt']),q['QC']['verification'],q['QC']['manifests'],q['QC']['fold_binding'],q['fold'],8192)
    plan=metadata.validate_order(bound(q['order_plan']),fold['train_case_ids'])
    require(PurePosixPath(q['data_root']).parent==PurePosixPath(PROJECT)/'data' and PurePosixPath(q['model_root']).parent==PurePosixPath(PROJECT)/'third_party','explicit project roots')
    require(PurePosixPath(q['output']).parent==PurePosixPath(PROJECT)/'logs/cranial_bcsp_fullmamba','output boundary')
    controls=PurePosixPath(q['implementation']['entry']['path']).parent/'control'/q['run_id']
    expected=dict(request_path=str(PurePosixPath(q['implementation']['entry']['path']).parent/(q['run_id']+'_execution_request_v1.json')),authorization_path=str(controls/'authorization_v1.json'),runtime_path=str(controls/'runtime_v1.json'),launcher_path=str(controls/'launch_once_v1.sh'),tmux_session=q['run_id'])
    require(q['launch_contract']==expected and q['launch_attempt']==str(controls/'attempt_claim_v1.json'),'fresh fixed POSIX control paths')
    return q,static,metadata,selected,fold,plan,admission,common


def scq_geometry(model,ret):
    import torch
    result=geometry_record(torch,ret);info=model.base_model._scq_last_info
    require(hasattr(model.base_model,'rf') and model.base_model.rf.variant in ('RF-Static','RF-Requery'),'Requery logging model')
    require(torch.equal(info['Qused'],ret[0].detach()),'Q2 training return identity')
    if model.base_model.rf.variant=='RF-Static':require(torch.equal(info['N0'],info['N1']),'Static must reuse N0')
    def position(t):
        t=t.detach();center=t.mean(1)
        return dict(centroid=center.cpu().tolist(),radius=((t-center[:,None])**2).sum(-1).mean(1).sqrt().cpu().tolist())
    def delta(t):
        t=t.detach();norm=t.square().sum(-1).sqrt()
        return dict(centroid=t.mean(1).cpu().tolist(),mean_norm=norm.mean(1).cpu().tolist(),max_norm=norm.max(1).values.cpu().tolist())
    with torch.no_grad():
        result.update(Q0=position(info['Q0']),Q1=position(info['Q1']),Q2=position(info['Qused']),delta=delta(info['delta']),delta0=delta(info['delta0']),delta1=delta(info['delta1']),N0_N1_equal=bool(torch.equal(info['N0'],info['N1'])),neighbor_set_overlap=((info['N0'][...,None]==info['N1'][...,None,:]).any(-1).float().mean((1,2))).cpu().tolist())
    return result

def dispatch_training(q,selected,fold,plan,*,factory,model_builder,runtime,bridge,admission,expected_common,helper,budget,torch,knn_enable,device='cuda:0',artificial_cpu=False):
    require((device=='cpu') is artificial_cpu,'CPU only explicit artificial contract')
    model,evidence=factory(model_builder,q['variant'],q['initialization'],q['rf_initialization'])
    require(evidence['parent']['parent']['artificial_fixture'] is artificial_cpu,'native factory or explicit fixture')
    helper.validate_model(model)
    require(hasattr(model.base_model,'rf') and model.base_model.rf.variant==q['arm'],'Static second head required')
    require(evidence['rf']['variant']==q['arm'] and evidence['rf']['additional_parameters']==231171,'frozen RF head')
    if not artificial_cpu:require(evidence['rf']['total_parameters']==40827847 and sum(p.numel() for p in model.parameters())==40827847,'native Requery parameter count')
    common={n:helper.tensor_sha(t) for n,t in model.state_dict().items() if not n.startswith('base_model.rf.')}
    common_sha=hashlib.sha256(json.dumps(common,sort_keys=True).encode()).hexdigest()
    require(common_sha==expected_common,'same admitted common initialization')
    if not artificial_cpu:
        require(helper.state_sha(model,True)==q['expected_model_initialization']['parameter_sha256'] and helper.state_sha(model)==q['expected_model_initialization']['persistent_state_sha256'],'same frozen RF initial parameters and buffers; D order is separate')
    budget.first_step_evidence=dict(factory=evidence,common_initial_state_SHA256=common_sha,variant=q['variant'],arm=q['arm'],stage=q['stage'])
    _,group_rows=runtime.optimizer_groups(model)
    expected_new={'base_model.scq.W1.weight':.0005,'base_model.scq.W2.weight':.0005,'base_model.scq.W1.bias':0.,'base_model.scq.W2.bias':0.}
    expected_new.update({'base_model.rf.V1.weight':.0005,'base_model.rf.V2.weight':.0005,'base_model.rf.V1.bias':0.,'base_model.rf.V2.bias':0.})
    actual_new={r['name']:r['weight_decay'] for r in group_rows if r['name'].startswith(('base_model.scq.','base_model.rf.'))}
    require(actual_new==expected_new,'original optimizer handles exact new weights/biases')
    budget.first_step_evidence['new_optimizer_groups']=actual_new
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
        return bridge.train_lifecycle(runtime,q['implementation']['runtime']['sha256'],model,lambda epoch:runtime.make_loader(dataset,plan,epoch),selected,plan,q['output'],admission=admission,device=device,numeric_check=helper.assert_numeric,resources=budget,knn_enable=knn_enable,state_fingerprint=helper.state_sha)
    finally:
        for h in hooks:h.remove()

def make_budget(parent,limits,out,torch,helper,q,plan):
    class SCQBudget(parent.TrainingBudget):
        def before_step(self,step):
            super().before_step(step)
            if step==0:
                emit(self.output/'model_construction.json',self.first_step_evidence)
                emit(self.output/'run_identity.json',dict(stage=q['stage'],arm=q['arm'],variant=q['variant'],fold=q['fold'],seed=0,mode='A',pair_contract_sha256=q['pair_contract']['sha256'],native_reference_sha256=NATIVE_AUDIT_SHA,effective_resources=q['resources'],legacy_resources=LEGACY_RESOURCES,checkpoint_legacy_stage='BCSP_INPUT_DENSITY_V1',legacy_stage_is_provenance_only=True,SSM_gradient_non_bitwise_reproducibility_disclosed=True))
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

def startup_read_records(q):
    """Finite request-bound source set; deduplicate exact identities, reject conflicts."""
    records={}
    for r in [*q['implementation'].values(),q['initialization'],q['rf_initialization']]:
        p=str(no_links(r['path']))
        if p in records:
            require(records[p]['bytes']==r['bytes'] and records[p]['sha256']==r['sha256'],'conflicting startup read identity: '+p)
        else:records[p]=r
    return list(records.values())

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
    require(parent_args[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','3600s'],'external timeout')
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
    gpu=[s.strip() for s in startup_smi_identity_query(helper,q,out)[0].split(',')]
    require(gpu[:4]==[I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4])<=256,'GPU identity and idle')
    require(out.is_dir() and {p.name for p in out.iterdir()}=={'launch.log'},'fresh output')
    require(shutil.disk_usage(out).free >= RESOURCES['output_bytes'] + RESOURCES['minimum_free_disk_bytes'], 'single-run output plus safety space')
    with (out/'worker.pid').open('x') as f:f.write(str(os.getpid())+'\n')
    timezone=source_module('scq_training_timezone',q['implementation']['timezone']);utc=timezone.ExactUTCReader(timezone.UTC_RESOURCE)
    guard=cuda_entry.ExactSCQReads(native.ExactSourceReads(q['implementation']),startup_read_records(q))
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
        source_module('bcsp_scq_factory_v1',q['implementation']['scq_factory']);source_module('bcsp_scq_rf_residual_v1',q['implementation']['rf_residual'])
        factory=source_module('bcsp_scq_rf_factory_v1',q['implementation']['rf_factory']);bridge=source_module('bcsp_scq_training_bridge_v1',q['implementation']['bridge']);runtime=source_module('scq_parent_training_runtime',q['implementation']['runtime'])
        random.seed(0);np.random.seed(0);torch.manual_seed(0)
        budget=make_budget(parent,q['resources'],out,torch,helper,q,plan)
        result=dispatch_training(q,selected,fold,plan,factory=factory.build_model,model_builder=lambda:cls(EasyDict(static['model'])),runtime=runtime,bridge=bridge,admission=admission,expected_common=common,helper=helper,budget=budget,torch=torch,knn_enable=transformer.enable_bcsp_knn)
        budget.local();emit(out/'payload_manifest.json',dict(files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ('launch.log','worker.pid')]))
        return result
    except BaseException as exc:
        if not (out/'failure.json').exists() and not (out/'completion.json').exists():emit(out/'startup_failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)))
        raise
    finally:guard.close();utc.close()

if __name__=='__main__':main()
