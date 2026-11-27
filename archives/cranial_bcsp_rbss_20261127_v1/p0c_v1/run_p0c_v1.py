"""RBSS P0c offline extension of the audited 15-case Fold D pilot."""
from collections import Counter
import io
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
import scipy
from threadpoolctl import threadpool_limits, threadpool_info

STAGE = Path(__file__).resolve().parent
PILOT_ROOT = STAGE.parent / "p0b_v1"
sys.path.insert(0, str(PILOT_ROOT))
import run_p0b_v1 as pilot
from rbss_geometry_v1 import fit_plane, native_order, normal_for, plan_orders

PLAN = "96ea381c31f4f29f872d6b7e29ef0b8d95b60f579b335fe7ac522ef33fa35036"
SCOPE = "6232f8a751f60360c0bb0cca9e509702dba005be275cb98182c62c13a44a94a8"
RESULT = "cd7a65a805b0dcf4f940a7fcbc9e35cdabe2dc42bc2ee4b86357426625002608"
AUDIT = "8393c1d724c19dd6e3ec247bb30bc4240dcf2e38a85ceaa05ce4de1ac5a57019"
need, digest, bound = pilot.need, pilot.digest, pilot.bound


def triples(data):
    return Counter(data[i:i + 12] for i in range(0, len(data), 12))


