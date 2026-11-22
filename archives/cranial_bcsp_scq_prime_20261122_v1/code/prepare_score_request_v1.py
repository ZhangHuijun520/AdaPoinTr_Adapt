"""Bind the audited archive and historical scoring assets after local CPU tests."""
import ast
import copy
import importlib.metadata
import io
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bcsp_scq_prime_BFS_C_score_v1 as score
import numpy as np

OUT = HERE.parents[1]
PRED = HERE.parent / "BFS_C_native_prediction_preparation_v1"
ARCH = PRED / "post_prediction_freeze_v2"
HISTORY = OUT / "scq_score_impl_20261114_v1"


def record(p):
    return dict(path=str(p), bytes=p.stat().st_size, sha256=score.sha(p))


def rejected(call):
    try:
        call()
    except ValueError:
        return True
    return False


def tests(cases, index, reference, legacy, indices):
    m = legacy.metric
    checks = {}
    points = np.array([[0.,0.,0.],[0.,1.,0.]], dtype=np.float64)
    checks["D_only_world_millimeters"] = np.array_equal(
        m.world_points(points,dict(center=[5.,6.,7.],scale=2)),np.array([[5.,6.,7.],[5.,8.,7.]]))
    checks["inclusive_two_mm_and_strict_outlier"] = m.stats([2.,2.00000001])["coverage"]["2.0"] == .5
    checks["weighted_P95_exact_boundary"] = (m.weighted_quantile([0.,20.],[95.,5.]) == 0.
                                             and m.weighted_quantile([0.,20.],[94.,6.]) == 20.)
    checks["severe_threshold_is_strict_or_zero_coverage"] = (not legacy.risk_labels(
        {"E_P95_mm":20.,"J_coverage_2.0mm":.1},dict(centroid_offset_mm=0,radius_gyration_ratio=1))["severe_geometry"]
        and legacy.risk_labels({"E_P95_mm":21.,"J_coverage_2.0mm":.1},dict(centroid_offset_mm=0,radius_gyration_ratio=1))["severe_geometry"]
        and legacy.risk_labels({"E_P95_mm":0.,"J_coverage_2.0mm":0.},dict(centroid_offset_mm=0,radius_gyration_ratio=1))["severe_geometry"])
    ref = dict(a_centers=np.array([[2.,0.,0.],[2.,1.,0.]]),a_weights=np.array([1.,2.]),
               a_is_j=np.array([False,True]),a_axes=np.array([0,0]),b_centers=np.array([[2.,.5,0.]]),
               b_weights=np.array([1.]),affine=np.eye(3),origin=np.zeros(3))
    values,_,_,_=score.case_metric(m,legacy,points,ref,points)
    checks["real_metric_core_on_synthetic_A1_A2"] = values["E_P95_mm"]==values["J_P95_mm"]==2. and values["J_coverage_2.0mm"]==1.
    invalid = {**ref,"a_is_j":np.array([False,False])}
    checks["empty_interface_rejected"] = rejected(lambda:score.case_metric(m,legacy,points,invalid,points))
    def npz(**items):
        f = io.BytesIO()
        np.savez(f,**items)
        return f.getvalue()
    coarse = np.zeros((256,3),np.float32)
    dense = np.zeros((8192,3),np.float32)
    basic = dict(coarse=coarse,prediction=dense)
    expanded = {**basic,"Qraw":coarse,"delta":coarse}
    trace = {**expanded,"neighbor_indices":np.zeros((256,8),np.int64)}
    checks["model_specific_prediction_schema"] = (set(score.decode_prediction(npz(**basic),"B",True))==set(basic)
        and set(score.decode_prediction(npz(**expanded),"F",False))==set(expanded)
        and set(score.decode_prediction(npz(**trace),"S",True))==set(trace))
    checks["missing_or_extra_diagnostic_fields_rejected"] = (
        rejected(lambda:score.decode_prediction(npz(**expanded),"F",True))
        and rejected(lambda:score.decode_prediction(npz(**trace),"B",True)))
    modified = copy.deepcopy(cases)
    modified[0]["normalization"]["scale"] += 1
    checks["changed_coordinate_frame_rejected"] = rejected(lambda:score.validate_cases(index,reference,modified))
    rows = []
    for case in cases:
        for a, base in zip(score.ARMS+score.CONTROLS,(5.,4.,3.,10.,1.)):
            metrics={k:base for k in score.KEYS}
            metrics["J_coverage_2.0mm"]=(6.-base)/100. if a in score.ARMS else .1
            rows.append(dict(case_id=case["case_id"],source_id=case["source_id"],arm=a,metrics=metrics,
                             risk_labels=dict(severe_geometry=False)))
    ids=sorted({r["source_id"] for r in rows})
    groups, pairs=score.summarize(rows,ids,indices)
    e="E_P95_mm"
    checks["exact_525_rows_and_three_source_contrasts"] = (len(groups)==105 and set(pairs)=={"S_minus_B","S_minus_F","F_minus_B"}
        and [pairs[k]["metrics"][e]["mean"] for k in ("S_minus_B","S_minus_F","F_minus_B")]==[-2.,-1.,-1.])
    p=pairs["S_minus_B"]["metrics"]
    checks["source_bootstrap_and_pp_direction"] = p[e]["CI95"]==[-2.,-2.] and p[e]["improved"]==21 and np.isclose(p["J_coverage_2.0mm"]["mean"],2.)
    checks["missing_paired_row_rejected"] = rejected(lambda:score.summarize(rows[:-1],ids,indices))
    checks["bootstrap_2000_by_21_PCG64_repeat"] = indices.shape==(2000,21) and np.array_equal(indices,score.bootstrap_indices())
    assert all(checks.values()), checks
    return {name: bool(ok) for name, ok in checks.items()}


