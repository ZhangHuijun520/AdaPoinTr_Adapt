"""One bounded artificial CPU batch. Actual mother loss AST; no native model/provider/CUDA."""
import ast
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import types
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P1 = ROOT / 'outputs/cranial_bcsp_mamba_p1_20261104'
GEO = ROOT / 'outputs/cranial_bcsp_geov1_20261024'
QA = ROOT / 'outputs/cranial_scqr_v12_qa_github_publish_20261019'
OUT = HERE / 'artificial_cpu_batch_v1'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m

def bind(path):
    b = path.read_bytes()
    return dict(path=str(path.absolute()), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())

def main():
    OUT.mkdir(exist_ok=False)
    checks = []
    torch.set_num_threads(2)
    torch.manual_seed(7301)
    entry = load('p2_cpu_entry', HERE / 'bcsp_p2_h1_training_entry_v1.py')
    metadata = load('bcsp_training_contract_v1', GEO / 'training_closure_v5/bcsp_training_contract_v1.py')
    if 'tools' not in sys.modules:
        pkg = types.ModuleType('tools'); pkg.__path__ = []; sys.modules['tools'] = pkg
    load('tools.bcsp_adapter', GEO / 'implementation_candidate_v4/overlay/tools/bcsp_adapter.py')
    runtime = load('p2_cpu_runtime', HERE / 'bcsp_p2_h1_training_runtime_v1.py')
    def check(name, value):
        if not bool(value): raise AssertionError(name)
        checks.append(name)
    def rejects(name, fn):
        try: fn()
        except (ValueError, RuntimeError): checks.append(name)
        else: raise AssertionError(name)
    def emit(name, value):
        path = OUT / name
        with path.open('x', encoding='utf-8') as f: json.dump(value, f, allow_nan=False, indent=2)
        return bind(path)
    try:
        # Compile only unchanged selected AST nodes; never import the model package/native providers.
        model_path = QA / 'models/AdaPoinTr.py'
        tree = ast.parse(model_path.read_text(encoding='utf-8'))
        guard = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'coarse_geometry_guard_components')
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AdaPoinTr')
        methods = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in ('get_loss','get_fine_loss_components')]
        ns = dict(torch=torch, F=torch.nn.functional, math=math, chamfer=None)
        chamfer_path = QA / 'extensions/chamfer_dist/__init__.py'
        ct = ast.parse(chamfer_path.read_text(encoding='utf-8'))
        cn = [n for n in ct.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('_torch_chamfer_forward','ChamferDistanceL1','ChamferDistanceL1Directional')]
        exec(compile(ast.Module(body=cn + [guard] + methods, type_ignores=[]), str(model_path), 'exec'), ns)
        fn = ns['coarse_geometry_guard_components']
        def h(q,g): return fn(q,g,requested_mode='centroid_radius')['centroid_radius']
        g = torch.randn(2,16,3,dtype=torch.float64)
        q = g.clone()
        check('H01 identical H1 zero finite gradient', h(q.requires_grad_(),g).item() == 0 and torch.isfinite(torch.autograd.grad(h(q,g),q)[0]).all())
        q = (g + torch.tensor([.7,-.2,.4])).detach().requires_grad_()
        v = h(q,g)
        check('H02 displaced prediction positive',v.item()>0)
        shift=torch.tensor([1.1,-2.,3.],dtype=g.dtype)
        check('H03 common translation invariance',torch.allclose(v,h(q+shift,g+shift),atol=1e-12,rtol=1e-12))
        rot=torch.tensor([[0.,-1.,0.],[1.,0.,0.],[0.,0.,1.]],dtype=g.dtype)
        check('H04 common orthogonal transform invariance',torch.allclose(v,h(q@rot,g@rot),atol=1e-12,rtol=1e-12))
        c=fn(q,g,requested_mode='centroid_radius')
        check('H05 exact half coefficient and no CVaR',torch.equal(c['centroid_radius'],.5*(c['centroid']+c['radius'])) and 'coverage_cvar' not in c)
        check('H06 batch mean reduction',torch.allclose(h(q,g),sum(h(q[i:i+1],g[i:i+1]) for i in range(2))/2))
        check('H07 point permutation invariant',torch.allclose(h(q.flip(1),g.roll(3,1)),v))
        line=torch.tensor([[[-1.,0.,0.],[1.,0.,0.]]],dtype=torch.float64)
        perpendicular=line[:,:,[1,0,2]]
        check('H08 equal moments different geometry counterexample',h(line,perpendicular)==0 and torch.cdist(line,perpendicular).min()>1)
        collapsed=torch.zeros_like(g,requires_grad=True)
        collapse_gradient=torch.autograd.grad(h(collapsed,g),collapsed)[0]
        radius_gradient=torch.autograd.grad(fn(collapsed,g,requested_mode='centroid_radius')['radius'],collapsed)[0]
        check('H09 complete collapse finite but zero radius gradient',torch.isfinite(h(collapsed,g)) and torch.isfinite(collapse_gradient).all() and torch.equal(radius_gradient,torch.zeros_like(radius_gradient)))
        check('H10 tiny GT scale finite',torch.isfinite(h(q,g*1e-9)))
        scale_difference=float((h(q*.001,g*.001)-v).abs())
        check('H11 fixed epsilon scale limitation observed',scale_difference>1e-5)
        grad=torch.autograd.grad(v,q)[0];step=1e-5
        plus=q.detach().clone();minus=plus.clone();plus[0,0,0]+=step;minus[0,0,0]-=step
        check('H12 finite difference away from singularities',abs(float((h(plus,g)-h(minus,g))/(2*step)-grad[0,0,0]))<1e-7)

        class Tiny(nn.Module):
            get_loss=ns['get_loss']; get_fine_loss_components=ns['get_fine_loss_components']
            def __init__(self,enabled=True):
                super().__init__()
                self.coarse=nn.Parameter(torch.tensor([[.1,.2,.3],[-.2,-.1,.15]]))
                self.relative=nn.Parameter(torch.tensor([[.03,.01,.02],[-.02,.03,-.01]]))
                self.coarse_geometry_guard_enabled=enabled
                self.coarse_geometry_guard_mode='centroid_radius';self.coarse_geometry_guard_weight=.1
                self.coarse_geometry_guard_beta=.1;self.coarse_geometry_guard_eps=1e-6;self.coarse_geometry_guard_cvar_fraction=.1
                self.denoise_weight=0;self.fine_local_weight=0
                self.loss_func=ns['ChamferDistanceL1']();self.fine_loss_func=ns['ChamferDistanceL1Directional']()
                self.local_rim_guard_enabled=self.moment_trust_enabled=self.dense_contact_enabled=self.rim_query_enabled=False
                self.scqr_contract=types.SimpleNamespace(contact_supervision_enabled=False)
            def forward(self,x):
                coarse=self.coarse.unsqueeze(0).expand(x.shape[0],-1,-1)
                dense=(coarse[:,:,None,:]+self.relative[None,None,:,:]).reshape(x.shape[0],4,3)
                return coarse,coarse[:,:0],dense[:,:0],dense
        tiny=Tiny();x=torch.ones(8,4,3);target=torch.randn(8,4,3)*.3+.6;ret=tiny(x)
        on=tiny.get_loss(ret,target,0,partial=x)
        tiny.coarse_geometry_guard_enabled=False;off=tiny.get_loss(ret,target,0,partial=x)
        check('H13 actual get_loss OFF equals original coarse plus fine CD',torch.equal(off[1],tiny.loss_func(ret[0],target)+tiny.fine_loss_func(ret[3],target)) and off[0]==0)
        tiny.coarse_geometry_guard_enabled=True
        check('H14 actual get_loss ON adds exactly once',torch.allclose(on[1],off[1]+.1*h(ret[0],target),atol=1e-7))
        cg,dg=torch.autograd.grad(h(ret[0],target),(tiny.coarse,tiny.relative),allow_unused=True,retain_graph=True)
        check('H15 direct H1 reaches coarse not downstream relative head',cg.abs().sum()>0 and dg is None)
        before=[p.grad for p in tiny.parameters()]
        event=runtime.h1_log_components(tiny,ret,target,on[0]+on[1])
        check('H16 log values match actual formula without modifying gradients',abs(event['H1_raw']-float(h(ret[0],target)))<1e-7 and [p.grad for p in tiny.parameters()]==before)
        tiny.coarse_geometry_guard_enabled=False
        check('H17 OFF log zero',runtime.h1_log_components(tiny,ret,target,off[1])['H1_weighted']==0)
        tiny.coarse_geometry_guard_enabled=True
        static=json.loads((GEO/'first_run_freeze_foldC_8192_v1/static_training_config_v1.json').read_bytes())
        candidate=copy.deepcopy(static);candidate['model']['coarse_geometry_guard']=copy.deepcopy(entry.H1)
        check('H18 exact H1-only static accepted',entry.validate_static_h1(candidate,static,metadata)==candidate)
        for name,change in [('H19 weight drift rejected',lambda z:z['model']['coarse_geometry_guard'].update(weight=.2)),('H20 raw formula field rejected',lambda z:z['model']['coarse_geometry_guard'].update(raw_centroid=True)),('H21 3900 step drift rejected',lambda z:z['counts'].update(updates=3901)),('H22 denoise enabled rejected',lambda z:z['model'].update(denoise_weight=.1)),('H23 16k input-side model drift rejected',lambda z:z['model'].update(center_num=[1024,256]))]:
            bad=copy.deepcopy(candidate);change(bad);rejects(name,lambda:entry.validate_static_h1(bad,static,metadata))

        # Full authorize() with real metadata validator and 420 artificial metadata rows.
        sources=['fixture:'+str(i).zfill(3) for i in range(84)]
        ids=[s.replace(':','__')+'__defect'+str(j) for s in sources for j in range(5)]
        manifests={}
        for count in (8192,16384):
            path=OUT/('manifest_'+str(count)+'.jsonl')
            rows=[dict(case_id=cid,source_id=sources[i//5],target_array_sha256='0'*64,normalization={'center':[0,0,0],'scale':1},raw={'origin':'ARTIFICIAL_ONLY'},schema='BCSP-normalized-v1',normalization_source='defective_bbox',n_input=count,n_target=8192,point_path='points/'+cid+'_'+str(count)+'.npz',sha256='1'*64) for i,cid in enumerate(ids)]
            with path.open('x') as f:
                for row in rows:f.write(json.dumps(row)+'\n')
            manifests[str(count)]=bind(path)
        selected_ids=ids[:315]
        fold=dict(train_case_ids=selected_ids,train_sources=sources[:63],dev_sources=sources[63:],train_allowlist_sha256=hashlib.sha256(('\n'.join(selected_ids)+'\n').encode()).hexdigest())
        fr=emit('fold.json',dict(folds={'C':fold},confirmation_count_excluded=20))
        verification=emit('QC.json',dict(status=metadata.QC_STATUS,verified_sources=84,verified_cases=420,verified_point_files=840,interpretation={'anatomical_semantics':'UNRESOLVED artificial fixture'},important_file_hashes={'manifest_'+k+'.jsonl':v['sha256'] for k,v in manifests.items()}))
        qualified,selected,_=metadata.bind_metadata(verification,manifests,fr,'C',8192)
        qualified_record=emit('qualified.json',qualified)
        plan=dict(schema='bcsp-shared-order-v1',case_ids=selected_ids,epochs=[dict(epoch=e,batches=[selected_ids[i:i+8] for i in range(0,312,8)],dropped=selected_ids[312:]) for e in range(100)])
        order=emit('order.json',plan)
        impl=dict(entry=bind(HERE/'bcsp_p2_h1_training_entry_v1.py'),runtime=bind(HERE/'bcsp_p2_h1_training_runtime_v1.py'),contract=bind(GEO/'training_closure_v5/bcsp_training_contract_v1.py'))
        baseline=dict(schema='ARTIFICIAL_BASELINE_ONLY',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='P1',variant='M0',fold='C',n_input=8192,n_output=8192,static_config=emit('baseline_static.json',static),QC=dict(qualified_receipt=qualified_record,verification=verification,manifests=manifests,fold_binding=fr),order_plan=order,implementation=impl,identity={'ARTIFICIAL_ONLY':True},run_id='ARTIFICIAL_BASELINE',output=str(OUT/'baseline'),launch_attempt=str(OUT/'old_claim'),launch_contract={},provenance={},not_authorized=[])
        br=emit('baseline.json',baseline)
        ba=emit('baseline_audit.json',dict(status='FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS',request_sha256=br['sha256'],checks_passed=1,checks={'ARTIFICIAL_ONLY':True}))
        realpins=copy.deepcopy(entry.FROZEN_BASELINES)
        entry.FROZEN_BASELINES={'C':dict(request_sha256=br['sha256'],audit_sha256=ba['sha256'])}
        p3=emit('p3_fixture.json',dict(status='LOCAL_P2_H1_IMPLEMENTATION_P3_PASS',entry_sha256=impl['entry']['sha256'],runtime_sha256=impl['runtime']['sha256']))
        formula=emit('formula_fixture.json',dict(parameters=entry.H1,cvar_branch_executed=False))
        request=dict(baseline,schema='bcsp-p2-H1-training-request-v1',stage='CRANIAL_BCSP_MAMBA_P2_H1',run_id='ARTIFICIAL_H1_ONLY',static_config=emit('candidate_static.json',candidate),baseline_request=br,baseline_audit=ba,h1_formula=formula,p3=p3,h1_config=entry.H1)
        serial=0
        def triplet(q,auth=True,bad_runtime=False):
            nonlocal serial
            serial+=1;qr=emit('request_'+str(serial)+'.json',q)
            ar=emit('authorization_'+str(serial)+'.json',dict(schema='bcsp-p2-H1-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=auth,user_authorization_text='ARTIFICIAL TEST ONLY'))
            rr=emit('runtime_'+str(serial)+'.json',dict(schema='bcsp-p2-H1-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if bad_runtime else ar['sha256']))
            return qr,ar,rr
        try:
            authorized=entry.authorize(*triplet(request))
            check('H24 full authorize actual metadata 315 selected',len(authorized[3])==315 and authorized[1]==candidate)
            rejects('H25 no user authorization rejected',lambda:entry.authorize(*triplet(request,False)))
            rejects('H26 reverse runtime hash mismatch rejected',lambda:entry.authorize(*triplet(request,bad_runtime=True)))
            bad=copy.deepcopy(request);bad['identity']={'DRIFT':True}
            rejects('H27 unapproved identity drift rejected',lambda:entry.authorize(*triplet(bad)))
            bad=copy.deepcopy(request);bad['implementation']['runtime']['sha256']='0'*64
            rejects('H28 wrong runtime rejected',lambda:entry.authorize(*triplet(bad)))
        finally:entry.FROZEN_BASELINES=realpins

        # Actual unchanged 3900-update lifecycle on tiny artificial geometry, not a real model.
        trainout=OUT/'tiny_lifecycle';knn=[]
        class Budget:
            def before_step(self,step):pass
            def after_step(self,step):pass
            def before_final(self):pass
            def after_final(self):pass
        records=[dict(case_id=cid,source_id=sources[i//5]) for i,cid in enumerate(selected_ids)]
        source_for={r['case_id']:r['source_id'] for r in records}
        def loader(epoch):
            for batch in plan['epochs'][epoch]['batches']:
                yield x,target,batch,[source_for[cid] for cid in batch]
        class Loader:
            def __init__(self,e):self.e=e
            def __len__(self):return 39
            def __iter__(self):return loader(self.e)
        def state_sha(model,parameter_only=False):
            return hashlib.sha256(b''.join(p.detach().contiguous().numpy().tobytes() for p in model.parameters())).hexdigest()
        receipt=runtime.train_lifecycle(tiny,lambda e:Loader(e),records,plan,trainout,device='cpu',numeric_check=lambda t:None,resources=Budget(),knn_enable=lambda:knn.append(True),state_fingerprint=state_sha)
        check('H29 actual lifecycle exact updates/traversals/exposure',receipt['counts']['step']==3900 and receipt['traversals']==100 and receipt['case_exposures']==31200 and len(knn)==1)
        events=[json.loads(v) for v in (trainout/'metrics.jsonl').read_text().splitlines()]
        check('H30 3900 H1 logs finite and single-weight coherent',len(events)==3900 and all(row['H1_enabled'] and math.isclose(row['H1_raw'],.5*(row['H1_centroid']+row['H1_radius']),abs_tol=1e-6) and math.isclose(row['H1_weighted'],.1*row['H1_raw'],abs_tol=1e-6) for row in events))
        exposure=json.loads((trainout/'exposure.json').read_text())
        check('H31 original 300 drops and no BNCal evaluation resume',sum(exposure['dropped_case'].values())==300 and not receipt['bncal_executed'] and not receipt['evaluation_executed'] and not receipt['resume'])
        check('H32 parent production source hashes unchanged',bind(model_path)['sha256']=='1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4' and bind(P1/'minimal_implementation_v1/bcsp_p1_training_runtime_v1.py')['sha256']=='939e317dd447d04c62897849c0230f1918dc65c46ec556acdb60c9d69dfebeee')
        validation=types.SimpleNamespace(num_query=256,num_points=8192,factor=32,decoder_type='fc',denoise_weight=0,fine_coverage_weight=1,fine_local_weight=0,
            base_model=types.SimpleNamespace(center_num=[512,256],encoder_type='graph',query_selection='learned_only',use_denoise=False,encoder_adapter=types.SimpleNamespace(enabled=False)),
            scqr_contract=types.SimpleNamespace(enabled=False),local_rim_guard_enabled=False,moment_trust_enabled=False,dense_contact_enabled=False,rim_query_enabled=False,
            coarse_geometry_guard_enabled=True,coarse_geometry_guard_mode='centroid_radius',coarse_geometry_guard_weight=.1,coarse_geometry_guard_beta=.1,coarse_geometry_guard_cvar_fraction=.1,coarse_geometry_guard_eps=1e-6)
        entry.validate_model_h1(validation)
        check('H33 actual attribute contract permits only frozen H1',True)
        validation.dense_contact_enabled=True
        rejects('H34 unrelated objective remains rejected',lambda:entry.validate_model_h1(validation))
        emit('result_v1.json',dict(status='ARTIFICIAL_CPU_CONTRACT_PASS',checks=checks,checks_passed=len(checks),python=sys.version,torch=torch.__version__,cuda_used=False,actual_mamba_model_loaded=False,actual_provider_imported=False,real_payloads_read=0,synthetic_optimizer_steps=3900,production_optimizer_steps=0,scope_limit='AST-selected original loss and tiny artificial lifecycle; not real Mamba/PointNet2/CUDA equivalence',scale_difference_observed=scale_difference,source_bindings=[bind(model_path),bind(chamfer_path),bind(HERE/'bcsp_p2_h1_training_entry_v1.py'),bind(HERE/'bcsp_p2_h1_training_runtime_v1.py')]))
        print(json.dumps({'status':'ARTIFICIAL_CPU_CONTRACT_PASS','checks_passed':len(checks),'production_optimizer_steps':0}))
    except BaseException as exc:
        emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),checks_passed=len(checks),checks=checks))
        raise

if __name__=='__main__':main()
