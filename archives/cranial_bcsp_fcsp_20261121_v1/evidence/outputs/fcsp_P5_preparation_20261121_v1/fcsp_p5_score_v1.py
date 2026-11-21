"""Score all three arms of P5 in identical coordinates using frozen surface references."""

import io
import json
import math
import os
import shutil
import sys
import tarfile
import time
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fcsp_p5_common_v1 as common
from fcsp_p5_common_v1 import append, clean, file_record, read, require, sha, write_json


ARMS = ("N", "B0-Global", "B1-Local")
PAIRS = ((ARMS[2], ARMS[1]), (ARMS[2], ARMS[0]), (ARMS[1], ARMS[0]))
COUNTS = dict(cases=210, scoring_rows=630, sources=42)
DEFECTS = {"bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"}


def read_npz(raw, required, exact=False):
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        require(set(required) <= set(z.files) and len(set(z.files)) == len(z.files), "NPZ fields")
        require(not exact or set(required) == set(z.files), "exact prediction NPZ fields")
        return {k: z[k] for k in required}


def tensor(array, shape):
    require(array.shape == shape and array.dtype == np.dtype("<f4") and np.isfinite(array).all(), "finite ordered FP32")
    return array


def area(weights, mask):
    return float(weights[mask].sum(dtype=np.float64))


def region_metrics(metric, dist, qdist, native_dist, weights, reach):
    require(len(weights)>0 and np.isfinite(weights).all() and np.all(weights>0), "positive region area")
    covered, qcovered = dist <= 2., qdist <= 2.
    total = float(weights.sum(dtype=np.float64))
    unmet = area(weights, ~qcovered)
    recovered = area(weights, ~qcovered & covered)
    transitions = dict(persistent=area(weights, qcovered & covered), recovered=recovered,
                       lost=area(weights, qcovered & ~covered), missed=area(weights, ~qcovered & ~covered))
    require(abs(sum(transitions.values())/total-1.) <= 1e-10, "coverage partition")
    require(abs((area(weights,covered)-area(weights,qcovered)-(recovered-transitions["lost"]))/total)<=1e-10,
            "net coverage conservation")
    s0_reach = ~qcovered & (native_dist <= reach)
    return dict(p95_mm=metric["weighted_quantile"](dist,weights),
                cover={str(t):area(weights,dist<=t)/total for t in (.5,1.,2.)},
                S0_area_mm2=unmet, region_area_mm2=total, S0_fraction=unmet/total,
                Rec=recovered/unmet if unmet/total>=.01 else None, AbsRec=recovered/total,
                transition_area_mm2=transitions,
                reachable_all_fraction=area(weights,native_dist<=reach)/total,
                reachable_S0_fraction=area(weights,s0_reach)/unmet if unmet/total>=.01 else None,
                reachable_S0_absolute_fraction=area(weights,s0_reach)/total)


