"""Lock and evaluate the 15 RBSS cases using authenticated historical OASG coordinates."""
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import sys
import time

import numpy as np
import scipy

from rbss_geometry_v1 import fit_plane, plan_orders


STAGE = Path(__file__).resolve().parent
OUTPUTS = STAGE.parents[1]
PAYLOAD = OUTPUTS / "cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload"
POINTS = OUTPUTS / "cranial_bcsp_geov1_20261024/real_data_qc_v1"
CISC = OUTPUTS / "bcsp_cisc_20261125_v2"
ARCHIVE = Path("E:/ResearchBackups/AdaPoinTr/BCSP_CISC/2026-11-25_archive_v1")
PLAN = STAGE.parent / "BCSP-RBSS_可靠性约束双侧对称序列化_正式实验计划_2026-11-26_v2.md"
SELECTION = STAGE / "P0b_cases_and_protocol_v1.json"
RESULT = STAGE / "P0b_results_v1.json"
FOLD = "cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90"
MANIFEST = "f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758"
CHECKPOINT = "e2c459cb59ec7c198df4daec9e80978c04bec45dad88ef53592e00d012ebd41b"
PILOT = "108619195c5a6cc472e78184f87c988feb66fcf1c8ce3957745e2d28235eace2"
EXTENSION = "e34a752219f8f2db74980b095854fba5fdb65bc127dd969975f137c9cb2452a8"
STATE = "600a3309b568d345e3fd95c86eae9f8a06a933e1ff90fe432d3dfcaa275fd706"
TYPES = ("bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2")
SALT = "RBSS-P0-v2|2026112705|"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def bound(path, expected):
    data = path.read_bytes()
    need(digest(data) == expected, f"SHA256 mismatch: {path}")
    return data


def local_source_hashes():
    return {name: digest((STAGE / name).read_bytes()) for name in
            ("rbss_geometry_v1.py", "run_p0b_v1.py", "test_rbss_geometry_v1.py")}


