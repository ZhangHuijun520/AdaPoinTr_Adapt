"""Authorized P1 only. Exercise unchanged OASG+LQI with one order substitution."""
import argparse
import base64
from contextlib import ExitStack, nullcontext
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import time


def need(ok, msg):
    if not ok:
        raise ValueError(msg)


def source(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def verdict(np, times, peaks, steps):
    metrics = {}
    margins = {}
    for path in ("hot", "cold"):
        t = {a: [x for x in times[path][a]] for a in "RCS"}
        need(all(len(x) == 25 for x in t.values()), "exact timing sample count")
        metrics[path] = {a: dict(p50=float(np.percentile(v, 50)), p95=float(np.percentile(v, 95)))
                         for a, v in t.items()}
        m = metrics[path]
        for a in "CS":
            if path == "hot":
                margins[path + a] = m[a]["p50"] <= 1.25*m["R"]["p50"] and m[a]["p95"] <= 1.50*m["R"]["p95"]
            else:
                margins[path + a] = (m[a]["p50"] <= min(250, 3*m["R"]["p50"])
                                     and m[a]["p95"] <= min(500, 4*m["R"]["p95"]))
    for a in "CS":
        for kind in ("hot", "cold", "batch8"):
            margins["allocated_" + kind + a] = peaks[kind][a] <= 1.10 * peaks[kind]["R"]
    need(all(len(v) == 3 for v in steps.values()), "three batch8 observations per arm")
    return dict(timing_ms=metrics, allocated_peaks=peaks, step_ms=steps, gates=margins,
                base_training_wall_seconds=11700 * max(x for v in steps.values() for x in v) * 1.3 / 1000,
                passed=all(margins.values()))


def plane_signature(plane):
    return [dict(best=part["best"]["abc"] if part["best"] is not None else None,
                 coarse=[(r["abc"], r["valid"], r["counts"], r["donors"]) for r in part["coarse"]],
                 fine=[(r["abc"], r["valid"], r["counts"], r["donors"]) for r in part["fine"]])
            for part in plane["splits"]]


def cold_order(np, geo, orderlib, x, anchors, spec):
    frame = spec["normalization"]
    center, scale = np.asarray(frame["center"]), frame["scale"]
    p = geo.fit_plane(x.astype(np.float64) * scale + center)
    seq = geo.plan_orders(anchors, anchors.astype(np.float64) * scale + center, p)
    signature = orderlib.sha(json.dumps(plane_signature(p), separators=(",", ":")).encode())
    need(signature == spec["candidate_signature"] and seq["joint_active"] == spec["active"]
         and seq["order"] == spec["orders"] and seq["inverse"] == spec["inverse"]
         and seq["reasons"] == spec["reasons"], "cold geometry runtime differs from frozen CPU result")
    return seq["order"], seq["inverse"]


def run(q, request_sha, prefix, orderlib, geo, out, support, parent, started):
    import resource

    native = support.source("rbss_p1_oasg_loader", q["bindings"]["native_loader"])
    torch, np, helper, _ = native.prepare_models(parent, support)
    from scipy import __version__ as scipy_version
    need((np.__version__, scipy_version) == tuple(q["geometry_runtime"]), "geometry runtime binding")
    helper._MONITOR = None
    model, target = prefix.build_model(parent, support, torch, helper, *q["initialization"])
    model = model.to("cuda:0")
    state = helper.state_sha(model)
    training_flags = [(m, m.training) for m in model.modules()]
    base = model.base_model
    root = Path(parent["data_root"])
    points, labels = {}, {}
    for cid, spec in q["inputs"].items():
        f = support.exact(dict(path=str(root / spec["path"]), bytes=spec["bytes"], sha256=spec["npz_sha256"]))
        with np.load(io.BytesIO(f.read_bytes()), allow_pickle=False) as z:
            x, y = z["partial"], z["implant"]
        need(x.shape == y.shape == (8192,3) and x.dtype == y.dtype == np.float32
             and np.isfinite(x).all() and np.isfinite(y).all() and orderlib.sha(x.tobytes()) == spec["input_sha256"], cid)
        points[cid], labels[cid] = x, y
    for cid in q["active"]:
        spec = q["inputs"][cid]
        raw = base64.b64decode(spec["cold_anchor_reference"], validate=True)
        need(len(raw) == 256 * 12 and orderlib.sha(raw) == spec["anchors_sha256"], "cold comparison asset")
        cold_order(np, geo, orderlib, points[cid], np.frombuffer(raw, dtype="<f4").reshape(256,3), spec)
    prefix.emit(out/"cold_equivalence.json", dict(cases=q["active"], forward_calls=0,
                                                  geometry_runtime=q["geometry_runtime"]), "x")
    decoder = base.decoder
    mixmods = [m.mixer for m in (b.attn for b in base.encoder.blocks.blocks)]
    mixmods.extend(m for block in decoder.blocks for m in (block.self_ssm, block.cond_ssm))
    need(len({id(m) for m in mixmods}) == 22, "22 distinct native Mamba modules")
    attnmods = [m for m in model.modules() if type(m).__name__.lower() in
                {"attention","crossattention","multiheadattention","selfattention","attn"}]
    times = {k:{a:[] for a in "RCS"} for k in ("hot","cold")}
    step_times = {a:[] for a in "RCS"}
    peaks = {k:{a:0 for a in "RCS"} for k in ("hot","cold","batch8")}
    counts = dict(forward=0,loss=0,backward=0,optimizer_steps=0)
    references = []
    native_hash = {}
    tol = None

    def emit(file, record):
        prefix.emit(out/file, record, "a")

    def compare(first, other):
        need(len(first) == len(other) and all(a.shape==b.shape and a.device==b.device for a,b in zip(first,other)), "trace shape/device")
        return max(float((a-b).abs().max()) for a,b in zip(first,other))

    geometry_id = q["bindings"]["geometry"]["sha256"]
    cache = {}
    for row in q["schedule"]:
        phase, arm, cases, kind = (row[k] for k in ("phase","arm","cases","kind"))
        need(counts["forward"] + 1 == row["index"] <= 200, "forward budget")
        training = phase=="batch8"
        contract = phase in ("native","forced","manipulation")
        model.train(training)
        helper.assert_numeric(torch)
        buffers = {n:v.clone() for n,v in model.named_buffers()} if training else {}
        state_check = {}
        captures, chosen = [], []
        mix_count = [0,0]
        batch = [points[c] for c in cases]
        start = end = peak = reserved = 0

        def select(pos, native_order, inverse):
            per_order, per_inverse = [], []
            for j,cid in enumerate(cases):
                spec=q["inputs"][cid]
                a=pos[j].detach().cpu().numpy()
                o=native_order[j].detach().cpu().numpy()
                frame=spec["normalization"]
                key=orderlib.content_key(batch[j],frame,a,o,geometry_id,"RBSS-v2")
                need(orderlib.sha(batch[j].tobytes())==spec["input_sha256"],"input identity")
                need(orderlib.sha(a.tobytes())==spec["anchors_sha256"] and o.tolist()==spec["orders"]["R"],
                     "live anchors differ from P0c")
                if kind=="cold":
                    plan, inv = cold_order(np, geo, orderlib, batch[j], a, spec)
                else:
                    # The key includes the actual tensor bytes, frame, version and native permutation.
                    plan,inv=cache.setdefault(key,(spec["orders"],spec["inverse"]))
                    need(plan==spec["orders"] and inv==spec["inverse"],"content cache collision")
                active=spec["active"] and phase!="forced"
                selected=arm if active else "R"
                if contract:
                    chosen.append(dict(case=cid, active=active, order=plan[selected], inverse=inv[selected], anchor_sha256=spec["anchors_sha256"]))
                per_order.append(plan[selected]);per_inverse.append(inv[selected])
            if arm=="R" or (phase!="forced" and not any(q["inputs"][cid]["active"] for cid in cases)):
                return None
            return (torch.tensor(per_order,device=pos.device,dtype=torch.long),
                    torch.tensor(per_inverse,device=pos.device,dtype=torch.long))

        def coarse_hook(_m, args, result):
            need(not captures and len(args)==3 and len(result)==2,"one OASG head trace")
            captures.extend(v.detach().clone() for v in (args[1],args[0],result[0],args[2]))

        def hook(index):
            def record(*_):
                mix_count[index]+=1
            return record

        model.zero_grad(set_to_none=True)
        emit("attempts.jsonl",row)
        with helper.rng_preserved(torch,np,cuda=True,evidence=state_check), ExitStack() as stack:
            stack.enter_context(nullcontext() if training else torch.no_grad())
            if contract:
                stack.callback(base.coarse_pred.register_forward_hook(coarse_hook).remove)
                for i,modules in enumerate((mixmods,attnmods)):
                    for mod in modules:
                        stack.callback(mod.register_forward_hook(hook(i)).remove)
            if phase!="native" and (arm!="R" or contract):
                stack.enter_context(orderlib.temporary_order(target,torch,select))
            try:
                torch.cuda.synchronize()
                torch.cuda.reset_peak_memory_stats()
                start=time.perf_counter()
                x=torch.from_numpy(np.stack(batch)).to("cuda:0")
                counts["forward"]+=1
                ret=model(x)
                if training:
                    need(counts["loss"]<9 and counts["backward"]<9,"gradient budget")
                    y=torch.from_numpy(np.stack([labels[c] for c in cases])).to("cuda:0")
                    counts["loss"]+=1
                    den,recon=model.get_loss(ret,y,0,partial=x)
                    loss=den+recon
                    need(bool(torch.isfinite(loss)) and float(den.detach())==0.0,"inherited loss")
                    counts["backward"]+=1
                    loss.backward()
                torch.cuda.synchronize()
                end=time.perf_counter()
                peak=torch.cuda.max_memory_allocated()
                reserved=torch.cuda.max_memory_reserved()
                if training:
                    grads={id(p):p.grad for p in model.parameters() if p.grad is not None}
                    needed=(target.mixer,base.coarse_pred,base.grouper,base.decoder,model.decode_head)
                    need(grads and all(bool(torch.isfinite(g).all()) for g in grads.values())
                         and all(any(id(p) in grads and bool((grads[id(p)]!=0).any()) for p in m.parameters()) for m in needed),
                         "finite nonzero gradients in selected and inherited branches")
            finally:
                with torch.no_grad():
                    for name,buff in model.named_buffers():
                        if name in buffers:buff.copy_(buffers[name])
                model.zero_grad(set_to_none=True)
        need(state_check.get("rng_restored") and all(torch.equal(b,buffers[n]) for n,b in model.named_buffers() if n in buffers),
             "restored RNG and buffers")
        elapsed=(end-start)*1000
        if contract:
            need(mix_count==[36,0] and len(captures)==4 and isinstance(ret,(tuple,list)) and len(ret)==2,"SSM/attention count and trace")
            need(all(v.device==x.device and bool(torch.isfinite(v).all()) for v in (*captures,ret[-1])),"trace finite, same device")
            actual=[v for v in (*captures,ret[-1])]
            if phase=="native":
                references.append(actual)
                if len(references)==2:
                    error=compare(*references)
                    need(error<=1e-5,"native replay drift")
                    tol=min(1e-5,max(1e-6,2*error))
            elif phase=="forced":
                need(len(chosen)==1 and chosen[0]["order"]==q["inputs"][cases[0]]["orders"]["R"]
                     and compare(references[0],actual)<=tol,"forced native parity")
            elif arm=="R":
                native_hash[cases[0]]=actual
            elif not q["inputs"][cases[0]]["active"]:
                need(chosen[0]["order"]==q["inputs"][cases[0]]["orders"]["R"]
                     and compare(native_hash[cases[0]],actual)<=tol,"fallback parity")
            else:
                need(chosen[0]["order"]==q["inputs"][cases[0]]["orders"][arm]
                     and chosen[0]["order"]!=q["inputs"][cases[0]]["orders"]["R"],"effective target permutation")
        if phase=="timed":
            times[kind][arm].append(elapsed)
            peaks[kind][arm]=max(peaks[kind][arm],peak)
        if training:
            step_times[arm].append(elapsed)
            peaks["batch8"][arm]=max(peaks["batch8"][arm],peak)
        r=q["binding"]["resources"]
        rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
        need(time.monotonic()-started<=r["wall_seconds"] and rss<=r["rss_bytes"]
             and peak<=r["torch_peak_bytes"] and shutil.disk_usage(out).free>=r["minimum_disk_bytes"],"resource cap")
        gpu = prefix.gpu_sample(q,out,started,torch) if training or row["index"] in (1,20,110,200) else None
        emit("records.jsonl",dict(**row,ms=elapsed,peak_allocated=peak,peak_reserved=reserved,RSS_bytes=rss,gpu=gpu,
                                 restored=True,gradients_verified=training,contract_observations=chosen,
                                 native_ssm_calls=mix_count[0] if contract else None,native_attention_calls=mix_count[1] if contract else None))
        del ret, x
        if training:
            del y,loss,recon,den,grads
    for module, training in training_flags:
        module.training = training
    need(counts==q["counts"] and helper.state_sha(model)==state
         and all(m.training==v for m,v in training_flags),"exact execution counts and persistent state")
    need(sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) <= q["binding"]["resources"]["output_bytes"], "output bytes")
    report=verdict(np,times,peaks,step_times)
    report.update(request_sha256=request_sha,counts=counts,state_sha256=state,tolerance=tol,
                  status="P1_CUDA_COMPLETE_PENDING_FREEZE_AUDIT" if report["passed"] else "P1_RESOURCE_GATE_FAIL_STOP")
    prefix.emit(out/"completion.json",report,"x")


