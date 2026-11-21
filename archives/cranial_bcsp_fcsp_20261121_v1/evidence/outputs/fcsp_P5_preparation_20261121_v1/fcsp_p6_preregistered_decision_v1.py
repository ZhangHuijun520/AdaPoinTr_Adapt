"""P6 source-level bootstrap and preregistered FCSP decision from frozen P5 results."""

import hashlib
import json
import math
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parent
SCORES = ROOT / "unified_cpu_scores_v1"
SEEDS = {"C": 2026112001, "D": 2026112002}
MAIN = "B1-Local-B0-Global"
NATIVE = "B1-Local-N"
CONTROL = "B0-Global-N"
PROPORTIONS = {"E_Rec", "E_AbsRec", "J_Cover2", "far20"}
BENEFIT_POSITIVE = {"E_Rec", "E_AbsRec", "J_Cover2"}
METRICS = ("E_Rec", "E_AbsRec", "E_P95_mm", "J_P95_mm", "J_Cover2",
           "reverse_A2_P95_mm", "far20", "CD_L1_mm")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write("\n")


def summarize(fold, rows, cases, risks, dst):
    source_order = tuple(row["source_id"] for row in rows)
    assert len(source_order) == len(set(source_order)) == 21
    matrices = {}

    def matrix(ids):
        if ids not in matrices:
            label = f"{fold}_sources_{len(matrices) + 1}"
            rng = np.random.Generator(np.random.PCG64(SEEDS[fold]))
            draws = rng.integers(0, len(ids), size=(2000, len(ids)), dtype=np.int64)
            path = dst / (label + ".npy")
            with path.open("xb") as f:
                np.save(f, draws, allow_pickle=False)
            matrices[ids] = (draws, dict(file=path.name, sha256=sha(path.read_bytes()),
                                       source_order=list(ids), shape=list(draws.shape), seed=SEEDS[fold]))
        return matrices[ids]

    matrix(source_order)
    comparisons = {}
    for pair in (MAIN, NATIVE, CONTROL):
        summary = {}
        risk = risks[pair]
        assert sum(risk.values()) == 105
        for metric in METRICS:
            valid = []
            for row in rows:
                x = row["comparisons"][pair]["delta"][metric]
                if x["mean"] is not None:
                    assert math.isfinite(x["mean"]) and 1 <= x["cases"] <= 5
                    valid.append((row["source_id"], x["mean"], x["cases"]))
                else:
                    assert metric == "E_Rec" and x["cases"] == 0
            assert valid and (metric == "E_Rec" or len(valid) == 21)
            ids = tuple(x[0] for x in valid)
            v = np.array([x[1] for x in valid], dtype=np.float64)
            draws, info = matrix(ids)
            eps = 1e-12 if metric in PROPORTIONS else 1e-9
            sign = 1 if metric in BENEFIT_POSITIVE else -1
            recorded = [(x["case_id"], x["comparisons"][pair]["delta"][metric]) for x in cases]
            worst = min(((k, d) for k, d in recorded if d is not None), key=lambda x: (sign*x[1], x[0]))
            summary[metric] = dict(mean=float(v.mean()),
                                   CI95=np.percentile(v[draws].mean(axis=1), [2.5, 97.5], method="linear").tolist(),
                                   improved=int(np.count_nonzero(sign*v > eps)), direction_denominator=21,
                                   estimable=len(v), estimable_cases=sum(x[2] for x in valid),
                                   matrix=info["file"], worst_case_id=worst[0], worst_case_delta=worst[1],
                                   unit="fraction" if metric in PROPORTIONS else "mm")
        comparisons[pair] = dict(metrics=summary, risk=risk)
    return comparisons, [info for _, info in matrices.values()]


