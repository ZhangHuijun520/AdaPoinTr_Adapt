"""Run the separately authorized SCQ-PRIME Fold C offline score."""
import argparse
from collections import Counter
import csv
import hashlib
import importlib.metadata
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import sys
import tarfile
import time

os.environ.update(CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2")

import numpy as np
import psutil

ARMS = ("B", "F", "S")
CONTROLS = ("Nop_D", "GT_8192")
PAIRS = (("B", "S"), ("F", "S"), ("B", "F"))
BOOTSTRAP_SEED = 2026112103
KEYS = ("E_P95_mm", "J_P95_mm", "J_coverage_2.0mm", "reverse_A2_P95_mm", "reverse_A2_outlier_20.0mm")
METRIC_SHA = "af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766"
ARCHIVE_SHA = "3ce5c5906a301d3672458b7fc0b6fcdb4a0a187e27a333265534fea4486b463c"
LIMITS = dict(wall_seconds=18000, RSS_bytes=8589934592, output_bytes=2147483648, threads=2)
COUNTS = dict(cases=105, sources=21, model_rows=315, control_rows=210, total_rows=525)
DEFECTS = {"bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def hash_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def exact(record):
    p = Path(record["path"])
    require(p.is_absolute() and not any(x.is_symlink() for x in (p, *p.parents)) and p.is_file()
            and p.stat().st_size == record["bytes"] and sha(p) == record["sha256"], f"frozen file: {p}")
    return p


def read(record):
    return json.loads(exact(record).read_bytes())


def load_source(name, record):
    path = exact(record)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), "exec"), mod.__dict__)
    return mod


