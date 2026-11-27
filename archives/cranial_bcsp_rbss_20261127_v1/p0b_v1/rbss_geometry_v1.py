"""CPU geometry for the frozen BCSP-RBSS v2 P0b protocol."""
from itertools import product
import math

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
from scipy.spatial import cKDTree, distance


N_ANCHORS = 256
COARSE = list(product((-8, 0, 8), (-8, 0, 8), (-16, -8, 0, 8, 16)))
FINE_OFFSETS = list(product((-4, 0, 4), repeat=3))


def normal_for(a, d):
    n = np.array([1.0, math.tan(math.radians(a)), math.tan(math.radians(d))])
    return n / np.linalg.norm(n)


def nearest(query, donors, ids):
    """Euclidean exact nearest neighbour with smallest donor ID at exact ties."""
    if len(donors) == 0:
        return np.full(len(query), np.inf), np.full(len(query), -1, dtype=np.int64)
    k = min(len(donors), 2)
    tree = cKDTree(donors)
    dd, ii = tree.query(query, k=list(range(1, k + 1)), eps=0, workers=1)
    winners = ii[:, 0].copy()
    if k == 2:
        for i in np.flatnonzero(dd[:, 0] == dd[:, 1]):
            shortlist = tree.query_ball_point(query[i], np.nextafter(dd[i, 0], np.inf), workers=1)
            delta = donors[shortlist] - query[i]
            squared = np.sum(delta * delta, axis=1)
            winners[i] = shortlist[np.lexsort((ids[shortlist], squared))[0]]
    distances = np.linalg.norm(donors[winners] - query, axis=1)
    return distances, ids[winners]


def evaluate_candidate(points, centered, abc, split_indices):
    a, d, b = abc
    n = normal_for(a, d)
    signed = centered @ n - b
    sides = [np.flatnonzero(signed < -2.0), np.flatnonzero(signed > 2.0)]
    distances = []
    used_ids = []
    # The two fixed row subsets share the exact same donor tree for each side.
    for sign_index, donor in enumerate(reversed(sides)):
        queries = []
        for indices in split_indices:
            is_side = signed[indices] < -2.0 if sign_index == 0 else signed[indices] > 2.0
            queries.append(indices[is_side])
        ids = np.concatenate(queries)
        reflected = points[ids] - 2 * signed[ids, None] * n
        gap, _ = nearest(reflected, points[donor], donor)
        cut = len(queries[0])
        distances.append((gap[:cut], gap[cut:]))
        used_ids.append(tuple(map(len, queries)))
    result = []
    for i in range(2):
        counts = [used_ids[side][i] for side in (0, 1)]
        record = dict(abc=abc, valid=min(counts) >= 128, counts=counts,
                      donors=list(map(len, sides)), cost_mm=None, overlap=None)
        if record["valid"]:
            arrays = [ds[i] for ds in distances]
            record["cost_mm"] = float(np.mean([np.minimum(ds, 10).mean() for ds in arrays]))
            record["overlap"] = [float(np.mean(ds <= 5)) for ds in arrays]
        result.append(record)
    return result


def best_candidate(records):
    valid = [r for r in records if r["valid"]]
    if not valid:
        return None
    minimum = min(r["cost_mm"] for r in valid)

    def tie_key(record):
        a, d, b = record["abc"]
        return abs(a) + abs(d), abs(b), a, d, b

    return min((r for r in valid if r["cost_mm"] - minimum <= 1e-9), key=tie_key)


