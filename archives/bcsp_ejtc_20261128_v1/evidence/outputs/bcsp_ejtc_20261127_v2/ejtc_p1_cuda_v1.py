
"""BCSP-EJTC P1 zero-update worker. Separate final request, authorization and runtime required."""
import argparse
from contextlib import ExitStack, contextmanager
import hashlib
import importlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import random
import socket
import statistics
import sys
import threading
import time

COUNTS = dict(forward=53, base_loss=51, auxiliary=46, autograd_grad=32,
              backward=39, optimizer_steps=0)
SEEDS = (2026112801, 2026112803)
DEFECTS = ("bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2")


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def schedule(batches):
    need(len(batches)==5 and all(len(b)==8 for b in batches), "5 real training batches of 8")
    need(len(set(sum(batches, [])))==40, "40 unique training cases")
    rows = [dict(phase="equivalence", state="initial", arm="R", batch=batches[0])]
    rows += [dict(phase="calibration", state=state, arm="TJ", batch=batch)
             for state in ("initial","historical") for batch in batches]
    rows += [dict(phase="timing",state="initial",arm=arm,batch=batches[0],warmup=i<3)
             for i in range(13) for arm in "RTJ"]
    rows += [dict(phase="native",state="initial",arm=arm,batch=batches[0][:1]) for arm in "RTJ"]
    return rows


def planned_counts(rows):
    n = dict.fromkeys(COUNTS,0)
    for row in rows:
        n["forward"] += 1
        phase,arm=row["phase"],row["arm"]
        if phase=="equivalence":
            n["base_loss"]+=2
            n["autograd_grad"]+=2
        elif phase=="calibration":
            n["base_loss"]+=1
            n["auxiliary"]+=2
            n["autograd_grad"]+=3
        elif phase=="timing":
            n["base_loss"]+=1
            n["auxiliary"]+=int(arm!="R")
            n["backward"]+=1
    return n


def calibrate(records):
    first=[r for r in records if r["state"]=="initial"]
    last=[r for r in records if r["state"]=="historical"]
    need(len(first)==len(last)==5,"20 arm-batch calibration observations")
    obs=[r["arms"][a] for r in first for a in "TJ"]
    max_v=max(o["value_ratio"] for o in obs)
    max_g=max(o["ratios"]["P"] for o in obs)
    need(max_v>0 and max_g>0 and math.isfinite(max_v+max_g),"calibration denominator")
    lam=min(0.10,0.20/max_v,0.25/max_g)
    gates={"lambda_floor":lam>=0.001}
    for split,cases,vc,pc,gc in (("initial",first,.20,.25,.50),("historical",last,.40,.50,1.0)):
        for arm in "TJ":
            a=[r["arms"][arm] for r in cases]
            gates[split+"_"+arm+"_values"]=all(lam*r["value_ratio"]<=vc+1e-6 for r in a)
            gates[split+"_"+arm+"_P"]=all(lam*r["ratios"]["P"]<=pc+1e-6 for r in a)
            gates[split+"_"+arm+"_Q_and_parameters"]=all(
                lam*v<=gc+1e-6 for r in a for k,v in r["ratios"].items() if k!="P")
            if split=="initial":
                gates["initial_"+arm+"_median"]=statistics.median(lam*r["ratios"]["P"] for r in a)>=.01-1e-6
    hist=[v for batch in last for v in batch["manipulation"]]
    good=[v for v in hist if v["TV"]>=.10]
    gates["TV_count"]=len(hist)==40 and len(good)>=32
    gates["TV_each_type"]=set(v["case_id"].split("__")[-1] for v in good)==set(DEFECTS)
    return lam,gates


def state_snapshot(torch,model):
    return {k:v.detach().to("cpu",copy=True) for k,v in model.state_dict().items()}


@contextmanager
def protected(torch,np,helper,model,training,evidence):
    flags=[(m,m.training) for m in model.modules()]
    buffers={n:b.detach().clone() for n,b in model.named_buffers()}
    need(all(p.grad is None for p in model.parameters()), "preexisting gradient")
    with helper.rng_preserved(torch,np,cuda=True,evidence=evidence):
        try:
            model.train(training)
            yield
        finally:
            with torch.no_grad():
                for n,b in model.named_buffers():
                    b.copy_(buffers[n])
            for m,s in flags:
                m.training=s
            model.zero_grad(set_to_none=True)
            need(all(torch.equal(b,buffers[n]) for n,b in model.named_buffers()) and
                 all(m.training==s for m,s in flags) and
                 all(p.grad is None for p in model.parameters()), "state restore")
            evidence["buffers_flags_grad_restored"]=True


