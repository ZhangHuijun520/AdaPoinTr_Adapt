"""Five source-grouped held-out readouts on the frozen OASG pilot and extension."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


ROOT = Path(__file__).resolve().parent
GEOMETRY = ROOT.parent / "cranial_bcsp_geov1_20261024"
WEIGHTS = "e2c459cb59ec7c198df4daec9e80978c04bec45dad88ef53592e00d012ebd41b"
PILOT = "108619195c5a6cc472e78184f87c988feb66fcf1c8ce3957745e2d28235eace2"
MODELS = ("constant", "geometry", "memory")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def ordered_hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_metadata(meta, count):
    assert meta["checkpoint_sha256"] == WEIGHTS and meta["state_rng_unchanged"]
    assert meta["calls"] == dict(prefix=count, coarse=0, dense=0, loss=0, backward=0, optimizer_steps=0)


def read_prefix(path, expected_hash, count):
    assert sha(path) == expected_hash, path
    with np.load(path, allow_pickle=False) as z:
        ids, xhash, s, f = (z[key] for key in ("case_ids", "input_sha256", "S", "F"))
        meta = json.loads(z["metadata"].item()) if "metadata" in z else None
    assert len(set(ids)) == len(xhash) == count and s.shape == (count, 256, 3) and f.shape == (count, 256, 384)
    assert s.dtype == f.dtype == np.float32 and np.isfinite(s).all() and np.isfinite(f).all()
    return {cid: (xhash[i], s[i], f[i]) for i, cid in enumerate(ids)}, meta


def case_features(prefix, rec, labels_path):
    cid = rec["case_id"]
    xhash, s, f = prefix
    point = GEOMETRY / "real_data_qc_v1/points" / f"{cid}_8192.npz"
    labels = labels_path / f"{cid}_labels.npz"
    assert sha(point) == rec["point_file_sha256"] and sha(labels) == rec["label_file_sha256"]
    with np.load(point, allow_pickle=False) as z:
        x = z["partial"]
    with np.load(labels, allow_pickle=False) as z:
        y = z["is_j"]
        assert np.array_equal(z["row_id"], np.arange(8192))
    assert x.shape == (8192, 3) and x.dtype == np.float32 and y.shape == (8192,) and y.dtype == np.bool_
    assert hashlib.sha256(x.tobytes()).hexdigest() == xhash == rec["partial_array_sha256"]
    assert y.sum() == rec["j_points"]
    assigned = []
    for chunk in np.split(x, 8):
        delta = chunk[:, None, :] - s[None, :, :]
        assigned.append(np.argmin(np.sum(delta * delta, axis=2, dtype=np.float32), axis=1))
    v = np.concatenate(assigned)
    n = np.bincount(v, minlength=256)
    j = np.bincount(v[y], minlength=256)
    assert n.sum() == 8192 and j.sum() == y.sum()
    delta = x.astype(np.float64) - s[v]
    columns = [np.bincount(v, weights=delta[:, d], minlength=256) for d in range(3)]
    columns.append(np.bincount(v, weights=np.sum(delta ** 2, axis=1), minlength=256))
    local = np.column_stack(columns) / np.maximum(n[:, None], 1)
    geometry = np.column_stack((s, np.log1p(n), local))
    return geometry, np.column_stack((geometry, f)), j / np.maximum(n, 1), n / 8192


def ridge(features, target, weight, test):
    active = weight > 0
    features, target, weight = features[active], target[active], weight[active]
    weight = weight / weight.sum()
    mean = weight @ features
    centered = features - mean
    scale = np.sqrt(weight @ (centered ** 2))
    valid = (np.ptp(features, axis=0) > 0) & (scale > 0)
    train_z = centered[:, valid] / scale[valid]
    test_z = (test[:, valid] - mean[valid]) / scale[valid]
    intercept = weight @ target
    design = train_z * np.sqrt(weight[:, None])
    covariance = design.T @ design
    covariance.flat[::covariance.shape[0] + 1] += 0.01
    coef = np.linalg.solve(covariance, train_z.T @ (weight * (target - intercept)))
    return np.clip(intercept + test_z @ coef, 0, 1)


def metrics(p, t, w):
    pi = float(w @ t)
    brier = float(w @ ((p - t) ** 2))
    if not 0 < pi < 1:
        return dict(pi=pi, ap=None, lift=None, brier=brier)
    use = w > 0
    p, t, w = p[use], t[use], w[use]
    order = np.argsort(-p, kind="stable")
    p, pos, mass = p[order], (w * t)[order], w[order]
    ends = np.r_[np.flatnonzero(p[:-1] != p[1:]), len(p) - 1]
    cumulative = np.cumsum(pos)[ends]
    precision = cumulative / np.cumsum(mass)[ends]
    ap = float(np.diff(np.r_[0, cumulative]) @ precision / pi)
    if len(ends) == 1:
        ap = pi
    return dict(pi=pi, ap=ap, lift=ap - pi, brier=brier)


def average(values):
    good = [x for x in values if x is not None]
    return float(np.mean(good)) if good else None


def main():
    capture_dir = Path(sys.argv[1])
    receipt = capture_dir / "capture_receipt.json"
    assert sha(receipt) == sys.argv[2]
    captured = read_json(receipt)
    check_metadata(captured["metadata"], 300)
    pilot, meta = read_prefix(ROOT / "prefix_15.npz", PILOT, 15)
    check_metadata(meta, 15)
    assert meta["model_state_sha256"] == captured["metadata"]["model_state_sha256"]
    extension = {}
    for index, item in enumerate(captured["shards"], 1):
        assert item["name"] == f"prefix_{index:02}.npz" and item["count"] == 30
        path = capture_dir / item["name"]
        assert path.stat().st_size == item["bytes"]
        shard, no_meta = read_prefix(path, item["sha256"], 30)
        assert no_meta is None and not set(shard) & set(extension)
        extension.update(shard)
    assert list(extension) == captured["case_ids"] and not set(pilot) & set(extension)
    pilot_dir = ROOT / "p0b_replay_15_v1"
    extension_dir = ROOT / "p0b_replay_300_v1"
    replays = {d: read_json(d / "summary.json")["cases"] for d in (pilot_dir, extension_dir)}
    assert [r["case_id"] for r in replays[pilot_dir]] == list(pilot)
    assert [r["case_id"] for r in replays[extension_dir]] == list(extension)
    prefix = pilot | extension
    binding = GEOMETRY / "consolidated_binding_v1/fold_binding.json"
    assert sha(binding) == "cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90"
    fold = read_json(binding)["folds"]["D"]
    ids = fold["train_case_ids"]
    assert len(prefix) == len(ids) == 315 and set(ids) == set(prefix)
    label_paths = {r["case_id"]: (d, r) for d, records in replays.items() for r in records}
    records = [label_paths[cid][1] for cid in ids]
    sources = np.asarray([r["source_id"] for r in records])
    ordered = sorted(set(sources), key=ordered_hash)
    assert len(ordered) == 63 and set(ordered) == set(fold["train_sources"])
    assert all(np.count_nonzero(sources == source) == 5 for source in ordered)
    pass_labels = [i for i, r in enumerate(records) if r["j_points"] >= 16 and r["non_j_points"] > 0]
    assert len(pass_labels) >= 284
    for defect in ("bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"):
        assert sum(ids[i].endswith("__" + defect) for i in pass_labels) >= 51
    partitions = {source: i % 5 for i, source in enumerate(ordered)}
    case_folds = np.asarray([partitions[source] for source in sources])
    observations = [case_features(prefix[cid], label_paths[cid][1], label_paths[cid][0]) for cid in ids]
    g, m, t, w = [np.stack(x) for x in zip(*observations)]
    preds = {key: np.full(t.shape, np.nan) for key in MODELS}
    for split in range(5):
        train = case_folds != split
        test = ~train
        weights, target = w[train].ravel(), t[train].ravel()
        preds["constant"][test] = weights @ target / weights.sum()
        for name, feature in (("geometry", g), ("memory", m)):
            dim = feature.shape[-1]
            score = ridge(feature[train].reshape(-1, dim), target, weights, feature[test].reshape(-1, dim))
            preds[name][test] = score.reshape(-1, 256)
        print("HELD_OUT", split, int(test.sum()), flush=True)
    assert all(np.isfinite(p).all() for p in preds.values())
    cases = [dict(case_id=cid, source_id=str(sources[i]), held_out_fold=int(case_folds[i]),
                  metrics={key: metrics(p[i], t[i], w[i]) for key, p in preds.items()})
             for i, cid in enumerate(ids)]
    result = {
        source: {key: {metric: average([row["metrics"][key][metric] for row in cases if row["source_id"] == source])
                       for metric in ("ap", "lift", "brier")} for key in MODELS}
        for source in ordered
    }
    summary = {key: {metric: average([row[key][metric] for row in result.values()])
                     for metric in ("ap", "lift", "brier")} for key in MODELS}
    for key in MODELS:
        summary[key]["strict_positive_sources"] = sum((r[key]["lift"] or 0) > 0 for r in result.values())
    deltas = {}
    for field in ("ap", "lift", "brier"):
        delta = [v["memory"][field] - v["geometry"][field]
                 for v in result.values() if v["memory"][field] is not None and v["geometry"][field] is not None]
        loo = [np.mean(delta[:i] + delta[i + 1:]) for i in range(len(delta))] if len(delta) > 1 else []
        deltas[field] = dict(mean=average(delta), leave_one_range=[float(min(loo)), float(max(loo))] if loo else None)
    n_ap = sum(r["metrics"]["memory"]["ap"] is not None for r in cases)
    gate = dict(ap_defined=n_ap >= 284, soft_ap_lift=summary["memory"]["lift"] >= 0.05,
                positive_sources=summary["memory"]["strict_positive_sources"] >= 42,
                beats_constant_brier=summary["memory"]["brier"] < summary["constant"]["brier"])
    output = dict(status="P0B_READOUT_PASS" if all(gate.values()) else "P0B_READOUT_FAIL",
                  gate=gate, ap_defined=n_ap, labels_gate_cases=len(pass_labels),
                  capture_receipt_sha256=sys.argv[2], pilot_sha256=PILOT, checkpoint_sha256=WEIGHTS,
                  partitions=partitions, summary=summary, memory_minus_geometry=deltas,
                  by_source=result, by_case=cases)
    path = ROOT / "p0b_probe_315_result_v1.json"
    with path.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
    print(json.dumps({key: output[key] for key in ("status", "gate", "ap_defined", "summary", "memory_minus_geometry")}))
    print("RESULT_SHA256", sha(path))


if __name__ == "__main__":
    main()
