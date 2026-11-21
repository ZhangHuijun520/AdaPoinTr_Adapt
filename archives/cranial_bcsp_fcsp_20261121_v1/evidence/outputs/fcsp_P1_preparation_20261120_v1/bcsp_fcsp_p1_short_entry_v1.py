"""P1 computation entry for an already-authorized, identity-checked launcher."""

import gc
import hashlib
import json

import numpy as np
import torch

from bcsp_fcsp_capture_v1 import _snapshot, load_partial, same_fp32_bytes, verify_capture_pair
from bcsp_fcsp_head_v1 import CHILDREN, PARENTS, PlacementHead, coarse_geometry, geometry_condition


CASES = (
    ("C", "train", "train__000__bilateral"),
    ("C", "development", "train__001__bilateral"),
    ("D", "train", "train__000__bilateral"),
    ("D", "development", "train__004__bilateral"),
)
ARMS = ("B0-Global", "B1-Local")
COUNTS = dict(donor_forward=8, fc_replay=4, zero_head_forward=8, pressure_head_forward=2,
              dense_loss=2, backward=2, optimizer_step=0)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def emit_json(path, value, mode="x"):
    with path.open(mode, encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(value, allow_nan=False) + "\n")


def record(path):
    raw = path.read_bytes()
    return {"file": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def snapshot_sha(model):
    return hashlib.sha256(repr(_snapshot(model)).encode("utf-8")).hexdigest()


def new_head(width, device):
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(0)
        head = PlacementHead(width, 0.125)
    return head.to(device)


def frozen_case(model, row, output, journal, counts, sample, device):
    item = row["input"]
    x = torch.from_numpy(load_partial(item["path"], item["bytes"], item["sha256"]))
    x = x.unsqueeze(0).to(device)
    state = snapshot_sha(model)
    first = counts["donor_forward"]

    def claim_forward(_model, _args):
        index = counts["donor_forward"] + 1
        need(index <= COUNTS["donor_forward"] and index <= first + 2, "extra full donor forward")
        sample("before_donor_forward", index)
        emit_json(journal, {"stage": "donor_forward", "index": index, "fold": row["fold"],
                           "case_id": row["case_id"], "observation": index == first + 2}, "a")
        counts["donor_forward"] = index

    handle = model.register_forward_pre_hook(claim_forward)
    try:
        cache = verify_capture_pair(model, x)
    finally:
        handle.remove()
    need(counts["donor_forward"] == first + 2, "missing donor call")

    sample("before_fc_replay", counts["donor_forward"])
    counts["fc_replay"] += 1
    with torch.inference_mode():
        replay = model.decode_head(cache.h) + cache.q.unsqueeze(-2)
    need(same_fp32_bytes(replay, cache.p0), "actual FC replay mismatch")
    need(snapshot_sha(model) == state, "FC replay mutated model state or RNG")
    local, neighbors, scale = coarse_geometry(cache.q)
    width = cache.h.shape[-1]
    head = new_head(width, device).eval()
    for arm in ARMS:
        counts["zero_head_forward"] += 1
        with torch.no_grad():
            shifted = head(cache.h, geometry_condition(local, arm), cache.p0)
        need(same_fp32_bytes(shifted, cache.p0), "zero placement changed native P0 bytes")
    sample("after_case", counts["donor_forward"])

    path = output / f"{row['fold']}_{row['split']}_capture.npz"
    arrays = {key: value[0].detach().cpu().contiguous().numpy()
              for key, value in dict(Q=cache.q, H=cache.h, P0=cache.p0, geometry=local,
                                     neighbors=neighbors, scale=scale).items()}
    with path.open("xb") as file:
        np.savez_compressed(file, **arrays)
    return {"fold": row["fold"], "split": row["split"], "case_id": row["case_id"],
            "source_id": row["source_id"], "input_sha256": item["sha256"],
            "normalization": row["normalization"], "checkpoint_sha256": row["checkpoint_sha256"],
            "observed_parent_width": width, "state_and_rng_sha256": state,
            "small_scale_parents": int((scale <= 1e-8).sum().item()),
            "observed_native_zero_and_fc_replay_bitwise": True, "capture": record(path)}


def pressure(width, loss_fn, counts, journal, sample, device):
    need(loss_fn.__class__.__name__ == "ChamferDistanceL1Directional"
         and loss_fn.pred_to_ref_weight == loss_fn.ref_to_pred_weight == 1.0,
         "expected bound equal-weight directional Chamfer")
    index = torch.arange(PARENTS * CHILDREN, device=device, dtype=torch.int64)
    points = torch.stack(tuple((index % modulus).float() / modulus for modulus in (61, 67, 71)), -1)
    p0 = points.reshape(1, PARENTS, CHILDREN, 3).expand(8, -1, -1, -1).contiguous()
    target = (p0.flatten(1, 2) + p0.new_tensor([.007, -.009, .011])).contiguous()
    target[:, 0, :] = 0.0
    need(bool((p0[:, 0, 0, :] == 0).all() and (target[:, 0, :] == 0).all()), "exact overlap fixture")
    q = p0[:, :, 0, :].contiguous()
    local = coarse_geometry(q)[0]
    h = local[..., (torch.arange(width, device=device) % local.shape[-1])].contiguous()
    head = new_head(width, device)
    before = snapshot_sha(head)
    rows = []
    for arm in ARMS:
        head.zero_grad(set_to_none=True)
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
        sample("before_pressure_" + arm, counts["donor_forward"])
        emit_json(journal, {"stage": "artificial_batch8_pressure", "arm": arm,
                           "explicit_exact_overlap_pairs": 8}, "a")
        counts["pressure_head_forward"] += 1
        prediction = head(h, geometry_condition(local, arm), p0).flatten(1, 2)
        need(same_fp32_bytes(prediction, p0.flatten(1, 2)), "pressure zero output identity")
        counts["dense_loss"] += 1
        value = loss_fn(prediction, target)
        need(value.ndim == 0 and bool(torch.isfinite(value)), "nonfinite artificial dense loss")
        counts["backward"] += 1
        value.backward()
        torch.cuda.synchronize(device)
        peak_allocated = torch.cuda.max_memory_allocated(device)
        peak_reserved = torch.cuda.max_memory_reserved(device)
        gradients = {}
        for name, parameter in head.named_parameters():
            gradient = parameter.grad
            gradients[name] = dict(finite=gradient is not None and bool(torch.isfinite(gradient).all()),
                                   nonzero=int(gradient.count_nonzero()) if gradient is not None else 0)
        row = dict(arm=arm, loss=float(value.detach()), gradients=gradients,
                   peak_allocated_bytes=peak_allocated, peak_reserved_bytes=peak_reserved)
        emit_json(journal, {"stage": "pressure_evidence", **row}, "a")
        need(all(g["finite"] for g in gradients.values()), "nonfinite artificial CUDA gradients")
        need(all(g["nonzero"] == 0 for n, g in gradients.items() if n.startswith("net.0.")),
             "first layer must have zero initial data gradient")
        need(gradients["net.2.weight"]["nonzero"] > 0, "zero output-layer gradient")
        need(snapshot_sha(head) == before, "zero-update pressure changed parameters or RNG")
        sample("after_pressure_" + arm, counts["donor_forward"])
        rows.append(row)
        del value, prediction
    return rows


def run_p1(rows, output, builder, loss_fn, sample):
    """Call only after loader, file policy, and single-attempt checks have passed."""
    need(tuple((r["fold"], r["split"], r["case_id"]) for r in rows) == CASES,
         "incorrect fixed P1 rows")
    device = torch.device("cuda:0")
    need(torch.cuda.is_available() and torch.cuda.device_count() == 1, "one approved device required")
    counts = dict.fromkeys(COUNTS, 0)
    journal = output / "p1_journal.jsonl"
    journal.open("x").close()
    captures = []
    try:
        for fold in ("C", "D"):
            model = builder(fold).eval().requires_grad_(False).to(device)
            if hasattr(model, "enable_full_instrumentation"):
                model.enable_full_instrumentation(False)
            for row in rows:
                if row["fold"] == fold:
                    captures.append(frozen_case(model, row, output, journal, counts, sample, device))
            del model
            gc.collect()
            torch.cuda.empty_cache()
        widths = {item["observed_parent_width"] for item in captures}
        need(len(captures) == 4 and len(widths) == 1, "capture count or parent width mismatch")
        stress = pressure(widths.pop(), loss_fn, counts, journal, sample, device)
        need(counts == COUNTS, "P1 exact counter mismatch")
        sample("complete", counts["donor_forward"])
        emit_json(output / "p1_completion.json", {"status": "AWAITING_READ_ONLY_FREEZE_AUDIT",
                                                   "counts": counts, "captures": captures,
                                                   "pressure": stress, "journal": record(journal)})
    except BaseException as error:
        emit_json(output / "p1_failure.json", {"status": "FAILED_STOP_NO_RETRY",
                                                "counts": counts, "error": repr(error)})
        raise