@contextmanager
def expose_target(ch,candidate,model,captured):
    layer=model.fine_loss_func
    need("forward" not in vars(layer),"dense module was already patched")
    def wrapped(prediction,target):
        need(not captured,"unexpected repeated dense loss")
        value,distance=candidate.dense_loss_and_target_distances(ch,layer,prediction,target)
        captured.append(distance)
        return value
    layer.forward=wrapped
    try:
        yield
    finally:
        del layer.forward


def parameter_groups(model):
    groups={n:[] for n in ("Encoder","OASG","LQI","FC")}
    for name,p in model.named_parameters():
        if name.startswith(("base_model.grouper.","base_model.encoder.","base_model.pos_embed.")):
            groups["Encoder"].append(p)
        elif name.startswith("base_model.coarse_pred."):
            groups["OASG"].append(p)
        elif name.startswith("base_model.decoder."):
            groups["LQI"].append(p)
        elif name.startswith(("decode_head.","increase_dim.","reduce_map.")):
            groups["FC"].append(p)
    need(all(groups.values()) and all(p.requires_grad for v in groups.values() for p in v),
         "verified disjoint gradient groups")
    return groups


def gradient_stats(torch, original, aux, parts):
    summary={}
    for name,indices in parts.items():
        a=[original[i] for i in indices if original[i] is not None]
        b=[aux[i] for i in indices if aux[i] is not None]
        need(a and b and all(bool(t.isfinite().all()) for t in a+b),
             "missing or nonfinite gradient: "+name)
        # Accumulate as Python float64 after reducing one tensor at a time on device.
        na=math.sqrt(sum(float(t.detach().double().square().sum()) for t in a))
        nb=math.sqrt(sum(float(t.detach().double().square().sum()) for t in b))
        dot=sum(float((original[i].detach().double()*aux[i].detach().double()).sum())
                for i in indices if original[i] is not None and aux[i] is not None)
        need(na>0 and nb>0 and math.isfinite(na+nb+dot),"degenerate "+name+" gradient")
        summary[name]=dict(base=na,aux=nb,dot=dot,cosine=dot/(na*nb),ratio=nb/na)
    return summary


def manipulation(torch,candidate,d,lab,batch,squared_nn_indices):
    rows=[]
    for v,j,cid,nn in zip(d.detach(),lab,batch,squared_nn_indices):
        all_i=candidate.tail_indices(v)
        ei=torch.where(~j)[0]
        ji=torch.where(j)[0]
        ie,ij=ei[candidate.tail_indices(v[ei])],ji[candidate.tail_indices(v[ji])]
        wt=torch.zeros_like(v,dtype=torch.float64)
        wj=torch.zeros_like(wt)
        wt[all_i]=1/len(all_i)
        wj[ie]=.5/len(ie)
        wj[ij]=.5/len(ij)
        def load(indices):
            _,count=torch.unique(nn[indices],return_counts=True)
            return dict(unique=int(count.numel()),max_load=int(count.max()))
        rows.append(dict(case_id=cid,TV=float((wt-wj).abs().sum()/2),T_J_mass=float(wt[j].sum()),
                         J_J_mass=float(wj[j].sum()),T=all_i.tolist(),E=ie.tolist(),J=ij.tolist(),
                         neighbors_T=load(all_i),neighbors_E=load(ie),neighbors_J=load(ij)))
    return rows


@contextmanager
def capture_dense_neighbors(torch, candidate, indices):
    from torch.utils._python_dispatch import TorchDispatchMode

    class DenseMinObserver(TorchDispatchMode):
        def __torch_dispatch__(self, func, types, args=(), kwargs=None):
            result = func(*args, **(kwargs or {}))
            if func == torch.ops.aten.min.dim and len(args) > 1 and args[1] == 1:
                indices.append(result[1].detach())
            return result

    frozen = candidate.dense_loss_and_target_distances

    def observe(module, layer, prediction, target):
        with DenseMinObserver():
            return frozen(module, layer, prediction, target)

    candidate.dense_loss_and_target_distances = observe
    try:
        yield
        need(len(indices) == 1, "one target-direction min in the frozen dense backend")
    finally:
        candidate.dense_loss_and_target_distances = frozen