def score_case(case, clouds, ref, gt, scale, metric):
    world = metric["world_points"]
    norm = case["normalization"]
    q = world(clouds["Q"],norm)
    point = {k:world(clouds[k].reshape(8192,3),norm) for k in ARMS}
    gt = world(gt,norm)
    a1,w1,j1=(ref[k] for k in ("a_centers","a_weights","a_is_j"))
    a2,w2,j2=metric["a2_reference"](ref)
    xyz={"A1":(a1,w1,j1),"A2":(a2,w2,j2)}
    # Reuse trees whose queries are shared between arms.
    qt = tree(q)
    a2t, gtt = tree(a2), tree(gt)
    qdist = {name:query(qt,v[0]) for name,v in xyz.items()}
    parent_far = np.repeat(query(a2t,q)>20.,32)
    native = tree(point["N"])
    ndist = {name:query(native,v[0]) for name,v in xyz.items()}
    reach = 2. + math.sqrt(3.)*scale*norm["scale"]
    rows = {}
    for arm,p in point.items():
        pt = native if arm=="N" else tree(p)
        regions = {}
        for name,(a,w,j) in xyz.items():
            require(j.dtype == np.bool_ and len(a)==len(w)==len(j), "reference mask/weights")
            dist = ndist[name] if arm=="N" else query(pt,a)
            regions[name] = {k:region_metrics(metric,dist[mask],qdist[name][mask],ndist[name][mask],w[mask],reach)
                             for k,mask in (("E",~j),("J",j))}
        reverse = query(a2t,p)
        far = reverse>20.
        trans = {f"parent_{int(u)}_child_{int(v)}":float(np.mean((parent_far==u)&(far==v)))
                 for u in (False,True) for v in (False,True)}
        require(abs(sum(trans.values())-1.)<1e-12, "parent/child partition")
        reverse_p95=metric["weighted_quantile"](reverse,np.ones(len(reverse)))
        cd=.5*(float(query(gtt,p).mean())+float(query(pt,gt).mean()))
        m=dict(E_Rec=regions["A1"]["E"]["Rec"], E_AbsRec=regions["A1"]["E"]["AbsRec"],
               E_P95_mm=regions["A1"]["E"]["p95_mm"],J_P95_mm=regions["A1"]["J"]["p95_mm"],
               J_Cover2=regions["A1"]["J"]["cover"]["2.0"],reverse_A2_P95_mm=reverse_p95,
               far20=float(far.mean()),CD_L1_mm=cd)
        require(all(v is None or math.isfinite(v) for v in m.values()), "finite case metrics")
        severe=m["E_P95_mm"]>20. or m["J_Cover2"]==0.
        rows[arm]=dict(metrics=m,regions=regions,reverse_A2_P95_mm=reverse_p95,far20=m["far20"],
                       far_transitions=trans,severe=severe,residual_reach_bound_mm=reach)
    return rows


def query(t, points):
    require(points.ndim==2 and points.shape[1]==3 and np.isfinite(points).all(), "finite world points")
    return np.concatenate([t.query(points[i:i+65536],workers=2)[0] for i in range(0,len(points),65536)])


def pair_case(case, rows):
    result = {}
    for a,b in PAIRS:
        x,y=rows[a],rows[b]
        metrics={}
        for k,u in x["metrics"].items():
            v=y["metrics"][k]
            require((u is None)==(v is None), f"paired missing metric: {k}")
            metrics[k]=None if u is None else u-v
        result[a+"-"+b]=dict(delta=metrics,risk=f"{int(y['severe'])}{int(x['severe'])}")
    return dict(fold=case["fold"],case_id=case["case_id"],source_id=case["source_id"],defect=case["defect"],comparisons=result)


def source_rows(pairs):
    groups={}
    for x in pairs:
        groups.setdefault((x["fold"],x["source_id"]),[]).append(x)
    require(len(groups)==42 and all(sum(k[0]==fold for k in groups)==21 for fold in "CD"), "exact 42 sources")
    rows=[]
    for (f,s),group in sorted(groups.items()):
        require(len(group)==5 and {r["defect"] for r in group}==DEFECTS, f"complete source: {s}")
        comparisons={}
        for a,b in PAIRS:
            name=a+"-"+b
            values=[x["comparisons"][name] for x in group]
            summary={}
            for k in values[0]["delta"]:
                finite=[x["delta"][k] for x in values if x["delta"][k] is not None]
                summary[k]=dict(mean=math.fsum(finite)/len(finite) if finite else None, cases=len(finite))
            comparisons[name]=dict(delta=summary,risk={k:sum(x["risk"]==k for x in values) for k in ("00","01","10","11")})
        rows.append(dict(fold=f,source_id=s,comparisons=comparisons))
    return rows


