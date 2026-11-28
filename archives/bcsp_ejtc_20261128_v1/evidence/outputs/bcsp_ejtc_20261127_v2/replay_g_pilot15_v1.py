
"""BCSP-EJTC v2, fixed Fold D pilot. Reads original files and writes only the pilot directory."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "p0b_pilot15_v1"
GEO = ROOT / "outputs/cranial_bcsp_geov1_20261024"
SOURCE = GEO / "real_data_qc_v1.py"
MANIFEST = GEO / "real_data_qc_v1/manifest_8192.jsonl"
FOLD = GEO / "consolidated_binding_v1/fold_binding.json"
PLAN = ROOT / "outputs/BCSP-EJTC_自由表面与共享切壁感知尾部覆盖监督_正式实验计划_2026-11-27_v2.md"
READER = ROOT / "outputs/cranial_geometry_diagnostic_20261023/analyze_raw_pairs_v1.py"
CLASSES = ("bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2")
EXPECTED = {
    SOURCE: "6f487dca7457d56efa00b47caa468c148fdd24b51e6e461b5aa8437810cb5420",
    READER: "cc27ae2b43cadd0a5ea1b3e1dc928c8fe4a73d9a049d49916ef55e1323ad006a",
    MANIFEST: "f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758",
    FOLD: "cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90",
    PLAN: "c2598f0a069969672de5e69a3dcfc2c4267153da019a236e8234b198e0bf4e9b",
}


def verify(condition, message):
    if not condition:
        raise ValueError(message)


def sha(file):
    digest = hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(4194304), b""):
            digest.update(block)
    return digest.hexdigest()


def array_sha(arr):
    return hashlib.sha256(arr.tobytes(order="C")).hexdigest()


def read_json(file):
    return json.loads(file.read_text(encoding="utf-8"))


def save(file, document):
    with file.open("x", encoding="utf-8") as stream:
        json.dump(document, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def matched_rows():
    for path, expected in EXPECTED.items():
        verify(sha(path) == expected, f"frozen source identity drift: {path}")
    train = read_json(FOLD)["folds"]["D"]["train_case_ids"]
    verify(len(train) == len(set(train)) == 315, "Fold D train cardinality")
    train_set = set(train)
    rows = {}
    with MANIFEST.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["case_id"] in train_set:
                verify(row["case_id"] not in rows, "duplicate training case")
                rows[row["case_id"]] = row
    verify(set(rows) == train_set, "Fold D training manifest mismatch")
    used = set()
    selected = []
    for defect in CLASSES:
        group = []
        for case in sorted(cid for cid in train if cid.endswith("__" + defect)):
            row = rows[case]
            if row["source_id"] not in used:
                group.append(row)
                used.add(row["source_id"])
            if len(group) == 3:
                break
        verify(len(group) == 3, f"insufficient distinct sources in {defect}")
        selected.extend(group)
    return selected


def geometry(m, d, g, affine, origin):
    np = m.np
    sd, sg = m.surface(d), m.surface(g)
    jd, jg = m.contact(sd, g), m.contact(sg, d)
    keys_d, signs_d = m.keys(sd, jd)
    keys_g, signs_g = m.keys(sg, jg)
    verify(len(keys_g) > 0 and np.array_equal(keys_d, keys_g), "shared face key mismatch")
    verify(np.array_equal(signs_d, -signs_g), "shared face orientation mismatch")
    verify(len(np.unique(keys_g, axis=0)) == len(keys_g), "duplicate shared face key")
    _, wd = m.face_geometry(sd, affine, origin)
    _, wg = m.face_geometry(sg, affine, origin)
    verify(np.isclose(wd[jd].sum(), wg[jg].sum(), rtol=1e-12, atol=0), "shared face area mismatch")
    voxel, axis, sign = sg
    neighbor = voxel.copy()
    neighbor[np.arange(len(axis)), axis] += sign
    inside = np.all((neighbor >= 0) & (neighbor < np.asarray(g.shape)), axis=1)
    verify(not np.any(jg & ~inside) and not np.any(g[tuple(neighbor[inside].T)]),
           "G surface includes a foreground neighbor or an out-of-grid J face")
    verify(np.all(g[tuple(voxel.T)]) and np.all(wg > 0), "invalid G face")
    verify(np.array_equal(jg[inside], d[tuple(neighbor[inside].T)]), "J/E partition mismatch")
    return sg, jg, ~inside, wg, neighbor


def toys(m):
    np = m.np
    d = np.zeros((5, 5, 5), dtype=bool)
    g = np.zeros_like(d)
    g[0, 2, 2] = True
    d[1, 2, 2] = True
    affine = np.diag([2.0, 3.0, 4.0])
    origin = np.array([3.0, -2.0, 7.0])
    sg, jg, fov, wg, _ = geometry(m, d, g, affine, origin)
    centers, _ = m.face_geometry(sg, affine, origin)
    verify(len(wg) == 6 and jg.sum() == fov.sum() == 1, "single voxel face counts")
    verify(wg[jg].item() == 12.0 and wg.sum() == 52.0, "anisotropic area")
    verify(np.array_equal(centers[jg][0], [4.0, 4.0, 15.0]), "world face center")
    verify(not jg[fov].any(), "FOV face labeled J")
    g[3, 3, 3] = True
    _, jg, fov, wg, _ = geometry(m, d, g, affine, origin)
    verify(len(wg) == 12 and jg.sum() == fov.sum() == 1, "disconnected G labels")
    g[0, 2, 3] = True
    _, jg, fov, wg, _ = geometry(m, d, g, affine, origin)
    verify(len(wg) == 16 and jg.sum() == 1 and fov.sum() == 2, "adjacent G faces must be excluded")
    return ["anisotropic shared and FOV face", "disconnected G", "adjacent G internal face exclusion"]


def replay(m, row, rng):
    np = m.np
    start = time.monotonic()
    case = row["case_id"]
    cloud = MANIFEST.parent / row["point_path"]
    verify(sha(cloud) == row["sha256"], f"{case}: frozen NPZ file hash")
    raw = {key: Path(value["path"]) for key, value in row["raw"].items()}
    for name, path in raw.items():
        verify(sha(path) == row["raw"][name]["sha256"], f"{case}: {name} raw hash")
    d, affine, origin = m.raw.read_mask(raw["defective"])
    g, ag, og = m.raw.read_mask(raw["implant"])
    c, ac, oc = m.raw.read_mask(raw["complete"])
    verify(d.shape == g.shape == c.shape and np.array_equal(affine, ag)
           and np.array_equal(affine, ac) and np.array_equal(origin, og)
           and np.array_equal(origin, oc), f"{case}: physical grid mismatch")
    verify(not np.any(d & g) and np.array_equal(c, d | g), f"{case}: occupancy partition mismatch")
    del c
    norm = row["normalization"]
    center = np.asarray(norm["center"], dtype=np.float64)
    scale = float(norm["scale"])
    recalculated_center, recalculated_scale = m.frame(d, affine, origin)
    sg, jg, fov, wg, neighbor = geometry(m, d, g, affine, origin)
    world, face_ids, _, sample_weights = m.sample(sg, affine, origin, 0, 8192)
    verify(np.array_equal(wg, sample_weights) and np.isfinite(world).all(), f"{case}: sampling geometry")
    xyz = ((world - center) / scale).astype(np.float32)
    with np.load(cloud, allow_pickle=False) as payload:
        target = payload["implant"]
    verify(target.dtype == np.float32 and target.shape == (8192, 3)
           and array_sha(target) == row["target_array_sha256"], f"{case}: target identity")
    recomputed = ((world - recalculated_center) / recalculated_scale).astype(np.float32)
    recalc_row_byte_diffs = int(np.count_nonzero(np.any(
        recomputed.view(np.uint32) != target.view(np.uint32), axis=1)))
    if xyz.tobytes() != target.tobytes():
        save(OUT / f"{case}_mismatch.json", {
            "replay_sha256": array_sha(xyz), "target_sha256": array_sha(target),
            "frozen_frame_mismatched_rows": int(np.count_nonzero(np.any(
                xyz.view(np.uint32) != target.view(np.uint32), axis=1))),
            "recalculated_frame_mismatched_rows": recalc_row_byte_diffs,
            "maximum_abs_mm": float(np.max(np.abs(xyz.astype(float) - target) * scale)),
        })
        raise ValueError(f"{case}: frozen-frame ordered G target byte mismatch")
    labels = jg[face_ids].astype(np.uint8)
    keys = np.column_stack((sg[0][face_ids], sg[1][face_ids], sg[2][face_ids])).astype("<i4")
    fov_rows = fov[face_ids]
    n_j = int(labels.sum())
    n_e = 8192 - n_j
    verify(min(n_j, n_e) >= 32, f"{case}: insufficient region samples")
    historical = read_json(MANIFEST.parent / "cases" / f"{case}.json")
    verify((n_j, n_e) == (historical["G_J_sample_count"], historical["G_native_sample_count"]),
           f"{case}: historical G region count differs")
    checked = []
    for label in (0, 1):
        candidates = np.flatnonzero(labels == label)
        for index in np.sort(rng.choice(candidates, size=8, replace=False)):
            i, j, k, axis, sign = (int(v) for v in keys[index])
            q = [i, j, k]
            q[axis] += sign
            inside = all(0 <= coord < bound for coord, bound in zip(q, g.shape))
            opposite_d = bool(d[tuple(q)]) if inside else False
            opposite_g = bool(g[tuple(q)]) if inside else False
            verify(g[i, j, k] and not opposite_g and opposite_d == bool(label)
                   and (not inside) == bool(fov_rows[index])
                   and np.array_equal(q, neighbor[face_ids[index]]), f"{case}: row-level face spot check")
            checked.append({"row": int(index), "face_key": keys[index].tolist(),
                            "is_j": bool(label), "opposite_inside": inside, "opposite_d": opposite_d})
    label_path = OUT / f"{case}_labels.npz"
    with label_path.open("xb") as stream:
        np.savez_compressed(stream, labels_G=labels, face_index=face_ids.astype("<i8"),
                            face_key=keys, is_fov=fov_rows)
    area_e, area_j = float(wg[~jg].sum()), float(wg[jg].sum())
    a_j = area_j / (area_e + area_j)
    record = {
        "case_id":case, "source_id":row["source_id"], "split":"D/train",
        "source_point_sha256":row["sha256"], "raw":row["raw"],
        "target_ordered_fp32_sha256":array_sha(xyz), "ordered_target_byte_match":True,
        "face_index_sha256":array_sha(face_ids.astype("<i8")), "face_key_sha256":array_sha(keys),
        "labels_sha256":array_sha(labels), "sidecar":label_path.name,
        "sidecar_sha256":sha(label_path), "affine_sha256":array_sha(np.column_stack((affine,origin))),
        "normalization":norm, "normalization_sha256":hashlib.sha256(
            json.dumps(norm,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
        "sampler_sha256":EXPECTED[SOURCE], "rng_manifest_sha256":sha(OUT/"pilot_scope.json"),
        "n_E":n_e, "n_J":n_j, "k_E":(n_e + 9)//10, "k_J":(n_j + 9)//10,
        "E_area_mm2":area_e, "J_area_mm2":area_j, "J_area_fraction":a_j,
        "J_sample_fraction":n_j/8192, "J_sample_minus_area_pp":100*(n_j/8192-a_j),
        "FOV_sample_count":int(fov_rows.sum()), "FOV_area_mm2":float(wg[fov].sum()),
        "unique_sampled_faces":int(np.unique(face_ids).size),
        "duplicate_target_rows":8192-int(np.unique(xyz,axis=0).shape[0]),
        "recomputed_center_max_abs_mm":float(np.max(np.abs(center-recalculated_center))),
        "recomputed_scale_delta_mm":recalculated_scale-scale,
        "recomputed_frame_mismatched_rows":recalc_row_byte_diffs,
        "world_roundtrip_max_mm":float(np.linalg.norm(xyz.astype(float)*scale+center-world,axis=1).max()),
        "spot_checks":checked, "seconds":time.monotonic()-start,
    }
    save(OUT / f"{case}.json", record)
    return record


def main():
    selected = matched_rows()
    scope = {
        "fold":"D", "split":"train", "case_ids":[row["case_id"] for row in selected],
        "source_ids":[row["source_id"] for row in selected],
        "selection":"ordered defect types, lexical case IDs, first three unmatched sources each",
        "sampler":{"rng":"numpy.default_rng/PCG64", "seed":0, "rows":8192,
                   "draws":"weighted face choice followed by all 8192x2 face offsets"},
        "spot_checks":{"rng":"PCG64","seed":2026112811,"rows_per_region":8,"region_order":["E","J"]},
        "input_sha256":{str(path.relative_to(ROOT)):digest for path,digest in EXPECTED.items()},
        "pilot_code_sha256":sha(Path(__file__)),
    }
    if sys.argv[1:] == ["freeze"]:
        OUT.mkdir(exist_ok=False)
        save(OUT / "pilot_scope.json", scope)
        print("FROZEN", sha(OUT / "pilot_scope.json"), flush=True)
        return
    verify(sys.argv[1:] == ["run"] and read_json(OUT/"pilot_scope.json") == scope, "pilot scope drift")
    verify(list(OUT.iterdir()) == [OUT/"pilot_scope.json"], "existing pilot result")
    spec = importlib.util.spec_from_file_location("ejtc_frozen_sampler", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    np = module.np
    rng = np.random.Generator(np.random.PCG64(2026112811))
    records = []
    started = time.monotonic()
    case = None
    try:
        toy_checks = toys(module)
        for row in selected:
            case = row["case_id"]
            module.CASE_START = time.monotonic()
            rec = replay(module, row, rng)
            records.append(rec)
            print("PASS", case, rec["n_E"], rec["n_J"], rec["recomputed_frame_mismatched_rows"], flush=True)
    except Exception as exc:
        save(OUT/"pilot_result.json", {"status":"P0_HOLD_LABELS","completed":len(records),
                                      "failed_case":case,"error":repr(exc)})
        raise
    stats = {}
    for field in ("n_E","n_J","k_E","k_J","E_area_mm2","J_area_mm2","J_area_fraction",
                  "J_sample_fraction","J_sample_minus_area_pp","FOV_sample_count","FOV_area_mm2",
                  "duplicate_target_rows","unique_sampled_faces","world_roundtrip_max_mm"):
        stats[field] = np.percentile([r[field] for r in records],[0,5,50,95,100]).tolist()
    save(OUT/"pilot_result.json", {
        "status":"P0B_PILOT15_PASS","scope_sha256":sha(OUT/"pilot_scope.json"),
        "completed":len(records),"distinct_sources":len(set(scope["source_ids"])),
        "rows_matched":8192*len(records),"spot_checks":sum(len(r["spot_checks"]) for r in records),
        "toy_checks":toy_checks,"numpy":np.__version__, "raw_files_sha256_matched":len(records)*3,
        "percentile_order":[0,5,50,95,100],"statistics":stats,
        "recomputed_frame_mismatched_rows":sum(r["recomputed_frame_mismatched_rows"] for r in records),
        "records":[{"case_id":r["case_id"], "sidecar_sha256":r["sidecar_sha256"],
                    "record_sha256":sha(OUT/f"{r['case_id']}.json")} for r in records],
        "elapsed_seconds":time.monotonic()-started,
        "other_training_cases_processed":0,"forward":0,"optimizer_steps":0,
    })


if __name__ == "__main__":
    main()
