"""Read-only audit of the completed CISC scoring run, with independent aggregation."""
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "scored_once_v2"
REQUEST_SHA = "e8e73364e376c3ff2a8e42287afb3c7b89f09bfc3afc41512b2538f788615a28"
ARMS = ("R", "U", "I")
STAGES = ("coarse", "dense")
COMPARISONS = (("I", "R"), ("I", "U"), ("U", "R"))
FILES = {"attempt.json", "bootstrap_indices.npy", "completion.json", "model_scores.jsonl",
         "paired_cases.json", "source_summary.json"}


def require(ok, detail):
    if not ok:
        raise ValueError(detail)


def read(path):
    require(path.resolve(strict=True) == path and path.is_file(), f"exact file: {path}")
    return path.read_bytes()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(path):
    raw = read(path)
    return dict(bytes=len(raw), sha256=sha(raw))


def bound(record):
    path = Path(record["path"])
    raw = read(path)
    require(len(raw) == record["bytes"] and sha(raw) == record["sha256"], f"binding: {path}")
    return raw


def average(values):
    values = list(values)
    return math.fsum(values) / len(values) if values else None


def same(expected, observed, key):
    if isinstance(expected, dict):
        require(isinstance(observed, dict) and expected.keys() == observed.keys(), f"fields: {key}")
        for field, value in expected.items():
            same(value, observed[field], f"{key}.{field}")
    elif isinstance(expected, list):
        require(isinstance(observed, list) and len(expected) == len(observed), f"length: {key}")
        for i, (value, actual) in enumerate(zip(expected, observed)):
            same(value, actual, f"{key}[{i}]")
    elif isinstance(expected, float):
        require(type(observed) in (float, int) and math.isclose(expected, observed, rel_tol=1e-12, abs_tol=1e-12),
                f"value: {key}: {expected!r} versus {observed!r}")
    else:
        require(type(observed) is type(expected) and expected == observed, f"value: {key}")


def inventory(ids):
    require({p.name for p in OUT.iterdir()} == FILES | {"labels"}, "exact score output names")
    labels = OUT / "labels"
    require(labels.is_dir() and labels.resolve(strict=True) == labels, "label directory identity")
    names = {f"{case}{ext}" for case in ids for ext in (".json", ".npz")}
    require({p.name for p in labels.iterdir()} == names, "exact label names")
    files = [*(OUT / name for name in sorted(FILES)), *(labels / name for name in sorted(names))]
    return {p.relative_to(OUT).as_posix(): pin(p) for p in files}


def replay_evidence(cases):
    results = {}
    different_frames = 0
    max_scale_diff = 0.0
    for case in cases:
        cid = case["case_id"]
        receipt = json.loads(read(OUT / "labels" / (cid + ".json")))
        frame = receipt["replay_frame"]
        require(receipt["case_id"] == frame["case_id"] == cid
                and frame["frozen"] == case["normalization"] and frame["replay_frame"] == "frozen"
                and frame["input_rows"] == 8192 and frame["input_row_bytes_identical"] is True,
                f"ordered frozen replay: {cid}")
        s, t = frame["frozen"]["scale"], frame["recomputed"]["scale"]
        delta = t - s
        require(s > 0 and t > 0 and math.isfinite(delta)
                and frame["scale_difference_mm"] == delta
                and frame["frozen_scale_hex"] == s.hex() and frame["recomputed_scale_hex"] == t.hex()
                and frame["center_difference_mm"] == [x-y for x,y in zip(
                    frame["recomputed"]["center"], frame["frozen"]["center"])], f"frame differences: {cid}")
        different_frames += frame["recomputed"] != frame["frozen"]
        max_scale_diff = max(max_scale_diff, abs(delta))
        raw = bound(case["point_file"])
        with np.load(io.BytesIO(raw), allow_pickle=False) as points:
            x = points["partial"]
            require(x.dtype == np.float32 and x.shape == (8192, 3)
                    and sha(x.tobytes()) == receipt["points_sha256"], f"input array: {cid}")
        with np.load(io.BytesIO(read(OUT / "labels" / (cid + ".npz"))), allow_pickle=False) as labels:
            require(set(labels.files) == {"is_j", "component", "face_id"}, f"label fields: {cid}")
            y, component, faces = labels["is_j"], labels["component"], labels["face_id"]
            require(y.dtype == np.bool_ and component.dtype.kind == faces.dtype.kind == "i"
                    and y.shape == component.shape == faces.shape == (8192,)
                    and np.array_equal(y, component >= 0) and np.all(component[~y] == -1)
                    and np.all(component[y] < receipt["components"])
                    and faces.min() >= 0 and int(y.sum()) == receipt["positive"],
                    f"label counts and payload: {cid}")
        results[cid] = receipt
    return results, different_frames, max_scale_diff