def observe_native(torch, np, native, model, x):
    base = model.base_model
    mixers = [block.attn.mixer for block in base.encoder.blocks.blocks]
    mixers.extend(m for block in base.decoder.blocks for m in (block.self_ssm, block.cond_ssm))
    need(len({id(m) for m in mixers}) == 22, "native mixer module count")
    attention = [m for m in model.modules() if type(m).__name__.lower() in
                 {"attention", "crossattention", "multiheadattention", "selfattention", "attn"}]
    calls = [0, 0]

    def hook(slot):
        def increment(*_):
            calls[slot] += 1
        return increment

    with ExitStack() as stack:
        for slot, modules in enumerate((mixers, attention)):
            for m in modules:
                stack.callback(m.register_forward_hook(hook(slot)).remove)
        output = native.observe_once(torch, np, model, x, "A")
    need(calls == [36, 0], "native SSM and monitored Attention calls")
    return dict(output, ssm_calls=calls[0], monitored_attention_calls=calls[1])


def run(q,parent,support,native,prefix,candidate,out,emit,sample):
    torch,np,helper,_=native.prepare_models(parent,support)
    ch=importlib.import_module("extensions.chamfer_dist")
    helper._MONITOR=None
    random.seed(SEEDS[0])
    np.random.seed(SEEDS[0])
    torch.manual_seed(SEEDS[0])
    model,_=prefix.build_model(parent,support,torch,helper,*SEEDS)
    model.to("cuda:0")
    need(all(p.dtype==torch.float32 and p.is_cuda for p in model.parameters()),"FP32 GPU model")
    initial=state_snapshot(torch,model)
    initial_hash=helper.state_sha(model)
    counts=dict.fromkeys(COUNTS,0)
    records=[]
    timings={a:[] for a in "RTJ"}
    peak={a:0 for a in "RTJ"}
    native_refs=[]
    groups=parameter_groups(model)
    current="initial"
    reference_state=initial_hash
    data={}
    for cid,row in q["inputs"].items():
        cloud=support.exact(row["points"])
        label=support.exact(row["labels"])
        with np.load(io.BytesIO(cloud.read_bytes()),allow_pickle=False) as z:
            x,g=z["partial"],z["implant"]
        with np.load(io.BytesIO(label.read_bytes()),allow_pickle=False) as z:
            j=z["labels_G"]
        need(x.shape==g.shape==(8192,3) and x.dtype==g.dtype==np.float32 and
             np.isfinite(x).all() and np.isfinite(g).all() and sha(g.tobytes())==row["target_sha256"]
             and j.dtype==np.uint8 and j.shape==(8192,) and np.isin(j,[0,1]).all()
             and int(j.sum())==row["n_J"] and min(row["n_J"],8192-row["n_J"])>=32,
             "frozen training rows "+cid)
        data[cid]=(x,g,j.astype(bool))

    def count(k):
        counts[k]+=1
        need(counts[k]<=COUNTS[k],k+" budget")

    def original(ret,g,x,with_vector=False):
        count("base_loss")
        values=[]
        with ExitStack() as hooks:
            if with_vector:
                hooks.enter_context(expose_target(ch,candidate,model,values))
            den,recon=model.get_loss(ret,g,0,partial=x)
        need(float(den.detach())==0.0 and bool(recon.isfinite()),"frozen loss branch")
        need(len(values)==int(with_vector),"exact dense vector count")
        return den+recon,values[0] if values else None

    def extra(d,arm,j):
        count("auxiliary")
        return candidate.auxiliary(d,arm,j if arm=="J" else None)

    def grads(loss,params,retain):
        count("autograd_grad")
        return torch.autograd.grad(loss,params,retain_graph=retain,allow_unused=True)

    lam=None
    gate={}
    for i,row in enumerate(q["schedule"],1):
        phase,arm,batch=row["phase"],row["arm"],row["batch"]
        if row["state"]!=current:
            need(helper.state_sha(model)==reference_state,"state changed between phases")
            current=row["state"]
            if current=="historical":
                ck=torch.load(support.exact(q["checkpoint"]),map_location="cpu",weights_only=True)
                need(ck["scq_prime_run_identity"]==dict(variant="A",fold="D",seed=2026112102)
                     and ck["epoch"]==99 and ck["updates"]==3900 and ck["stage"]=="BCSP_INPUT_DENSITY_V1",
                     "historical checkpoint payload")
                model.load_state_dict(ck["base_model"],strict=True)
                del ck
            else:
                model.load_state_dict(initial,strict=True)
                lam,gate=calibrate(records)
                for record in records:
                    for o in record["arms"].values():
                        for stat in o["gradients"].values():
                            square=stat["base"]**2+(lam*stat["aux"])**2+2*lam*stat["dot"]
                            stat["combined"]=math.sqrt(max(0.0,square))
                    emit(dict(event="calibration",**record))
                emit(dict(event="lambda",lambda_value=lam,gates=gate))
                if not all(gate.values()):
                    return dict(status="P1_HOLD_GRADIENT_OR_MANIPULATION",counts=counts,gates=gate,
                                lambda_value=lam,initial_state=initial_hash,restored_state=helper.state_sha(model))
            reference_state=helper.state_sha(model)
            need((reference_state==initial_hash)==(current=="initial"),"initial/historical state identity")
            emit(dict(event="model_state",state=current,sha256=reference_state))
        emit(dict(event="attempt",index=i,**row))
        x=torch.from_numpy(np.stack([data[c][0] for c in batch])).to("cuda:0")
        g=j=None
        if phase!="native":
            g=torch.from_numpy(np.stack([data[c][1] for c in batch])).to("cuda:0")
        if phase=="calibration" or (phase=="timing" and arm=="J"):
            j=torch.from_numpy(np.stack([data[c][2] for c in batch])).to("cuda:0")
        evidence={}
        with protected(torch,np,helper,model,phase!="native",evidence):
            if phase=="native":
                with torch.inference_mode():
                    count("forward")
                    trace=observe_native(torch,np,native,model,x)
                native_refs.append(trace)
                if len(native_refs)>1:
                    original_trace=native_refs[0]
                    need(trace.keys()==original_trace.keys(),"Native trace keys")
                    for name,val in trace.items():
                        if isinstance(val,np.ndarray):
                            np.testing.assert_allclose(val,original_trace[name],atol=1e-7,rtol=1e-5)
                        else:
                            need(val==original_trace[name],"Native identity "+name)
                emit(dict(event="native",index=i,arm=arm,
                          trace={k:sha(v.tobytes()) if isinstance(v,np.ndarray) else v for k,v in trace.items()}))
            else:
                # Record the actual coarse tensor consumed by the dense head. The returned
                # coarse tensor may be a contiguous copy and must not substitute for it.
                q_seen=[]
                def coarse_node(_m,_args,result):
                    q_seen.append(result[1])
                h=model.base_model.register_forward_hook(coarse_node) if phase!="timing" else None
                try:
                    torch.cuda.synchronize()
                    torch.cuda.reset_peak_memory_stats()
                    start=time.perf_counter()
                    count("forward")
                    ret=model(x)
                finally:
                    if h is not None:
                        h.remove()
                p=ret[3]
                need(len(ret)==4 and p.shape==(8,8192,3) and ret[0].shape==(8,256,3)
                     and ret[1].shape[1]==ret[2].shape[1]==0,"frozen reconstruction tensors")
                if phase!="timing":
                    need(len(q_seen)==1 and torch.equal(q_seen[0],ret[0]),"actual coarse consumer tensor")
                if phase=="equivalence":
                    ref,_=original(ret,g,x)
                    ref_value=ref.detach()
                    ref_grad=grads(ref,(p,q_seen[0]),True)
                    # Release the first CD graph before allocating the candidate CD graph.
                    del ref
                    candidate_loss,_=original(ret,g,x,True)
                    torch.testing.assert_close(ref_value,candidate_loss.detach(),atol=1e-7,rtol=1e-5)
                    tested=grads(candidate_loss,(p,q_seen[0]),False)
                    for a,b in zip(ref_grad,tested):
                        need(a is not None and b is not None and bool(a.isfinite().all()),"finite equivalence gradient")
                        torch.testing.assert_close(a,b,atol=1e-7,rtol=1e-5)
                    emit(dict(event="equivalence",loss_abs=float((ref_value-candidate_loss.detach()).abs()),
                              grad_abs=max(float((a-b).abs().max()) for a,b in zip(ref_grad,tested))))
                    del ref_value,candidate_loss,ref_grad,tested,_
                elif phase=="calibration":
                    indices=[]
                    with capture_dense_neighbors(torch,candidate,indices):
                        base,d=original(ret,g,x,True)
                    aux={a:extra(d,a,j) for a in "TJ"}
                    args=[p,q_seen[0]]
                    parts={"P":[0],"Q":[1]}
                    for name,group in groups.items():
                        parts[name]=list(range(len(args),len(args)+len(group)))
                        args.extend(group)
                    reference=grads(base,args,True)
                    arms={}
                    for a in "TJ":
                        compared=grads(aux[a],args,a=="T")
                        gstats=gradient_stats(torch,reference,compared,parts)
                        need(bool(aux[a].isfinite()) and float(base.detach())>0,"calibration loss finite")
                        arms[a]=dict(aux=float(aux[a].detach()),value_ratio=float((aux[a]/base).detach()),
                                     gradients=gstats,ratios={k:v["ratio"] for k,v in gstats.items()})
                    records.append(dict(state=current,batch=batch,base_loss=float(base.detach()),
                                        arms=arms,manipulation=manipulation(torch,candidate,d,j,batch,indices[0])))
                    del aux,base,d,indices,reference,compared,args
                else:
                    base,d=original(ret,g,x,arm!="R")
                    loss=base if arm=="R" else base+lam*extra(d,arm,j)
                    count("backward")
                    loss.backward()
                    torch.cuda.synchronize()
                    ms=(time.perf_counter()-start)*1000
                    alloc=torch.cuda.max_memory_allocated()
                    reserved=torch.cuda.max_memory_reserved()
                    need(bool(loss.isfinite()) and all(bool(v.grad.isfinite().all())
                         for v in model.parameters() if v.grad is not None),"timing gradient finite")
                    if not row["warmup"]:
                        timings[arm].append(ms)
                    peak[arm]=max(peak[arm],alloc)
                    emit(dict(event="timing",index=i,arm=arm,warmup=row["warmup"],ms=ms,
                              allocated=alloc,reserved=reserved,loss=float(loss.detach())))
                    del base,d,loss
                del ret,p,q_seen
        need(torch.cuda.max_memory_allocated()<=q["resources"]["torch_peak_bytes"],"absolute PyTorch cap")
        sample()
        emit(dict(event="restoration",index=i,**evidence))
        del x,g,j
    need(counts==COUNTS and helper.state_sha(model)==initial_hash,"exact counts and initial state restoration")
    p50={a:statistics.median(t) for a,t in timings.items()}
    p95={a:float(np.quantile(t,.95)) for a,t in timings.items()}
    need(all(len(t)==10 for t in timings.values()),"timing observations")
    resource={a:p50[a]<=1.5*p50["R"] and peak[a]<=1.25*peak["R"] for a in "TJ"}
    return dict(status="P1_CUDA_CONTRACT_PASS" if all(resource.values()) else "P1_HOLD_RESOURCE",
                counts=counts,gates=gate,resource_gates=resource,lambda_value=lam,
                initial_state=initial_hash,restored_state=helper.state_sha(model),p50_ms=p50,
                p95_ms=p95,peak_allocated=peak,model_only_floor_seconds=sum(p50.values())*3900/1000)


