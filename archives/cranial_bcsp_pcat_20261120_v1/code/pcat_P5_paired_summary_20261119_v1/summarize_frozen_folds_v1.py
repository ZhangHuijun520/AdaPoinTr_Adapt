import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUTPUTS = HERE.parent
PROTOCOL = ROOT / "docs/cranial_bcsp_pcat_20261119_v2/Cranial_BCSP_FullMamba_BCSP_PCAT_正式实验计划书_审阅修订v2_2026-11-19.md"
HISTORICAL = OUTPUTS / "coarse_dense_full_review_20261118_v1/paired_case_G2_minus_G1.csv"
KINDS = {"bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"}
SEEDS = {"C": 2026111901, "D": 2026111902}
MM_EPS = 1e-9
FRACTION_EPS = 1e-12


def require(condition, message):
    if not condition:
        raise ValueError(message)


def binding(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name, value):
    with (HERE / name).open("x", encoding="utf-8") as file:
        json.dump(value, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")


def write_csv(name, rows):
    with (HERE / name).open("x", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def paired_values(saved):
    result = saved["results"]
    values = {}
    for region in ("E", "J"):
        detail = result["regions"][region]
        for key in (
            "delta00", "delta_abs00", "delta_multi", "delta_shared_multi",
            "delta_shared_multi_conditional", "common_shared_area",
            "a2_s00_area", "a2_delta00", "a2_delta_abs00",
        ):
            values[f"{region}_{key}"] = detail[key]
        values[f"{region}_A1_s00_area"] = detail["G1"]["strata"]["S00"]["area"]
        for key in ("gain", "loss"):
            values[f"{region}_{key}"] = detail["G2"][key] - detail["G1"][key]
        for stage in ("coarse", "dense"):
            for surface in ("A1", "A2"):
                arm1, arm2 = [
                    result[arm][stage]["regions"][surface][region] for arm in ("G1", "G2")
                ]
                values[f"{region}_{stage}_{surface}_P95_mm"] = arm2["p95_mm"] - arm1["p95_mm"]
                for radius in ("0.5", "1.0", "2.0"):
                    values[f"{region}_{stage}_{surface}_cover_{radius}"] = (
                        arm2["coverage"][radius] - arm1["coverage"][radius]
                    )
    first, second = result["G1"], result["G2"]
    values["dense_CD_L1_mm"] = second["dense"]["CD_L1_mm"] - first["dense"]["CD_L1_mm"]
    for transition, value in first["far_transition"].items():
        values[transition] = second["far_transition"][transition] - value
    values["child_far_total"] = (
        values["parent_False_child_True"] + values["parent_True_child_True"]
    )
    reverse1, reverse2 = [arm["dense"]["reverse_discrete_reference"]["A2"] for arm in (first, second)]
    values["reverse_A2_P95_mm"] = reverse2["p95_mm"] - reverse1["p95_mm"]
    for radius in ("0.5", "1.0", "2.0"):
        values[f"reverse_A2_outlier_{radius}"] = (
            reverse2["outlier_fraction"][radius] - reverse1["outlier_fraction"][radius]
        )
    return values


def read_fold(fold, historical):
    folder = OUTPUTS / f"pcat_P4_full_{fold}_20261119_v1"
    directory = folder / ("fold_C_merged_v1" if fold == "C" else "fold_D_results_v1")
    cases_file = directory / "cases.jsonl"
    manifest_file = folder / f"fold_{fold}_input_manifest_v1.json"
    receipt_file = (directory / "merge_receipt_v1.json" if fold == "C"
                    else folder / "fold_D_formal_freeze_v1.json")
    receipt = read_json(receipt_file)
    paths = {name: binding(path) for name, path in (
        ("cases", cases_file), ("manifest", manifest_file), ("freeze", receipt_file)
    )}
    if fold == "C":
        require(receipt["status"] == "PCAT_FOLD_C_105_CASES_MERGED_AND_FROZEN", fold)
        expected = receipt["artifacts"]["cases.jsonl"]
        require(paths["manifest"]["sha256"] == receipt["bindings"]["original_manifest"]["sha256"], fold)
    else:
        require(receipt["status"] == "PCAT_FOLD_D_FORMAL_READ_ONLY_FREEZE_PASS", fold)
        expected = receipt["files"][str(cases_file.relative_to(folder))]
        request_path = folder / "PCAT_full_D_execution_request_v1.json"
        require(binding(request_path)["sha256"] == receipt["request_sha256"], fold)
        require(paths["manifest"]["sha256"] == read_json(request_path)["case_manifest"]["sha256"], fold)
    for key in ("bytes", "sha256"):
        require(paths["cases"][key] == expected[key], f"{fold} {key}")
    manifest = read_json(manifest_file)
    saved_rows = [json.loads(line) for line in cases_file.read_text(encoding="utf-8").splitlines()]
    expected_order = [case["case_id"] for case in manifest["cases"]]
    require([row["case_id"] for row in saved_rows] == expected_order, fold)
    require(len(set(expected_order)) == len(expected_order) == 105, fold)
    sources = defaultdict(set)
    rows = []
    for saved, case in zip(saved_rows, manifest["cases"]):
        case_id, source = case["case_id"], case["source_id"]
        kind = case_id.split("__")[-1]
        require(saved["fold"] == case["fold"] == manifest["fold"] == fold, case_id)
        sources[source].add(kind)
        values = paired_values(saved)
        old = historical[(fold, case_id)]
        require(old["source_id"] == source, case_id)
        for region in ("E", "J"):
            for stage in ("coarse", "dense"):
                name = f"{region}_{stage}"
                require(abs(values[f"{name}_A1_P95_mm"] - float(old[f"{name}_P95_mm"])) <= MM_EPS,
                        f"{case_id} {name}")
        coarse_bad = values["E_coarse_A1_P95_mm"] > MM_EPS
        dense_bad = values["E_dense_A1_P95_mm"] > MM_EPS
        risks = saved["results"]
        severe1, severe2 = [risks[arm]["risk"]["severe_geometry"] for arm in ("G1", "G2")]
        severity = {
            (False, True): "new_severe", (True, False): "rescued",
            (True, True): "shared_severe", (False, False): "neither_severe",
        }[(severe1, severe2)]
        require((severity == "new_severe") == (old["new_dense_severe"] == "True"), case_id)
        require((severity == "rescued") == (old["rescued_dense_severe"] == "True"), case_id)
        for risk in ("placement_tail", "compact_distribution", "severe_geometry"):
            for arm in ("G1", "G2"):
                values[f"{arm}_{risk}"] = int(risks[arm]["risk"][risk])
        rows.append({
            "fold": fold, "case_id": case_id, "source_id": source, "defect_type": kind,
            "quadrant": ("coarse_worse" if coarse_bad else "coarse_not_worse")
            + ("__dense_worse" if dense_bad else "__dense_not_worse"),
            "severity_transition": severity, **values,
        })
    require(len(sources) == 21 and all(kinds == KINDS for kinds in sources.values()), fold)
    return rows, paths


def summarize(fold, rows, metrics, cache, matrix_metadata):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["source_id"]].append(row)
    source_rows = [{"fold": fold, "source_id": source} for source in sorted(grouped)]
    report = {}
    for key in metrics:
        valid_count = 0
        kind_counts = Counter()
        values = []
        estimable = []
        for source_row in source_rows:
            source = source_row["source_id"]
            cases = [row for row in grouped[source] if row[key] is not None]
            valid_count += len(cases)
            kind_counts.update(row["defect_type"] for row in cases)
            value = math.fsum(row[key] for row in cases) / len(cases) if cases else None
            source_row[key] = value
            source_row[f"{key}__n"] = len(cases)
            if value is not None:
                values.append(value)
                estimable.append(source)
        if not values:
            report[key] = {"mean": None, "estimable_cases": 0, "estimable_sources": 0}
            continue
        source_array = np.asarray(values, dtype=np.float64)
        signature = (fold, tuple(estimable))
        if signature not in cache:
            name = f"{fold}_{len(cache):03d}"
            matrix = np.random.Generator(np.random.PCG64(SEEDS[fold])).integers(
                0, len(estimable), size=(2000, len(estimable)), dtype=np.int64
            )
            cache[signature] = (name, matrix)
            matrix_metadata[name] = {
                "fold": fold, "seed": SEEDS[fold], "source_order": estimable, "shape": list(matrix.shape),
                "int64_little_endian_sha256": hashlib.sha256(matrix.astype("<i8").tobytes()).hexdigest(),
            }
        name, matrix = cache[signature]
        eps = MM_EPS if key.endswith("_mm") else FRACTION_EPS
        positive = int(np.sum(source_array > eps))
        negative = int(np.sum(source_array < -eps))
        mean = float(source_array.mean())
        loo = (source_array.sum() - source_array) / (len(values) - 1) if len(values) > 1 else []
        report[key] = {
            "mean": mean, "median_source": float(np.median(source_array)),
            "ci95_percentile": np.quantile(source_array[matrix].mean(axis=1), [.025, .975]).tolist(),
            "estimable_cases": valid_count, "estimable_sources": len(values),
            "case_count_by_type": {kind: kind_counts[kind] for kind in sorted(KINDS)},
            "positive": positive, "negative": negative, "flat": len(values) - positive - negative,
            "na_sources": len(grouped) - len(values), "bootstrap_matrix": name,
            "leave_one_source_out_min_max": [float(min(loo)), float(max(loo))] if len(loo) else None,
        }
    return report, source_rows


def main():
    require(np.__version__ == "1.26.4", "unexpected NumPy")
    protocol = binding(PROTOCOL)
    require(protocol["sha256"] == "b395495afa3781965f697f1d783c9a9fa7d1289ffada2509c0cb8820ae7df5d5",
            "protocol changed")
    with HISTORICAL.open(encoding="utf-8-sig", newline="") as file:
        historical = {(row["fold"], row["case_id"]): row for row in csv.DictReader(file)}
    require(len(historical) == 210, "historical scope")
    pressure_key = "coarse_not_worse__dense_worse"
    comparisons = ("E_delta00", "E_delta_abs00", "E_delta_multi", "E_delta_shared_multi",
                   "J_delta00", "J_delta_abs00", "J_delta_multi", "J_delta_shared_multi",
                   "E_coarse_A1_P95_mm", "E_dense_A1_P95_mm", "parent_False_child_True",
                   "parent_True_child_True", "child_far_total", "reverse_A2_P95_mm")
    cache, metadata, folds, sources, cases, gate = {}, {}, {}, [], [], {}
    for fold in ("C", "D"):
        rows, paths = read_fold(fold, historical)
        metrics = list(rows[0])[6:]
        full, source_rows = summarize(fold, rows, metrics, cache, metadata)
        quadrants = Counter(row["quadrant"] for row in rows)
        severity = Counter(row["severity_transition"] for row in rows)
        require((quadrants[pressure_key], severity["new_severe"], severity["rescued"])
                == ({"C": (17, 9, 4), "D": (41, 7, 0)}[fold]), fold)
        groups = {}
        for field in ("quadrant", "severity_transition", "defect_type"):
            for name in sorted({row[field] for row in rows}):
                groups[f"{field}/{name}"] = [row for row in rows if row[field] == name]
        groups["pressure_complement"] = [row for row in rows if row["quadrant"] != pressure_key]
        stratified = {}
        for name, selected in groups.items():
            summary, _ = summarize(fold, selected, comparisons, cache, metadata)
            stratified[name] = {"cases": len(selected), "metrics": summary}
        folds[fold] = {
            "inputs": paths, "cases": len(rows), "sources": len(source_rows),
            "quadrant_counts": dict(quadrants), "severity_counts": dict(severity),
            "quadrant_by_severity": {
                name: dict(Counter(row["severity_transition"] for row in rows if row["quadrant"] == name))
                for name in sorted(quadrants)
            },
            "new_severe_coarse_worse": sum(row["severity_transition"] == "new_severe"
                                           and row["E_coarse_A1_P95_mm"] > MM_EPS for row in rows),
            "metrics": full, "descriptive_strata": stratified,
        }
        gate[fold] = {
            "conditional_sources_at_least_17": full["E_delta00"]["estimable_sources"] >= 17,
            "conditional_recovery_at_most_minus_3pp": full["E_delta00"]["mean"] <= -.03,
            "negative_recovery_sources_at_least_14": full["E_delta00"]["negative"] >= 14,
            "absolute_recovery_negative": full["E_delta_abs00"]["mean"] < -FRACTION_EPS,
            "multiparent_at_least_3pp": full["E_delta_multi"]["mean"] >= .03,
            "positive_multiparent_sources_at_least_14": full["E_delta_multi"]["positive"] >= 14,
            "shared_multiparent_positive": full["E_delta_shared_multi"]["mean"] > FRACTION_EPS,
        }
        sources.extend(source_rows)
        cases.extend(rows)
    require(not ({row["source_id"] for row in sources if row["fold"] == "C"}
                 & {row["source_id"] for row in sources if row["fold"] == "D"}), "fold overlap")
    recovery = all(all(result[key] for key in (
        "conditional_recovery_at_most_minus_3pp", "negative_recovery_sources_at_least_14",
        "absolute_recovery_negative",
    )) for result in gate.values())
    overlap = all(all(result[key] for key in (
        "multiparent_at_least_3pp", "positive_multiparent_sources_at_least_14",
        "shared_multiparent_positive",
    )) for result in gate.values())
    if not all(result["conditional_sources_at_least_17"] for result in gate.values()):
        status = "INSUFFICIENT_CONDITIONAL_SUPPORT"
    elif recovery and overlap:
        status = "ALLOCATION_PATTERN_SUPPORTED"
    elif recovery and not any(result["shared_multiparent_positive"] for result in gate.values()):
        status = "RECOVERY_DEFICIT_WITHOUT_OVERLAP_SUPPORT"
    elif overlap:
        status = "OVERLAP_WITHOUT_RECOVERY_DEFICIT"
    else:
        status = "NO_STABLE_ALLOCATION_SIGNAL"
    write_csv("case_pairs_v1.csv", cases)
    write_csv("source_pairs_v1.csv", sources)
    with (HERE / "bootstrap_indices_v1.npz").open("xb") as file:
        np.savez_compressed(file, **{name: matrix for name, matrix in cache.values()})
    write_json("paired_summary_v1.json", {
        "status": status, "gate_by_fold": gate, "folds": folds,
        "protocol": protocol, "historical_pairs": binding(HISTORICAL), "numpy": np.__version__,
        "bootstrap": {"algorithm": "PCG64", "replicates": 2000, "matrices": metadata},
        "new_geometry_queries": 0, "new_model_forward": 0, "new_training": 0,
        "artifacts": {name: binding(HERE / name) for name in (
            "case_pairs_v1.csv", "source_pairs_v1.csv", "bootstrap_indices_v1.npz",
            "summarize_frozen_folds_v1.py",
        )},
    })
    print(json.dumps({"status": status, "gate": gate}, indent=2))


if __name__ == "__main__":
    main()
