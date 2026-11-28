
"""One versioned local CPU contract check against the frozen OASG loss methods."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import torch

here = Path(__file__).resolve().parent
root = here.parents[1]
base = root / "outputs/cranial_scqr_v12_qa_github_publish_20261019"
files = {
    base / "models/AdaPoinTr.py": "1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4",
    base / "extensions/chamfer_dist/__init__.py": "6456934164750c2d326236effe4827dc37c77a7d6d915d3c28fa65a90a9b1c50",
    root / "outputs/cranial_bcsp_geov1_20261024/first_run_freeze_foldC_8192_v1/static_training_config_v1.json":
        "86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647",
}
out = here / "p1_cpu_numeric_v1"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def eq(a, b):
    torch.testing.assert_close(a, b, rtol=0, atol=0)


def scalar(a, b):
    eq(a, a.new_tensor(b))


def rejected(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("invalid input accepted")


def make_original():
    model_path, ch_path, cfg_path = files
    ch = load("frozen_chamfer", ch_path)
    assert ch.chamfer is None
    cfg = json.loads(cfg_path.read_bytes())["model"]
    tree = ast.parse(model_path.read_bytes())
    names = ("build_loss_func","get_fine_loss_components","get_loss")
    host = [cls for cls in tree.body if isinstance(cls,ast.ClassDef)
            and {n.name for n in cls.body if isinstance(n,ast.FunctionDef)}.issuperset(names)]
    assert len(host) == 1
    code = ast.Module(body=[n for n in host[0].body if isinstance(n,ast.FunctionDef) and n.name in names],
                      type_ignores=[])
    env = vars(ch).copy()
    exec(compile(code,str(model_path),"exec"),env)
    cpu_class = type("IsolatedFrozenLoss", (), {name:env[name] for name in names})
    loss = cpu_class()
    for k in ("denoise_weight","fine_coverage_weight","fine_local_weight"):
        setattr(loss,k,cfg[k])
    for k in ("coarse_geometry_guard","local_rim_guard","moment_trust","dense_contact","rim_query"):
        setattr(loss,k+"_enabled",False)
    loss.scqr_contract = SimpleNamespace(contact_supervision_enabled=False)
    loss.build_loss_func()
    return ch,loss,host[0].name


def main():
    out.mkdir(exist_ok=False)
    for p,h in files.items():
        assert sha(p)==h,p
    candidate=load("ejtc_cpu_candidate",here/"ejtc_loss_cpu_candidate_v1.py")
    ch,origin,origin_class=make_original()
    torch.set_num_threads(2)
    f64=torch.float64
    reports=[]

    def check(name, test):
        try:
            details=test()
            reports.append({"check":name,"status":"PASS","details":details})
        except Exception as exc:
            reports.append({"check":name,"status":"FAIL","details":repr(exc)})
        print(reports[-1]["status"],name,flush=True)

    def tail(n,value):
        scalar(candidate.tail_mean(torch.arange(n,dtype=f64)),value)

    check("U01_top10_percent_of_10",lambda:tail(10,9.0))
    check("U02_ceiling_at_11",lambda:tail(11,9.5))

    def ties():
        d=torch.ones(31,dtype=f64,requires_grad=True)
        picked=candidate.tail_indices(d)
        assert picked.tolist()==[0,1,2,3]
        grad,=torch.autograd.grad(candidate.tail_mean(d),d)
        eq(grad,torch.tensor([0.25]*4+[0.0]*27,dtype=f64))
        x=torch.tensor([[[-1.,0.,0.],[1.,0.,0.]]],dtype=f64,requires_grad=True)
        g=torch.tensor([[[0.,0.,0.],[0.,0.,0.]]],dtype=f64)
        _,v=candidate.dense_loss_and_target_distances(ch,origin.fine_loss_func,x,g)
        grad,=torch.autograd.grad(v.mean(),x)
        expected=torch.tensor([[[-1.,0.,0.],[0.,0.,0.]]],dtype=f64)
        eq(grad,expected)
        actual=origin.fine_loss_func(x,g)
        ref,=torch.autograd.grad(actual,x)
        dense,_=candidate.dense_loss_and_target_distances(ch,origin.fine_loss_func,x,g)
        tested,=torch.autograd.grad(dense,x)
        eq(tested,ref)
        return {"tail_rows":picked.tolist(),"nn_winner":0,"duplicates_same_neighbor":2}

    check("U03_stable_tail_and_original_nn_ties",ties)

    def test_regions():
        lab=torch.zeros((2,128),dtype=torch.bool)
        lab[0,:32]=True
        lab[1,:64]=True
        v=torch.zeros((2,128),dtype=f64)
        v[0,lab[0]]=10
        v[1,lab[1]]=6
        v.requires_grad_()
        t=candidate.auxiliary(v,"T")
        j=candidate.auxiliary(v,"J",lab)
        scalar(t,8.)
        scalar(j,4.)
        g,=torch.autograd.grad(j,v)
        for i in range(2):
            scalar(g[i,lab[i]].sum(),.25)
            scalar(g[i,~lab[i]].sum(),.25)
        return {"T":t.item(),"J":j.item()}

    check("U04_region_and_case_equal_weights",test_regions)
    check("U05_same_distance_distribution",lambda:eq(
          candidate.auxiliary(torch.ones(2,64,dtype=f64),"T"),
          candidate.auxiliary(torch.ones(2,64,dtype=f64),"J",
                              torch.tensor([[True]*32+[False]*32]*2))))

    def direction():
        p=torch.tensor([[[2.,0.,0.],[10.,0.,0.]]],dtype=f64,requires_grad=True)
        g=torch.tensor([[[0.,0.,0.],[3.,0.,0.],[4.,0.,0.]]],dtype=f64)
        value,d=candidate.dense_loss_and_target_distances(ch,origin.fine_loss_func,p,g)
        eq(d,torch.tensor([[2.,1.,2.]],dtype=f64))
        eq(value,origin.fine_loss_func(p,g))
        dx,=torch.autograd.grad(d.sum(),p)
        eq(dx,torch.tensor([[[-1.,0.,0.],[0.,0.,0.]]],dtype=f64))
        return {"G_to_P":d.tolist(),"gradient":dx.tolist()}

    check("U06_G_to_prediction_direction",direction)

    def vectors(n, dt, coincide, mixed=False):
        # Different exact, binary-grid positions for the direct and default MM paths.
        a=torch.arange(n,dtype=dt) % 16
        p=torch.stack((a/8,(a%5)/8,(a%3)/8),dim=-1).unsqueeze(0)
        g=p.clone()
        if not coincide:
            offset=torch.tensor([0.125,0.0625,0.25],dtype=dt)
            g+=offset
            if mixed:
                g[:,0]=p[:,0]
        return p.requires_grad_(),g

    def zero():
        evidence=[]
        for dt in (torch.float32, f64):
            for n,mixed in ((4,False),(64,False),(64,True),(8192,False)):
                p,g=vectors(n,dt,not mixed,mixed)
                raw=origin.fine_loss_func(p,g)
                native_grad,=torch.autograd.grad(raw,p)
                dense,distance=candidate.dense_loss_and_target_distances(ch,origin.fine_loss_func,p,g)
                dc,=torch.autograd.grad(dense,p,retain_graph=True)
                eq(dense,raw)
                eq(dc,native_grad)
                finite={}
                if n>=64:
                    lab=torch.arange(n).unsqueeze(0)<n//2
                    for arm,labels in (("T",None),("J",lab)):
                        aux=candidate.auxiliary(distance,arm,labels)
                        grad,=torch.autograd.grad(aux,p,retain_graph=(arm=="T"))
                        assert torch.isfinite(aux) and torch.isfinite(grad).all()
                        finite[arm]=True
                        if not mixed:
                            scalar(aux,0.0)
                            eq(grad,torch.zeros_like(grad))
                assert torch.isfinite(raw) and torch.isfinite(native_grad).all()
                if not mixed:
                    scalar(raw,0.0)
                    eq(native_grad,torch.zeros_like(native_grad))
                evidence.append({"dtype":str(dt),"rows":n,"mixed":mixed,
                    "exact_zero_G_to_P":int((distance==0).sum()),"native_gradient_finite":True,
                    "auxiliary_gradient_finite":finite})
        return evidence

    check("U07_zero_distance_and_mixed_neighbors",zero)

    def equivalent():
        info=[]
        for dt,n in ((torch.float32,64),(f64,64),(torch.float32,8192)):
            p,g=vectors(n,dt,False)
            q=p.detach()[:,::max(2,n//256)].clone().requires_grad_()
            empty=p.detach()[:,:0]
            a,b=origin.get_loss((q,empty,empty,p),g)
            ref=a+b
            expected=torch.autograd.grad(ref,(p,q))
            dense,d=candidate.dense_loss_and_target_distances(ch,origin.fine_loss_func,p,g)
            replay=a+(origin.loss_func(q,g)+dense)
            scalar(a,0.)
            eq(replay,ref)
            assert d.shape==(1,n) and d.requires_grad
            real=torch.autograd.grad(replay+0.0*candidate.auxiliary(d,"T"),(p,q))
            for x,y in zip(real,expected):
                eq(x,y)
                assert torch.isfinite(x).all()
            info.append({"dtype":str(dt),"dense":n,"coarse":q.shape[1],
                         "max_loss_abs_diff":abs((ref-replay).item()),
                         "max_gradient_abs_diff":max((x-y).abs().max().item() for x,y in zip(real,expected))})
        return info

    check("U08_original_get_loss_and_lambda_zero",equivalent)

    def permutation():
        d=torch.arange(64,dtype=f64).view(1,-1)
        l=torch.arange(64).view(1,-1)<32
        perm=torch.randperm(64,generator=torch.Generator().manual_seed(42))
        eq(candidate.auxiliary(d,"J",l),candidate.auxiliary(d[:,perm],"J",l[:,perm]))
        stamp=lambda a:hashlib.sha256(bytes(a.flatten().tolist())).hexdigest()
        expected=stamp(l[:,perm])
        def guarded(labels):
            if stamp(labels)!=expected:
                raise ValueError("ordered label fingerprint mismatch")
        guarded(l[:,perm])
        rejected(lambda:guarded(l))
        return {"identity_check":"synthetic ordered-label hash; real sidecar binding deferred"}

    check("U09_synchronized_permutation_and_alignment_fixture",permutation)

    def invalid():
        d=torch.ones(1,64,dtype=f64)
        for label in (torch.zeros(1,64,dtype=torch.bool),torch.zeros(1,63,dtype=torch.bool),
                      torch.arange(64).view(1,-1)<31,torch.zeros(1,64,dtype=torch.int32)):
            rejected(lambda:candidate.auxiliary(d,"J",label))
        for value in (float("nan"),float("inf")):
            invalid=d.clone()
            invalid[0,-1]=value
            rejected(lambda:candidate.auxiliary(invalid,"T"))
        rejected(lambda:candidate.auxiliary(d,"R"))
        rejected(lambda:candidate.auxiliary(torch.ones(1,0),"T"))

    check("U10_invalid_inputs_and_R_aux_bypass",invalid)

    def scale():
        p=torch.tensor([[[1.,2.,4.],[7.,2.,3.]]],dtype=f64)
        g=torch.tensor([[[1.,2.,6.],[6.,2.,3.]]],dtype=f64)
        c=torch.tensor([[[3.,2.,5.]]],dtype=f64)
        _,d=candidate.dense_loss_and_target_distances(ch,origin.fine_loss_func,(p-c)/4,(g-c)/4)
        eq(d,torch.tensor([[.5,.25]],dtype=f64))

    check("U11_frozen_D_frame_scale",scale)

    def finite_difference():
        p=torch.tensor([[[0.,0.,0.],[10.,0.,0.]]],dtype=f64,requires_grad=True)
        x=torch.cat((torch.linspace(.12,.32,32,dtype=f64),torch.linspace(10.5,10.8,32,dtype=f64)))
        g=torch.stack((x,torch.ones_like(x)*.04,torch.zeros_like(x)),dim=-1).unsqueeze(0)
        label=torch.arange(64).view(1,-1)>=32
        def j(points):
            _,d=candidate.dense_loss_and_target_distances(ch,origin.fine_loss_func,points,g)
            return candidate.auxiliary(d,"J",label)
        grad,=torch.autograd.grad(j(p),p)
        numeric=torch.zeros_like(p)
        eps=1e-5
        for i in range(p.numel()):
            step=torch.zeros_like(p)
            step.view(-1)[i]=eps
            numeric.view(-1)[i]=(j(p.detach()+step)-j(p.detach()-step))/(2*eps)
        torch.testing.assert_close(grad,numeric,rtol=1e-5,atol=1e-8)
        return {"max_abs_error":(grad-numeric).abs().max().item()}

    check("U12_differentiable_tail_finite_difference",finite_difference)
    for p,h in files.items():
        assert sha(p)==h,p
    passed=sum(r["status"]=="PASS" for r in reports)
    document={"status":"P1_CPU_CONTRACT_PASS" if passed==12 else "P1_HOLD_NUMERIC",
        "passed":passed,"total":len(reports),"checks":reports,"torch":str(torch.__version__),
        "python":sys.version,"interpreter":sys.executable,"device":"cpu","torch_threads":torch.get_num_threads(),
        "source_sha256":{p.relative_to(root).as_posix():h for p,h in files.items()},
        "original_class":origin_class,"frozen_get_loss_execution":"original methods on isolated loss-only CPU fixture",
        "candidate_sha256":sha(here/"ejtc_loss_cpu_candidate_v1.py"),"test_sha256":sha(Path(__file__)),
        "model_forward":0,"cuda_calls":0,"optimizer_steps":0}
    path=out/"cpu_numeric_gradient_receipt_v1.json"
    with path.open("x",encoding="utf-8") as f:
        json.dump(document,f,indent=2,allow_nan=False)
    print(document["status"],sha(path),flush=True)
    return int(passed!=12)


if __name__ == "__main__":
    raise SystemExit(main())