def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def control(path,digest):
    p=Path(path)
    need(p.is_absolute() and p.resolve(strict=True)==p and p.is_file() and p.stat().st_size<=262144,
         "bounded control path")
    raw=p.read_bytes()
    need(sha(raw)==digest,"control SHA256 "+str(p))
    return json.loads(raw)


def main():
    parser=argparse.ArgumentParser()
    for name in ("request","request-sha256","authorization","authorization-sha256","runtime","runtime-sha256"):
        parser.add_argument("--"+name,required=True)
    args=parser.parse_args()
    q=control(args.request,args.request_sha256)
    auth=control(args.authorization,args.authorization_sha256)
    runtime=control(args.runtime,args.runtime_sha256)
    need(q["schema"]=="bcsp-ejtc-p1-cuda-v1" and q["status"]=="AWAITING_EXPLICIT_USER_AUTHORIZATION"
         and q["execution_authorized"] is False and [args.request,args.authorization,args.runtime]==q["control_paths"]
         and auth==dict(schema="bcsp-development-authorization-v1",request_sha256=args.request_sha256,
                       explicit_user_authorization=True,user_authorization_text=auth.get("user_authorization_text"))
         and isinstance(auth["user_authorization_text"],str) and args.request_sha256 in auth["user_authorization_text"]
         and runtime==dict(schema="bcsp-development-runtime-v1",request_sha256=args.request_sha256,
                           authorization_sha256=args.authorization_sha256),"separate exact execution authorization")
    i=q["identity"]
    need(sys.platform=="linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
         and (socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0],
              os.environ.get("CUDA_VISIBLE_DEVICES"))==
             (i["hostname"],i["uid"],i["python_realpath"],i["python_version"],i["gpu_uuid"]),"fresh identity")
    need(q["schedule"]==schedule(q["batches"]) and planned_counts(q["schedule"])==q["counts"]==COUNTS
         and q["initialization"]==list(SEEDS),"frozen budget and schedule")
    need(set(q["inputs"])==set(sum(q["batches"],[])) and len({r["source_id"] for r in q["inputs"].values()})==40,
         "40 training-only sources")
    bindings=q["bindings"]
    need(bindings["worker"]["path"]==str(Path(__file__).resolve()),"worker binding")
    parent=control(bindings["parent"]["path"],bindings["parent"]["sha256"])
    parent["identity"].update(i)
    support_rec=parent["p2_support"]
    p=Path(support_rec["path"])
    need(p.resolve(strict=True)==p and p.stat().st_size==support_rec["bytes"] and
         sha(p.read_bytes())==support_rec["sha256"],"P2 support bytes")
    support=load("ejtc_frozen_oasg_support",p)
    for x in [*bindings.values(),q["interpreter"]]:
        support.exact(x)
    prefix=load("ejtc_frozen_constructor",support.exact(bindings["prefix"]))
    native=load("ejtc_frozen_native",support.exact(bindings["native_loader"]))
    out=Path(q["output"])
    need(out.is_absolute() and out.resolve()==out and out.parent.is_dir() and not os.path.lexists(out),"fresh output")
    res=dict(output=str(out),resources=q["resources"],identity=i)
    need(q["resources"]["device_used_MiB"]<=.90*int(i["total_MiB"]),"90% hard cap")
    first=support.resources(res,out,initial=True)
    for k in ("CUBLAS_WORKSPACE_CONFIG","CUDA_CACHE_DISABLE","HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","MPLBACKEND"):
        os.environ[k]=parent["environment"][k]
    for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS"):
        os.environ[k]="1"
    out.mkdir()
    for k in ("TMPDIR","XDG_CACHE_HOME","MPLCONFIGDIR","TRITON_CACHE_DIR","HF_HOME"):
        os.environ[k]=str(out/k)
        (out/k).mkdir()
    stop=threading.Event()
    lock=threading.Lock()
    resource_peaks=[]
    begun=time.monotonic()

    def emit(r):
        with lock,(out/"events.jsonl").open("a",encoding="utf-8") as f:
            f.write(json.dumps(r,separators=(",",":"),allow_nan=False)+"\n")

    def sample():
        need(time.monotonic()-begun<=q["resources"]["wall_seconds"],"wall budget")
        stats=support.resources(res,out)
        emit(dict(event="resources",**stats))
        resource_peaks.append(stats["used_MiB"])

    def monitor():
        while not stop.wait(q["resources"]["monitor_interval_seconds"]):
            try:
                sample()
            except Exception as exc:
                emit(dict(event="resource_failure",error=repr(exc)))
                os._exit(29)

    emit(dict(event="initial_resources",**first))
    t=threading.Thread(target=monitor,daemon=True)
    t.start()
    try:
        sys.path.insert(0,parent["site_packages"])
        candidate=load("ejtc_candidate",support.exact(bindings["candidate"]))
        result=run(q,parent,support,native,prefix,candidate,out,emit,sample)
        if "peak_allocated" in result:
            need(max(result["peak_allocated"].values())<=q["resources"]["torch_peak_bytes"],"absolute PyTorch cap")
    except Exception as exc:
        emit(dict(event="failure",error=repr(exc)))
        raise
    finally:
        stop.set()
        t.join(q["resources"]["smi_timeout_seconds"]*2+1)
        need(not t.is_alive(),"monitor exit")
    result.update(request_sha256=args.request_sha256,max_sampled_SMI_MiB=max([first["used_MiB"],*resource_peaks]))
    with (out/"completion.json").open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,allow_nan=False)
    return 0 if result["status"]=="P1_CUDA_CONTRACT_PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())

