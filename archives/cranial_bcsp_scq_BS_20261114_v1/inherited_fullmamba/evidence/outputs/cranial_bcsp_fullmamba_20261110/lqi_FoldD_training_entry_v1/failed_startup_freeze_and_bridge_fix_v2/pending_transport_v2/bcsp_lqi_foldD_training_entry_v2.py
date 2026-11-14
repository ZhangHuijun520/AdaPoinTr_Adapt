"""F0 Fold C only. Inert stdlib import; separate exact-hash authorization to train."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import random
import shlex
import socket
import sys

PROJECT = '/home/jovyan/adapointr_work/PoinTr'
ADMISSION_SHA = '5bcb2cff36e02e14acd4609e601fbc6d63aa776489ea2dda1b887f6b180de770'
CUDA_REQUEST_SHA = 'd1324b1b754e2eea91e00ea5ede802c6bd506815b82db82f3c41a070811e9812'
FOLDC_AUDIT_SHA = '17a45cb85282051a4448e31d8e9fe38b8d291c836c52cd7cf3e87320d7864291'
FOLDC_REQUEST_SHA = 'b616a762783fd4f43af4467c6c47e41e73aa40a24fac223317e710ee7372825e'
FOLDD_REFERENCE_SHA = '55793bca2fa9472d45b3cca0b9598154cdb12a84a3eb89633daa52b85a039d5f'
COUNTS = dict(cases=315,sources=63,batch=8,epochs=100,batches_per_epoch=39,updates=3900,exposures=31200)
RESOURCES = dict(wall_seconds=86400,RSS_bytes=8589934592,device_MiB=22528,torch_peak_bytes=21474836480,
                 output_bytes=2147483648,minimum_free_disk_bytes=4294967296)
PINS = dict(factory='59ce47093ce97c217dfe46d7075e460e798fe552adaeec54740c75d84ce405e4',
 encoder='5c5d32ccaead239ca4db542a8041f0f81ac1596e8f5c6519788a879642111bd8',
 lqi_factory='56d4cbe89660106f255a0d58e28c7cbaf38374c7788219d5a21779bd97aaf106',
 lqi_decoder='92a52949ec037edd13bac7bfae7395bfafad84c5ffc204e1d178ea1f68507ea8',
 bridge='37946f9f04e20718adee4fe2559ffe9bc3446977d3341197bca19600e6064a8c',
 runtime='939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee',
 contract='08a9af361ef0279cfccf27f9d094020501bfcc9859692ca64322d8dd4c7fd499',
 budget_parent='095cabb0ab9b098172840432d40699dd18279671cf650894fab9eb9b54575ebe',
 preflight_helper='7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291',
 timezone='038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e')


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


def validate_admission(q):
    a = q['admission']
    require(set(a) == {'receipt','audit','construction','completion','request'}, 'admission fields')
    require(a['receipt']['sha256'] == ADMISSION_SHA and a['request']['sha256'] == CUDA_REQUEST_SHA, 'actual native admission anchors')
    receipt = bound(a['receipt']); audit = bound(a['audit']); cuda = bound(a['request'])
    # A copied proof retains original provenance paths. Compare content hashes; never open Windows provenance on Linux.
    require(receipt['status'] == 'LQI_NATIVE_CUDA_ADMISSION_PASS' and receipt['request_sha256'] == CUDA_REQUEST_SHA
            and receipt['audit']['sha256'] == a['audit']['sha256'] and receipt['audit']['bytes'] == a['audit']['bytes'], 'receipt/audit chain')
    require(audit['status'] == 'FORMAL_LQI_POST_CUDA_FREEZE_AUDIT_PASS' and audit['request_sha256'] == CUDA_REQUEST_SHA
            and audit['check_count'] == len(audit['checks']) > 0 and all(audit['checks'].values()), 'formal audit pass')
    expected = dict(full_forward=2,full_backward=2,full_loss=2,decoder_forward=0,decoder_backward=0,optimizer_steps=0)
    require(audit['counts'] == receipt['scope'] == expected, 'actual GPU scope')
    rows = {r['name']:r for r in audit['output_hashes']}
    for key, name in [('construction','construction.json'),('completion','completion.json')]:
        r = rows[name]
        require((r['bytes'],r['sha256']) == (a[key]['bytes'],a[key]['sha256']), 'audited content: '+key)
    complete = bound(a['completion']); construction = bound(a['construction'])['factory']
    require(complete['counts'] == expected and complete['request_sha256'] == CUDA_REQUEST_SHA
            and not complete['optimizer_constructed'] and complete['real_data_reads'] == complete['checkpoint_loads'] == 0,
            'completion identity')
    for key in ('factory','encoder','lqi_factory','lqi_decoder'):
        require(q['implementation'][key] == receipt['implementation'][key] == cuda['implementation'][key], 'tested model binding: '+key)
    for key in ('identity','model_root','preflight_scope','dependencies','environment','static_config'):
        require(q[key] == cuda[key], 'same admitted environment: '+key)
    require(construction['artificial_fixture'] is False and construction['version'] == 'F0-LQI-implementation-v1', 'native F0 construction')
    return receipt, construction


def validate_FoldC_and_reference(q, expected_factory):
    p = q['FoldC_pairing']
    require(set(p) == {'audit','request','construction','initialization','order','completion'}, 'FoldC evidence fields')
    require(p['audit']['sha256'] == FOLDC_AUDIT_SHA and p['request']['sha256'] == FOLDC_REQUEST_SHA, 'frozen FoldC anchors')
    audit = bound(p['audit']); prior = bound(p['request'])
    require(audit['status'] == 'FORMAL_LQI_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS' and audit['request_sha256'] == FOLDC_REQUEST_SHA
            and audit['checks_passed'] == len(audit['checks']) > 0 and all(audit['checks'].values()), 'formal FoldC audit')
    require(audit['counts'] == dict(updates=3900,traversals=100,case_exposures=31200,drop_events=300,metric_records=3900,geometry_records=3900,resource_records=3902), 'completed FoldC counts')
    records = {r['name']:r for r in audit['artifacts'] if r['role'] == 0}
    for key,name in [('construction','model_construction.json'),('initialization','initialization.json'),('order','order_plan.json'),('completion','completion.json')]:
        require((p[key]['bytes'],p[key]['sha256']) == (records[name]['bytes'],records[name]['sha256']), 'audited FoldC '+key)
        exact(p[key])
    require(bound(p['construction'])['factory'] == expected_factory, 'same actual F0 initialization factory')
    initial = bound(p['initialization']); completed = bound(p['completion'])
    require(initial == audit['initialization'] and initial['seed'] == 0 and audit['initialization_matches_GPU_admission'] is True, 'complete initial replay identity')
    order = bound(p['order']); canonical = hashlib.sha256(json.dumps(order,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    require(canonical == initial['order_sha256'] == completed['order_sha256'] == audit['actual_order_canonical_sha256']
            and completed['checkpoint_sha256'] == audit['checkpoint']['sha256'], 'FoldC frozen order/checkpoint evidence without weight load')
    require(prior['fold'] == 'C' and prior['variant'] == q['variant'] and prior['static_config'] == q['static_config']
            and completed['bncal_executed'] is False and completed['evaluation_executed'] is False and completed['resume'] is False, 'FoldC protocol unchanged')
    require(q['FoldD_reference']['sha256'] == FOLDD_REFERENCE_SHA, 'frozen historical M0 D reference')
    reference = bound(q['FoldD_reference'])
    require(reference['variant'] == 'M0' and reference['fold'] == 'D' and reference['n_input'] == reference['n_output'] == 8192, 'historical FoldD identity')
    for key in ('static_config','QC','order_plan','data_root','model_root','preflight_scope'):
        require(q[key] == reference[key], 'exact same FoldD reference '+key)


def authorize(qr, ar, rr):
    q = bound(qr); a = bound(ar); r = bound(rr)
    fields = {'schema','status','stage','run_id','variant','fold','seed','n_input','n_output','static_config','QC',
              'order_plan','identity','data_root','model_root','implementation','preflight_scope','dependencies',
              'environment','output','launch_attempt','launch_contract','admission','readiness','pair_contract','P3','not_authorized','FoldC_pairing','FoldD_reference'}
    require(set(q) == fields and q['schema'] == 'bcsp-lqi-training-request-v1'
            and q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['stage'] == 'CRANIAL_BCSP_FULLMAMBA', 'pending F0 request')
    require(q['variant'] == 'F0-LQI-v1' and q['fold'] == 'D' and q['seed'] == 0 and q['n_input'] == q['n_output'] == 8192,
            'first F0 Fold C seed0 only')
    require(set(a) == {'schema','request_sha256','explicit_user_authorization','user_authorization_text'}
            and a['schema'] == 'bcsp-lqi-training-authorization-v1' and a['request_sha256'] == qr['sha256']
            and a['explicit_user_authorization'] is True and bool(a['user_authorization_text'].strip()), 'separate explicit execution authorization')
    require(r == dict(schema='bcsp-lqi-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']), 'one-way runtime')
    require(set(q['implementation']) == set(PINS)|{'entry'}, 'exact implementation set')
    for key, h in PINS.items():
        require(q['implementation'][key]['sha256'] == h, 'frozen implementation: '+key)
        exact(q['implementation'][key])
    exact(q['implementation']['entry']); p3 = bound(q['P3']); ready = bound(q['readiness'])
    require(p3['status'] == 'LQI_TRAINING_ENTRY_CPU_P3_PASS'
            and p3['entry_sha256'] == q['implementation']['entry']['sha256']
            and p3['native_admission_sha256'] == ADMISSION_SHA, 'entry P3 content binding')
    require(ready['status'] == 'LQI_FOLDD_METADATA_RESOURCE_READINESS_PASS' and ready['identity'] == q['identity']
            and ready['payload_arrays_read'] == 0, 'bounded readiness proof')
    receipt, expected_factory = validate_admission(q)
    validate_FoldC_and_reference(q,expected_factory)
    metadata = source_module('bcsp_training_contract_v1',q['implementation']['contract'])
    static = metadata.validate_static(bound(q['static_config']))
    require(static['counts'] == COUNTS and static['resources'] == RESOURCES, '3900/resource contract unchanged')
    selected, fold = metadata.verify_qualified_receipt(bound(q['QC']['qualified_receipt']), q['QC']['verification'],
            q['QC']['manifests'], q['QC']['fold_binding'], 'D',8192)
    plan = metadata.validate_order(bound(q['order_plan']),fold['train_case_ids'])
    pair = bound(q['pair_contract'])
    require(pair['status'] == 'FROZEN_LQI_CD_TRAINING_CONTRACT_NOT_AUTHORIZATION' and pair['counts'] == COUNTS
            and pair['resources'] == RESOURCES and pair['seed'] == 0 and pair['arm_order'] == ['C','D']
            and pair['static_config'] == q['static_config'] and pair['FoldD_QC'] == q['QC']
            and pair['FoldD_order_plan'] == q['order_plan'] and pair['native_admission_sha256'] == ADMISSION_SHA, 'fixed pair contract')
    return q, static, metadata, selected, fold, plan, receipt, expected_factory


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


def dispatch_training(q, selected, fold, plan, *, factory, model_builder, runtime, bridge, admission,
                      expected_factory, helper, budget, torch, knn_enable, device='cuda:0', artificial_cpu=False):
    require((device == 'cpu') is artificial_cpu, 'CPU allowed only explicit artificial contract')
    model, evidence = factory(model_builder)
    require(evidence == expected_factory and evidence['artificial_fixture'] is artificial_cpu, 'exact admitted initialization')
    helper.validate_model(model)
    dataset = runtime.BCSPDataset(q['data_root'],selected,fold['train_sources'],q['n_input'])
    budget.pending_geometry = None; budget.logged_geometry = 0
    total = sum(p.numel() for p in model.parameters())
    encoder = sum(p.numel() for p in model.base_model.encoder.parameters())
    decoder = sum(p.numel() for p in model.base_model.decoder.parameters())
    budget.first_step_evidence = dict(factory=evidence, parameters=dict(total=total,encoder=encoder,decoder=decoder,other=total-encoder-decoder))
    def capture(module, args, ret):
        require(module.training and len(args) == 1 and budget.pending_geometry is None, 'one GT-free training forward per step')
        budget.pending_geometry = geometry_record(torch,ret)
    hook = model.register_forward_hook(capture)
    try:
        return bridge.train_lifecycle(runtime,q['implementation']['runtime']['sha256'],model,
            lambda epoch:runtime.make_loader(dataset,plan,epoch),selected,plan,q['output'],
            admission=admission,device=device,numeric_check=helper.assert_numeric,resources=budget,
            knn_enable=knn_enable,state_fingerprint=helper.state_sha)
    finally:
        hook.remove()


def make_budget(parent, limits, out, torch, helper, q, plan):
    class F0Budget(parent.TrainingBudget):
        def before_step(self, step):
            super().before_step(step)
            if step == 0:
                emit(self.output/'model_construction.json',self.first_step_evidence)
                emit(self.output/'run_identity.json',dict(stage=q['stage'],variant=q['variant'],fold='D',seed=0,conditional_sequence='query_aligned_local_memory_interleaving',trace_prefix_suffix_semantics='interleaved conditional query-position output',
                    native_admission_sha256=ADMISSION_SHA,SSM_gradient_non_bitwise_reproducibility_disclosed=True,
                    checkpoint_legacy_stage='BCSP_INPUT_DENSITY_V1',legacy_stage_is_provenance_only=True))
        def after_step(self, step):
            require(self.pending_geometry is not None and self.logged_geometry == step-1, 'exact geometry count')
            epoch, batch = divmod(step-1,39)
            row = dict(step=step,epoch=epoch,batch=batch,case_ids=plan['epochs'][epoch]['batches'][batch],
                       coordinate_frame='D-only normalized, not world mm',geometry=self.pending_geometry)
            with (self.output/'LQI_geometry.jsonl').open('x' if step == 1 else 'a',encoding='ascii') as f:
                f.write(json.dumps(row,allow_nan=False)+'\n'); f.flush(); os.fsync(f.fileno())
            self.pending_geometry = None; self.logged_geometry += 1
            super().after_step(step)
        def before_final(self):
            require(self.logged_geometry == 3900 and self.pending_geometry is None, '3900 geometry rows')
            super().before_final()
    return F0Budget(limits,out,torch,helper)


def render_launcher(q, qsha, asha, rsha):
    for h in (qsha,asha,rsha):
        require(len(h) == 64 and all(c in '0123456789abcdef' for c in h), 'full hash')
    out = PurePosixPath(q['output']); L = q['launch_contract']
    cmd = ['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s',q['identity']['python_realpath'],'-I','-S','-B',
           q['implementation']['entry']['path'],'--request',L['request_path'],'--request-sha256',qsha,
           '--authorization',L['authorization_path'],'--authorization-sha256',asha,'--runtime',L['runtime_path'],'--runtime-sha256',rsha]
    env = '\n'.join('export '+k+'='+shlex.quote(v.replace('<owned_output>',str(out))) for k,v in q['environment'].items())
    return '#!/bin/bash\nset -eu\numask 077\ncd '+shlex.quote(PROJECT)+'\nmkdir -p '+shlex.quote(str(out.parent))+'\nmkdir '+shlex.quote(str(out))+'\n'+env+'\nset +e\n'+shlex.join(cmd)+' >'+shlex.quote(str(out/'launch.log'))+' 2>&1\nrc=$?\nset -e\nprintf "%s\\n" "$rc" >'+shlex.quote(str(out/'exit_code.txt'))+'\nexit "$rc"\n'


def main():
    parser = argparse.ArgumentParser()
    for key in ('request','request-sha256','authorization','authorization-sha256','runtime','runtime-sha256'):
        parser.add_argument('--'+key,required=True)
    args = vars(parser.parse_args())
    def record(k):
        p = no_links(args[k]); return dict(path=str(p),bytes=p.stat().st_size,sha256=args[k+'_sha256'])
    qr = record('request')
    q,static,metadata,selected,fold,plan,admission,expected = authorize(qr,record('authorization'),record('runtime'))
    I = q['identity']; out = no_links(q['output']); root = no_links(q['model_root'])
    require(sys.platform == 'linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, 'Linux -I -S -B')
    require(socket.gethostname() == I['hostname'] and os.getuid() == I['uid'] and str(Path(sys.executable).resolve()) == I['python_realpath']
            and sys.version.split()[0] == I['python_version'], 'current identity')
    require(Path.cwd().resolve() == Path(PROJECT) and out.parent == Path(PROJECT)/'logs/cranial_bcsp_fullmamba', 'project/output')
    require(exact(q['implementation']['entry']) == Path(__file__).absolute(), 'entry origin')
    parent_args = Path('/proc/'+str(os.getppid())+'/cmdline').read_bytes().decode().rstrip('\0').split('\0')
    require(parent_args[:4] == ['/usr/bin/timeout','--signal=TERM','--kill-after=5s','86400s'], 'fixed external timeout')
    require(bound(dict(path=q['launch_attempt'],bytes=Path(q['launch_attempt']).stat().st_size,sha256=sha(q['launch_attempt']))) ==
            dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qr['sha256']), 'single attempt')
    for r in q['dependencies']:
        exact(r)
    allowed = payload_paths(q['data_root'],selected)
    for p,h in allowed.items():
        require(p.is_file() and sha(p) == h, 'training payload drift: '+str(p))
    helper = source_module('f0_training_helper',q['implementation']['preflight_helper'])
    parent = source_module('f0_training_budget_parent',q['implementation']['budget_parent'])
    scope = bound(q['preflight_scope']); sources = helper.source_map(scope)
    for rel,r in sources.items():
        helper.exact(root/rel,r['sha256'],r['bytes'])
    helper.exact(root/'base_model.yaml',scope['bindings']['base_config']['sha256'])
    for r in scope['bindings']['provider']+scope['bindings']['environment_metadata']:
        helper.exact(r['path'],r['sha256'],r['bytes'])
    for k,v in q['environment'].items():
        require(os.environ.get(k) == v.replace('<owned_output>',str(out)), 'environment: '+k)
    gpu = [s.strip() for s in helper.smi('uuid,name,driver_version,memory.total,memory.used')[0].split(',')]
    require(gpu[:4] == [I['gpu_uuid'],I['gpu_name'],I['driver_version'],str(I['nvidia_smi_memory_total_MiB'])] and int(gpu[4]) <= 256, 'GPU identity/idle')
    require(out.is_dir() and {p.name for p in out.iterdir()} == {'launch.log'}, 'fresh launcher-only output')
    with (out/'worker.pid').open('x') as f:
        f.write(str(os.getpid())+'\n')
    utc_module = source_module('f0_training_UTC',q['implementation']['timezone'])
    utc = utc_module.ExactUTCReader(utc_module.UTC_RESOURCE)
    try:
        envroot = Path('/opt/conda/envs/adapointr-mamba'); provider = Path(scope['bindings']['provider'][0]['path']).parent.parent
        entryroot = Path(q['implementation']['entry']['path']).parent
        sys.path[:0] = [str(entryroot),str(provider),str(envroot/'lib/python3.10/site-packages')]
        helper.namespace_packages(root); sys.meta_path.insert(0,helper.FiniteProjectImports(root,sources))
        (out/'tmp').mkdir()
        read_roots = [root,entryroot,envroot,provider,Path(q['implementation']['contract']['path']).parent,
                      Path(q['implementation']['factory']['path']).parent,Path(q['implementation']['lqi_factory']['path']).parent,Path(q['implementation']['budget_parent']['path']),
                      Path(q['implementation']['timezone']['path']),Path(q['implementation']['bridge']['path']),'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom']
        sys.addaudithook(parent.make_training_policy(helper,read_roots,out,allowed,utc).audit)
        import numpy as np
        import torch
        import timm
        import yaml
        import importlib
        from easydict import EasyDict
        require((torch.__version__,np.__version__,timm.__version__) == (I['torch_version'],I['numpy_version'],I['timm_version']), 'versions')
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1, 'one CUDA device')
        torch.cuda.set_device(0); helper.configure_numeric(torch)
        require(torch.version.cuda == I['torch_cuda_version'], 'admitted torch CUDA build')
        ch = importlib.import_module('extensions.chamfer_dist'); pn = importlib.import_module('utils.pointnet2_utils')
        pm = importlib.import_module('pointnet2_ops.pointnet2_utils'); ext = importlib.import_module('pointnet2_ops._ext')
        helper.check_backend(ch,pn,pm)
        require(str(Path(pm.__file__).resolve()) == scope['bindings']['provider'][1]['path'] and
                str(Path(ext.__file__).resolve()) == scope['bindings']['provider'][2]['path'], 'PointNet2 origin')
        transformer = importlib.import_module('models.Transformer_utils'); cls = importlib.import_module('models.AdaPoinTr').AdaPoinTr
        require(static['model'] == yaml.safe_load((root/'base_model.yaml').read_text())['model'], 'unchanged model config')
        source_module('bcsp_mamba_encoder_v1',q['implementation']['encoder'])
        source_module('bcsp_p1_model_factory_v1',q['implementation']['factory'])
        source_module('bcsp_lqi_decoder_v1',q['implementation']['lqi_decoder'])
        factory = source_module('bcsp_lqi_factory_v1',q['implementation']['lqi_factory'])
        bridge = source_module('bcsp_lqi_runtime_adapter_v1',q['implementation']['bridge'])
        runtime = source_module('f0_parent_training_runtime',q['implementation']['runtime'])
        random.seed(0); np.random.seed(0); torch.manual_seed(0)
        budget = make_budget(parent,static['resources'],out,torch,helper,q,plan)
        result = dispatch_training(q,selected,fold,plan,factory=factory.build_model,model_builder=lambda:cls(EasyDict(static['model'])),
            runtime=runtime,bridge=bridge,admission=admission,expected_factory=expected,helper=helper,budget=budget,
            torch=torch,knn_enable=transformer.enable_bcsp_knn)
        files = [p for p in out.iterdir() if p.is_file() and p.name not in ('launch.log','worker.pid')]
        emit(out/'payload_manifest.json',dict(files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
        return result
    except BaseException as exc:
        if not (out/'failure.json').exists() and not (out/'completion.json').exists():
            emit(out/'startup_failure.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)))
        raise
    finally:
        utc.close()


if __name__ == '__main__':
    main()
