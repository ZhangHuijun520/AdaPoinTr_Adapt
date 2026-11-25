"""One authorized CPU run: recover development labels, then score R/U/I."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

os.environ.update(CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="2",
                  OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2")
import numpy as np
import psutil
import scipy
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


ARMS = ("R", "U", "I")
COMPARISONS = (("I", "R"), ("I", "U"), ("U", "R"))
SCHEMA = "bcsp-cisc-rui-d-cpu-score-v1"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(record):
    path = Path(record["path"])
    need(path.is_absolute() and path.resolve(strict=True) == path and path.is_file()
         and path.stat().st_size == record["bytes"], f"bound file: {path}")
    raw = path.read_bytes()
    need(digest(raw) == record["sha256"], f"bound SHA256: {path}")
    return raw


def json_file(record):
    return json.loads(read(record))


def module(record, name):
    raw = read(record)
    spec = importlib.util.spec_from_file_location(name, record["path"])
    obj = importlib.util.module_from_spec(spec)
    exec(compile(raw, record["path"], "exec"), obj.__dict__)
    return obj


def emit(path, obj):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(obj, stream, indent=2, allow_nan=False)
        stream.write("\n")


def bind_case_index(q):
    facts = json_file(q["readiness"])
    fold = json_file(q["fold"])["folds"]["D"]
    manifest = {r["case_id"]: r for r in map(json.loads, read(q["point_manifest"]).splitlines())}
    cases = json_file(q["case_index"])["cases"]
    ids = [c["case_id"] for c in cases]
    need(ids == facts["development_case_ids"] == fold["dev_case_ids"] and len(set(ids)) == 105
         and not set(ids) & set(fold["train_case_ids"]), "fixed development cases")
    need(Counter(c["source_id"] for c in cases) == Counter({s: 5 for s in q["sources"]}),
         "21 fixed development sources")
    for case in cases:
        row = manifest[case["case_id"]]
        need(case["source_id"] == row["source_id"] and case["normalization"] == row["normalization"]
             and case["target_array_sha256"] == row["target_array_sha256"]
             and case["point_file"]["sha256"] == row["sha256"], "case index and point identity")
        for record in row["raw"].values():
            need(facts["raw_pins"][record["path"]] == record["sha256"], "exact raw scoring data")
    return cases, manifest


def surface_components(keys):
    """Connected components of voxel faces joined along full edges."""
    face_ids = np.arange(len(keys))
    edges = []
    for tangent in (1, 2):
        for sign in (-1, 1):
            centers = keys[:, 1:].copy()
            centers[face_ids, (keys[:, 0] + tangent) % 3] += sign
            orientation = ((keys[:, 0] + 3 - tangent) % 3)[:, None]
            edges.append(np.column_stack((orientation, centers)))
    edges = np.concatenate(edges)
    faces = np.tile(face_ids, 4)
    order = np.lexsort(edges.T[::-1])
    links = np.all(edges[order[:-1]] == edges[order[1:]], axis=1)
    graph = coo_matrix((np.ones(int(links.sum()), dtype=bool),
                        (faces[order[:-1][links]], faces[order[1:][links]])),
                       shape=(len(keys), len(keys)))
    return connected_components(graph, directed=False)


def check_replay_frame(points, frozen, recomputed_center, recomputed_scale, partial, cid):
    center = np.asarray(frozen["center"], dtype=np.float64)
    scale = float(frozen["scale"])
    current = np.asarray(recomputed_center, dtype=np.float64)
    need(center.shape == current.shape == (3,) and np.isfinite(center).all()
         and np.isfinite(current).all() and np.isfinite(scale) and np.isfinite(recomputed_scale)
         and scale > 0 and recomputed_scale > 0, f"{cid} valid coordinate frames")
    replayed = ((points - center) / scale).astype(np.float32)[:8192]
    need(replayed.shape == partial.shape == (8192, 3) and partial.dtype == np.float32,
         f"{cid} ordered replay shape and dtype")
    equal = replayed.tobytes() == partial.tobytes()
    evidence = dict(
        case_id=cid, replay_frame="frozen",
        frozen=dict(center=center.tolist(), scale=scale),
        recomputed=dict(center=current.tolist(), scale=float(recomputed_scale)),
        center_difference_mm=(current - center).tolist(),
        scale_difference_mm=float(recomputed_scale - scale),
        frozen_scale_hex=scale.hex(), recomputed_scale_hex=float(recomputed_scale).hex(),
        input_rows=8192, input_row_bytes_identical=equal,
    )
    print("REPLAY_FRAME " + json.dumps(evidence, allow_nan=False), flush=True)
    need(equal, f"{cid} ordered point replay")
    return evidence


def replay(q, out, cid):
    cases, rows = bind_case_index(q)
    case = next(c for c in cases if c["case_id"] == cid)
    row = rows[cid]
    for binding in (q["reader"], q["source_protocol"]):
        read(binding)
    sampler = module(q["sampler"], "cisc_development_sampler")
    paths = {k: Path(v["path"]) for k, v in row["raw"].items()}
    need(all(p.resolve(strict=True) == p and sampler.sha(p) == row["raw"][k]["sha256"]
             for k, p in paths.items()), f"{cid} raw masks")
    d, affine, origin = sampler.raw.read_mask(paths["defective"])
    sd = sampler.surface(d)
    points, face_ids, _, weights = sampler.sample(sd, affine, origin, 0, 16384)
    center, scale = sampler.frame(d, affine, origin)
    with np.load(io.BytesIO(read(case["point_file"])), allow_pickle=False) as bundle:
        partial = bundle["partial"]
    frame_evidence = check_replay_frame(points, case["normalization"], center, scale, partial, cid)
    g, ga, go = sampler.raw.read_mask(paths["implant"])
    c, ca, co = sampler.raw.read_mask(paths["complete"])
    need(d.shape == g.shape == c.shape and np.array_equal(affine, ga) and np.array_equal(affine, ca)
         and np.array_equal(origin, go) and np.array_equal(origin, co)
         and not np.any(d & g) and np.array_equal(c, d | g), f"{cid} complementary masks")
    del c
    jd = sampler.contact(sd, g)
    sg = sampler.surface(g)
    jg = sampler.contact(sg, d)
    dk, ds = sampler.keys(sd, jd)
    gk, gs = sampler.keys(sg, jg)
    need(len(dk) and np.array_equal(dk, gk) and np.array_equal(ds, -gs), f"{cid} paired faces")
    _, wg = sampler.face_geometry(sg, affine, origin)
    need(np.isclose(weights[jd].sum(), wg[jg].sum(), rtol=1e-12), f"{cid} J area")
    n_components, components = surface_components(dk)
    src_face = np.flatnonzero(jd)
    xyz, axis, sign = sd
    centers = xyz[src_face].astype(np.int64) * 2
    centers[np.arange(len(src_face)), axis[src_face]] += sign[src_face]
    raw_keys = np.column_stack((axis[src_face], centers))
    indices = np.lexsort(raw_keys.T[::-1])
    need(np.array_equal(raw_keys[indices], dk), f"{cid} component face identity")
    by_face = np.full(len(xyz), -1, dtype=np.int32)
    by_face[src_face[indices]] = components
    face_ids = face_ids[:8192]
    is_j = jd[face_ids]
    emit(out / "labels" / (cid + ".json"), dict(case_id=cid, positive=int(is_j.sum()),
         points_sha256=digest(partial.tobytes()), interface_faces=len(dk),
         components=n_components, j_area_mm2=float(weights[jd].sum()), replay_frame=frame_evidence))
    with (out / "labels" / (cid + ".npz")).open("xb") as stream:
        np.savez_compressed(stream, is_j=is_j, component=by_face[face_ids], face_id=face_ids)


def soft_ap(p, w, t):
    positive = float(w @ t)
    if positive <= 0 or positive >= 1:
        return None
    order = np.argsort(-p, kind="stable")
    ends = np.r_[np.flatnonzero(p[order][1:] != p[order][:-1]), len(order) - 1]
    tp = np.cumsum((w * t)[order])[ends]
    total = np.cumsum(w[order])[ends]
    valid = total > 0
    return float(np.sum(np.diff(np.r_[0, tp[valid]]) * tp[valid] / total[valid]) / positive)


def decode(raw, arm):
    base = {"coarse", "prediction", "parent_index", "S", "delta", "token_index"}
    extra = {"logits", "p", "v", "n", "c", "V", "r", "uniform_r"}
    expect = base if arm == "R" else base | extra
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        need(set(z.files) == expect and len(z.files) == len(expect), "exact prediction payload")
        a = {k: z[k] for k in expect}
    shapes = dict(coarse=(256, 3), prediction=(8192, 3), S=(256, 3), delta=(256, 3))
    if arm != "R":
        shapes.update(logits=(256,), p=(256,), c=(3,), V=(6,), r=(256,), uniform_r=(256,))
    for k, shape in shapes.items():
        need(a[k].shape == shape and a[k].dtype == np.float32 and np.isfinite(a[k]).all(), f"shape/dtype of {k}")
    token = np.arange(256, dtype=np.int64)
    need(a["token_index"].dtype == a["parent_index"].dtype == np.int64
         and np.array_equal(a["token_index"], token)
         and np.array_equal(a["parent_index"], np.repeat(token, 32))
         and np.array_equal(a["S"] + a["delta"], a["coarse"]), "anchor and FC identity")
    return a


def mechanism(a, x, y, component, norm, prior):
    v, count = a["v"], a["n"]
    need(v.dtype == count.dtype == np.int64 and v.shape == (8192,) and count.shape == (256,)
         and v.min() >= 0 and v.max() < 256 and np.array_equal(np.bincount(v, minlength=256), count),
         "token assignment")
    need(y.shape == v.shape and y.dtype == np.bool_ and np.array_equal(y, component >= 0), "label arrays")
    pc = a["p"].astype(np.float64)
    need(np.all((pc >= 0) & (pc <= 1)), "token probabilities")
    w = count / 8192
    t = np.bincount(v, weights=y, minlength=256) / np.maximum(count, 1)
    pi = float(y.mean())
    ap = soft_ap(pc, w, t) if 0 < pi < 1 else None
    cov = np.zeros((3, 3), dtype=np.float64)
    tri = (np.array([0, 1, 2, 0, 0, 1]), np.array([0, 1, 2, 1, 2, 2]))
    cov[tri] = a["V"]
    cov[(tri[1], tri[0])] = a["V"]
    xyz = x.astype(np.float64)
    center = xyz.mean(axis=0)
    shifted = xyz - center
    uniform_cov = shifted.T @ shifted / len(xyz)
    support = a["r"].astype(np.float64)[v]
    alpha = support / support.sum()
    native_center = alpha @ xyz
    native_diff = xyz - native_center
    native_cov = (native_diff * alpha[:, None]).T @ native_diff
    need(np.allclose(a["c"], native_center, rtol=2e-5, atol=2e-6)
         and np.allclose(cov, native_cov, rtol=2e-5, atol=2e-6), "saved U/I moment identity")
    mixed = 0
    if y.any():
        pairs = np.unique(np.column_stack((v[y], component[y])), axis=0)
        mixed = int(np.sum(np.bincount(pairs[:, 0], minlength=256) > 1))
    return dict(soft_AP=ap, pi=pi, AP_minus_pi=None if ap is None else ap - pi,
                Brier=float(w @ (pc - t) ** 2), constant_Brier=float(w @ (prior - t) ** 2),
                center_shift_mm=float(np.linalg.norm(a["c"] - center) * norm["scale"]),
                covariance_relative=float(np.linalg.norm(cov - uniform_cov) /
                                          max(1e-8, np.linalg.norm(uniform_cov))),
                saturated_nonempty=int(((pc <= 1e-4) | (pc >= 1-1e-4))[count > 0].sum()),
                max_positive_cell_fraction=float(np.bincount(v, weights=y, minlength=256).max() / y.sum())
                if y.any() else None, positive_cells=int(np.sum(t > 0)), mixed_component_cells=mixed)


def summarize(rows, sources, bootstrap):
    indexed = {(r["arm"], r["case_id"]): r for r in rows}
    groups = {s: [r["case_id"] for r in rows if r["arm"] == "R" and r["source_id"] == s] for s in sources}
    ids = [cid for s in sources for cid in groups[s]]
    need(len(indexed) == len(rows) == 315 and len(set(ids)) == 105
         and all(len(g) == 5 for g in groups.values()) and set(indexed) == {(a, c) for a in ARMS for c in ids},
         "three paired scores for each development case")
    pairs, stats = [], {}
    for hi, lo in COMPARISONS:
        label = hi + "_minus_" + lo
        stats[label] = {}
        block = []
        for cid in ids:
            a, b = indexed[hi, cid], indexed[lo, cid]
            need(a["source_id"] == b["source_id"], "paired scoring source")
            block.append(dict(comparison=label, case_id=cid, source_id=a["source_id"],
                              higher_severe=a["severe_geometry"], lower_severe=b["severe_geometry"],
                              delta={s: {k: a[s][k] - b[s][k] for k in a[s]} for s in ("coarse", "dense")}))
        byid = {r["case_id"]: r for r in block}
        pairs.extend(block)
        for stage in ("coarse", "dense"):
            fields = {}
            for k in block[0]["delta"][stage]:
                coverage = "Cover" in k
                factor = 100 if coverage or k == "far20" else 1
                delta = np.array([np.mean([byid[c]["delta"][stage][k] for c in groups[s]]) for s in sources]) * factor
                leave = (delta.sum() - delta) / 20
                fields[k] = dict(unit="pp" if factor == 100 else "ratio" if k.endswith("_ratio") else "mm",
                                 mean=float(delta.mean()), per_source=delta.tolist(),
                                 arm_mean={a: float(np.mean([np.mean([indexed[a,c][stage][k] for c in groups[s]])
                                                             for s in sources]) * factor) for a in (hi, lo)},
                                 CI95=np.percentile(delta[bootstrap].mean(axis=1), [2.5, 97.5]).tolist(),
                                 leave_one_source=[float(leave.min()), float(leave.max())],
                                 improved_sources=None if k.endswith("_ratio") else int((delta > 0 if coverage else delta < 0).sum()))
            stats[label][stage] = fields
        stats[label]["severe"] = {name: [r["case_id"] for r in block if pred(r)] for name,pred in (
            ("higher",lambda r:r["higher_severe"]), ("lower",lambda r:r["lower_severe"]),
            ("new",lambda r:r["higher_severe"] and not r["lower_severe"]),
            ("rescued",lambda r:r["lower_severe"] and not r["higher_severe"]),
            ("common",lambda r:r["higher_severe"] and r["lower_severe"]))}
        stats[label]["defect_deltas"] = {
            defect: {stage: {k: float(np.mean([r["delta"][stage][k] for r in block
                                               if r["case_id"].endswith("__"+defect)]))
                             for k in block[0]["delta"][stage]} for stage in ("coarse", "dense")}
            for defect in sorted({c.split("__")[-1] for c in ids})}
    m = {}
    for arm in ("U", "I"):
        cases = [r["mechanism"] for r in rows if r["arm"] == arm]
        summaries = {}
        for field in ("AP_minus_pi", "Brier", "constant_Brier", "center_shift_mm", "covariance_relative"):
            per_source = []
            for s in sources:
                values = [indexed[arm, c]["mechanism"][field] for c in groups[s]]
                good = [v for v in values if v is not None]
                per_source.append(float(np.mean(good)) if good else None)
            good = [v for v in per_source if v is not None]
            summaries[field] = dict(per_source=per_source, mean=float(np.mean(good)) if good else None)
        m[arm] = dict(AP_defined=sum(r["soft_AP"] is not None for r in cases), metrics=summaries,
            AP_improved_sources=sum(v is not None and v>0 for v in summaries["AP_minus_pi"]["per_source"]),
            manipulation_sources=sum(c>=2 or v>=.10 for c,v in zip(
                summaries["center_shift_mm"]["per_source"], summaries["covariance_relative"]["per_source"])))
    return pairs, dict(sources=sources, comparisons=stats, mechanism=m, formal_gate=False)


def score(q, out, cases, watch):
    old = module(q["geometry_scoring"], "frozen_oasg_geometry_methods")
    metric = module(q["geometry_metrics"], "frozen_cisc_geometry_metrics")
    proof = json_file(q["prediction_freeze"])
    local = json_file(q["local_archive"])
    need(proof["status"] == "FORMAL_CISC_RUI_D_NATIVE_POST_PREDICTION_FREEZE_AUDIT_PASS"
         and proof["request_sha256"] == q["prediction_request_sha256"]
         and local["remote_freeze"] == q["prediction_freeze"], "prediction and download proof")
    arc = read(local["archive"])
    checks = {k: read(v) for k, v in local["sidecars"].items()}
    name = Path(local["archive"]["path"]).name
    need(checks["sha256"].decode().strip() == digest(arc) + "  " + name
         and int(checks["bytes"]) == len(arc), "archive bytes and SHA256 sidecars")
    stamps = {name: sha for sha,name in (x.split("  ", 1) for x in checks["contents.sha256"].decode().splitlines())}
    with tarfile.open(fileobj=io.BytesIO(arc), mode="r:gz") as tar:
        ms = tar.getmembers()
        need(len(stamps) == len(ms) == 319 and [m.name for m in ms] == list(stamps)
             and all(m.isfile() for m in ms), "archive member order")
        data = {m.name: tar.extractfile(m).read() for m in ms}
    need(all(digest(raw) == stamps[k] for k,raw in data.items()), "archive member SHA256")
    manifest = list(map(json.loads, data["inference_manifest.jsonl"].splitlines()))
    expected = [(a,c["case_id"]) for a in ARMS for c in cases]
    need([(r["variant"],r["case_id"]) for r in manifest] == expected, "315 prediction cases and order")
    lookup = {(r["variant"],r["case_id"]): r for r in manifest}
    rows = []
    with (out / "model_scores.jsonl").open("x", encoding="utf-8", newline="\n") as log:
        for case in cases:
            cid = case["case_id"]
            watch()
            with np.load(io.BytesIO(read(case["reference"])), allow_pickle=False) as z:
                ref = {k: z[k] for k in z.files}
            with np.load(io.BytesIO(read(case["point_file"])), allow_pickle=False) as z:
                x, y = z["partial"], z["implant"]
            norm = case["normalization"]
            need(y.shape == x.shape == (8192, 3) and x.dtype == y.dtype == np.float32
                 and np.isfinite(x).all() and np.isfinite(y).all()
                 and digest(y.tobytes()) == case["target_array_sha256"], "formal input and target")
            evidence = json.loads((out/"labels"/(cid+".json")).read_bytes())
            with np.load(out/"labels"/(cid+".npz"), allow_pickle=False) as z:
                labels, comp = z["is_j"], z["component"]
            need(evidence["points_sha256"] == digest(x.tobytes()) and evidence["positive"] == labels.sum(),
                 "development replay binding")
            gt = metric.world_points(y, norm)
            a2, _, _ = metric.a2_reference(ref)
            for arm in ARMS:
                r = lookup[arm,cid]
                record = r["prediction"]
                need(r["checkpoint_sha256"] == q["checkpoint_hashes"][arm] and r["normalization"] == norm
                     and r["input_sha256"] == case["point_file"]["sha256"] and r["fold"] == "D"
                     and record["name"] == f"predictions/{arm}_D__{cid}.npz", "prediction identity and coordinates")
                raw = data.pop(record["name"])
                need(len(raw) == record["bytes"] and stamps[record["name"]] == record["sha256"], "prediction hash")
                arr = decode(raw, arm)
                need(sorted(arr) == r["diagnostic_fields"], "recorded prediction fields")
                geom = old.score_prediction(metric, arr, ref, a2, gt, norm)
                result = dict(arm=arm, fold="D", case_id=cid, source_id=case["source_id"],
                              j_points=evidence["positive"], interface_components=evidence["components"], **geom)
                if arm != "R":
                    result["mechanism"] = mechanism(arr, x, labels, comp, norm, q["prior"])
                rows.append(result)
                log.write(json.dumps(result, allow_nan=False) + "\n")
                log.flush()
    need(len(rows) == 315 and len(data) == 4, "all predictions consumed")
    boot = np.random.Generator(np.random.PCG64(2026112507)).integers(0,21,size=(2000,21),dtype=np.int64)
    with (out/"bootstrap_indices.npy").open("xb") as f:
        np.save(f,boot,allow_pickle=False)
    pairs,summaries = summarize(rows,q["sources"],boot)
    emit(out/"paired_cases.json",pairs)
    emit(out/"source_summary.json",summaries)
    emit(out/"completion.json",dict(status="SCORED_AWAITING_READ_ONLY_FREEZE",
          counts=dict(model_rows=315,paired_cases=105,contrasts=len(pairs),sources=21,development_label_rows=105),
          formal_gate=False,additional_forward=0,bootstrap_sha256=digest((out/"bootstrap_indices.npy").read_bytes())))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request",type=Path,required=True)
    parser.add_argument("--request-sha256",required=True)
    parser.add_argument("--authorization",type=Path,required=True)
    parser.add_argument("--replay-case")
    arg=parser.parse_args()
    for p in (arg.request,arg.authorization):
        need(p.is_absolute() and p.resolve(strict=True)==p and 0<p.stat().st_size<=65536,"control path")
    req=arg.request.read_bytes()
    q,auth=json.loads(req),json.loads(arg.authorization.read_bytes())
    need(digest(req)==arg.request_sha256==auth["request_sha256"] and auth["explicit_user_authorization"] is True
         and q["schema"]==SCHEMA and q["status"]=="AWAITING_EXPLICIT_USER_AUTHORIZATION"
         and q["single_attempt"] and q["device"]=="CPU" and sys.dont_write_bytecode,
         "frozen score and authorization")
    read(q["entry"])
    read(q["python"])
    need(Path(__file__).resolve()==Path(q["entry"]["path"]) and Path(sys.executable).resolve()==Path(q["python"]["path"])
         and [sys.version.split()[0],np.__version__,scipy.__version__,psutil.__version__]==q["runtime_versions"],
         "exact local runtime")
    out=Path(q["output"])
    need(out.is_absolute() and out.parent.resolve(strict=True)==out.parent and out.resolve()==out,
         "exact output path")
    if arg.replay_case is not None:
        attempt=json.loads((out/"attempt.json").read_bytes())
        need(attempt["request_sha256"]==arg.request_sha256,"active scoring attempt")
        replay(q,out,arg.replay_case)
        return
    cases,_=bind_case_index(q)
    out.mkdir()
    emit(out/"attempt.json",dict(request_sha256=arg.request_sha256,
                                   authorization_sha256=digest(arg.authorization.read_bytes())))
    (out/"labels").mkdir()
    start,proc=time.monotonic(),psutil.Process()
    def watch():
        need(time.monotonic()-start<q["limits"]["wall_seconds"]
             and proc.memory_info().rss<=q["limits"]["rss_bytes"],"scoring wall or RSS limit")
    try:
        for i,case in enumerate(cases,1):
            watch()
            subprocess.run([sys.executable,"-B",str(Path(__file__).resolve()),*sys.argv[1:],
                            "--replay-case",case["case_id"]],check=True,timeout=q["limits"]["case_replay_seconds"])
            print("REPLAY_VERIFIED",i,case["case_id"],flush=True)
        need(len(list((out/"labels").iterdir()))==210,"complete replay labels")
        print("STARTING_GEOMETRY_AND_MECHANISM_SCORE",flush=True)
        score(q,out,cases,watch)
        print("SCORED_AWAITING_READ_ONLY_FREEZE",flush=True)
    except BaseException as exc:
        emit(out/"failure.json",dict(status="FAILED_STOP_NO_RETRY",error=repr(exc)))
        raise


if __name__=="__main__":
    main()
