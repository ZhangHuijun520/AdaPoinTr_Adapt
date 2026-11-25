"""Complete missing P0b label replays while retaining verified first-attempt cases."""
import subprocess
import sys
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
    pilot_dir = stage / "p0b_replay_15_v1"
    pilot = json.loads((pilot_dir / "scope.json").read_text(encoding="utf-8"))
    pilot_ids = set(pilot["case_ids"])
    assert len(ids) == len(set(ids)) == 315 and len(pilot_ids) == 15 and pilot_ids <= set(ids)
    assert hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest() == json.loads(
        binding.read_text(encoding="utf-8"))["folds"]["D"]["train_allowlist_sha256"]
    selected = [rows[cid] for cid in ids if cid not in pilot_ids]
    assert len(selected) == 300
    out = stage / "p0b_replay_300_v1"
    assert out.is_dir() and not (out / "summary.json").exists()
    expected_scope = {
        "case_ids": [row["case_id"] for row in selected], "fold": "D/train",
        "request_sha256": digest(request_path), "manifest_sha256": digest(manifest),
        "fold_sha256": digest(binding), "sampler_sha256": digest(source),
        "reader_sha256": digest(sampler.READER), "numpy": np.__version__,
    }
    assert json.loads((out / "scope.json").read_text(encoding="utf-8")) == expected_scope
    started = time.monotonic()
    def replay(row):
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
        print("VERIFIED", case, record["j_points"], flush=True)
        return record

    verified = {}
    for row in selected:
        cid = row["case_id"]
        rec_path = out / f"{cid}.json"
        label_path = out / f"{cid}_labels.npz"
        assert rec_path.exists() == label_path.exists() or len(sys.argv) > 1, cid
        if rec_path.exists():
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            assert rec["case_id"] == cid and rec["point_file_sha256"] == row["sha256"]
            assert digest(label_path) == rec["label_file_sha256"]
            verified[cid] = rec
    missing = [row for row in selected if row["case_id"] not in verified]
    print("RETAINED", len(verified), "PENDING", len(missing), flush=True)
    if len(sys.argv) > 1:
        for cid in sys.argv[1:]:
            if cid not in verified:
                assert cid in {r["case_id"] for r in missing}, cid
                replay(rows[cid])
        return
    chunks = [[r["case_id"] for r in missing[start:start + 8]] for start in range(0, len(missing), 8)]
    for start in range(0, len(chunks), 2):
        batch = chunks[start:start + 2]
        procs = [subprocess.Popen([sys.executable, "-u", "-B", __file__, *chunk]) for chunk in batch]
        for child in procs:
            code = child.wait(timeout=270)
            if code not in (0, 3221225477, -1073741819):
                raise RuntimeError(f"label batch failed with {code}")
        for chunk in batch:
            for cid in chunk:
                rec = out / f"{cid}.json"
                if not rec.is_file():
                    assert not (out / f"{cid}_labels.npz").exists(), (cid, "partial result")
                    print("RETRY_AFTER_NATIVE_EXIT", cid, flush=True)
                    subprocess.run([sys.executable, "-u", "-B", __file__, cid], check=True, timeout=90)
                verified[cid] = json.loads(rec.read_text(encoding="utf-8"))
                assert verified[cid]["label_file_sha256"] == digest(out / f"{cid}_labels.npz")
    stats = [verified[row["case_id"]] for row in selected]
    assert len(stats) == 300
    write(out / "summary.json", {
        "status": "ROW_REPLAY_PASS_TOKEN_GATE_PENDING", "cases": stats,
        "elapsed_seconds": time.monotonic() - started, "peak_rss_bytes": sampler.PEAK_RSS,
    })


if __name__ == "__main__":
    main()