def plane_gates(winners):
    reasons = []
    for label, row in zip(("A", "B"), winners):
        if row is None:
            reasons.append(f"{label}_NO_VALID_CANDIDATE")
            continue
        a, d, b = row["abc"]
        if abs(a) == 12 or abs(d) == 12 or abs(b) == 20:
            reasons.append(f"{label}_SEARCH_BOUNDARY")
        if min(row["overlap"]) < 0.45:
            reasons.append(f"{label}_LOW_OVERLAP")
        if row["cost_mm"] > 6:
            reasons.append(f"{label}_HIGH_COST")
    angle = offset = None
    if all(row is not None for row in winners):
        a, d, b = winners[0]["abc"]
        a_b, d_b, b_b = winners[1]["abc"]
        dot = float(normal_for(a, d) @ normal_for(a_b, d_b))
        angle = math.degrees(math.acos(min(1.0, max(-1.0, dot))))
        offset = abs(b - b_b)
        if angle > 6:
            reasons.append("AB_ANGLE")
        if offset > 5:
            reasons.append("AB_OFFSET")
    return dict(plane_ok=not reasons, reasons=reasons, angle_deg=angle, offset_mm=offset)


def fit_plane(points):
    if points.shape != (8192, 3) or points.dtype != np.float64 or not np.isfinite(points).all():
        raise ValueError("8192 finite float64 physical points required")
    center = np.median(points, axis=0)
    centered = points - center
    table = {}
    split_indices = (np.arange(0, len(points), 8), np.arange(1, len(points), 8))

    def records(candidates, split):
        out = []
        for abc in candidates:
            if abc not in table:
                table[abc] = evaluate_candidate(points, centered, abc, split_indices)
            out.append(table[abc][split])
        return out

    winners, details = [], []
    for split in range(2):
        coarse = records(COARSE, split)
        start = best_candidate(coarse)
        finer = []
        if start is not None:
            a, d, b = start["abc"]
            grid = [(a + da, d + dd, b + db) for da, dd, db in FINE_OFFSETS]
            finer = records(grid, split)
        winners.append(best_candidate(finer))
        details.append(dict(coarse=coarse, fine=finer, coarse_best=start, best=winners[-1]))
    return {**plane_gates(winners), "center_mm": center.tolist(), "splits": details,
            "unique_candidate_count": len(table)}


def native_order(anchors):
    x, y, z = anchors.T
    return np.lexsort((np.arange(len(anchors)), z, y, x))


def invert(order):
    ids = np.arange(len(order))
    inverse = np.empty_like(order)
    inverse[order] = ids
    if not (np.array_equal(order[inverse], ids) and np.array_equal(inverse[order], ids)):
        raise ValueError("invalid permutation or inverse")
    return inverse


def block_order(order, edges):
    partner = {i: j for a, b in edges for i, j in ((a, b), (b, a))}
    used = set()
    result = []
    for i in order:
        if i not in used:
            result.append(i)
            used.add(i)
            if i in partner:
                j = partner[i]
                result.append(j)
                used.add(j)
    return np.array(result, dtype=np.int64)


def reflected_edges(coordinates, signed, n, tau):
    # The normal points towards +LR in LPS, i.e. towards the patient's left.
    left = np.flatnonzero(signed > 3.0)
    right = np.flatnonzero(signed < -3.0)
    mirrored = coordinates - 2 * signed[:, None] * n
    wrong_side_distance = distance.cdist(mirrored[left], coordinates[right])
    reverse_distance = distance.cdist(coordinates[left], mirrored[right])
    if not len(left) or not len(right):
        return np.empty((0, 2), dtype=np.int64), left, right, wrong_side_distance, reverse_distance
    lr = wrong_side_distance.argmin(axis=1)
    rl = reverse_distance.argmin(axis=0)
    left_ix = np.arange(len(left))
    mutual = (rl[lr] == left_ix) & (wrong_side_distance[left_ix, lr] <= tau) & (reverse_distance[left_ix, lr] <= tau)
    edges = np.column_stack((left[mutual], right[lr[mutual]]))
    return edges, left, right, wrong_side_distance, reverse_distance


def solve_control(allowed, cost):
    if np.any(maximum_bipartite_matching(csr_matrix(allowed), perm_type="column") < 0):
        return None
    scaled = np.rint(cost * 1e6).astype(np.int64)
    k = len(allowed)
    forbidden = 1 + k * int(scaled[allowed].max())
    row, column = linear_sum_assignment(np.where(allowed, scaled, forbidden))
    if len(row) != k or not allowed[row, column].all():
        raise ValueError("assignment used a forbidden edge")
    return row, column, int(scaled[row, column].sum())