def reaggregate(rows, cases, sources, draws, label_receipts):
    indexed = {(r["case_id"], r["arm"]): r for r in rows}
    case_groups = {s: [c["case_id"] for c in cases if c["source_id"] == s] for s in sources}
    ids = [cid for s in sources for cid in case_groups[s]]
    expected_order = [(c["case_id"], a) for c in cases for a in ARMS]
    require(len(indexed) == len(rows) == 315 and [(r["case_id"], r["arm"]) for r in rows] == expected_order
            and len(sources) == 21 and all(len(g) == 5 for g in case_groups.values()), "row and source order")
    bycase = {c["case_id"]: c for c in cases}
    for r in rows:
        cid = r["case_id"]
        dense = r["dense"]
        counts = label_receipts[cid]
        require(r["source_id"] == bycase[cid]["source_id"] and r["fold"] == "D"
                and r["j_points"] == counts["positive"] and r["interface_components"] == counts["components"]
                and r["severe_geometry"] is (dense["E_P95_mm"] > 20.0 or dense["J_Cover_at_2"] == 0.0),
                f"row identity and severity: {cid}")
        require(("mechanism" in r) == (r["arm"] != "R"), f"mechanism scope: {cid}")
        component = r["geometry"]["far_parent_child"]
        require(component["near_parent_far_child"] + component["far_parent_far_child"] == component["far_children"]
                and component["children"] == 8192 and dense["far20"] == component["far_children"] / 8192,
                f"far20 accounting: {cid}")

    pair_rows, summaries = [], {}
    for a, b in COMPARISONS:
        key = f"{a}_minus_{b}"
        pairs = {}
        cuts = {n: [] for n in ("higher", "lower", "new", "rescued", "common")}
        for cid in ids:
            x, y = indexed[cid,a], indexed[cid,b]
            sx, sy = x["severe_geometry"], y["severe_geometry"]
            for name, chosen in zip(cuts, (sx, sy, sx and not sy, sy and not sx, sx and sy)):
                if chosen:
                    cuts[name].append(cid)
            delta = {s: {k: v - y[s][k] for k,v in x[s].items()} for s in STAGES}
            pairs[cid] = dict(comparison=key, case_id=cid, source_id=x["source_id"], higher_severe=sx,
                              lower_severe=sy, delta=delta)
        pair_rows.extend(pairs.values())
        result = {"severe": cuts}
        for stage in STAGES:
            metrics = {}
            for field in pairs[ids[0]]["delta"][stage]:
                groups = [case_groups[s] for s in sources]
                coverage = "Cover" in field
                ratio = field.endswith("_ratio")
                pp = coverage or field == "far20"
                factor = 100 if pp else 1
                source_delta = [factor * average(pairs[c]["delta"][stage][field] for c in g) for g in groups]
                # Use a separate reduction and linear percentile interpolation.
                replicate = sorted(average(source_delta[int(i)] for i in draw) for draw in draws)
                def percentile(p):
                    lo, fraction = divmod((len(replicate) - 1) * p, 1)
                    k = int(lo)
                    return replicate[k] + (replicate[k+1] - replicate[k]) * fraction
                leave = [average(v for j,v in enumerate(source_delta) if j != i) for i in range(len(sources))]
                # Replicate the original floating-point reduction only for strict zero ties.
                strict = [factor * np.mean([pairs[c]["delta"][stage][field] for c in g]) for g in groups]
                metrics[field] = dict(unit="pp" if pp else "ratio" if ratio else "mm",
                    mean=average(source_delta), per_source=source_delta,
                    arm_mean={arm: factor * average(average(indexed[c,arm][stage][field] for c in g)
                                                    for g in groups) for arm in (a,b)},
                    CI95=[percentile(0.025),percentile(0.975)], leave_one_source=[min(leave),max(leave)],
                    improved_sources=None if ratio else int(sum(v>0 if coverage else v<0 for v in strict)))
            result[stage] = metrics
        defects = {c.split("__")[-1] for c in ids}
        result["defect_deltas"] = {}
        for defect in defects:
            group = [c for c in ids if c.endswith("__"+defect)]
            require(len(group) == 21, f"defect stratum: {defect}")
            result["defect_deltas"][defect] = {
                stage:{k: average(pairs[c]["delta"][stage][k] for c in group)
                       for k in pairs[group[0]]["delta"][stage]} for stage in STAGES}
        summaries[key] = result
    mechanism = {}
    for arm in ("U","I"):
        data = {c:indexed[c,arm]["mechanism"] for c in ids}
        for cid,m in data.items():
            pi = label_receipts[cid]["positive"] / 8192
            same(pi,m["pi"],f"{arm}.{cid}.pi")
            if 0 < pi < 1:
                require(m["soft_AP"] is not None and 0 <= m["soft_AP"] <= 1+1e-12, f"AP defined: {cid}")
                same(m["soft_AP"]-pi,m["AP_minus_pi"],f"{arm}.{cid}.AP_minus_pi")
            else:
                require(m["soft_AP"] is m["AP_minus_pi"] is None, f"AP undefined: {cid}")
        metrics = {}
        fields = ("AP_minus_pi","Brier","constant_Brier","center_shift_mm","covariance_relative")
        for field in fields:
            by_source = [average(data[c][field] for c in case_groups[s] if data[c][field] is not None) for s in sources]
            metrics[field] = {"per_source": by_source, "mean": average(v for v in by_source if v is not None)}
        mechanism[arm] = dict(metrics=metrics, AP_defined=int(sum(r["soft_AP"] is not None for r in data.values())),
            AP_improved_sources=int(sum(x is not None and x > 0 for x in metrics["AP_minus_pi"]["per_source"])),
            manipulation_sources=int(sum(c>=2.0 or v>=0.10 for c,v in zip(metrics["center_shift_mm"]["per_source"],
                                                                      metrics["covariance_relative"]["per_source"]))))
    return pair_rows, dict(sources=sources, comparisons=summaries, mechanism=mechanism, formal_gate=False)