def freeze_json(path, value):
    if path.exists():
        assert score.read(record(path)) == value
    else:
        score.emit(path,value)


def main():
    historical = json.loads((HISTORY / "local_scoring_execution_request_v1.json").read_bytes())
    environment = historical["environment"]
    assert score.exact(environment["python"]) == Path(sys.executable) and sys.version == environment["python_version"]
    assert all(importlib.metadata.version(k) == v for k,v in environment["packages"].items())
    expected_primitives = {"helpers":historical["implementation"]["scorer"],"metrics":historical["implementation"]["metrics"]}
    assert expected_primitives["metrics"]["sha256"]==score.METRIC_SHA
    implementation = {**expected_primitives, "scorer":record(HERE/"bcsp_scq_prime_BFS_C_score_v1.py")}
    for k,v in implementation.items():
        p = score.exact(v)
        ast.parse(p.read_bytes(),filename=str(p))
    prediction = record(PRED/"SCQ_PRIME_BFS_C_native_execution_request_v1.json")
    audit_path=ARCH/"BFS_C_post_prediction_freeze_receipt_v1.json"
    audit=score.read(record(audit_path))
    assert audit["status"]=="FORMAL_PRIME_BFS_C_NATIVE_POST_PREDICTION_FREEZE_PASS"
    assert audit["request_sha256"]==prediction["sha256"] and audit["archive_sha256"]==score.ARCHIVE_SHA
    assert audit["per_arm"]==dict(B=105,F=105,S=105) and audit["stable_remote_inventory"] is True
    frozen_server=score.read(record(ARCH/"server_inventory_after_v1.json"))["files"]
    local=ARCH/"audit_readback"
    archive=record(local/"development_predictions_v1.tar.gz")
    assert archive["sha256"]==score.ARCHIVE_SHA and archive["bytes"]==audit["archive_bytes"]
    sidecars=[record(Path(archive["path"]+"."+s)) for s in ("sha256","bytes","contents.sha256")]
    completion=record(local/"completion.json")
    assert all([r["bytes"],r["sha256"]]==frozen_server[Path(r["path"]).name] for r in (archive,*sidecars,completion))
    pred=score.read(prediction)
    pr_index=record(PRED/"SCQ_PRIME_BFS_C_development_index_v1.json")
    assert pr_index["sha256"]==pred["input_index"]["sha256"]
    index=score.read(pr_index)
    reference=score.read(historical["reference_manifest"])
    old_cases=score.read(historical["score_case_index"])
    prior={c["case_id"]:c for c in old_cases["cases"] if c["fold"]=="C"}
    assert len(prior)==105 and set(prior)=={r["case_id"] for r in index["inputs"]}
    cases=[{**prior[r["case_id"]],"trace":r["selected_neighborhood_trace"]} for r in index["inputs"]]
    score.validate_cases(index,reference,cases)
    for r in cases:
        score.exact(r["reference"])
        score.exact(r["point_file"])
    controls={}
    with score.exact(historical["frozen_baseline_scores"]).open(encoding="utf-8") as stream:
        for line in stream:
            r=json.loads(line)
            if r["fold"]=="C" and r["arm"] in score.CONTROLS:
                key=(r["arm"],r["case_id"])
                assert key not in controls
                controls[key]=r
    assert set(controls)=={(a,r["case_id"]) for r in cases for a in score.CONTROLS}
    assert all(all(k in r["metrics"] for k in score.KEYS) and r["status"]=="OK" for r in controls.values())
    legacy=score.load_source("bound_historical_scoring_helpers",implementation["helpers"])
    indices=score.bootstrap_indices()
    checks=tests(cases,index,reference,legacy,indices)
    checks["read_only_exact_archive_and_210_case_asset_hashes"]=True
    checks["210_historical_control_rows_exist"]=True
    checks["metric_core_hash_unchanged"]=True
    output=HERE/"unified_scores_v1"
    auth=HERE/"authorized_execution_v1/score_authorization_v1.json"
    assert not output.exists() and not auth.parent.exists()
    frozen_plan=next(Path(HERE.parents[2]/"docs/cranial_bcsp_scq_prime_20261121_v2").glob("*.md"))
    case_index=HERE/"BFS_C_score_case_index_v1.json"
    freeze_json(case_index,dict(status="FROZEN_FIXED_105_CASE_SCORE_INDEX",cases=cases))
    bootstrap=HERE/"BFS_C_bootstrap_indices_v1.npy"
    if bootstrap.exists():
        assert np.array_equal(np.load(bootstrap,allow_pickle=False),indices)
    else:
        with bootstrap.open("xb") as stream:
            np.save(stream,indices,allow_pickle=False)
    protocol=HERE/"BFS_C_score_protocol_v1.json"
    freeze_json(protocol,dict(status="FROZEN_NO_SCORING_AUTHORIZATION",plan=record(frozen_plan),counts=score.COUNTS,
        ordered_source_ids=sorted({r["source_id"] for r in cases}),pairs=["S−B","S−F","F−B"],
        bootstrap=dict(engine="PCG64",seed=score.BOOTSTRAP_SEED,replicates=2000,unit="paired_source"),
        frame="world_mm_D_only_inverse_normalization_no_GT_alignment",
        source_aggregation="five defects equal within source; all 21 sources equal",
        endpoint="A1 area-weighted E P95; A1 J P95/J Cover@2; Pred→A2 P95/>20 mm",
        shared_controls=["Nop_D","GT_8192"],formal_gate_in_this_execution=False))
    p3=HERE/"BFS_C_score_P3_v2.json"
    score.emit(p3,dict(status="SCQ_PRIME_FOLD_C_LOCAL_SCORE_P3_PASS",checks=checks,
        scorer_sha256=implementation["scorer"]["sha256"],metric_sha256=score.METRIC_SHA,
        validation=record(Path(__file__)),real_scores_computed=0,GPU_calls=0,server_writes=0))
    request=HERE/"BFS_C_CPU_scoring_execution_request_v1.json"
    score.emit(request,dict(schema="bcsp-scq-prime-BFS-C-score-request-v1",status="AWAITING_EXPLICIT_USER_AUTHORIZATION",
        execution_authorized=False,fold="C",seed=2026112101,counts=score.COUNTS,limits=score.LIMITS,
        archive=archive,sidecars=sidecars,prediction_completion=completion,prediction_audit=record(audit_path),
        prediction_request_sha256=prediction["sha256"],checkpoint_hashes={a:m["checkpoint"]["sha256"] for a,m in pred["model_records"].items()},
        prediction_index=pr_index,reference_manifest=historical["reference_manifest"],historical_controls=historical["frozen_baseline_scores"],
        implementation=implementation,environment=environment,score_case_index=record(case_index),
        bootstrap_indices=record(bootstrap),protocol=record(protocol),P3=record(p3),
        output=str(output),authorization_path=str(auth),execution_attempts=1,automatic_retry=False,
        foreground=True,external_wall_timeout_seconds=18030,
        expected_files=["case_metrics.jsonl","case_metrics.csv","source_metrics.json","paired_comparisons.json","completion.json"],
        real_scoring_executed_now=False,formal_gate_executed_now=False))
    print(json.dumps(dict(request=record(request),p3=record(p3),check_count=len(checks),references=105,point_sets=105)))


if __name__=="__main__":
    main()