def gaps(rank, edges):
    return np.abs(rank[edges[:, 0]] - rank[edges[:, 1]])


def distribution(values):
    return dict(mean=float(np.mean(values)), p50=float(np.median(values)),
                p95=float(np.percentile(values, 95)), max=float(np.max(values))) if len(values) else None


def sequence_metrics(order, rank0, metric, neighbors, matched):
    a, b = order[:-1], order[1:]
    jumps = metric[a, b]
    edges = {tuple(sorted(e)) for e in matched}
    nonmatched = [v for i, j, v in zip(a, b, jumps) if tuple(sorted((i, j))) not in edges]
    return dict(jump=distribution(jumps),
                nn8_fraction=float(np.mean(neighbors[a, b] | neighbors[b, a])),
                non_pair_jump_p95_mm=float(np.percentile(nonmatched, 95)) if nonmatched else None,
                rank_displacement=distribution(np.abs(invert(order) - rank0)))


def plan_orders(anchors_native, anchors_mm, plane):
    if (anchors_native.shape != (256, 3) or anchors_mm.shape != (256, 3)
            or not np.isfinite(anchors_native).all() or not np.isfinite(anchors_mm).all()):
        raise ValueError("256 finite native anchor coordinates required")
    order0 = native_order(anchors_native)
    rank0 = invert(order0)
    record = dict(joint_active=False, reasons=[], k=None, compact_anchors=None)

    def finish():
        s, c = (order_s, order_c) if record["joint_active"] else (order0, order0)
        return {**record, "order": {"R": order0.tolist(), "S": s.tolist(), "C": c.tolist()},
                "inverse": {"R": rank0.tolist(), "S": invert(s).tolist(), "C": invert(c).tolist()}}

    if not plane["plane_ok"]:
        record["reasons"] = ["PLANE_NOT_RELIABLE"]
        return finish()

    xyz = anchors_mm
    a, d, b = plane["splits"][0]["best"]["abc"]
    n = normal_for(a, d)
    signed = (xyz - plane["center_mm"]) @ n - b
    metric = distance.cdist(xyz, xyz)
    nonself = metric.copy()
    np.fill_diagonal(nonself, np.inf)
    median = float(np.median(nonself.min(axis=1)))
    record["d_med_mm"] = median
    if not np.isfinite(median) or median <= 0:
        record["reasons"] = ["DEGENERATE_ANCHOR_SPACING"]
        return finish()
    tau = float(np.clip(1.25 * median, 4, 12))
    edges_s, left, right, dlr, drl = reflected_edges(xyz, signed, n, tau)
    k = len(edges_s)
    record.update(tau_mm=tau, k=k, s_edges=edges_s.tolist(),
                  compact_anchors=dict(left_eligible=len(left), right_eligible=len(right),
                                       near_plane=int(np.sum(np.abs(signed) <= 3)),
                                       left_unmatched=np.setdiff1d(left, edges_s[:, 0]).tolist(),
                                       right_unmatched=np.setdiff1d(right, edges_s[:, 1]).tolist()))
    if k < 16:
        record["reasons"] = ["INSUFFICIENT_SYMMETRY_EDGES"]
        return finish()

    l_used, r_used = edges_s[:, 0], np.sort(edges_s[:, 1])
    lr_ix, rl_ix = np.searchsorted(left, l_used), np.searchsorted(right, r_used)
    dlr, drl = dlr[np.ix_(lr_ix, rl_ix)], drl[np.ix_(lr_ix, rl_ix)]
    s_right = np.searchsorted(r_used, edges_s[:, 1])
    s_left = np.arange(k)
    record["s_mirror_residual_mm"] = distribution(np.maximum(dlr[s_left, s_right], drl[s_left, s_right]))
    required_new = (k + 1) // 2
    g_star = gaps(rank0, edges_s)
    record["s_new_adjacent"] = int(np.sum(g_star != 1))
    if record["s_new_adjacent"] < required_new:
        record["reasons"] = ["S_INSUFFICIENT_NEW_ADJACENCIES"]

    allowed = (dlr > tau) & (drl > tau)
    allowed[s_left, s_right] = False
    d_star = metric[l_used, edges_s[:, 1]]
    jump = metric[np.ix_(l_used, r_used)]
    rank_delta = np.abs(rank0[l_used, None] - rank0[r_used])
    length_diff = np.abs(jump - d_star[:, None])
    rank_diff = np.abs(rank_delta - g_star[:, None])
    costs = length_diff / np.maximum(d_star[:, None], 10) + 0.25 * rank_diff / 255
    solved = solve_control(allowed, costs)
    record["control_allowed_edges"] = int(allowed.sum())
    if solved is None:
        record["reasons"].append("NO_PERFECT_MATCH")
        return finish()
    row, col, cost = solved
    edges_c = np.column_stack((l_used[row], r_used[col]))
    length_match = float(np.mean(length_diff[row, col] <= np.maximum(10, 0.20 * d_star[row])))
    rank_match = float(np.median(rank_diff[row, col]))
    c_new_adjacent = int(np.sum(gaps(rank0, edges_c) != 1))
    record.update(c_edges=edges_c.tolist(), control_cost_integer=cost,
                  c_length_match_fraction=length_match, c_rank_deviation_median=rank_match,
                  c_new_adjacent=c_new_adjacent,
                  c_mirror_residual_mm=distribution(np.maximum(dlr[row, col], drl[row, col])))
    if length_match < 0.80 or rank_match > 32 or c_new_adjacent < required_new:
        record["reasons"].append("CONTROL_POSTCHECK_FAIL")

    order_s, order_c = block_order(order0, edges_s), block_order(order0, edges_c)
    r_s, r_c = invert(order_s), invert(order_c)
    if np.any(gaps(r_s, edges_s) != 1) or np.any(gaps(r_c, edges_c) != 1):
        raise ValueError("paired blocks lost adjacency")
    c_mirror_fraction = float(np.mean(gaps(r_c, edges_s) == 1))
    record["c_true_mirror_adjacency"] = c_mirror_fraction
    if 1 - c_mirror_fraction < 0.25:
        record["reasons"].append("MIRROR_ADJACENCY_CONTRAST_FAIL")
    # Stable distance sorting keeps the native ID as the tie break.
    near = np.argsort(nonself, axis=1, kind="stable")[:, :8]
    neighbors = np.zeros(nonself.shape, dtype=bool)
    neighbors[np.arange(N_ANCHORS)[:, None], near] = True
    metrics_r = sequence_metrics(order0, rank0, metric, neighbors, ())
    metrics_s = sequence_metrics(order_s, rank0, metric, neighbors, edges_s)
    metrics_c = sequence_metrics(order_c, rank0, metric, neighbors, edges_c)
    record["sequence_attempt"] = dict(R=metrics_r, S=metrics_s, C=metrics_c)
    limits = dict(mean=max(2, 0.10 * metrics_r["jump"]["mean"]),
                  p95=max(5, 0.20 * metrics_r["jump"]["p95"]), nn8=0.05)
    observed = dict(mean=abs(metrics_s["jump"]["mean"] - metrics_c["jump"]["mean"]),
                    p95=abs(metrics_s["jump"]["p95"] - metrics_c["jump"]["p95"]),
                    nn8=abs(metrics_s["nn8_fraction"] - metrics_c["nn8_fraction"]))
    record["whole_sequence"] = dict(limits=limits, observed=observed)
    for key, value in observed.items():
        if value > limits[key]:
            record["reasons"].append(f"SEQUENCE_{key.upper()}_MISMATCH")
    record["joint_active"] = not record["reasons"]
    return finish()
