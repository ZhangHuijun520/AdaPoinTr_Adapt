"""Validate only artificial metrics and freeze the audited Fold D CPU scoring request."""
import ast
import copy
import importlib.metadata
import io
import json
from pathlib import Path
import sys
import tarfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bcsp_scq_fv_BF_D_score_v1 as score
import numpy as np

OUT = HERE.parents[1]
PRED = HERE.parent / "foldD_BF_native_prediction_pending_v2"
ARCH = PRED / "post_prediction_freeze_v2"
HISTORY = OUT / "scq_score_impl_20261114_v1"
PLAN = OUT.parent / "docs/cranial_bcsp_scq_prime_20261121_v2/SCQ-F_FoldD_BF_两臂复现协议_2026-11-23_v1.md"


def record(p):
    return dict(path=str(p), bytes=p.stat().st_size, sha256=score.sha(p))


def pinned(p, digest):
    r=record(p)
    assert r["sha256"]==digest, p
    return r


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
    expanded = {**basic,"Qraw":coarse,"Qused":coarse,"delta":coarse}
    checks["model_specific_prediction_schema"] = (set(score.decode_prediction(npz(**basic),"B"))==set(basic)
        and set(score.decode_prediction(npz(**expanded),"F"))==set(expanded))
    inconsistent = {**expanded,"Qused":np.ones_like(coarse)}
    checks["missing_extra_or_inconsistent_diagnostics_rejected"] = (
        rejected(lambda:score.decode_prediction(npz(**basic),"F"))
        and rejected(lambda:score.decode_prediction(npz(**expanded),"B"))
        and rejected(lambda:score.decode_prediction(npz(**inconsistent),"F")))
    modified = copy.deepcopy(cases)
    modified[0]["normalization"]["scale"] += 1
    checks["changed_coordinate_frame_rejected"] = rejected(lambda:score.validate_cases(index,reference,modified))
    rows = []
    for case in cases:
        for a, base in zip(score.ARMS,(5.,4.)):
            metrics={k:base for k in score.KEYS}
            metrics["J_coverage_2.0mm"]=(6.-base)/100. if a in score.ARMS else .1
            rows.append(dict(case_id=case["case_id"],source_id=case["source_id"],arm=a,metrics=metrics,
                             risk_labels=dict(severe_geometry=False)))
    ids=sorted({r["source_id"] for r in rows})
    groups, pairs=score.summarize(rows,ids,indices)
    e="E_P95_mm"
    checks["exact_210_model_rows_and_F_minus_B"] = len(groups)==42 and set(pairs)=={"F_minus_B"} and pairs["F_minus_B"]["metrics"][e]["mean"]==-1.
    p=pairs["F_minus_B"]["metrics"]
    checks["source_bootstrap_pp_direction_and_leave_one"] = (
        p[e]["CI95"]==[-1.,-1.] and p[e]["improved"]==21 and p[e]["leave_one_source_range"]==[-1.,-1.]
        and np.isclose(p["J_coverage_2.0mm"]["mean"],1.))
    checks["missing_paired_row_rejected"] = rejected(lambda:score.summarize(rows[:-1],ids,indices))
    checks["bootstrap_2000_by_21_PCG64_repeat"] = indices.shape==(2000,21) and np.array_equal(indices,score.bootstrap_indices())
    assert all(checks.values()), checks
    return {name: bool(ok) for name, ok in checks.items()}