def gates(comparisons):
    b = comparisons[MAIN]
    n = comparisons[NATIVE]
    m, s = b["metrics"], n["metrics"]

    def safety(metrics, risk):
        return dict(J_P95=metrics["J_P95_mm"]["mean"] <= .25,
                    J_Cover2=metrics["J_Cover2"]["mean"] >= -.005,
                    reverse_A2_P95=metrics["reverse_A2_P95_mm"]["mean"] <= .50,
                    far20=metrics["far20"]["mean"] <= .0025,
                    no_new_severe=risk["01"] == 0)

    return dict(
        primary=dict(E_Rec_estimable=m["E_Rec"]["estimable"] >= 17,
                     E_Rec_mean=m["E_Rec"]["mean"] >= .03, E_Rec_direction=m["E_Rec"]["improved"] >= 14,
                     E_AbsRec_mean=m["E_AbsRec"]["mean"] >= .02, E_AbsRec_direction=m["E_AbsRec"]["improved"] >= 14,
                     E_P95_mean=m["E_P95_mm"]["mean"] <= -.50, E_P95_direction=m["E_P95_mm"]["improved"] >= 14,
                     **safety(m, b["risk"])),
        native=dict(E_AbsRec_mean=s["E_AbsRec"]["mean"] >= .01, E_P95_mean=s["E_P95_mm"]["mean"] <= -.25,
                    **safety(s, n["risk"])),
        strengthened=dict(E_Rec_CI_low=m["E_Rec"]["CI95"][0] > 0, E_P95_CI_high=m["E_P95_mm"]["CI95"][1] < 0))


def main():
    assert np.__version__ == "1.26.4"
    proof_raw = (ROOT / "P5_formal_scoring_freeze_receipt_v1.json").read_bytes()
    proof_hash = sha(proof_raw)
    assert proof_hash == "f68ed040a1478a20a1477b4a6e62a8ef4b52e4b244f215c894dc3d60fb21a1a2"
    proof = json.loads(proof_raw)
    assert proof["status"] == "PASS_FORMAL_READ_ONLY_P5_SCORING_FREEZE_AUDIT"
    data = {}
    for n, expected in proof["outputs"].items():
        raw = (SCORES / n).read_bytes()
        assert len(raw) == expected["bytes"] and sha(raw) == expected["sha256"], n
        data[n] = list(map(json.loads, raw.splitlines())) if n.endswith(".jsonl") else json.loads(raw)
    assert proof["counts"] == dict(cases=210, scoring_rows=630, sources=42)
    assert len(data["case_metrics.jsonl"]) == 630
    plan, = (ROOT.parents[1] / "docs/cranial_bcsp_fcsp_20261120_v2").glob("*正式*.md")
    prep = json.loads((ROOT / "FCSP_P5_twofold_evaluation_preparation_scope_v1.json").read_bytes())
    assert prep["protocol"]["sha256"] == sha(plan.read_bytes())
    dst = ROOT / "P6_preregistered_decision_v1"
    dst.mkdir()
    folds = {}
    for fold in SEEDS:
        cases = [x for x in data["paired_cases.jsonl"] if x["fold"] == fold]
        rows = sorted((x for x in data["source_metrics.json"] if x["fold"] == fold),
                      key=lambda x: x["source_id"])
        assert len(cases) == len({x["case_id"] for x in cases}) == 105
        comparison, draws = summarize(fold, rows, cases, data["risk_transitions.json"][fold], dst)
        folds[fold] = dict(comparisons=comparison, matrices=draws, gates=gates(comparison))
    point = all(all(x["gates"][part].values()) for x in folds.values() for part in ("primary", "native"))
    strong = all(all(x["gates"]["strengthened"].values()) for x in folds.values())
    status = "ELIGIBLE_TO_REQUEST_SECOND_SEED" if point and strong else (
        "DEVELOPMENT_EXPLORATORY_ONLY" if point else "DO_NOT_ADVANCE")
    result = dict(status=status, both_folds_point_gates=point, both_folds_strengthened_gates=strong,
                  folds=folds, protocol_sha256=sha(plan.read_bytes()), P5_audit_sha256=proof_hash,
                  script_sha256=sha(Path(__file__).read_bytes()), engine="NumPy 1.26.4 PCG64",
                  draws_per_matrix=2000, seed_application="Each distinct sorted estimable set starts with its fold seed; identical sets reuse one matrix.",
                  new_inference=0, new_training=0)
    write_json(dst / "P6_decision.json", result)
    files = sorted(dst.iterdir())
    write_json(dst / "artifact_manifest.json",
               {p.name: dict(bytes=p.stat().st_size, sha256=sha(p.read_bytes())) for p in files})
    print(status)
    for fold, row in folds.items():
        for name in (MAIN, NATIVE):
            c = row["comparisons"][name]
            print(fold, name, {k: (round(c["metrics"][k]["mean"], 6), c["metrics"][k]["improved"])
                               for k in METRICS}, c["risk"])
        print(fold, "failed", {k: [n for n,v in gates.items() if not v] for k,gates in row["gates"].items()})
    print("decision_sha256", sha((dst / "P6_decision.json").read_bytes()))


if __name__ == "__main__":
    main()
