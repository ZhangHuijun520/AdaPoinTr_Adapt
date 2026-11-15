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
OUT = HERE/'artificial_cpu_batch_v1'
CONTRACT = ROOT/'outputs/cranial_bcsp_geov1_20261024/resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1/bcsp_training_contract_01dt08_v3.py'
OLD = ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/training_entry_v1/transport_payload/T0_foldC_seed0_training_execution_request_v1.json'
GPU = HERE.parent/'gpu_admission_v1'
AUDIT = GPU/'post_CUDA_freeze_audit_v1'
sys.path.insert(0,str(HERE))
import bcsp_f0_training_entry_v1 as entry


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
    original = json.loads(OLD.read_bytes()); cuda = json.loads((GPU/'F0_artificial_cuda_execution_request_v1.json').read_bytes())
    sources = ['artificial:'+str(i).zfill(3) for i in range(84)]
    ids = ['artificial__'+str(i).zfill(3)+'__'+str(d) for i in range(84) for d in range(5)]
    manifests = {}
    for count in (8192,16384):
        p = F/('manifest_'+str(count)+'.jsonl')
        with p.open('x') as stream:
            for i,cid in enumerate(ids):
                stream.write(json.dumps(dict(case_id=cid,source_id=sources[i//5],point_path='points/'+cid+'_'+str(count)+'.npz',
                    sha256='1'*64,schema='BCSP-normalized-v1',normalization_source='defective_bbox',n_input=count,n_target=8192,
                    target_array_sha256='2'*64,normalization={'center':[0,0,0],'scale':1},raw={'origin':'ARTIFICIAL_ONLY'}))+'\n')
        manifests[str(count)] = bind(p)
    fold = dict(train_case_ids=ids[:315],train_sources=sources[:63],dev_sources=sources[63:],
                train_allowlist_sha256=hashlib.sha256(('\n'.join(ids[:315])+'\n').encode()).hexdigest())
    folds = emit('folds.json',dict(folds={'C':fold},confirmation_count_excluded=20))
    verify = emit('verification.json',dict(status=metadata.QC_STATUS,verified_sources=84,verified_cases=420,verified_point_files=840,
        interpretation={'anatomical_semantics':'UNRESOLVED ARTIFICIAL_ONLY'},
        important_file_hashes={'manifest_'+k+'.jsonl':r['sha256'] for k,r in manifests.items()}))
    qualified, selected, spec = metadata.bind_metadata(verify,manifests,folds,'C',8192)
    qc = dict(qualified_receipt=emit('qualified.json',qualified),verification=verify,manifests=manifests,fold_binding=folds)
    plan = dict(schema='bcsp-shared-order-v1',case_ids=ids[:315],epochs=[dict(epoch=e,batches=[ids[i:i+8] for i in range(0,312,8)],dropped=ids[312:315]) for e in range(100)])
    order = emit('order.json',plan)
    impl = dict(original['implementation'])
    impl.update(cuda['implementation'])
    impl['runtime'] = cuda['training_runtime']
    impl['budget_parent'] = impl.pop('entry')
    bridge_path = HERE.parent/'implementation_v1/bcsp_f0_runtime_adapter_v1.py'
    impl['bridge'] = bind(bridge_path)
    impl['entry'] = bind(HERE/'bcsp_f0_training_entry_v1.py')
    # Mirror exact server identities to local frozen bytes ONLY inside this test process.
    mirror = {}
    def mirrored(record,path):
        assert bind(path)['sha256'] == record['sha256'] and bind(path)['bytes'] == record['bytes']
        mirror[record['path']] = path
        return record
    downloaded = AUDIT/'downloaded/installed'
    for key in ('factory','encoder','f0_factory','f0_decoder','runtime'):
        mirrored(impl[key],downloaded/Path(impl[key]['path']).name)
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
    admission = dict(receipt=bind(AUDIT/'native_admission_receipt_v2.json'),audit=bind(AUDIT/'post_CUDA_freeze_audit_result_v2.json'),
                     construction=bind(AUDIT/'downloaded/output/construction.json'),completion=bind(AUDIT/'downloaded/output/completion.json'),
                     request=bind(GPU/'F0_artificial_cuda_execution_request_v1.json'))
    p3 = emit('P3.json',dict(status='F0_TRAINING_ENTRY_CPU_P3_PASS',entry_sha256=impl['entry']['sha256'],native_admission_sha256=entry.ADMISSION_SHA))
    readiness = emit('readiness.json',dict(status='F0_FOLDC_METADATA_RESOURCE_READINESS_PASS',identity=cuda['identity'],payload_arrays_read=0))
    pair = emit('pair.json',dict(status='FROZEN_F0_CD_TRAINING_CONTRACT_NOT_AUTHORIZATION',counts=entry.COUNTS,resources=entry.RESOURCES,
         seed=0,arm_order=['C','D'],static_config=cuda['static_config'],FoldC_QC=qc,FoldC_order_plan=order,native_admission_sha256=entry.ADMISSION_SHA))
    q = dict(schema='bcsp-f0-training-request-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='CRANIAL_BCSP_FULLMAMBA',
        run_id='ARTIFICIAL_CPU_NOT_AUTHORIZED',variant='F0-P-v2',fold='C',seed=0,n_input=8192,n_output=8192,
        static_config=cuda['static_config'],QC=qc,order_plan=order,identity=cuda['identity'],data_root=str((F/'never_read_points').resolve()),
        model_root=cuda['model_root'],implementation=impl,preflight_scope=cuda['preflight_scope'],dependencies=cuda['dependencies'],
        environment=cuda['environment'],output=str((F/'tiny_dispatch').resolve()),launch_attempt='ARTIFICIAL_NEVER_LAUNCH',
        launch_contract={},admission=admission,readiness=readiness,pair_contract=pair,P3=p3,not_authorized=['real execution'])
    index = 0
    def authorize(value, auth_mutator=None, runtime_mutator=None):
        nonlocal index
        index += 1; sys.modules.pop('bcsp_training_contract_v1',None)
        qr = emit('q'+str(index)+'.json',value)
        auth = dict(schema='bcsp-f0-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL CPU fixture only')
        if auth_mutator:
            auth_mutator(auth)
        ar = emit('a'+str(index)+'.json',auth)
        runtime = dict(schema='bcsp-f0-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256'])
        if runtime_mutator:
            runtime_mutator(runtime)
        return entry.authorize(qr,ar,emit('r'+str(index)+'.json',runtime))
    result = authorize(q)
    check('complete authorize path with actual pinned admission',result[0] == q and len(result[3]) == 315 and result[5] == plan)
    for label,field,value in [('FoldD rejected','fold','D'),('non8k rejected','n_input',16384),('hybrid label rejected','variant','M0'),
                               ('seed scan rejected','seed',1),('not pending rejected','status','AUTHORIZED')]:
        bad = copy.deepcopy(q); bad[field] = value
        reject(label,lambda bad=bad:authorize(bad))
    reject('missing explicit consent rejected',lambda:authorize(q,lambda a:a.update(explicit_user_authorization=False)))
    reject('reverse receipt cycle rejected',lambda:authorize(q,lambda a:a.update(runtime_sha256='0'*64)))
    reject('wrong one-way runtime rejected',lambda:authorize(q,runtime_mutator=lambda r:r.update(authorization_sha256='0'*64)))
    bad = copy.deepcopy(q); bad['admission']['receipt']['sha256'] = '0'*64
    reject('arbitrary admission PASS not trusted',lambda:authorize(bad))
    bad = copy.deepcopy(q); bad['implementation']['f0_factory']['sha256'] = '0'*64
    reject('untested factory hash rejected',lambda:authorize(bad))
    bad = copy.deepcopy(q); bad['identity']['gpu_uuid'] = 'GPU-OTHER'
    reject('resource rebind requires new admission decision',lambda:authorize(bad))
    allowed = entry.payload_paths(q['data_root'],selected)
    check('exact315 allowlist without opening payloads',len(allowed) == 315 and not Path(q['data_root']).exists())
    bad_selected = copy.deepcopy(selected); bad_selected[0]['point_path'] = '../dev.npz'
    reject('path escape rejected',lambda:entry.payload_paths(q['data_root'],bad_selected))
    bad_selected = copy.deepcopy(selected); bad_selected[1] = bad_selected[0]
    reject('duplicate payload rejected',lambda:entry.payload_paths(q['data_root'],bad_selected))
    sys.path[:0] = [str(HERE.parent/'implementation_v1'),str(ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1')]
    import bcsp_f0_factory_v1 as factory
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
            assert runtime_sha == entry.PINS['runtime'] and kwargs['admission']['status'] == 'F0_NATIVE_CUDA_ADMISSION_PASS'
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
    geometry = [json.loads(s) for s in (budget.output/'F0_geometry.jsonl').read_text().splitlines()]
    check('detached geometry exact step and case mapping',len(geometry) == 1 and geometry[0]['step'] == 1 and geometry[0]['case_ids'] == plan['epochs'][0]['batches'][0])
    check('coarse/dense geometry eightcenters bounds radius',all(len(geometry[0]['geometry'][k]['centroid']) == 8 and 'minimum' in geometry[0]['geometry'][k] for k in ['coarse','dense']))
    construction = json.loads((budget.output/'model_construction.json').read_bytes())
    check('parameter totals separated without oldparent count confusion',construction['parameters']['total'] == sum(construction['parameters'][k] for k in ['encoder','decoder','other']))
    reject('finalization before3900 geometry rows blocked',budget.before_final)
    reject('CPU dispatch cannot masquerade as production',lambda:entry.dispatch_training(q,selected,fold,plan,factory=build,model_builder=TrainingFixture,runtime=None,bridge=None,admission={},expected_factory={},helper=None,budget=None,torch=torch,knn_enable=None,device='cpu'))
    launchq = copy.deepcopy(q); launchq['output'] = '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/F0_fixture'
    launchq['launch_contract'] = dict(request_path='/tmp/q.json',authorization_path='/tmp/a.json',runtime_path='/tmp/r.json')
    launch = entry.render_launcher(launchq,'a'*64,'b'*64,'c'*64)
    check('POSIX safeparent before redirect and86400hard timeout',launch.index('mkdir -p') < launch.index(' >') and '--kill-after=5s 86400s' in launch and '\\' not in launch.replace('\\n',''))
    reject('truncated execution hash rejected',lambda:entry.render_launcher(launchq,'a'*8,'b'*64,'c'*64))
    status = dict(status='ARTIFICIAL_F0_TRAINING_ENTRY_CPU_PASS',checks=checks,check_count=len(checks),native_Mamba=False,
        CUDA_calls=0,real_payload_arrays_read=0,optimizer_steps=0,fixture_forward=1,fixture_backward=1,
        actual_3900_training_not_run=True,warning='full authorize actual anchors/metadata; artificial front/loss/mixers and runtime spies validate dispatch only')
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