def anchor_replay(record, historical):
    g=historical["metrics"]
    m=record["metrics"]
    d=record["regions"]["A1"]
    for region in ("E","J"):
        require(abs(d[region]["p95_mm"]-g[f"{region}_P95_mm"])<=1e-9, "native P95 replay")
        for t in (".5","1.0","2.0"):
            z="0.5" if t==".5" else t
            require(abs(d[region]["cover"][z]-g[f"{region}_coverage_{z}mm"])<=1e-12, "native coverage replay")
    require(abs(m["CD_L1_mm"]-g["CD_L1_mm"])<=1e-9
            and abs(m["reverse_A2_P95_mm"]-g["reverse_A2_P95_mm"])<=1e-9
            and m["far20"]==g["reverse_A2_outlier_20.0mm"]
            and record["severe"]==historical["risk_labels"]["severe_geometry"],"native reverse/CD/risk replay")


def manifest_lookup(t, idx, prediction_request_hash):
    names=t.getnames()
    cases={(r["fold"],r["case_id"]):r for r in idx["cases"]}
    require(len(idx["cases"])==len(cases)==210 and idx["counts"]==COUNTS,"fixed local case set")
    expected={f"predictions/{f}__{c}__{a}.npz" for f,c in cases for a in ARMS}
    extras={"completion.json","prediction_manifest.jsonl","head_forward_journal.jsonl"}
    require(set(names)==expected|extras and len(names)==len(expected|extras)
            and all(item.isfile() and not PurePosixPath(item.name).is_absolute() and ".." not in PurePosixPath(item.name).parts
                    and 0<item.size<=1048576 for item in t.getmembers()), "safe, exact prediction archive set")
    complete=json.load(t.extractfile("completion.json"))
    require(complete["status"]=="AWAITING_READ_ONLY_PREDICTION_FREEZE_AUDIT"
            and complete["request_sha256"]==prediction_request_hash and complete["state_and_rng_equal"] is True
            and complete["counts"]==dict(cases=210,head_forward=420,shared_native=210,donor_forward=0,optimizer_step=0)
            and set(complete["snapshots"])=={f+"/"+a for f in "CD" for a in ARMS[1:]}, "frozen inference completion")
    rows=list(map(json.loads,t.extractfile("prediction_manifest.jsonl").read().splitlines()))
    journal=list(map(json.loads,t.extractfile("head_forward_journal.jsonl").read().splitlines()))
    result={}
    ordered=[]
    require(len(rows)==630 and len(journal)==420,"full manifest/journal")
    for r in rows:
        f,c,a=(r[k] for k in ("fold","case_id","arm"))
        require((f,c) in cases and a in ARMS and (f,c,a) not in result
                and r["member"]==f"predictions/{f}__{c}__{a}.npz"
                and t.getmember(r["member"]).size==r["bytes"],"prediction manifest identity")
        require(r["cache_sha256"]==cases[f,c]["cache_sha256"],"scoring index/cache binding")
        result[f,c,a]=r
        if a!="N":
            ordered.append(dict(index=len(ordered)+1,fold=f,case_id=c,arm=a,status="CLAIMED_BEFORE_HEAD_FORWARD"))
    require(journal==ordered and len(result)==630,"exact prediction attempts")
    return result


