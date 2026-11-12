"""Artificial CPU-only authorize/dispatch integration. No actual training or CUDA."""
import ast
import copy
import hashlib
import importlib.util
import json
from functools import partial
from pathlib import Path
import sys
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE/'artificial_cpu_batch_v2'
CONTRACT = ROOT/'outputs/cranial_bcsp_geov1_20261024/resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1/bcsp_training_contract_01dt08_v3.py'
OLD = ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/training_entry_v1/transport_payload/T0_foldC_seed0_training_execution_request_v1.json'
GPU = HERE.parent/'lqi_gpu_admission_v1'
AUDIT = GPU/'post_CUDA_freeze_audit_v1'
sys.path.insert(0,str(HERE))
import bcsp_lqi_foldD_training_entry_v1 as entry


def bind(path, logical=None):
    b = path.read_bytes()
    return dict(path=str(logical or path.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    import torch
    from torch import nn
    torch.set_num_threads(2); torch.random.default_generator.manual_seed(802)
    OUT.mkdir(exist_ok=False); F = OUT/'fixtures'; F.mkdir()
    checks = []
    def check(name, value):
        assert bool(value),name
        checks.append(name)
    def reject(name, function):
        try:
            function()
        except (ValueError,RuntimeError):
            checks.append(name); return
        raise AssertionError('accepted '+name)
    def emit(name, value):
        p = F/name
        with p.open('x',encoding='ascii') as f:
            json.dump(value,f,allow_nan=False)
        return bind(p)
    def load(name,path):
        spec = importlib.util.spec_from_file_location(name,path); m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m; spec.loader.exec_module(m); return m
    metadata = load('fixture_metadata_builder',CONTRACT)
    original = json.loads(OLD.read_bytes()); cuda = json.loads((GPU/'pending_transport_v1/payload/LQI_artificial_cuda_execution_request_v1.json').read_bytes())
    reference = json.loads((HERE/'frozen_M0_FoldD_reference_request_v1.json').read_bytes())
    qc = reference['QC']; order = reference['order_plan']
    G = ROOT/'outputs/cranial_bcsp_geov1_20261024'
    metadata_mirror = {
        qc['qualified_receipt']['path']:G/'foldD_8192_training_v1/qualified_data_qc_foldD_8192_v1.json',
        qc['verification']['path']:G/'real_data_qc_verification_v1.json',
        qc['manifests']['8192']['path']:G/'real_data_qc_v1/manifest_8192.jsonl',
        qc['manifests']['16384']['path']:G/'real_data_qc_v1/manifest_16384.jsonl',
        qc['fold_binding']['path']:G/'consolidated_binding_v1/fold_binding.json',
        order['path']:ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/FoldD_pair_preparation_20261106_v1/shared_order_foldD_seed0_v1.json'}
    original_metadata_exact = metadata.exact
    metadata.exact = lambda r:original_metadata_exact(dict(r,path=str(metadata_mirror[r['path']].resolve())))
    selected,fold = metadata.verify_qualified_receipt(json.loads(metadata_mirror[qc['qualified_receipt']['path']].read_bytes()),
        qc['verification'],qc['manifests'],qc['fold_binding'],'D',8192)
    plan = json.loads(metadata_mirror[order['path']].read_bytes())
    ids = plan['case_ids']
    impl = dict(original['implementation'])
    impl.update(cuda['implementation'])
    impl['runtime'] = json.loads((HERE.parent/'training_entry_v1/F0_FoldC_training_execution_request_v1.json').read_bytes())['implementation']['runtime']
    impl['budget_parent'] = impl.pop('entry')
    bridge_path = HERE.parent/'lqi_training_entry_v1/bcsp_lqi_runtime_adapter_v1.py'
    impl['bridge'] = bind(bridge_path)
    impl['entry'] = bind(HERE/'bcsp_lqi_foldD_training_entry_v1.py')
    # Mirror exact server identities to local frozen bytes ONLY inside this test process.
    mirror = dict(metadata_mirror)
    def mirrored(record,path):
        assert bind(path)['sha256'] == record['sha256'] and bind(path)['bytes'] == record['bytes']
        mirror[record['path']] = path
        return record
    downloaded = AUDIT/'downloads/installed'
    for key in ('factory','encoder','lqi_factory','lqi_decoder','runtime'):
        local = (ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'/Path(impl[key]['path']).name) if key in ('factory','encoder') else (HERE.parent/'gpu_admission_v1/post_CUDA_freeze_audit_v1/downloaded/installed'/Path(impl[key]['path']).name) if key=='runtime' else downloaded/Path(impl[key]['path']).name
        mirrored(impl[key],local)
    mirrored(impl['contract'],CONTRACT)
    mirrored(impl['budget_parent'],ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/training_entry_v1/bcsp_p1_training_entry_v1.py')
    mirrored(impl['preflight_helper'],ROOT/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py')
    mirrored(impl['timezone'],ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/gpu_admission_v3/exact_utc_resource_v1.py')
    mirrored(cuda['static_config'],ROOT/'outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/static_training_config_v1.json')
    real_exact = entry.exact
    def fixture_exact(r):
        if r['path'] in mirror:
            return real_exact(dict(r,path=str(mirror[r['path']].resolve())))
        return real_exact(r)
    entry.exact = fixture_exact
    original_source_module = entry.source_module
    def fixture_source_module(name, record):
        result = original_source_module(name, record)
        if name == 'bcsp_training_contract_v1':
            result.exact = fixture_exact
        return result
    entry.source_module = fixture_source_module
    admission = dict(receipt=bind(HERE.parent/'lqi_training_entry_v1/native_LQI_admission_receipt_v1.json'),audit=bind(AUDIT/'formal_post_CUDA_freeze_audit_result_v1.json'),
                     construction=bind(AUDIT/'downloads/output/construction.json'),completion=bind(AUDIT/'downloads/output/completion.json'),
                     request=bind(GPU/'pending_transport_v1/payload/LQI_artificial_cuda_execution_request_v1.json'))
    p3 = emit('P3.json',dict(status='LQI_TRAINING_ENTRY_CPU_P3_PASS',entry_sha256=impl['entry']['sha256'],native_admission_sha256=entry.ADMISSION_SHA))
    readiness = emit('readiness.json',dict(status='LQI_FOLDD_METADATA_RESOURCE_READINESS_PASS',identity=cuda['identity'],payload_arrays_read=0))
    pair = emit('pair.json',dict(status='FROZEN_LQI_CD_TRAINING_CONTRACT_NOT_AUTHORIZATION',counts=entry.COUNTS,resources=entry.RESOURCES,
         seed=0,arm_order=['C','D'],static_config=cuda['static_config'],FoldD_QC=qc,FoldD_order_plan=order,native_admission_sha256=entry.ADMISSION_SHA))
    q = dict(schema='bcsp-lqi-training-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='CRANIAL_BCSP_FULLMAMBA',
        run_id='ARTIFICIAL_CPU_NOT_AUTHORIZED',variant='F0-LQI-v1',fold='D',seed=0,n_input=8192,n_output=8192,
        static_config=cuda['static_config'],QC=qc,order_plan=order,identity=cuda['identity'],data_root=reference['data_root'],
        model_root=cuda['model_root'],implementation=impl,preflight_scope=cuda['preflight_scope'],dependencies=cuda['dependencies'],
        environment=cuda['environment'],output=str((F/'tiny_dispatch').resolve()),launch_attempt='ARTIFICIAL_NEVER_LAUNCH',
        launch_contract={},admission=admission,readiness=readiness,pair_contract=pair,P3=p3,not_authorized=['real execution'])
    FC = HERE.parent/'lqi_training_entry_v1/post_training_freeze_audit_v1'
    q['FoldC_pairing'] = dict(audit=bind(FC/'post_training_freeze_audit_result_v1.json'),
        request=bind(FC/'downloaded/installed/LQI_FoldC_training_execution_request_v1.json'),
        construction=bind(FC/'downloaded/output/model_construction.json'),initialization=bind(FC/'downloaded/output/initialization.json'),
        order=bind(FC/'downloaded/output/order_plan.json'),completion=bind(FC/'downloaded/output/completion.json'))
    q['FoldD_reference'] = bind(HERE/'frozen_M0_FoldD_reference_request_v1.json')
    index = 0
    def authorize(value, auth_mutator=None, runtime_mutator=None):
        nonlocal index
        index += 1; sys.modules.pop('bcsp_training_contract_v1',None)
        qr = emit('q'+str(index)+'.json',value)
        auth = dict(schema='bcsp-lqi-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL CPU fixture only')
        if auth_mutator:
            auth_mutator(auth)
        ar = emit('a'+str(index)+'.json',auth)
        runtime = dict(schema='bcsp-lqi-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'])
        if runtime_mutator:
            runtime_mutator(runtime)
        return entry.authorize(qr,ar,emit('r'+str(index)+'.json',runtime))
    result = authorize(q)
    check('complete authorize path with actual pinned admission',result[0] == q and len(result[3]) == 315 and result[5] == plan)
    for label,field,value in [('FoldC rejected','fold','C'),('non8k rejected','n_input',16384),('hybrid label rejected','variant','M0'),
                               ('seed scan rejected','seed',1),('not pending rejected','status','AUTHORIZED')]:
        bad = copy.deepcopy(q); bad[field] = value
        reject(label,lambda bad=bad:authorize(bad))
    reject('missing explicit consent rejected',lambda:authorize(q,lambda a:a.update(explicit_user_authorization=False)))
    reject('reverse receipt cycle rejected',lambda:authorize(q,lambda a:a.update(runtime_sha256='0'*64)))
    reject('wrong one-way runtime rejected',lambda:authorize(q,runtime_mutator=lambda r:r.update(authorization_sha256='0'*64)))
    bad = copy.deepcopy(q); bad['admission']['receipt']['sha256'] = '0'*64
    reject('arbitrary admission PASS not trusted',lambda:authorize(bad))
    bad = copy.deepcopy(q); bad['implementation']['lqi_factory']['sha256'] = '0'*64
    reject('untested factory hash rejected',lambda:authorize(bad))
    bad = copy.deepcopy(q); bad['identity']['gpu_uuid'] = 'GPU-OTHER'
    reject('resource rebind requires new admission decision',lambda:authorize(bad))
    bad = copy.deepcopy(q); bad['FoldC_pairing']['audit']['sha256'] = '0'*64
    reject('unfrozen FoldC audit rejected',lambda:authorize(bad))
    bad = copy.deepcopy(q); bad['FoldC_pairing']['initialization']['sha256'] = '0'*64
    reject('wrong FoldC initialization evidence rejected',lambda:authorize(bad))
    bad = copy.deepcopy(q); bad['FoldD_reference']['sha256'] = '0'*64
    reject('wrong historical M0 D reference rejected',lambda:authorize(bad))
    bad = copy.deepcopy(q); bad['order_plan'] = original['order_plan']
    reject('FoldC order cannot substitute for FoldD order',lambda:authorize(bad))
    allowed = entry.payload_paths(q['data_root'],selected)
    check('exact315 allowlist without opening payloads',len(allowed) == 315 and not Path(q['data_root']).exists())
    bad_selected = copy.deepcopy(selected); bad_selected[0]['point_path'] = '../dev.npz'
    reject('path escape rejected',lambda:entry.payload_paths(q['data_root'],bad_selected))
    bad_selected = copy.deepcopy(selected); bad_selected[1] = bad_selected[0]
    reject('duplicate payload rejected',lambda:entry.payload_paths(q['data_root'],bad_selected))
    sys.path[:0] = [str(HERE.parent/'lqi_implementation_v1'),str(ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1')]
    import bcsp_lqi_factory_v1 as factory
    # Reuse only fixture definitions from prior test AST. Never execute its top-level writes or test batch.
    previous = HERE.parent/'implementation_v1/test_f0_cpu_v1.py'
    tree = ast.parse(previous.read_text(encoding='utf-8'))
    names = {'knn_point','index_points','extract','ArtificialCausalMixer','EncoderFixture','ArtificialModel'}
    nodes = [n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    env = dict(torch=torch,nn=nn,partial=partial,knn_point=None,index_points=None,trunc_normal_=nn.init.trunc_normal_)
    ns = dict(torch=torch,nn=nn,partial=partial,ast=ast,env=env,__name__='declared_artificial_f0_fixture')
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<prior_fixture_definitions_only>','exec'),ns)
    env.update(knn_point=ns['knn_point'],index_points=ns['index_points'])
    snap = ROOT/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/models'
    ns['extract'](snap/'Transformer_utils.py',['Mlp','Attention','CrossAttention','DynamicGraphAttention','LayerScale'])
    ns['extract'](snap/'AdaPoinTr.py',['CrossAttnBlockApi','TransformerDecoder','PointTransformerDecoder'])
    class TrainingFixture(ns['ArtificialModel']):
        def forward(self,x):
            q,p,_ = super().forward(x)
            return q,q[:,:0],p[:,:0],p
        def get_loss(self,ret,target,epoch,partial):
            assert self.seen_input is partial
            return ret[0].new_zeros(()),(ret[-1]-target).square().mean()+ret[0].square().mean()
    def build(builder):
        return factory.build_artificial_fixture(builder,ns['ArtificialCausalMixer'])
    model, expected = build(TrainingFixture); del model
    class BaseBudget:
        def __init__(self,limits,out,torch,helper):
            self.output = Path(out); self.output.mkdir(); self.events = []
        def before_step(self,step):
            self.events.append(('before_step',step))
        def after_step(self,step):
            self.events.append(('after_step',step))
        def before_final(self):
            self.events.append(('before_final',3900))
    helpers = SimpleNamespace(validate_model=lambda m:check('actual factory yields8layer F0',len(m.base_model.decoder.blocks) == 8),
                              assert_numeric=lambda *a:None,state_sha=lambda *a:'ARTIFICIAL')
    budget = entry.make_budget(SimpleNamespace(TrainingBudget=BaseBudget),entry.RESOURCES,q['output'],torch,helpers,q,plan)
    called = []
    class Runtime:
        def BCSPDataset(self,root,rows,sources,n_input):
            called.append(('dataset',len(rows),len(sources),n_input)); return 'ARTIFICIAL_DATASET_NO_PAYLOAD'
        def make_loader(self,dataset,plan,epoch):
            called.append(('loader',dataset,epoch)); return 'ARTIFICIAL_LOADER'
    class Bridge:
        def train_lifecycle(self,runtime,runtime_sha,model,loader,records,plan,out,**kwargs):
            assert runtime_sha == entry.PINS['runtime'] and kwargs['admission']['status'] == 'LQI_NATIVE_CUDA_ADMISSION_PASS'
            assert loader(0) == 'ARTIFICIAL_LOADER'
            budget.before_step(0); model.train()
            x = torch.randn(8,8192,3); target = torch.randn_like(x)
            ret = model(x); sparse,dense = model.get_loss(ret,target,0,partial=x)
            loss = sparse+dense; loss.backward(); budget.after_step(1)
            called.append(('one_fixture_FB',float(loss.detach())))
            return dict(status='ARTIFICIAL_DISPATCH_ONLY',optimizer_steps=0)
    outcome = entry.dispatch_training(q,selected,fold,plan,factory=build,model_builder=TrainingFixture,runtime=Runtime(),
        bridge=Bridge(),admission=result[6],expected_factory=expected,helper=helpers,budget=budget,torch=torch,
        knn_enable=lambda:None,device='cpu',artificial_cpu=True)
    check('genuine F0factory and bridge/runtime dispatch reached',outcome['status'] == 'ARTIFICIAL_DISPATCH_ONLY' and called[0] == ('dataset',315,63,8192))
    check('one8k batch8 artificial loss/backward no optimizer',outcome['optimizer_steps'] == 0 and called[-1][0] == 'one_fixture_FB')
    geometry = [json.loads(s) for s in (budget.output/'LQI_geometry.jsonl').read_text().splitlines()]
    check('detached geometry exact step and case mapping',len(geometry) == 1 and geometry[0]['step'] == 1 and geometry[0]['case_ids'] == plan['epochs'][0]['batches'][0])
    check('coarse/dense geometry eightcenters bounds radius',all(len(geometry[0]['geometry'][k]['centroid']) == 8 and 'minimum' in geometry[0]['geometry'][k] for k in ['coarse','dense']))
    construction = json.loads((budget.output/'model_construction.json').read_bytes())
    check('parameter totals separated without oldparent count confusion',construction['parameters']['total'] == sum(construction['parameters'][k] for k in ['encoder','decoder','other']))
    reject('finalization before3900 geometry rows blocked',budget.before_final)
    reject('CPU dispatch cannot masquerade as production',lambda:entry.dispatch_training(q,selected,fold,plan,factory=build,model_builder=TrainingFixture,runtime=None,bridge=None,admission={},expected_factory={},helper=None,budget=None,torch=torch,knn_enable=None,device='cpu'))
    launchq = copy.deepcopy(q); launchq['output'] = '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_fixture'
    launchq['implementation']['entry']['path'] = '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_f0_foldD_training_20261110_v1/bcsp_lqi_foldD_training_entry_v1.py'
    launchq['launch_contract'] = dict(request_path='/tmp/q.json',authorization_path='/tmp/a.json',runtime_path='/tmp/r.json')
    launch = entry.render_launcher(launchq,'a'*64,'b'*64,'c'*64)
    check('POSIX safeparent before redirect and86400hard timeout',launch.index('mkdir -p') < launch.index(' >') and '--kill-after=5s 86400s' in launch and '\\' not in launch.replace('\\n',''))
    reject('truncated execution hash rejected',lambda:entry.render_launcher(launchq,'a'*8,'b'*64,'c'*64))
    status = dict(status='ARTIFICIAL_LQI_FOLDD_TRAINING_ENTRY_CPU_PASS',checks=checks,check_count=len(checks),native_Mamba=False,
        CUDA_calls=0,real_payload_arrays_read=0,optimizer_steps=0,fixture_forward=1,fixture_backward=1,
        actual_3900_training_not_run=True,warning='actual frozen metadata and anchors only; artificial front/loss/mixers/runtime spies, no real point payloads')
    with (OUT/'result_v1.json').open('x',encoding='ascii') as f:
        json.dump(status,f,indent=2)
    print(json.dumps(status))


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        OUT.mkdir(exist_ok=True)
        with (OUT/'failure_v1.json').open('x',encoding='ascii') as f:
            json.dump(dict(status='FAILED_STOP_NO_RETRY',error=repr(exc)),f)
        raise
