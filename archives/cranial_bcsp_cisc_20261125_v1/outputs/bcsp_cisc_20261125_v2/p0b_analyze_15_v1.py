"""Audit the exact pilot capture and compute the predeclared token gates."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np


def digest(data):
    return hashlib.sha256(data).hexdigest()


def weighted_moments(x, weight):
    alpha = weight / weight.sum()
    center = alpha @ x
    residual = x - center
    return center, (residual * alpha[:, None]).T @ residual


def main():
    stage = Path(__file__).resolve().parent
    evidence = stage / "p0b_replay_15_v1"
    replay = json.loads((evidence / "summary.json").read_text(encoding="utf-8"))
    upload = Path(sys.argv[1])
    assert digest(upload.read_bytes()) == sys.argv[2]
    assert len(replay["cases"]) == 15
    with np.load(upload, allow_pickle=False) as saved:
        meta = json.loads(saved["metadata"].item())
        assert meta["checkpoint_sha256"] == "e2c459cb59ec7c198df4daec9e80978c04bec45dad88ef53592e00d012ebd41b"
        assert meta["calls"] == dict(prefix=15, coarse=0, dense=0, loss=0, backward=0, optimizer_steps=0)
        assert meta["state_rng_unchanged"] is True
        assert saved["case_ids"].tolist() == [row["case_id"] for row in replay["cases"]]
        assert saved["input_sha256"].tolist() == [row["partial_array_sha256"] for row in replay["cases"]]
        s, f = saved["S"], saved["F"]
    assert s.shape == (15, 256, 3) and f.shape == (15, 256, 384)
    assert s.dtype == f.dtype == np.float32 and np.isfinite(s).all() and np.isfinite(f).all()
    root = stage.parent / "cranial_bcsp_geov1_20261024/real_data_qc_v1/points"
    cases = []
    for i, row in enumerate(replay["cases"]):
        cid = row["case_id"]
        cloud = root / f"{cid}_8192.npz"
        labels = evidence / f"{cid}_labels.npz"
        assert digest(cloud.read_bytes()) == row["point_file_sha256"]
        assert digest(labels.read_bytes()) == row["label_file_sha256"]
        with np.load(cloud, allow_pickle=False) as z:
            x = z["partial"]
        with np.load(labels, allow_pickle=False) as z:
            y = z["is_j"]
            assert np.array_equal(z["row_id"], np.arange(8192))
        assert digest(x.tobytes()) == row["partial_array_sha256"]
        assert y.dtype == np.bool_ and y.shape == (8192,) and y.sum() == row["j_points"]
        assigned = []
        for chunk in np.split(x, 8):
            delta = chunk[:, None, :] - s[i][None, :, :]
            distance_squared = np.sum(delta * delta, axis=2, dtype=np.float32)
            assigned.append(np.argmin(distance_squared, axis=1))
        v = np.concatenate(assigned)
        n = np.bincount(v, minlength=256)
        positives = np.bincount(v[y], minlength=256)
        w = n / len(y)
        t = positives / np.maximum(n, 1)
        p = np.mean(y)
        assert n.sum() == 8192 and positives.sum() == y.sum()
        assert abs(np.sum(w * t) - p) < 1e-12
        variance = np.sum(w * (t - p) ** 2)
        world = x.astype(np.float64)
        c0, cov0 = weighted_moments(world, np.ones(len(world)))
        c1, cov1 = weighted_moments(world, t[v])
        center_mm = np.linalg.norm(c1 - c0) * row["scale_mm"]
        covariance_diff = np.linalg.norm(cov1 - cov0) / max(np.linalg.norm(cov0), 1e-8)
        j_cells = np.count_nonzero(positives)
        label_gate = j_cells >= 3 and variance >= 1e-5
        spatial_gate = center_mm >= 2 or covariance_diff >= 0.10
        cases.append(dict(case_id=cid, source_id=row["source_id"], j_points=int(y.sum()),
                          j_cells=int(j_cells), empty_cells=int(np.count_nonzero(n == 0)),
                          mixed_cells=int(np.count_nonzero((positives > 0) & (positives < n))),
                          weighted_variance=float(variance), retained_fraction=float(variance / (p * (1 - p))),
                          center_diff_mm=float(center_mm), covariance_relative=float(covariance_diff),
                          label_gate=bool(label_gate), spatial_gate=bool(spatial_gate),
                          joint_pass=bool(label_gate and spatial_gate), n=n.tolist(), j_counts=positives.tolist()))
    passed = sum(r["joint_pass"] for r in cases)
    out = upload.with_name("token_gate_15_v1.json")
    with out.open("x", encoding="utf-8") as stream:
        json.dump(dict(status="PILOT_GATE_PASS" if passed >= 12 else "PILOT_GATE_FAIL",
                       passed=passed, minimum=12, count=15, capture_sha256=sys.argv[2],
                       capture=meta, cases=cases), stream, indent=2, allow_nan=False)
    print(out)
    print("PASS", passed, "OF", len(cases))


if __name__ == "__main__":
    main()