def main():
    req = ROOT / "CISC_RUI_D_CPU_scoring_execution_request_v2.json"
    auth = ROOT / "authorization_v2.json"
    q = json.loads(read(req))
    authorization = json.loads(read(auth))
    require(sha(read(req)) == REQUEST_SHA == authorization["request_sha256"]
            and authorization["explicit_user_authorization"] is True
            and q["output"] == str(OUT), "frozen request and authorization")
    bound(q["entry"])
    local = json.loads(bound(q["local_archive"]))
    require(local["remote_freeze"] == q["prediction_freeze"] and local["predictions"] == 315
            and local["members_hash_verified"] == 319, "prediction freeze binding")
    bound(q["prediction_freeze"])
    bound(local["archive"])
    cases = json.loads(bound(q["case_index"]))["cases"]
    ids = [c["case_id"] for c in cases]
    fold = json.loads(bound(q["fold"]))["folds"]["D"]
    require(ids == fold["dev_case_ids"] and len(ids) == len(set(ids)) == 105
            and q["sources"] == sorted(fold["dev_sources"]), "frozen Fold D development split")
    before = inventory(ids)
    attempt = json.loads(read(OUT / "attempt.json"))
    require(attempt == dict(request_sha256=REQUEST_SHA, authorization_sha256=sha(read(auth))), "attempt binding")
    completed = json.loads(read(OUT / "completion.json"))
    require(completed["status"] == "SCORED_AWAITING_READ_ONLY_FREEZE"
            and completed["counts"] == dict(model_rows=315, paired_cases=105, contrasts=315, sources=21,
                                            development_label_rows=105)
            and completed["formal_gate"] is False and completed["additional_forward"] == 0,
            "completion scope")
    boot = read(OUT / "bootstrap_indices.npy")
    draws = np.load(io.BytesIO(boot), allow_pickle=False)
    independently_generated = np.random.default_rng(q["bootstrap_seed"]).integers(0,21,size=(2000,21),dtype=np.int64)
    require(q["bootstrap_seed"] == 2026112507 and draws.dtype == np.int64 and np.array_equal(draws,independently_generated)
            and sha(boot) == completed["bootstrap_sha256"], "bootstrap array and SHA256")
    labels, changed, max_scale_diff = replay_evidence(cases)
    rows = [json.loads(line) for line in read(OUT / "model_scores.jsonl").splitlines()]
    pairs, summary = reaggregate(rows, cases, q["sources"], draws, labels)
    same(pairs, json.loads(read(OUT / "paired_cases.json")), "pairs")
    same(summary, json.loads(read(OUT / "source_summary.json")), "source_summary")
    require(inventory(ids) == before, "score artifacts stable across two hash passes")
    receipt = dict(status="FORMAL_CISC_RUI_D_CPU_SCORE_POST_FREEZE_AUDIT_PASS",
                  request_sha256=REQUEST_SHA, authorization_sha256=attempt["authorization_sha256"],
                  completion=completed, stable_two_pass_sha256=True, artifact_count=len(before),
                  artifact_hashes=before, verified_case_labels=len(labels),
                  frame_difference_cases=changed, max_abs_scale_difference_mm=max_scale_diff,
                  independent_contrasts=list(summary["comparisons"]), bootstrap_replicates=len(draws),
                  numeric_comparison=dict(rtol=1e-12,atol=1e-12), formal_gate_executed=False,
                  rescoring_executed=False, additional_forward=0)
    path = ROOT / "formal_post_score_freeze_receipt_v2.json"
    with path.open("x",encoding="utf-8",newline="\n") as f:
        json.dump(receipt,f,indent=2,allow_nan=False)
        f.write("\n")
    print(json.dumps(dict(status=receipt["status"], receipt_sha256=pin(path)["sha256"],
                          artifacts=len(before), contrasts=len(pairs), changed_frame_cases=changed,
                          max_scale_difference_mm=max_scale_diff)))


if __name__ == "__main__":
    main()
