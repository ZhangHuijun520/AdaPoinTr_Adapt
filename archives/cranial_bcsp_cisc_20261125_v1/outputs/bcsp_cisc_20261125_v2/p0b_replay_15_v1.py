"""Replay the fifteen predeclared Fold D training inputs with the frozen sampler."""
import gc
import importlib.util
import hashlib
import json
from pathlib import Path
import time


def load_source(path):
    spec = importlib.util.spec_from_file_location("cisc_frozen_geometry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def main():
    stage = Path(__file__).resolve().parent
    outputs = stage.parent
    geo = outputs / "cranial_bcsp_geov1_20261024"
    request_path = outputs / "bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json"
    request = json.loads(request_path.read_text(encoding="utf-8"))
    source = geo / "real_data_qc_v1.py"
    binding = geo / "consolidated_binding_v1/fold_binding.json"
    manifest = geo / "real_data_qc_v1/manifest_8192.jsonl"
    assert digest(source) == "6f487dca7457d56efa00b47caa468c148fdd24b51e6e461b5aa8437810cb5420"
    assert digest(binding) == request["fold"]["sha256"]
    assert digest(manifest) == request["point_manifest"]["sha256"]
    sampler = load_source(source)
    np = sampler.np
    ids = json.loads(binding.read_text(encoding="utf-8"))["folds"]["D"]["train_case_ids"]
    rows = {row["case_id"]: row for row in map(json.loads, manifest.read_text(encoding="utf-8").splitlines())}
    selected = []
    sources = set()
    for defect in ("bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"):
        ordered = sorted((cid for cid in ids if cid.endswith("__" + defect)),
                         key=lambda cid: hashlib.sha256(cid.encode("utf-8")).hexdigest())
        chosen = []
        for cid in ordered:
            row = rows[cid]
            if row["source_id"] in sources:
                continue
            sources.add(row["source_id"])
            chosen.append(row)
            if len(chosen) == 3:
                break
        assert len(chosen) == 3
        selected.extend(chosen)
    assert len(selected) == len(sources) == 15
    out = stage / "p0b_replay_15_v1"
    out.mkdir()
    write(out / "scope.json", {
        "case_ids": [row["case_id"] for row in selected], "fold": "D/train",
        "request_sha256": digest(request_path), "manifest_sha256": digest(manifest),
        "fold_sha256": digest(binding), "sampler_sha256": digest(source),
        "reader_sha256": digest(sampler.READER), "numpy": np.__version__,
    })
    started = time.monotonic()
    stats = []
    for row in selected:
        sampler.CASE_START = time.monotonic()
        case = row["case_id"]
        print("REPLAY", case, flush=True)
        cloud = manifest.parent / row["point_path"]
        assert digest(cloud) == row["sha256"]
        paths = {name: Path(rec["path"]) for name, rec in row["raw"].items()}
        for name, path in paths.items():
            assert digest(path) == row["raw"][name]["sha256"], (case, name)
        d, a, o = sampler.raw.read_mask(paths["defective"])
        sd = sampler.surface(d)
        points, face_ids, _, weights = sampler.sample(sd, a, o, 0, 16384)
        center, scale = sampler.frame(d, a, o)
        assert center.tolist() == row["normalization"]["center"] and scale == row["normalization"]["scale"]
        x = ((points - center) / scale).astype(np.float32)[:8192]
        with np.load(cloud, allow_pickle=False) as frozen:
            actual = frozen["partial"]
            assert actual.shape == (8192, 3) and actual.dtype == np.float32
            assert x.tobytes() == actual.tobytes(), (case, "ordered replay mismatch")
        g, ga, go = sampler.raw.read_mask(paths["implant"])
        c, ca, co = sampler.raw.read_mask(paths["complete"])
        assert d.shape == g.shape == c.shape
        assert np.array_equal(a, ga) and np.array_equal(a, ca)
        assert np.array_equal(o, go) and np.array_equal(o, co)
        assert not np.any(d & g) and np.array_equal(c, d | g)
        del c
        jd = sampler.contact(sd, g)
        sg = sampler.surface(g)
        jg = sampler.contact(sg, d)
        dk, ds = sampler.keys(sd, jd)
        gk, gs = sampler.keys(sg, jg)
        assert len(dk) and np.array_equal(dk, gk) and np.array_equal(ds, -gs)
        _, gw = sampler.face_geometry(sg, a, o)
        assert np.isclose(weights[jd].sum(), gw[jg].sum(), rtol=1e-12)
        face_ids = face_ids[:8192]
        labels = jd[face_ids]
        prior = json.loads((manifest.parent / "cases" / f"{case}.json").read_text(encoding="utf-8"))
        assert int(labels.sum()) == prior["arms"]["8192"]["J_sample_count"]
        label_file = out / f"{case}_labels.npz"
        with label_file.open("xb") as stream:
            np.savez_compressed(stream, row_id=np.arange(8192), face_id=face_ids, is_j=labels)
        record = {
            "case_id": case, "source_id": row["source_id"], "point_file_sha256": row["sha256"],
            "partial_array_sha256": hashlib.sha256(x.tobytes()).hexdigest(),
            "label_file_sha256": digest(label_file), "j_points": int(labels.sum()),
            "non_j_points": int((~labels).sum()), "paired_faces": len(dk),
            "j_area_mm2": float(weights[jd].sum()), "scale_mm": scale,
        }
        write(out / f"{case}.json", record)
        stats.append(record)
        print("VERIFIED", case, record["j_points"], flush=True)
        del d, g, sd, sg, dk, gk
        gc.collect()
    write(out / "summary.json", {
        "status": "ROW_REPLAY_PASS_TOKEN_GATE_PENDING", "cases": stats,
        "elapsed_seconds": time.monotonic() - started, "peak_rss_bytes": sampler.PEAK_RSS,
    })


if __name__ == "__main__":
    main()