def main():
    import hashlib

    p=argparse.ArgumentParser()
    for k in ("request","request-sha256","authorization","authorization-sha256","runtime","runtime-sha256"):
        p.add_argument("--"+k,required=True)
    a=p.parse_args()
    def bound(path, sha):
        f=Path(path)
        raw=f.read_bytes()
        need(f.resolve()==f and hashlib.sha256(raw).hexdigest()==sha,"exact bound bytes "+str(f))
        return raw
    q=json.loads(bound(a.request,a.request_sha256))
    auth=json.loads(bound(a.authorization,a.authorization_sha256))
    rt=json.loads(bound(a.runtime,a.runtime_sha256))
    need(q["status"]=="AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["execution_authorized"] is False
         and q["schema"]=="bcsp-rbss-p1-cuda-v1" and sys.platform=="linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,"frozen request")
    need(set(auth)=={"schema","request_sha256","explicit_user_authorization","user_authorization_text"}
         and auth.get("schema")=="bcsp-development-authorization-v1"
         and auth.get("request_sha256")==a.request_sha256 and auth.get("explicit_user_authorization") is True
         and bool(auth.get("user_authorization_text","").strip())
         and rt==dict(schema="bcsp-development-runtime-v1",request_sha256=a.request_sha256,authorization_sha256=a.authorization_sha256),
         "separate execution authorization")
    b=q["binding"];i=b["identity"]
    need((socket.gethostname(),os.getuid(),os.environ.get("CUDA_VISIBLE_DEVICES"),
          str(Path(sys.executable).resolve()),sys.version.split()[0])==
         (i["hostname"],i["uid"],i["gpu_uuid"],i["python_realpath"],i["python_version"]),"fresh server identity")
    need(Path(q["bindings"]["worker"]["path"])==Path(__file__).resolve(),"worker path")
    for rec in list(q["bindings"].values())+q["scipy_files"]:
        bound(rec["path"],rec["sha256"])
    prefix=source(Path(q["bindings"]["prefix"]["path"]))
    order=source(Path(q["bindings"]["order"]["path"]))
    need(q["schedule"]==order.schedule(q["active"],q["fallback"],q["batch"])
         and q["counts"]==dict(forward=200,loss=9,backward=9,optimizer_steps=0),"fixed 200/9/9/0 schedule")
    out=Path(b["output"])
    need(out.resolve()==out and out.parent.is_dir() and not os.path.lexists(out),"new output only")
    started=time.monotonic()
    gpu=prefix.gpu_sample(q,out,started)
    out.mkdir()
    prefix.emit(out/"startup.json",gpu,"x")
    parent=json.loads(bound(b["historical_request"],prefix.PARENT_SHA))
    parent["identity"].update(i)
    for k in ("CUBLAS_WORKSPACE_CONFIG","CUDA_CACHE_DISABLE","HF_HUB_OFFLINE","TRANSFORMERS_OFFLINE","MPLBACKEND"):
        os.environ[k]=parent["environment"][k]
    for k in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS"):
        os.environ[k]="1"
    for k in ("TMPDIR","XDG_CACHE_HOME","MPLCONFIGDIR","TRITON_CACHE_DIR","HF_HOME"):
        os.environ[k]=str(out/k)
        (out/k).mkdir()
    support=prefix.load_support(parent)
    sys.path.append(parent["site_packages"])
    geo=source(Path(q["bindings"]["geometry"]["path"]))
    run(q,a.request_sha256,prefix,order,geo,out,support,parent,started)


if __name__=="__main__":
    main()