def main():
    history_request = pinned(HISTORY/"local_scoring_execution_request_v1.json",
                             "7e5cb8f286e215b4b1712254d7c1068a5bc5d4048a8ec128fa446997a3ef4ad9")
    historical = score.read(history_request)
    environment=historical["environment"]
    assert score.exact(environment["python"])==Path(sys.executable) and sys.version==environment["python_version"]
    assert all(importlib.metadata.version(k)==v for k,v in environment["packages"].items())
    implementation=dict(helpers=historical["implementation"]["scorer"],metrics=historical["implementation"]["metrics"],
                        scorer=record(HERE/"bcsp_scq_fv_BF_D_score_v1.py"))
    assert implementation["metrics"]["sha256"]==score.METRIC_SHA
    for r in implementation.values():
        p=score.exact(r)
        ast.parse(p.read_bytes(),filename=str(p))
    prediction=pinned(PRED/"SCQ_FV_BF_D_native_execution_request_v1.json",
                      "4a5eee455d20025369f13c6e5b1a568e60acb394bee6bc65908e3094aaf08005")
    audit_record=pinned(ARCH/"BF_D_post_prediction_freeze_receipt_v1.json",
                        "3bb476dc5416cd3f6a9d38d98121336998a4a2047a42c4d81ab303b724a00d05")
    audit=score.read(audit_record)
    assert audit["status"]=="FORMAL_SCQ_FV_BF_D_NATIVE_POST_PREDICTION_FREEZE_PASS"
    assert audit["request_sha256"]==prediction["sha256"] and audit["archive_sha256"]==score.ARCHIVE_SHA
    assert audit["per_arm"]==dict(B=105,F=105) and audit["stable_remote_inventory"] is True
    local=ARCH/"audit_readback"
    archive=pinned(local/"development_predictions_v1.tar.gz",score.ARCHIVE_SHA)
    sidecars=[record(local/(Path(archive["path"]).name+"."+suffix)) for suffix in ("sha256","bytes","contents.sha256")]
    completion=record(local/"completion.json")
    frozen_server=json.loads((ARCH/"server_inventory_after_v1.json").read_bytes())["files"]
    assert all([r["bytes"],r["sha256"]]==frozen_server[Path(r["path"]).name] for r in (archive,*sidecars,completion))
    pred=score.read(prediction)
    pr_index=pinned(PRED/"SCQ_FV_BF_D_development_index_v1.json",pred["input_index"]["sha256"])
    index=score.read(pr_index)
    assert index["fold"]=="D" and index["arms"]==list(score.ARMS)
    reference=score.read(historical["reference_manifest"])
    old_cases=score.read(historical["score_case_index"])
    prior={c["case_id"]:c for c in old_cases["cases"] if c["fold"]=="D"}
    assert len(prior)==105 and set(prior)=={r["case_id"] for r in index["inputs"]}
    cases=[prior[r["case_id"]] for r in index["inputs"]]
    score.validate_cases(index,reference,cases)
    for case in cases:
        score.exact(case["reference"])
        score.exact(case["point_file"])
    assert score.check_historical_controls(historical["frozen_baseline_scores"],cases)==210
    legacy=score.load_source("frozen_score_helpers",implementation["helpers"])
    assert Path(legacy.METRIC_PATH)==score.exact(implementation["metrics"])
    indices=score.bootstrap_indices()
    checks=tests(cases,index,reference,legacy,indices)
    checkpoint_hashes={arm:val["checkpoint"]["sha256"] for arm,val in pred["model_records"].items()}
    with tarfile.open(score.exact(archive),"r:gz") as stream:
        lookup=score.check_archive(stream,cases,dict(checkpoint_hashes=checkpoint_hashes),
                                   score.read(completion),Path(sidecars[2]["path"]).read_text(encoding="ascii"))
    assert len(lookup)==210
    checks.update(frozen_archive_case_pairing=True,reference_and_point_asset_hashes=True,
                  historical_controls_bound_without_rescoring=True,metric_core_hash_unchanged=True)
    output=HERE/"unified_scores_v1"
    auth=HERE/"authorized_execution_v1/score_authorization_v1.json"
    assert not output.exists() and not auth.parent.exists()
    case_index=HERE/"BF_D_score_case_index_v1.json"
    score.emit(case_index,dict(status="FROZEN_FIXED_105_CASE_SCORE_INDEX",cases=cases))
    bootstrap=HERE/"BF_D_bootstrap_indices_v1.npy"
    with bootstrap.open("xb") as stream:
        np.save(stream,indices,allow_pickle=False)
    protocol=HERE/"BF_D_score_protocol_v1.json"
    score.emit(protocol,dict(status="FROZEN_NO_SCORING_AUTHORIZATION",
        plan=pinned(PLAN,"8c8cde70a16b5b8cc599fa9355116c3ea32085a0fa496a33a1b6d0a1291e4cce"),counts=score.COUNTS,
        ordered_source_ids=sorted({r["source_id"] for r in cases}),pairs=["F minus B"],
        bootstrap=dict(engine="PCG64",seed=score.BOOTSTRAP_SEED,replicates=2000,unit="paired_source"),
        frame="world_mm_D_only_inverse_normalization_no_GT_alignment",
        source_aggregation="five defects equal within source; all 21 sources equal",
        endpoint="A1 area-weighted E P95; A1 J P95/J Cover@2; Pred to A2 P95 and strictly greater than 20 mm",
        severe="E P95 > 20 mm or J Cover@2 = 0",shared_controls_reused=list(score.CONTROLS),
        gate_parameters=dict(E_P95_max_mm=-0.50,E_improved_sources_min=14,J_P95_max_mm=0.25,
            J_Cover_at_2_min_pp=-0.50,reverse_A2_P95_max_mm=0.50,far20_max_pp=0.25,
            severe_F_no_more_than_B=True,new_severe_max=2),formal_gate_in_this_execution=False))
    p3=HERE/"BF_D_score_P3_v1.json"
    score.emit(p3,dict(status="SCQ_FV_FOLD_D_LOCAL_SCORE_P3_PASS",checks=checks,
        scorer_sha256=implementation["scorer"]["sha256"],metric_sha256=score.METRIC_SHA,validation=record(Path(__file__)),
        real_scores_computed=0,GPU_calls=0,server_writes=0))
    request=HERE/"BF_D_CPU_scoring_execution_request_v1.json"
    score.emit(request,dict(schema="bcsp-scq-fv-BF-D-score-request-v1",status="AWAITING_EXPLICIT_USER_AUTHORIZATION",
        execution_authorized=False,fold="D",seed=2026112101,counts=score.COUNTS,limits=score.LIMITS,
        archive=archive,sidecars=sidecars,prediction_completion=completion,prediction_audit=audit_record,
        prediction_request_sha256=prediction["sha256"],checkpoint_hashes=checkpoint_hashes,
        prediction_index=pr_index,reference_manifest=historical["reference_manifest"],historical_controls=historical["frozen_baseline_scores"],
        implementation=implementation,environment=environment,score_case_index=record(case_index),
        bootstrap_indices=record(bootstrap),protocol=record(protocol),P3=record(p3),
        output=str(output),authorization_path=str(auth),execution_attempts=1,automatic_retry=False,
        foreground=True,external_wall_timeout_seconds=18030,
        expected_files=["case_metrics.jsonl","case_metrics.csv","source_metrics.json","paired_comparisons.json","completion.json"],
        real_scoring_executed_now=False,formal_gate_executed_now=False))
    assert score.read(record(request))["P3"]==record(p3)
    print(json.dumps(dict(request=record(request),p3=record(p3),protocol=record(protocol),check_count=len(checks),references=105,point_sets=105)))


if __name__=="__main__":
    main()