def emit(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def bootstrap_indices():
    return np.random.Generator(np.random.PCG64(BOOTSTRAP_SEED)).integers(0, 21, size=(2000, 21), dtype=np.int64)


def validate_cases(index, references, cases):
    expected = index["inputs"]
    require(len(expected) == len(cases) == 105 and len({r["case_id"] for r in cases}) == 105,
            "exactly 105 unique cases")
    refs = {r["case_id"]: r for r in references["cases"] if r["fold"] == "C"}
    require(len(refs) == 105 and set(refs) == {x["case_id"] for x in cases}, "complete frozen C references")
    counts = Counter(r["source_id"] for r in cases)
    require(len(counts) == 21 and set(counts.values()) == {5}, "five cases per 21 sources")
    for case, row in zip(cases, expected):
        cid = case["case_id"]
        ref = refs[cid]
        require(case["fold"] == "C" and all(case[k] == row[k] == ref[k] for k in ("case_id", "source_id", "normalization")),
                f"matching case/source/D-only frame: {cid}")
        require(case["normalization_source"] == row["normalization_source"] == "defective_bbox"
                and case["target_array_sha256"] == ref["target_array_sha256"]
                and case["reference"] == {k:ref[k] for k in ("path", "bytes", "sha256")}
                and all(case["point_file"][k] == row["input"][k] for k in ("bytes", "sha256"))
                and case["trace"] is row["selected_neighborhood_trace"], f"fixed geometry/assets: {cid}")
    require(all({r["case_id"].split("__", 2)[-1] for r in cases if r["source_id"] == s} == DEFECTS for s in counts),
            "all fixed defect types")


def check_archive(tar, case_rows, q, completion, sidecar_text):
    records = completion["archive"]["members"]
    hashes = [f"{r['sha256']}  {r['name']}" for r in records]
    require(sidecar_text.splitlines() == hashes, "exact contents sidecar")
    members = tar.getmembers()
    require(len(members) == len(records) == 320 and len({r["name"] for r in records}) == 320, "315 predictions and five logs")
    expected = [f"predictions/{a}_C__{r['case_id']}.npz" for a in ARMS for r in case_rows]
    require([r["name"] for r in records[:315]] == expected
            and {r["name"] for r in records[315:]} == {"inference_manifest.jsonl", "forward_attempts.jsonl",
                "geometry_summary.jsonl", "inference_complete.json", "resources.jsonl"}, "exact archive members")
    for m,r in zip(members,records):
        require(m.isfile() and m.name == r["name"] and m.size == r["bytes"] and 0 < m.size < 2097152, "regular frozen member")
    paths = {r["name"]:r for r in records}
    def lines(name):
        return [json.loads(row) for row in member_bytes(tar, paths[name]).splitlines()]
    manifest, geom = lines("inference_manifest.jsonl"), lines("geometry_summary.jsonl")
    require(len(manifest) == len(geom) == 315, "315 aligned index/geometry journal records")
    for i, (m, g) in enumerate(zip(manifest, geom)):
        arm, case = ARMS[i//105], case_rows[i%105]
        require(m["run"] == g["run"] == f"{arm}_C" and m["variant"] == arm and m["case_id"] == g["case_id"] == case["case_id"]
                and m["source_id"] == case["source_id"] and m["fold"] == "C" and m["seed"] == 2026112101
                and m["input_sha256"] == case["point_file"]["sha256"] and m["normalization"] == case["normalization"]
                and m["checkpoint_sha256"] == q["checkpoint_hashes"][arm] and m["forward_index"] == i+1
                and m["prediction"] == paths[expected[i]], "prediction/paired identity")
        require(g["frame"] == "native_D_only_normalized_no_GT", "prediction coordinate frame")
    return {(a, r["case_id"]): (paths[expected[i]], manifest[i], geom[i])
            for i,(a,r) in enumerate((a,r) for a in ARMS for r in case_rows)}


def member_bytes(tar, record):
    raw = tar.extractfile(record["name"]).read(record["bytes"]+1)
    require(len(raw) == record["bytes"] and hash_bytes(raw) == record["sha256"], "frozen archive member content")
    return raw


def decode_prediction(raw, arm, trace):
    fields = {"coarse", "prediction"}
    if arm != "B":
        fields |= {"Qraw", "delta"}
        if trace:
            fields.add("neighbor_indices")
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        require(len(z.files) == len(fields) and set(z.files) == fields, f"exact {arm} prediction fields")
        arrays = {k:z[k].copy() for k in fields}
    for k in fields - {"neighbor_indices"}:
        a = arrays[k]
        require(a.shape == (8192 if k == "prediction" else 256, 3)
                and a.dtype == np.float32 and np.isfinite(a).all(), f"finite FP32 {k}")
    if arm != "B":
        require(np.allclose(arrays["Qraw"] + arrays["delta"], arrays["coarse"], rtol=2e-6, atol=2e-7),
                "Qraw + delta agrees with native output")
    if "neighbor_indices" in arrays:
        a = arrays["neighbor_indices"]
        require(a.shape == (256, 8) and a.dtype == np.int64 and a.min() >= 0 and a.max() < 256, "fixed neighborhood trace")
    return arrays


def case_metric(metric, legacy, points, ref, gt):
    score = metric.score_cloud(points, ref, gt)
    require(score["status"] == "OK" and all(score["regions"]["A1"][r]["status"] == "OK" for r in ("E", "J")),
            "valid prediction and nonempty E/J")
    metrics = legacy.select_metrics(score)
    a2, _, _ = metric.a2_reference(ref)
    metrics["reverse_A2_outlier_20.0mm"] = float(np.mean(metric.nearest(points, a2) > 20.))
    pose = legacy.position_shape(points, gt)
    labels = legacy.risk_labels(metrics, pose)
    metrics.update(centroid_offset_mm=pose["centroid_offset_mm"], radius_gyration_ratio=pose["radius_gyration_ratio"],
                   **{k:float(v) for k,v in labels.items()})
    require(all(isinstance(metrics[k], (int, float)) and math.isfinite(metrics[k]) for k in KEYS), "finite primary and safety metrics")
    return metrics, metric.json_safe(score), pose, labels


def score_case(tar, lookup, case, metric, legacy, controls, guard):
    with np.load(exact(case["reference"]), allow_pickle=False) as z:
        ref = {k:z[k] for k in z.files}
    with np.load(exact(case["point_file"]), allow_pickle=False) as z:
        require(set(z.files) == {"partial", "implant"}, "frozen point file fields")
        partial, target = z["partial"].copy(), z["implant"].copy()
    require(all(x.shape == (8192,3) and x.dtype == np.float32 and np.isfinite(x).all() for x in (partial, target))
            and hash_bytes(target.tobytes()) == case["target_array_sha256"], "untouched GT layout")
    gt = metric.world_points(target, case["normalization"])
    rows = []
    for arm in ARMS + CONTROLS:
        guard()
        stage = None
        if arm in ARMS:
            rec, manifest, geometry = lookup[(arm,case["case_id"])]
            arr = decode_prediction(member_bytes(tar,rec),arm,case["trace"])
            require(sorted(arr) == manifest["diagnostic_fields"], "NPZ journal fields")
            points = metric.world_points(arr["prediction"],case["normalization"])
            stage = legacy.stage_geometry(geometry,points,gt,case["normalization"],
                                          metric.world_points(arr["coarse"],case["normalization"]))
        elif arm == "GT_8192":
            points = gt
        else:
            points = metric.world_points(partial,case["normalization"])
        values, full, pose, labels = case_metric(metric, legacy, points, ref, gt)
        if arm in CONTROLS:
            old = controls[(arm,case["case_id"])]
            require(values.keys() == old["metrics"].keys() and all(
                values[k] == old["metrics"][k] if values[k] is None or old["metrics"][k] is None else
                math.isclose(values[k],old["metrics"][k],rel_tol=1e-10,abs_tol=1e-10) for k in values),
                "historical shared control replay")
        rows.append(dict(fold="C",case_id=case["case_id"],source_id=case["source_id"],arm=arm,
                    status="OK",metrics=values,full_metrics=full,position_shape=pose,risk_labels=labels,stage_geometry=stage))
    return rows


def summarize(rows, source_ids, indices):
    lookup = {(r["arm"],r["case_id"]):r for r in rows}
    ids = sorted({r["case_id"] for r in rows})
    require(len(ids) == 105 and len(rows) == len(lookup) == 525
            and set(lookup) == {(a,c) for a in ARMS+CONTROLS for c in ids}, "525 complete paired rows")
    by_source = {s:[c for c in ids if lookup["B",c]["source_id"] == s] for s in source_ids}
    require(len(by_source) == 21 and all(len(cs) == 5 for cs in by_source.values()), "21 equal-source groups")
    source = []
    for s, cs in by_source.items():
        for arm in ARMS + CONTROLS:
            batch = [lookup[arm,c] for c in cs]
            keys = batch[0]["metrics"]
            source.append(dict(source_id=s,arm=arm, metrics={k:float(np.mean([r["metrics"][k] for r in batch]))
                          if all(r["metrics"][k] is not None for r in batch) else None for k in keys}))
    source_map = {(r["source_id"],r["arm"]):r["metrics"] for r in source}
    comparisons = {}
    for baseline, arm in PAIRS:
        pairs, by_metric = [], {}
        for cid in ids:
            b, a = lookup[baseline,cid], lookup[arm,cid]
            delta = {k:(a["metrics"][k]-b["metrics"][k]) if None not in (a["metrics"][k],b["metrics"][k]) else None
                     for k in a["metrics"]}
            old,new = b["risk_labels"]["severe_geometry"], a["risk_labels"]["severe_geometry"]
            pairs.append(dict(case_id=cid,source_id=a["source_id"],defect=cid.split("__",2)[-1],metrics=delta,
                              baseline_severe=old,candidate_severe=new,new_severe=bool(new and not old),
                              rescued_severe=bool(old and not new),common_severe=bool(old and new)))
        for key in lookup[arm,ids[0]]["metrics"]:
            a,b = ([source_map[s,m][key] for s in source_ids] for m in (arm,baseline))
            positive = "coverage" in key
            ordered = key != "radius_gyration_ratio"
            unit = "pp" if positive or "outlier_fraction" in key or "_outlier_" in key else "native"
            factor = 100 if unit == "pp" else 1
            if any(v is None for v in a+b):
                by_metric[key] = dict(status="UNDEFINED",source_deltas=[
                    None if x is None or y is None else (x-y)*factor for x,y in zip(a,b)])
                continue
            d = (np.asarray(a)-np.asarray(b))*factor
            ci = np.percentile(d[indices].mean(axis=1),[2.5,97.5])
            result = dict(status="OK",unit=unit,baseline_mean=float(np.mean(b)*factor),candidate_mean=float(np.mean(a)*factor),
                          mean=float(d.mean()),median=float(np.median(d)),CI95=ci.tolist(),source_deltas=d.tolist())
            if ordered:
                improve = d > 0 if positive else d < 0
                result.update(improved=int(improve.sum()),tied=int((d==0).sum()),worse=int((~improve & (d!=0)).sum()))
            by_metric[key] = result
        defects = {defect:{k:float(np.mean([p["metrics"][k] for p in pairs if p["defect"] == defect])) for k in KEYS}
                   for defect in sorted(DEFECTS)}
        comparisons[f"{arm}_minus_{baseline}"] = dict(metrics=by_metric,case_pairs=pairs,defect_means_native_units=defects,
            severe={k:sum(p[k] for p in pairs) for k in ("baseline_severe","candidate_severe","new_severe","rescued_severe","common_severe")})
    return source,comparisons


def authorize(qr, ar):
    q, a = read(qr),read(ar)
    require(q["schema"] == "bcsp-scq-prime-BFS-C-score-request-v1" and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION"
            and q["execution_authorized"] is False and q["fold"] == "C" and q["seed"] == 2026112101
            and q["limits"] == LIMITS and q["counts"] == COUNTS and q["archive"]["sha256"] == ARCHIVE_SHA
            and q["implementation"]["metrics"]["sha256"] == METRIC_SHA, "fixed pending scoring contract")
    require(set(a) == {"schema","request_sha256","explicit_user_authorization","user_authorization_text"}
            and a["schema"] == "bcsp-scq-prime-BFS-C-score-authorization-v1" and a["request_sha256"] == qr["sha256"]
            and a["explicit_user_authorization"] is True and bool(a["user_authorization_text"].strip())
            and ar["path"] == q["authorization_path"], "separate explicit scoring authorization")
    return q


def main():
    parser = argparse.ArgumentParser()
    for key in ("request","request-sha256","authorization","authorization-sha256"):
        parser.add_argument("--"+key,required=True)
    args = vars(parser.parse_args())
    def rec(key):
        p = Path(args[key])
        return dict(path=str(p),bytes=p.stat().st_size,sha256=args[key+"_sha256"])
    start = time.monotonic()
    qr = rec("request")
    q = authorize(qr,rec("authorization"))
    require(exact(q["implementation"]["scorer"]) == Path(__file__).absolute(), "scorer binding")
    require(sys.flags.isolated and sys.dont_write_bytecode and not os.environ["CUDA_VISIBLE_DEVICES"]
            and exact(q["environment"]["python"]) == Path(sys.executable)
            and sys.version == q["environment"]["python_version"], "fixed CPU Python")
    require(all(importlib.metadata.version(k) == v for k,v in q["environment"]["packages"].items()), "frozen CPU packages")
    p3 = read(q["P3"])
    require(p3["status"] == "SCQ_PRIME_FOLD_C_LOCAL_SCORE_P3_PASS" and all(p3["checks"].values())
            and p3["scorer_sha256"] == q["implementation"]["scorer"]["sha256"], "bound scoring P3")
    audit = read(q["prediction_audit"])
    require(audit["status"] == "FORMAL_PRIME_BFS_C_NATIVE_POST_PREDICTION_FREEZE_PASS"
            and audit["archive_sha256"] == ARCHIVE_SHA and audit["request_sha256"] == q["prediction_request_sha256"],
            "formally frozen prediction archive")
    protocol = read(q["protocol"])
    require(protocol["counts"] == COUNTS and protocol["formal_gate_in_this_execution"] is False
            and protocol["bootstrap"] == dict(engine="PCG64",seed=BOOTSTRAP_SEED,replicates=2000,unit="paired_source"),
            "frozen scientific protocol")
    legacy = load_source("prime_history_score_helpers",q["implementation"]["helpers"])
    require(Path(legacy.METRIC_PATH) == exact(q["implementation"]["metrics"]), "same historical metrics module")
    metric = legacy.metric
    cases = read(q["score_case_index"])["cases"]
    validate_cases(read(q["prediction_index"]),read(q["reference_manifest"]),cases)
    ids = sorted({case["source_id"] for case in cases})
    indices = np.load(exact(q["bootstrap_indices"]),allow_pickle=False)
    require(np.array_equal(indices,bootstrap_indices()) and ids == protocol["ordered_source_ids"], "same source bootstrap index")
    controls = {}
    with exact(q["historical_controls"]).open("r",encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["fold"] == "C" and row["arm"] in CONTROLS:
                key = row["arm"],row["case_id"]
                require(key not in controls,"duplicate historical control")
                controls[key] = row
    require(set(controls) == {(a,c["case_id"]) for a in CONTROLS for c in cases}, "complete historical replay baselines")
    for case in cases:
        exact(case["reference"])
        exact(case["point_file"])
    path = exact(q["archive"])
    sidecars = [exact(r).read_text(encoding="ascii") for r in q["sidecars"]]
    require(len(sidecars) == 3 and sidecars[0].strip() == f"{ARCHIVE_SHA}  {path.name}"
            and sidecars[1].strip() == str(path.stat().st_size),"archive sidecars")
    out = Path(q["output"])
    require(out.parent == Path(qr["path"]).parent and not any(x.is_symlink() for x in (out,*out.parents)),"bound output directory")
    out.mkdir()
    proc = psutil.Process()
    def guard():
        require(time.monotonic()-start <= LIMITS["wall_seconds"] and proc.memory_info().rss <= LIMITS["RSS_bytes"]
                and sum(p.stat().st_size for p in out.iterdir() if p.is_file()) <= LIMITS["output_bytes"],"CPU budget")
    rows = []
    try:
        with tarfile.open(path,"r:gz") as tar:
            lookup = check_archive(tar,cases,q,read(q["prediction_completion"]),sidecars[2])
            # Walk regular bounded members once in archive order so gzip is not rescanned by case.
            payloads = {}
            for rec,m,g in lookup.values():
                payloads[rec["name"]] = member_bytes(tar,rec)
            class CachedArchive:
                def extractfile(self,name):
                    return io.BytesIO(payloads[name])
            cached = CachedArchive()
            with (out/"case_metrics.jsonl").open("x",encoding="utf-8",newline="\n") as log:
                for case in cases:
                    batch = score_case(cached,lookup,case,metric,legacy,controls,guard)
                    for row in batch:
                        log.write(json.dumps(row,allow_nan=False)+"\n")
                    log.flush()
                    rows.extend(batch)
        sources, comparisons = summarize(rows,ids,indices)
        emit(out/"source_metrics.json",sources)
        emit(out/"paired_comparisons.json",dict(source_order=ids,bootstrap_seed=BOOTSTRAP_SEED,
            source_conditional_interval=True,comparisons=comparisons,formal_gate_executed=False))
        with (out/"case_metrics.csv").open("x",encoding="utf-8",newline="") as stream:
            columns = ["case_id","source_id","arm",*rows[0]["metrics"]]
            writer = csv.DictWriter(stream,fieldnames=columns)
            writer.writeheader()
            for r in rows:
                writer.writerow({**{k:r[k] for k in columns[:3]},**r["metrics"]})
        guard()
        emit(out/"completion.json",dict(status="CPU_SCORE_COMPLETE_AWAITING_FORMAL_FREEZE",request_sha256=qr["sha256"],
            counts=COUNTS,shared_control_replays=210,formal_gate_executed=False,elapsed_seconds=time.monotonic()-start))
    except BaseException as exc:
        emit(out/"failure.json",dict(status="FAILED_STOP_NO_RETRY",scored_rows=len(rows),error=repr(exc)))
        raise


if __name__ == "__main__":
    main()