def check_serialization(plane, s, native, anchors_mm):
    ids = list(range(256))
    need(s["order"]["R"] == native.tolist(), "historical native ordering")
    for arm in ("R", "S", "C"):
        order, inv = s["order"][arm], s["inverse"][arm]
        need(sorted(order) == sorted(inv) == ids and all(inv[order[i]] == order[inv[i]] == i for i in ids),
             "bijective order/inverse")
    if not s["joint_active"]:
        for field in ("order", "inverse"):
            need(s[field]["R"] == s[field]["S"] == s[field]["C"], "exact common fallback")
        return
    k = s["k"]
    se, ce = s["s_edges"], s["c_edges"]
    need(plane["plane_ok"] and not s["reasons"] and len(se) == len(ce) == k >= 16, "active gate")
    need(not set(map(tuple, se)) & set(map(tuple, ce)), "no original mirror edge in control")
    for side in (0, 1):
        need(len({e[side] for e in se}) == k and sorted(e[side] for e in se) == sorted(e[side] for e in ce),
             "control endpoint match")
    a, d, b = plane["splits"][0]["best"]["abc"]
    n = normal_for(a, d)
    signed = (anchors_mm - plane["center_mm"]) @ n - b
    mirror = anchors_mm - 2 * signed[:, None] * n
    for edges, use_mirror in ((np.array(se), True), (np.array(ce), False)):
        l, r = edges.T
        forward = np.linalg.norm(mirror[l] - anchors_mm[r], axis=1)
        reverse = np.linalg.norm(mirror[r] - anchors_mm[l], axis=1)
        need(np.all(signed[l] > 3) and np.all(signed[r] < -3), "opposite eligible LPS endpoints")
        if use_mirror:
            need(np.all(forward <= s["tau_mm"]) and np.all(reverse <= s["tau_mm"]), "mirror distance")
        else:
            need(np.all(forward > s["tau_mm"]) and np.all(reverse > s["tau_mm"]), "forbidden control reflection")
    for arm, edges in (("S", se), ("C", ce)):
        old, new = s["inverse"]["R"], s["inverse"][arm]
        need(all(abs(new[a] - new[b]) == 1 for a, b in edges), "paired sequence adjacency")
        need(sum(abs(old[a] - old[b]) != 1 for a, b in edges) >= (k + 1) // 2, "new adjacencies")
    c = s["inverse"]["C"]
    need(1 - sum(abs(c[a] - c[b]) == 1 for a, b in se) / k >= 0.25, "mirror adjacency contrast")
    need(s["c_length_match_fraction"] >= 0.80 and s["c_rank_deviation_median"] <= 32, "local match")
    w = s["whole_sequence"]
    need(all(w["observed"][key] <= limit for key, limit in w["limits"].items()), "whole sequence match")


def angle(a, b):
    return math.degrees(math.atan2(float(np.linalg.norm(np.cross(a, b))), float(a @ b)))


def source_result(records, manifest):
    # Records retain the frozen Fold D case order, including representative tie order.
    xref = np.median([manifest[r["case_id"]]["normalization"]["center"] for r in records], axis=0)
    good = [r for r in records if r["plane"]["plane_ok"]]
    planes = []
    for r in good:
        fit = r["plane"]
        a, d, b = fit["splits"][0]["best"]["abc"]
        n = normal_for(a, d)
        planes.append((r["case_id"], n, float(n @ (xref - fit["center_mm"]) - b)))
    eligible = len(planes) >= 3
    representative = checks = None
    if eligible:
        rep = min(range(len(planes)), key=lambda i: sum(angle(planes[i][1], p[1]) for p in planes))
        representative, n, offset = planes[rep]
        checks = [dict(case_id=cid, angle_deg=angle(n, v), offset_difference_mm=abs(o - offset))
                  for cid, v, o in planes]
    return dict(plane_ok=len(good), joint_active=sum(r["serialization"]["joint_active"] for r in records),
                eligible=eligible, reference_point_mm=xref.tolist(), representative=representative,
                stable=eligible and all(r["angle_deg"] <= 8 and r["offset_difference_mm"] <= 8 for r in checks),
                comparisons=checks)


def main():
    started = time.perf_counter()
    scope_path = STAGE / "P0c_scope_v1.json"
    results_path = STAGE / "P0c_results_v1.json"
    need(not scope_path.exists() and not results_path.exists(), "fresh versioned paths")
    plans = list(STAGE.parent.glob("*2026-11-26_v2.md"))
    need(len(plans) == 1 and digest(plans[0].read_bytes()) == PLAN, "approved RBSS plan")
    scope = json.loads(bound(PILOT_ROOT / "P0b_cases_and_protocol_v1.json", SCOPE))
    need(scope["sources"] == pilot.local_source_hashes(), "frozen P0b implementation")
    seed = json.loads(bound(PILOT_ROOT / "P0b_results_v1.json", RESULT))
    final_audit = STAGE.parent / "p0b_prefix16_v1/P0b_prefix16_formal_post_diagnostic_freeze_audit_v1.json"
    audit = json.loads(bound(final_audit, AUDIT))
    need(seed["geometry_gate_pass"] and seed["scope_sha256"] == SCOPE
         and audit["status"] == "FORMAL_P0B_PREFIX16_READ_ONLY_FREEZE_AUDIT_PASS"
         and audit["verdict"]["outcome"] == "CONDITIONAL_CONTENT_KEYED_CACHE_PASS", "P0b gates")
    need((np.__version__, scipy.__version__) == (scope["numpy"], scope["scipy"]), "geometry dependencies")
    fold = json.loads(bound(pilot.PAYLOAD / "fold_binding.json", pilot.FOLD))["folds"]["D"]
    manifest = {r["case_id"]: r for r in map(json.loads, bound(
        pilot.PAYLOAD / "manifest_8192.jsonl", pilot.MANIFEST).splitlines())}
    train = fold["train_case_ids"]
    old = {row["case_id"]: row for row in seed["records"]}
    need(len(train) == len(set(train)) == 315 and not set(train) & set(fold["dev_case_ids"])
         and len(old) == 15 and set(old) == {r["case_id"] for r in scope["case_list"]}
         and set(old) <= set(train), "exact Fold D and pilot IDs")
    assets = pilot.capture_assets(set(train))
    input_records, records = [], []
    with threadpool_limits(limits=1):
        need(all(x["num_threads"] == 1 for x in threadpool_info()), "single-thread geometry")
        # Validate the entire input/cache population before computing new geometry.
        loaded = {}
        for cid in train:
            rec = manifest[cid]
            x_sha, anchors, capture_sha = assets[cid]
            with np.load(io.BytesIO(bound(pilot.POINTS / rec["point_path"], rec["sha256"])), allow_pickle=False) as z:
                x = z["partial"]
            xbytes, abytes = x.tobytes(), anchors.tobytes()
            need(x.shape == (8192, 3) and x.dtype == np.float32 and np.isfinite(x).all()
                 and digest(xbytes) == x_sha and not (triples(abytes) - triples(xbytes)), "historical anchor binding " + cid)
            n = rec["normalization"]
            center, scale = np.array(n["center"], dtype=np.float64), float(n["scale"])
            need(center.shape == (3,) and np.isfinite(center).all() and math.isfinite(scale) and scale > 0,
                 "physical frame " + cid)
            native = native_order(anchors)
            binding = dict(case_id=cid, source_id=rec["source_id"], type=cid.split("__", 2)[2], reusable_pilot=cid in old,
                           point_sha256=rec["sha256"], input_sha256=x_sha,
                           anchors_sha256=digest(abytes), historical_capture_sha256=capture_sha,
                           native_order_sha256=digest(native.astype("<i8").tobytes()))
            if cid in old:
                prev = old[cid]
                need((prev["input_sha256"], prev["anchor_sha256"], prev["historical_shard_sha256"])
                     == (x_sha, binding["anchors_sha256"], capture_sha), "pilot input continuity " + cid)
            if cid in audit["verdict"]["cases"]:
                need(audit["verdict"]["cases"][cid]["historical_equal"] is True, "audited focal anchors")
            input_records.append(binding)
            loaded[cid] = x, center, scale, anchors, native
        gates = dict(total_active_min=221, per_type_min=32, active_sources_min=45,
                     minimum_active_per_source=3, plane_eligible_sources_min=45,
                     minimum_plane_ok_per_source=3, plane_stable_share_min=0.80,
                     angle_deg_max=8, offset_mm_max=8)
        pilot.write_once(scope_path, dict(plan_sha256=PLAN, fold_sha256=pilot.FOLD, manifest_sha256=pilot.MANIFEST,
                                          p0b_result_sha256=RESULT, p0b_runtime_audit_sha256=AUDIT,
                                          p0c_runner_sha256=digest(Path(__file__).read_bytes()),
                                          all_cases=input_records, gates=gates, new_prefix_calls=0))
        for index, binding in enumerate(input_records, 1):
            cid = binding["case_id"]
            x, center, scale, anchors, native = loaded[cid]
            anchors_mm = anchors.astype(np.float64) * scale + center
            if cid in old:
                plane, ordering = (old[cid][k] for k in ("plane", "serialization"))
            else:
                plane = fit_plane(x.astype(np.float64) * scale + center)
                ordering = plan_orders(anchors, anchors_mm, plane)
            check_serialization(plane, ordering, native, anchors_mm)
            records.append(dict(**binding, plane=plane, serialization=ordering))
            if index % 50 == 0 or index == len(train):
                print("GEOMETRY", index, len(train), flush=True)
    by_source = {sid: source_result([r for r in records if r["source_id"] == sid], manifest)
                 for sid in fold["train_sources"]}
    need(len(by_source) == 63 and all(sum(r["source_id"] == sid for r in records) == 5
                                     for sid in by_source), "63 sources of five")
    by_type = {typ: dict(total=sum(r["type"] == typ for r in records),
                         plane_ok=sum(r["type"] == typ and r["plane"]["plane_ok"] for r in records),
                         active=sum(r["type"] == typ and r["serialization"]["joint_active"] for r in records))
               for typ in pilot.TYPES}
    need(all(v["total"] == 63 for v in by_type.values()), "five defect strata")
    active = sum(v["active"] for v in by_type.values())
    active_sources = sum(v["joint_active"] >= 3 for v in by_source.values())
    eligible = sum(v["eligible"] for v in by_source.values())
    stable = sum(v["stable"] for v in by_source.values())
    decisions = dict(total=active >= 221, each_type=min(v["active"] for v in by_type.values()) >= 32,
                     source_activation=active_sources >= 45, plane_source_count=eligible >= 45,
                     plane_source_stability=eligible > 0 and 5 * stable >= 4 * eligible,
                     all_active_controls_and_common_fallbacks_verified=True)
    summary = dict(status="P0C_OFFLINE_GEOMETRY_PASS" if all(decisions.values()) else "P0C_OFFLINE_GEOMETRY_STOP",
                   cases=315, reused_p0b=15, newly_computed=300, new_prefix_calls=0, optimizer_steps=0,
                   active=active, plane_ok=sum(v["plane_ok"] for v in by_type.values()),
                   active_sources=active_sources, eligible_plane_sources=eligible, stable_plane_sources=stable,
                   by_type=by_type, gates=decisions,
                   plane_reasons=dict(Counter(reason for r in records for reason in r["plane"]["reasons"])),
                   sequence_reasons=dict(Counter(reason for r in records for reason in r["serialization"]["reasons"])),
                   seconds=time.perf_counter() - started)
    pilot.write_once(results_path, dict(summary=summary, scope_sha256=digest(scope_path.read_bytes()),
                                        by_source=by_source, records=records))
    print(json.dumps(dict(summary=summary, result_sha256=digest(results_path.read_bytes()))), flush=True)


if __name__ == "__main__":
    main()
