"""Descriptive and bootstrap statistics for per-case evaluation metrics."""

import numpy as np


def describe_values(values, bootstrap_samples=2000, confidence=0.95, seed=0):
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {"count": 0}

    result = {
        "count": int(values.size),
        "mean": float(values.mean()),
        "std": float(values.std(ddof=1)) if values.size > 1 else 0.0,
        "median": float(np.median(values)),
        "q1": float(np.percentile(values, 25)),
        "q3": float(np.percentile(values, 75)),
        "min": float(values.min()),
        "max": float(values.max()),
    }

    if bootstrap_samples > 0:
        rng = np.random.RandomState(seed)
        indices = rng.randint(
            0,
            values.size,
            size=(int(bootstrap_samples), values.size),
        )
        means = values[indices].mean(axis=1)
        alpha = (1.0 - float(confidence)) / 2.0
        result["mean_ci"] = [
            float(np.quantile(means, alpha)),
            float(np.quantile(means, 1.0 - alpha)),
        ]
        result["confidence"] = float(confidence)
        result["bootstrap_samples"] = int(bootstrap_samples)
    return result


def describe_rows(
    rows,
    metric_keys,
    bootstrap_samples=2000,
    confidence=0.95,
    seed=0,
):
    return {
        key: describe_values(
            [row[key] for row in rows if key in row],
            bootstrap_samples=bootstrap_samples,
            confidence=confidence,
            seed=seed + index,
        )
        for index, key in enumerate(metric_keys)
    }


def paired_comparisons(
    rows,
    candidate_prefix="final",
    baseline_prefix="input",
    bootstrap_samples=2000,
    confidence=0.95,
    seed=10000,
):
    comparisons = {}
    candidate_tag = candidate_prefix + "_"
    for key in rows[0] if rows else ():
        if not key.startswith(candidate_tag):
            continue
        suffix = key[len(candidate_tag) :]
        baseline_key = f"{baseline_prefix}_{suffix}"
        if baseline_key not in rows[0]:
            continue

        candidate_values = np.asarray(
            [row[key] for row in rows], dtype=np.float64
        )
        baseline_values = np.asarray(
            [row[baseline_key] for row in rows], dtype=np.float64
        )
        if suffix == "rve":
            deltas = np.abs(candidate_values) - np.abs(baseline_values)
            delta_definition = (
                "abs(candidate)_minus_abs(baseline)"
            )
        else:
            deltas = candidate_values - baseline_values
            delta_definition = "candidate_minus_baseline"
        higher_is_better = (
            "nsd_at_" in suffix
            or "surface_dice_at_" in suffix
            or suffix == "dsc"
        )
        improved = deltas > 0 if higher_is_better else deltas < 0
        comparisons[suffix] = {
            "candidate": candidate_prefix,
            "baseline": baseline_prefix,
            "delta_definition": delta_definition,
            "higher_is_better": higher_is_better,
            "improved_cases": int(np.count_nonzero(improved)),
            "improvement_rate": float(np.mean(improved)),
            "delta": describe_values(
                deltas,
                bootstrap_samples=bootstrap_samples,
                confidence=confidence,
                seed=seed + len(comparisons),
            ),
        }
    return comparisons