def write_once(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def freeze_scope():
    need((np.__version__, scipy.__version__) == ("1.26.3", "1.11.4"), "frozen local versions")
    fold = json.loads(bound(PAYLOAD / "fold_binding.json", FOLD))["folds"]["D"]
    manifest = {row["case_id"]: row for row in
                map(json.loads, bound(PAYLOAD / "manifest_8192.jsonl", MANIFEST).splitlines())}
    need(digest(PLAN.read_bytes()) == "96ea381c31f4f29f872d6b7e29ef0b8d95b60f579b335fe7ac522ef33fa35036", "RBSS v2 plan")
    allowed = set(fold["train_case_ids"])
    need(len(allowed) == 315 and not allowed & set(fold["dev_case_ids"]), "training-only IDs")
    sources = fold["train_sources"]
    need(len(sources) == len(set(sources)) == 63 and not set(sources) & set(fold["dev_sources"]), "training-only sources")
    selected = []
    for i, sid in enumerate(sorted(sources, key=lambda s: digest((SALT + s).encode("utf-8")))[:15]):
        defect = TYPES[i // 3]
        cid = f"train__{sid.split(':')[1]}__{defect}"
        need(cid in allowed and manifest[cid]["source_id"] == sid, cid)
        row = manifest[cid]
        selected.append(dict(case_id=cid, source_id=sid, defect_type=defect,
                             source_digest=digest((SALT + sid).encode("utf-8")),
                             point_path=row["point_path"], npz_sha256=row["sha256"],
                             normalization=row["normalization"]))
    write_once(SELECTION, dict(schema="RBSS-P0b-local-v1", plan_sha256=digest(PLAN.read_bytes()),
                               fold_sha256=FOLD, point_manifest_sha256=MANIFEST, sources=local_source_hashes(),
                               selection_salt=SALT, case_list=selected, pass_minimum=12, pass_each_type=2,
                               reference_checkpoint_sha256=CHECKPOINT, cisc_pilot_sha256=PILOT,
                               cisc_extension_receipt_sha256=EXTENSION, numpy=np.__version__,
                               scipy=scipy.__version__, precision="float64 physical geometry, FP32 frozen input and anchors",
                               threading="one thread for BLAS, KDTree and numerical kernels",
                               assignment="SciPy linear_sum_assignment; sorted native IDs; np.rint ties-to-even",
                               left_side="positive signed LPS LR is patient's left",
                               edge_length="Euclidean distance between the two original endpoints"))
    print(f"LOCKED {len(selected)} cases {digest(SELECTION.read_bytes())}")


def prefix_metadata(meta, count):
    need(meta["checkpoint_sha256"] == CHECKPOINT and meta["model_state_sha256"] == STATE, "capture model identity")
    need(meta["state_rng_unchanged"] is True, "capture state/RNG status")
    need(meta["calls"] == dict(prefix=count, coarse=0, dense=0, loss=0, backward=0, optimizer_steps=0),
         "historical capture call counts")


def capture_assets(wanted):
    prefix = CISC / "prefix_15.npz"
    pilot_data = bound(prefix, PILOT)
    need(sha_archive(prefix) == PILOT, "pilot backup")
    with np.load(io.BytesIO(pilot_data), allow_pickle=False) as pack:
        prefix_metadata(json.loads(pack["metadata"].item()), 15)
        pilot_ids = pack["case_ids"].tolist()
    extension = CISC / "p0b_capture_300_v1/capture_receipt.json"
    receipt = json.loads(bound(extension, EXTENSION))
    need(sha_archive(extension) == EXTENSION, "extension receipt backup")
    prefix_metadata(receipt["metadata"], 300)
    train = json.loads(bound(PAYLOAD / "fold_binding.json", FOLD))["folds"]["D"]["train_case_ids"]
    need(len(pilot_ids) == len(set(pilot_ids)) == 15 and set(pilot_ids) <= set(train), "pilot training IDs")
    need(receipt["case_ids"] == [cid for cid in train if cid not in pilot_ids], "extension training IDs")
    assets = {}

    def add(pack, ids_expected, sha):
        ids = pack["case_ids"].tolist()
        need(ids == ids_expected, "prefix case order")
        hashes, coords = pack["input_sha256"].tolist(), pack["S"]
        need(coords.dtype == np.float32 and coords.shape == (len(ids), 256, 3), "historical coordinates layout")
        for i, cid in enumerate(ids):
            if cid in wanted:
                need(cid not in assets and np.isfinite(coords[i]).all(), f"historical coordinates: {cid}")
                assets[cid] = (hashes[i], coords[i].copy(), sha)

    if wanted.intersection(pilot_ids):
        with np.load(io.BytesIO(pilot_data), allow_pickle=False) as pack:
            add(pack, pilot_ids, PILOT)
    offset = 0
    for i, shard in enumerate(receipt["shards"], 1):
        name, count = shard["name"], shard["count"]
        need(name == f"prefix_{i:02d}.npz" and count == 30, "frozen shard layout")
        ids = receipt["case_ids"][offset:offset + count]
        offset += count
        if wanted.intersection(ids):
            data = bound(extension.parent / name, shard["sha256"])
            need(len(data) == shard["bytes"], "shard size")
            with np.load(io.BytesIO(data), allow_pickle=False) as pack:
                add(pack, ids, shard["sha256"])
    need(offset == 300 and set(assets) == wanted, "selected historical prefix coverage")
    return assets


def sha_archive(path):
    return digest((ARCHIVE / "code_results" / path.relative_to(OUTPUTS.parent)).read_bytes())


def analyze():
    from threadpoolctl import threadpool_limits, threadpool_info

    need(not RESULT.exists(), "result path already exists")
    scope_bytes = SELECTION.read_bytes()
    scope = json.loads(scope_bytes)
    need(scope["sources"] == local_source_hashes(), "frozen execution code")
    need((np.__version__, scipy.__version__) == (scope["numpy"], scope["scipy"]), "numerical dependency versions")
    selected = scope["case_list"]
    assets = capture_assets({row["case_id"] for row in selected})
    records = []
    started = time.perf_counter()
    with threadpool_limits(limits=1):
        threads = threadpool_info()
        need(all(p["num_threads"] == 1 for p in threads), "thread limit")
        for row in selected:
            cid = row["case_id"]
            bound_npz = bound(POINTS / row["point_path"], row["npz_sha256"])
            with np.load(io.BytesIO(bound_npz), allow_pickle=False) as pack:
                x = pack["partial"]
            need(x.shape == (8192, 3) and x.dtype == np.float32 and np.isfinite(x).all(), f"ordered input: {cid}")
            ordered_sha, anchors, shard_sha = assets[cid]
            need(digest(x.tobytes()) == ordered_sha, f"input byte identity: {cid}")
            input_bytes = np.ascontiguousarray(x).tobytes()
            remaining = Counter(input_bytes[i:i+12] for i in range(0, len(input_bytes), 12))
            anchor_bytes = anchors.tobytes()
            need(not (Counter(anchor_bytes[i:i+12] for i in range(0, anchors.nbytes, 12)) - remaining),
                 f"exact FPS subset: {cid}")
            center = np.array(row["normalization"]["center"], dtype=np.float64)
            scale = float(row["normalization"]["scale"])
            need(np.isfinite(center).all() and np.isfinite(scale) and scale > 0, f"physical normalization: {cid}")
            plane = fit_plane(x.astype(np.float64) * scale + center)
            order = plan_orders(anchors, anchors.astype(np.float64) * scale + center, plane)
            records.append(dict(case_id=cid, type=row["defect_type"], input_sha256=ordered_sha,
                                anchor_sha256=digest(anchor_bytes), historical_shard_sha256=shard_sha,
                                plane=plane, serialization=order))
            print(cid, plane["plane_ok"], order["joint_active"], order["k"],
                  ",".join(plane["reasons"] + order["reasons"]), flush=True)
    counts = {typ: {"plane_ok": sum(r["type"] == typ and r["plane"]["plane_ok"] for r in records),
                    "joint_active": sum(r["type"] == typ and r["serialization"]["joint_active"] for r in records)}
              for typ in TYPES}
    active = sum(r["serialization"]["joint_active"] for r in records)
    passed = active >= scope["pass_minimum"] and min(v["joint_active"] for v in counts.values()) >= scope["pass_each_type"]
    status = "OFFLINE_GEOMETRY_PASS_RUNTIME_ANCHOR_CHECK_PENDING" if passed else "P0B_GEOMETRY_GATE_FAIL_STOP"
    write_once(RESULT, dict(status=status, scope_sha256=digest(scope_bytes), cases=len(records),
                            plane_ok=sum(r["plane"]["plane_ok"] for r in records), joint_active=active,
                            by_type=counts, geometry_gate_pass=passed, model_calls=0, optimizer_steps=0,
                            cross_condition_anchor_invariance="NOT_TESTED", seconds=time.perf_counter() - started,
                            threads=threads, records=records))
    print(status, active, counts, digest(RESULT.read_bytes()))


if __name__ == "__main__":
    actions = {"freeze": freeze_scope, "analyze": analyze}
    need(len(sys.argv) == 2 and sys.argv[1] in actions, "usage: freeze or analyze")
    actions[sys.argv[1]]()
