"""Separately authorized, CPU-only Fold D Native scoring."""

import argparse
from collections import Counter
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tarfile
import time

os.environ.update(CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2")
import numpy as np
import psutil
import scipy

SCHEMA = "bcsp-oasg-ba-d-cpu-score-v1"
STATUS = "AWAITING_EXPLICIT_USER_AUTHORIZATION"
ARMS = ("B", "A")
SEED = 2026112401
COUNTS = dict(model_rows=210, case_pairs=105, sources=21, bootstrap_replicates=2000)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def exact(record):
    p = Path(record["path"])
    need(p.is_absolute() and p.resolve() == p and p.is_file() and p.stat().st_size == record["bytes"],
         f"frozen path or size: {p}")
    need(digest(p.read_bytes()) == record["sha256"], f"frozen hash: {p}")
    return p


def load_json(record):
    return json.loads(exact(record).read_bytes())


def emit(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def bootstrap():
    return np.random.Generator(np.random.PCG64(SEED)).integers(0, 21, size=(2000, 21), dtype=np.int64)


def authorize(q, request_sha, auth):
    need(q["schema"] == SCHEMA and q["status"] == STATUS and q["execution_authorized"] is False
         and q["counts"] == COUNTS and q["automatic_retry"] is False
         and q["formal_gate_executed_here"] is False, "frozen score scope")
    need(set(auth) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
         and auth["schema"] == SCHEMA + "-authorization" and auth["request_sha256"] == request_sha
         and auth["explicit_user_authorization"] is True and bool(auth["user_authorization_text"].strip()),
         "separate scoring authorization")


def index_cases(index, manifest, q):
    cases = index["cases"]
    ids = [x["case_id"] for x in cases]
    need(len(ids) == len(set(ids)) == 105 and len(manifest) == 210, "complete case set")
    counts = Counter(x["source_id"] for x in cases)
    need(len(counts) == 21 and set(counts.values()) == {5} and sorted(counts) == q["source_ids"],
         "five cases in each of 21 fixed sources")
    lookup = {}
    for i, (arm, c) in enumerate(((a, case) for a in ARMS for case in cases), 1):
        r = manifest[i - 1]
        cid = c["case_id"]
        need((r["run"], r["variant"], r["fold"], r["case_id"], r["source_id"], r["forward_index"])
             == (arm + "_D", arm, "D", cid, c["source_id"], i), "prediction order and identity")
        need(r["checkpoint_sha256"] == q["checkpoint_hashes"][arm]
             and r["normalization"] == c["normalization"] and c["normalization_source"] == "defective_bbox"
             and r["input_sha256"] == c["point_file"]["sha256"]
             and r["prediction"]["name"] == f"predictions/{arm}_D__{cid}.npz", "prediction asset/coordinate binding")
        lookup[arm, cid] = r
    return cases, lookup


def decode_prediction(raw, arm):
    names = {"coarse", "prediction", "parent_index"} | ({"S", "delta", "token_index"} if arm == "A" else set())
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        need(set(z.files) == names and len(z.files) == len(names), "exact prediction fields")
        v = {k: z[k] for k in names}
    for k in names - {"parent_index", "token_index"}:
        a = v[k]
        need(a.shape == (8192 if k == "prediction" else 256, 3)
             and a.dtype == np.float32 and np.isfinite(a).all(), f"finite FP32 {k}")
    idx = np.arange(256, dtype=np.int64)
    need(v["parent_index"].dtype == np.int64 and np.array_equal(v["parent_index"], np.repeat(idx, 32)), "FC parent order")
    if arm == "A":
        need(v["token_index"].dtype == np.int64 and np.array_equal(v["token_index"], idx)
             and np.array_equal(v["coarse"], v["S"] + v["delta"]), "A anchor identity")
    return v


def endpoint(metric, points, ref, a2, gt, *, dense):
    forward = metric.nearest(ref["a_centers"], points)
    reverse = metric.nearest(points, a2)
    groups = {}
    j = ref["a_is_j"].astype(bool)
    for name, mask in (("E", ~j), ("J", j)):
        group = metric.stats(forward[mask], ref["a_weights"][mask])
        need(group["status"] == "OK", f"nonempty {name} region")
        groups[name] = group
    rear = metric.stats(reverse)
    m = dict(E_P95_mm=groups["E"]["p95_mm"], J_P95_mm=groups["J"]["p95_mm"],
             E_Cover_at_2=groups["E"]["coverage"]["2.0"], J_Cover_at_2=groups["J"]["coverage"]["2.0"],
             reverse_A2_P95_mm=rear["p95_mm"], far20=float(np.mean(reverse > 20.0)))
    if dense:
        m["CD_L1_mm"] = 0.5 * (float(metric.nearest(points, gt).mean()) + float(metric.nearest(gt, points).mean()))
    centered = points - points.mean(axis=0)
    gc = gt - gt.mean(axis=0)
    gt_radius = float(np.sqrt(np.mean(np.sum(gc * gc, axis=1))))
    need(gt_radius > 0, "nondegenerate GT")
    m["centroid_offset_mm"] = float(np.linalg.norm(points.mean(axis=0) - gt.mean(axis=0)))
    m["radius_gyration_ratio"] = float(np.sqrt(np.mean(np.sum(centered * centered, axis=1))) / gt_radius)
    return m, dict(forward_A1=groups, reverse_A2=rear,
                   bbox_mm=[points.min(axis=0).tolist(), points.max(axis=0).tolist()]), reverse


def score_prediction(metric, arr, ref, a2, gt, norm):
    coarse = metric.world_points(arr["coarse"], norm)
    dense = metric.world_points(arr["prediction"], norm)
    cm, cstats, cr = endpoint(metric, coarse, ref, a2, gt, dense=False)
    dm, dstats, dr = endpoint(metric, dense, ref, a2, gt, dense=True)
    far_child = dr > 20.0
    far_parent = cr[arr["parent_index"]] > 20.0
    transfer = dict(near_parent_far_child=int((far_child & ~far_parent).sum()),
                    far_parent_far_child=int((far_child & far_parent).sum()),
                    far_children=int(far_child.sum()), children=8192)
    need(transfer["near_parent_far_child"] + transfer["far_parent_far_child"] == transfer["far_children"],
         "far-child accounting")
    geometry = dict(coarse=cstats, dense=dstats, far_parent_child=transfer)
    if "delta" in arr:
        displacement = np.linalg.norm(arr["delta"].astype(np.float64), axis=1) * norm["scale"]
        geometry["anchor_delta_mm_p50_p95"] = np.percentile(displacement, [50, 95]).tolist()
    return dict(coarse=cm, dense=dm, geometry=geometry,
                severe_geometry=dm["E_P95_mm"] > 20.0 or dm["J_Cover_at_2"] == 0.0)


def summarize(rows, source_ids, indices):
    by = {(r["arm"], r["case_id"]): r for r in rows}
    ids = [r["case_id"] for r in rows if r["arm"] == "B"]
    need(len(rows) == len(by) == 2 * len(set(ids)) and set(by) == {(a, c) for a in ARMS for c in ids},
         "matched model rows")
    pairs = []
    for c in ids:
        b, a = by["B", c], by["A", c]
        need(a["source_id"] == b["source_id"], "paired source")
        delta = {s: {k: a[s][k] - b[s][k] for k in a[s]} for s in ("coarse", "dense")}
        pairs.append(dict(case_id=c, source_id=a["source_id"], defect=c.split("__")[-1],
                          B_severe=b["severe_geometry"], A_severe=a["severe_geometry"], delta=delta))
    groups = [[p for p in pairs if p["source_id"] == s] for s in source_ids]
    need(len(source_ids) == 21 and all(len(g) == 5 for g in groups), "source-stratified pairs")
    stats = {}
    defects = {}
    for s in ("coarse", "dense"):
        stats[s], defects[s] = {}, {}
        for k in pairs[0]["delta"][s]:
            factor = 100 if k == "far20" or "Cover" in k else 1
            d = np.array([np.mean([p["delta"][s][k] for p in g]) for g in groups]) * factor
            per_arm = {
                arm: float(np.mean([np.mean([by[arm, p["case_id"]][s][k] for p in g]) for g in groups]) * factor)
                for arm in ARMS}
            leave = (d.sum() - d) / 20
            record = dict(unit="pp" if factor == 100 else ("ratio" if k.endswith("_ratio") else "mm"),
                          arm_mean=per_arm, delta_A_minus_B=float(d.mean()), by_source=d.tolist(),
                          CI95=np.percentile(d[indices].mean(axis=1), [2.5, 97.5]).tolist(),
                          leave_one_source_range=[float(leave.min()), float(leave.max())])
            if k != "radius_gyration_ratio":
                record["improved_sources"] = int((d > 0 if "Cover" in k else d < 0).sum())
            stats[s][k] = record
        for defect in sorted({p["defect"] for p in pairs}):
            group = [p for p in pairs if p["defect"] == defect]
            need(len(group) == 21, "one case per defect and source")
            defects[s][defect] = {k: float(np.mean([p["delta"][s][k] for p in group]))
                                  for k in group[0]["delta"][s]}
    severe = {"B": [p["case_id"] for p in pairs if p["B_severe"]],
              "A": [p["case_id"] for p in pairs if p["A_severe"]],
              "new": [p["case_id"] for p in pairs if p["A_severe"] and not p["B_severe"]],
              "rescued": [p["case_id"] for p in pairs if p["B_severe"] and not p["A_severe"]],
              "common": [p["case_id"] for p in pairs if p["A_severe"] and p["B_severe"]]}
    return pairs, dict(comparison="A_minus_B", source_ids=source_ids, ratios_and_defect_deltas_native_units=True,
                       metrics=stats, defect_deltas=defects, severe_case_ids=severe)


def score(q, out):
    meta = q["implementation"]
    p = exact(meta["geometry_metrics"])
    spec = importlib.util.spec_from_file_location("oasg_frozen_geometry_metrics", p)
    metric = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metric)
    ids = np.load(exact(q["bootstrap_indices"]), allow_pickle=False)
    need(ids.dtype == np.int64 and np.array_equal(ids, bootstrap()), "frozen PCG64 resampling")
    sidecars = {k: exact(v) for k, v in q["sidecars"].items()}
    p = exact(q["archive"])
    need(sidecars["sha256"].read_text() == q["archive"]["sha256"] + "  " + p.name + "\n"
         and sidecars["bytes"].read_text() == str(q["archive"]["bytes"]) + "\n", "archive sidecar content")
    index = load_json(q["case_index"])
    server = load_json(q["prediction_freeze"])
    local = load_json(q["local_download_verification"])
    need(server["status"] == "FORMAL_READ_ONLY_POST_PREDICTION_FREEZE_PASS"
         and server["request_sha256"] == q["prediction_request_sha256"]
         and local["server_freeze_sha256"] == q["prediction_freeze"]["sha256"]
         and local["files"][p.name] == q["archive"], "prediction and local download freeze")
    stamps = [line.split("  ", 1) for line in sidecars["members"].read_text().splitlines()]
    stamped = {name: digest_ for digest_, name in stamps}
    need(len(stamps) == len(stamped) == 214, "exact 214 approved archive members")
    start = time.monotonic()
    proc = psutil.Process()
    rows = []
    with tarfile.open(p, "r:gz") as tar, (out / "model_scores.jsonl").open("x", encoding="utf-8", newline="\n") as log:
        ms = tar.getmembers()
        need([m.name for m in ms] == list(stamped) and all(
            m.isfile() and 0 < m.size < 8 * 1024 * 1024 and not PurePosixPath(m.name).is_absolute()
            and ".." not in PurePosixPath(m.name).parts for m in ms), "safe exact archive inventory")
        # Read the gzip stream in archive order once, including the four audit members.
        raw = {}
        for m in ms:
            d = tar.extractfile(m).read()
            need(len(d) == m.size and digest(d) == stamped[m.name], f"archive member hash: {m.name}")
            raw[m.name] = d
        manifest = list(map(json.loads, raw["inference_manifest.jsonl"].splitlines()))
        cases, lookup = index_cases(index, manifest, q)
        for c in cases:
            with np.load(exact(c["reference"]), allow_pickle=False) as bank:
                ref = {k: bank[k] for k in bank.files}
            with np.load(exact(c["point_file"]), allow_pickle=False) as bank:
                need(set(bank.files) == {"partial", "implant"}, "point file keys")
                y = bank["implant"]
            need(y.shape == (8192, 3) and y.dtype == np.float32 and np.isfinite(y).all()
                 and digest(y.tobytes()) == c["target_array_sha256"], "frozen target array")
            gt = metric.world_points(y, c["normalization"])
            a2, _, _ = metric.a2_reference(ref)
            for arm in ARMS:
                lim = q["limits"]
                need(time.monotonic() - start <= lim["wall_seconds"] and proc.memory_info().rss <= lim["RSS_bytes"]
                     and log.tell() <= lim["output_bytes"], "CPU resource limit")
                info = lookup[arm, c["case_id"]]
                record = info["prediction"]
                data = raw.pop(record["name"])
                need(stamped[record["name"]] == record["sha256"] and len(data) == record["bytes"], "prediction bytes")
                arr = decode_prediction(data, arm)
                need(sorted(arr) == info["diagnostic_fields"], "logged prediction fields")
                result = dict(arm=arm, fold="D", case_id=c["case_id"], source_id=c["source_id"],
                              **score_prediction(metric, arr, ref, a2, gt, c["normalization"]))
                rows.append(result)
                log.write(json.dumps(result, allow_nan=False) + "\n")
                log.flush()
        need(len(rows) == 210 and len(raw) == 4, "all predictions consumed")
    pairs, summary = summarize(rows, q["source_ids"], ids)
    need(len(pairs) == 105, "all case pairs")
    emit(out / "paired_cases.json", pairs)
    emit(out / "source_summary.json", summary)
    emit(out / "completion.json", dict(status="SCORED_AWAITING_READ_ONLY_FREEZE", counts=COUNTS, formal_gate=False))


def main():
    parser = argparse.ArgumentParser()
    for name in ("request", "request-sha256", "authorization", "authorization-sha256"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    control = []
    for name in ("request", "authorization"):
        p = Path(getattr(args, name))
        need(p.is_absolute() and p.resolve() == p and p.is_file() and 0 < p.stat().st_size <= 128 * 1024,
             "exact bounded control")
        control.append(load_json(dict(path=str(p), bytes=p.stat().st_size, sha256=getattr(args, name + "_sha256"))))
    q, auth = control
    authorize(q, args.request_sha256, auth)
    need(args.request == q["request_path"] and args.authorization == q["authorization_path"]
         and exact(q["implementation"]["entry"]) == Path(__file__), "exact scoring paths")
    versions = dict(python=sys.version.split()[0], numpy=np.__version__, scipy=scipy.__version__, psutil=psutil.__version__)
    need(sys.dont_write_bytecode and versions == q["environment"]["versions"]
         and exact(q["environment"]["python"]) == Path(sys.executable).resolve(),
         "frozen CPU environment")
    out = Path(q["output"])
    need(out.parent.is_dir() and out.parent.resolve() == out.parent and out.resolve() == out,
         "owned scoring output")
    out.mkdir()
    emit(out / "attempt.json", dict(request_sha256=args.request_sha256, authorization_sha256=args.authorization_sha256))
    try:
        score(q, out)
        need(sum(p.stat().st_size for p in out.iterdir()) <= q["limits"]["output_bytes"], "final output budget")
    except BaseException as exc:
        emit(out / "failure.json", dict(status="FAILED_STOP_NO_RETRY", error=repr(exc)))
        raise


if __name__ == "__main__":
    main()