def score_all(q, idx, t, metric, historical, out, request_sha):
    lookup=manifest_lookup(t,idx,q["prediction_request_sha256"])
    require(set(historical)=={(r["fold"],r["case_id"]) for r in idx["cases"]},"210 historical anchors")
    start=time.monotonic()
    pairs=[]
    with (out/"case_metrics.jsonl").open("x",encoding="utf-8",newline="\n") as f, (
            out/"paired_cases.jsonl").open("x",encoding="utf-8",newline="\n") as fp:
        for row in idx["cases"]:
            require(time.monotonic()-start<=q["limits"]["wall_seconds"],"CPU scoring wall budget")
            fold,case=row["fold"],row["case_id"]
            clouds={}
            for arm in ARMS:
                r=lookup[fold,case,arm];raw=t.extractfile(r["member"]).read()
                require(len(raw)==r["bytes"] and sha(raw)==r["sha256"],"archived prediction hash")
                if arm=="N":
                    z=read_npz(raw,("Q","P0"),exact=True)
                    clouds["Q"]=tensor(z["Q"],(256,3));clouds["N"]=tensor(z["P0"],(256,32,3))
                    require(sha(z["Q"].tobytes())==row["shared_Q_sha256"]
                            and sha(z["P0"].tobytes())==row["shared_P0_sha256"],"same-case shared native Q/P")
                else:
                    clouds[arm]=tensor(read_npz(raw,("prediction",),exact=True)["prediction"],(256,32,3))
            gt=row["ground_truth"]
            require(gt["member"]=="implant","isolated GT member")
            label=tensor(read_npz(read(gt["file"],262144),("implant",))["implant"],(8192,3))
            require(sha(label.tobytes())==gt["member_sha256"],"frozen GT")
            ref=read_npz(read(row["reference"],8388608),("a_centers","a_weights","a_is_j","a_axes","affine"))
            v=score_case(row,clouds,ref,label,q["fold_scales"][fold],metric)
            anchor_replay(v["N"],historical[fold,case])
            for arm,values in v.items():
                append(f,dict(fold=fold,case_id=case,source_id=row["source_id"],arm=arm,
                              prediction_diagnostics=lookup[fold,case,arm]["diagnostics"],**values))
            p=pair_case(row,v);append(fp,p);pairs.append(p)
    require(len(pairs)==210 and time.monotonic()-start<=q["limits"]["wall_seconds"],"score completion")
    write_json(out/"source_metrics.json",source_rows(pairs))
    risks={fold:{a+"-"+b:{k:sum(x["comparisons"][a+"-"+b]["risk"]==k for x in pairs if x["fold"]==fold)
                          for k in ("00","01","10","11")} for a,b in PAIRS} for fold in "CD"}
    write_json(out/"risk_transitions.json",risks)
    files={p.name:file_record(p) for p in out.iterdir()}
    require(sum(x["bytes"] for x in files.values())<=q["limits"]["output_bytes"],"CPU score output bound")
    write_json(out/"completion.json",dict(status="AWAITING_READ_ONLY_SCORING_FREEZE_AUDIT",request_sha256=request_sha,
               counts=COUNTS,native_replay_cases=210,files=files,P6_executed=False))


def load_numeric():
    global np, tree
    import numpy as np
    from scipy.spatial import cKDTree as tree


def run(a):
    q=common.authorize(a,"score")
    require(sys.flags.isolated and sys.dont_write_bytecode and os.environ.get("CUDA_VISIBLE_DEVICES")=="",
            "isolated CPU scoring")
    require(q["counts"]==COUNTS and clean(q["entry"]["path"])==Path(__file__).resolve()
            and clean(q["common"]["path"])==Path(common.__file__).resolve()
            and clean(q["python"]["path"])==Path(sys.executable).resolve(), "frozen score paths")
    for n in ("entry","common","python"):
        read(q[n],1048576)
    out=clean(q["output"])
    require(not out.exists() and out.parent.is_dir()
            and shutil.disk_usage(out.parent).free>=q["limits"]["minimum_free_disk_bytes"],"fresh CPU output")
    load_numeric()
    import scipy
    require(dict(numpy=np.__version__,scipy=scipy.__version__)==q["packages"],"frozen score packages")
    idx=json.loads(read(q["input_index"],524288))
    require(idx["schema"]=="fcsp-p5-local-score-index-v2","frozen scorer index schema")
    src=idx["reference_metric_source"];metric={}
    exec(compile(read(src,65536),src["path"],"exec"),metric)
    records=list(map(json.loads,read(q["historical_case_metrics"],8388608).splitlines()))
    hist={(x["fold"],x["case_id"]):x for x in records if x["arm"]=="G2"}
    require(len(hist)==sum(x["arm"]=="G2" for x in records)==210,"frozen G2 score rows")
    b=read(q["prediction_archive"],134217728)
    out.mkdir()
    try:
        with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:
            score_all(q,idx,t,metric,hist,out,a.request_sha256)
    except Exception as exc:
        write_json(out/"failure.json",dict(status="FAILED_STOP_NO_RETRY",error=repr(exc)))
        raise


if __name__=="__main__":
    run(common.args())
