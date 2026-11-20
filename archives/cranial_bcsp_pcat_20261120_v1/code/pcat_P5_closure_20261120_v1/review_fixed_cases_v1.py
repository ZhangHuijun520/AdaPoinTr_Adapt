import csv
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

import matplotlib
import numpy as np
from scipy.spatial import cKDTree

matplotlib.use("Agg")
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator


HERE = Path(__file__).resolve().parent
OUT = HERE.parent
SUMMARY = OUT / "pcat_P5_paired_summary_20261119_v1/paired_summary_v1.json"
SUMMARY_SHA = "fd00c6e70f28ba065ed52e3073350754b8dac5efa18e61bb59136d8d49016f16"
REQUEST_SHA = {
    "C": "c4e54f945d846c53ad54aed5c1cf6f76c21cc5b94978896e65ba6e5c3f3e76ed",
    "D": "dc0a038f84e412c791ecd4bdceeeeebfe7adfb589c513ec0ce5535273a1edd48",
}
PRESSURE = "coarse_not_worse__dense_worse"
ARMS = ("G1", "G2")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(record):
    path = Path(record["path"])
    data = path.read_bytes()
    assert len(data) == record.get("bytes", len(data)) and sha(data) == record["sha256"], path
    return data


def file_record(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": sha(data)}


def read_npz(raw):
    with np.load(io.BytesIO(raw), allow_pickle=False) as arrays:
        return {name: arrays[name] for name in arrays.files}


def close(value, frozen, tolerance=1e-12):
    assert abs(value - frozen) <= tolerance, (value, frozen)


def rank_cases(case_rows, historical):
    selected = {}
    for fold in ("C", "D"):
        rows = [row for row in case_rows if row["fold"] == fold]
        assert len(rows) == 105
        def order(row):
            case = row["case_id"]
            return -float(historical[fold, case]["E_dense_P95_mm"]), case

        pressure = [row for row in rows if row["quadrant"] == PRESSURE]
        severe = [row for row in rows if row["severity_transition"] == "new_severe"]
        choices = [
            *[(row, f"pressure_rank_{i}") for i, row in enumerate(sorted(pressure, key=order)[:2], 1)],
            (min(severe, key=order), "largest_new_severe"),
            (min((row for row in rows if row["quadrant"] != PRESSURE),
                 key=lambda row: row["case_id"]), "first_non_pressure"),
        ]
        for row, reason in choices:
            key = (fold, row["case_id"])
            selected.setdefault(key, {"reasons": [], "pair": row})["reasons"].append(reason)
    return selected


def read_prediction(tar, record):
    member = tar.getmember(record["member"])
    assert member.isfile() and member.size == record["bytes"]
    raw = tar.extractfile(member).read()
    assert sha(raw) == record["sha256"], record["member"]
    data = read_npz(raw)
    assert data["coarse"].shape == (256, 3) and data["prediction"].shape == (8192, 3)
    return data


def metrics_and_masks(reference, data, old, normalization, parent_id, metric, reverse_tree):
    xyz, weights, is_j = (reference[key] for key in ("a_centers", "a_weights", "a_is_j"))
    q, p = (metric.world_points(data[key], normalization) for key in ("coarse", "prediction"))
    distances = [metric.nearest(xyz, cloud) for cloud in (q, p)]
    q_cover, p_cover = [values <= 2 for values in distances]
    q_far, p_far = [reverse_tree.query(cloud)[0] > 20 for cloud in (q, p)]
    transition = {}
    for a in (False, True):
        for b in (False, True):
            key = f"parent_{a}_child_{b}"
            transition[key] = int(np.sum((q_far[parent_id] == a) & (p_far == b)))
            close(transition[key] / 8192, old["far_transition"][key])

    def area_fraction(mask, region):
        return float(weights[region & mask].sum() / weights[region].sum())

    regions = {}
    for label, region in (("E", ~is_j), ("J", is_j)):
        regions[label] = {}
        for stage, distance in zip(("coarse", "dense"), distances):
            cover = area_fraction(distance <= 2, region)
            p95 = metric.weighted_quantile(distance[region], weights[region])
            close(cover, old[stage]["regions"]["A1"][label]["coverage"]["2.0"])
            close(p95, old[stage]["regions"]["A1"][label]["p95_mm"], 1e-9)
            regions[label][f"{stage}_cover2"] = cover
            regions[label][f"{stage}_p95_mm"] = float(p95)
        for key, mask in (("retained", q_cover & p_cover), ("recovered", ~q_cover & p_cover),
                          ("lost", q_cover & ~p_cover), ("missed", ~q_cover & ~p_cover)):
            regions[label][key] = area_fraction(mask, region)
        close(regions[label]["recovered"], old["regions"][label]["gain"])
        close(regions[label]["lost"], old["regions"][label]["loss"])
    assert old["risk"]["severe_geometry"] == (
        regions["E"]["dense_p95_mm"] > 20 or regions["J"]["dense_cover2"] == 0
    )
    return {
        "coarse": q, "dense": p, "q_cover": q_cover, "p_cover": p_cover, "q_far": q_far,
        "p_far": p_far, "parent_far_at_child": q_far[parent_id],
        "metrics": {"regions": regions, "far_transition_counts": transition,
                    "far_parents": int(q_far.sum()), "far_children": int(p_far.sum()),
                    "severe": old["risk"]["severe_geometry"]},
    }


def draw_points(ax, xyz, axes, **kwargs):
    ax.scatter(xyz[:, axes[0]], xyz[:, axes[1]], linewidths=0, rasterized=True, **kwargs)


def plot_case(path, fold, case_id, reasons, xyz, is_j, clouds):
    fig, grid = plt.subplots(4, 2, figsize=(12.0, 13.7), layout="constrained")
    fig.suptitle(f"Fold {fold}  /  {case_id}   |   {', '.join(reasons)}", fontsize=16)
    full = np.concatenate([xyz, *(cloud[key] for cloud in clouds.values() for key in ("coarse", "dense"))])
    local_center = (xyz.min(0) + xyz.max(0)) / 2
    local_span = np.ptp(xyz, axis=0) + 8
    local_axes = tuple(sorted(np.argsort(local_span)[-2:]))
    axes_names = "XYZ"
    support_colors = ["#d1d5db", "#2563a8", "#e78a22", "#ab3155"]
    support_names = ["Retained", "Recovered", "Lost", "Missed at both stages"]
    stride = max(1, len(xyz) // 45000)
    for col, arm in enumerate(ARMS):
        cloud = clouds[arm]
        q, p = cloud["coarse"], cloud["dense"]
        q_far, p_far, parent_far = cloud["q_far"], cloud["p_far"], cloud["parent_far_at_child"]
        for row, axes in enumerate(((0, 1), (0, 2), local_axes, local_axes)):
            ax = grid[row, col]
            ax.xaxis.set_major_locator(MaxNLocator(5))
            ax.yaxis.set_major_locator(MaxNLocator(5))
            ax.tick_params(labelsize=8)
            ax.set(xlabel=f"{axes_names[axes[0]]} (mm)", ylabel=f"{axes_names[axes[1]]} (mm)")
            ax.set_aspect("equal", adjustable="box")
            if row < 2:
                draw_points(ax, xyz[::stride], axes, s=1.5, c="#a8adb3", alpha=.32)
                draw_points(ax, p[~p_far], axes, s=1.1, c="#286e87", alpha=.55)
                draw_points(ax, p[p_far & parent_far], axes, s=4, c="#b53040", alpha=.7)
                draw_points(ax, p[p_far & ~parent_far], axes, s=5, c="#ab7512", alpha=.85)
                ax.scatter(q[:, axes[0]], q[:, axes[1]], s=13, facecolors="none",
                           edgecolors="#242833", linewidths=.5)
                for axis, setter in zip(axes, (ax.set_xlim, ax.set_ylim)):
                    lo, hi = full[:, axis].min(), full[:, axis].max()
                    setter(lo - .035 * (hi - lo), hi + .035 * (hi - lo))
                ax.set_title(f"{arm}  |  full view  |  far children {p_far.sum()}/8192")
                continue
            region = ~is_j if row == 2 else is_j
            tag = "E" if row == 2 else "J"
            masks = [cloud["q_cover"] & cloud["p_cover"], ~cloud["q_cover"] & cloud["p_cover"],
                     cloud["q_cover"] & ~cloud["p_cover"], ~cloud["q_cover"] & ~cloud["p_cover"]]
            for mask, color in zip(masks, support_colors):
                draw_points(ax, xyz[region & mask], axes, s=3, c=color, alpha=.8)
            for axis, setter in zip(axes, (ax.set_xlim, ax.set_ylim)):
                setter(local_center[axis] - local_span[axis] / 2,
                       local_center[axis] + local_span[axis] / 2)
            m = cloud["metrics"]["regions"][tag]
            ax.set_title(f"{arm}  |  {tag} reference support  |  Cover@2 "
                         f"{100*m['coarse_cover2']:.1f}% → {100*m['dense_cover2']:.1f}%")
    background = [("#a8adb3", "Reference"), ("#286e87", "Dense ≤20 mm"),
                  ("#b53040", "Far child, far parent"), ("#ab7512", "Far child, near parent")]
    handles = [Line2D([], [], marker="o", linestyle="none", color=color, label=label)
               for color, label in (*background, *zip(support_colors, support_names))]
    handles.insert(1, Line2D([], [], marker="o", linestyle="none", markerfacecolor="none",
                             color="#242833", label="Coarse parent"))
    grid[3, 0].legend(handles=handles, ncol=3, fontsize=8, frameon=False,
                      loc="upper center", bbox_to_anchor=(1.04, -.29))
    with path.open("xb") as file:
        fig.savefig(file, format="png", dpi=155)
    plt.close(fig)


def main():
    summary = json.loads(checked({"path": SUMMARY, "sha256": SUMMARY_SHA}))
    assert summary["status"] == "NO_STABLE_ALLOCATION_SIGNAL"
    table = list(csv.DictReader(io.StringIO(checked(summary["artifacts"]["case_pairs_v1.csv"]).decode())))
    historical = {(r["fold"], r["case_id"]): r for r in csv.DictReader(
        io.StringIO(checked(summary["historical_pairs"]).decode("utf-8-sig")))}
    assert len(table) == len(historical) == 210
    choices = rank_cases(table, historical)
    requests = {}
    for fold, digest in REQUEST_SHA.items():
        request = OUT / f"pcat_P4_full_{fold}_20261119_v1/PCAT_full_{fold}_execution_request_v1.json"
        requests[fold] = json.loads(checked({"path": request, "sha256": digest}))
    first = requests["C"]
    assert all(first[key] == requests["D"][key] for key in ("archive", "parent_map", "metric"))
    metric = type("Metric", (), {})()
    namespace = {"__name__": "pcat_frozen_metric"}
    exec(compile(checked(first["metric"]), first["metric"]["path"], "exec"), namespace)
    for name in ("world_points", "a2_reference", "nearest", "weighted_quantile"):
        setattr(metric, name, namespace[name])
    parent_id = np.asarray(json.loads(checked(first["parent_map"])))
    assert np.array_equal(parent_id, np.arange(8192) // 32)
    indices = {}
    for fold, item in summary["folds"].items():
        paths = item["inputs"]
        manifest = json.loads(checked(paths["manifest"]))
        saved = [json.loads(line) for line in checked(paths["cases"]).splitlines()]
        assert [r["case_id"] for r in saved] == [r["case_id"] for r in manifest["cases"]]
        indices.update({(fold, case["case_id"]): (case, row["results"])
                        for case, row in zip(manifest["cases"], saved)})
    records, masks = [], {}
    with gzip.GzipFile(fileobj=io.BytesIO(checked(first["archive"]))) as stream:
        tar_data = stream.read(128 * 1024**2 + 1)
    assert len(tar_data) <= 128 * 1024**2
    with tarfile.open(fileobj=io.BytesIO(tar_data), mode="r:") as tar:
        for (fold, case_id), selected in choices.items():
            case, frozen = indices[fold, case_id]
            ref = read_npz(checked(case["reference"]))
            xyz, is_j = ref["a_centers"], ref["a_is_j"]
            reverse_tree = cKDTree(metric.a2_reference(ref)[0])
            clouds = {}
            for arm in ARMS:
                data = read_prediction(tar, case["predictions"][arm])
                old = {**frozen[arm], "regions": {r: frozen["regions"][r][arm] for r in ("E", "J")}}
                clouds[arm] = metrics_and_masks(ref, data, old, case["normalization"],
                                                parent_id, metric, reverse_tree)
                for field in ("q_cover", "p_cover", "q_far", "p_far"):
                    masks[f"{fold}__{case_id}__{arm}__{field}"] = np.packbits(clouds[arm][field])
            figure = HERE / f"{fold}__{case_id}.png"
            plot_case(figure, fold, case_id, selected["reasons"], xyz, is_j, clouds)
            print(f"verified and plotted {fold} {case_id}", flush=True)
            records.append({
                "fold": fold, "case_id": case_id, "source_id": case["source_id"],
                "selection": selected["reasons"], "historical_pair": {
                    "quadrant": selected["pair"]["quadrant"],
                    "severity_transition": selected["pair"]["severity_transition"],
                    "delta00_E": float(selected["pair"]["E_delta00"]),
                    "delta00_J": float(selected["pair"]["J_delta00"]),
                },
                "reference": case["reference"], "prediction_members": case["predictions"],
                "reference_mask_length": len(xyz), "figure": file_record(figure),
                "arms": {arm: cloud["metrics"] for arm, cloud in clouds.items()},
            })
    mask_path = HERE / "selected_masks_v1.npz"
    with mask_path.open("xb") as file:
        np.savez_compressed(file, **masks)
    receipt = {
        "status": "PCAT_FIXED_CASE_GEOMETRY_REVIEW_COMPLETE",
        "cases": len(records), "existing_predictions": 2 * len(records),
        "new_forward": 0, "new_training": 0, "new_checkpoint_load": 0,
        "summary_sha256": SUMMARY_SHA, "request_sha256_by_fold": REQUEST_SHA,
        "code": file_record(Path(__file__)), "masks": file_record(mask_path),
        "mask_format": "uint8 np.packbits, big bit order, truncate A1 masks to reference_mask_length; q_far length 256; p_far length 8192",
        "records": records,
    }
    with (HERE / "fixed_case_review_v1.json").open("x", encoding="utf-8") as file:
        json.dump(receipt, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")


if __name__ == "__main__":
    main()
