"""Full zero-update cache collection using the P1-frozen observer."""

import gc
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import torch

from bcsp_fcsp_capture_v1 import _snapshot, capture_fc, load_partial
from bcsp_fcsp_head_v1 import coarse_geometry


COUNTS = dict(records=840, train_records=630, development_records=210,
              reused_p1=4, donor_forward=836, optimizer_step=0)


def need(value, why):
    if not value:
        raise ValueError(why)


def emit(path, value, append=False):
    with path.open("a" if append else "x", encoding="utf-8", newline="\n") as file:
        file.write(json.dumps(value, allow_nan=False) + "\n")
        file.flush()
        os.fsync(file.fileno())


def readback(path):
    data = path.read_bytes()
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def capture_name(row):
    return f"{row['fold']}__{row['case_id']}.npz"


def validate_index(index, checkpoints, input_roots, p1):
    rows = index["rows"]
    need(index["counts"] == COUNTS and len(rows) == 840, "fixed P3 count")
    identities = [(r["fold"], r["split"], r["source_id"], r["case_id"]) for r in rows]
    need(identities == sorted(set(identities)), "canonical distinct P3 identities")
    reused = set()
    input_records = {}
    split_sources = {}
    defect_types = {"bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"}
    for fold in ("C", "D"):
        parts = {}
        for split, size in (("train", 315), ("development", 105)):
            selected = [r for r in rows if (r["fold"], r["split"]) == (fold, split)]
            need(len(selected) == size and len({r["case_id"] for r in selected}) == size,
                 "fixed fold split")
            grouped = {}
            for row in selected:
                case = row["case_id"].split("__", 2)
                need(len(case) == 3 and case[0] == "train" and len(case[1]) == 3
                     and case[1].isascii() and case[1].isdigit()
                     and row["source_id"] == "train:" + case[1], "case/source identity")
                grouped.setdefault(row["source_id"], set()).add(case[2])
                rec = row["input"]
                path = Path(rec["path"])
                need(str(path.parent) in input_roots and path.name == row["case_id"] + "_8192.npz",
                     "fixed point-file roots")
                need(input_records.setdefault(str(path), rec) == rec, "conflicting input identities")
                need(row["checkpoint_sha256"] == checkpoints["G2_" + fold]["sha256"],
                     "fold/checkpoint identity")
                if row.get("reuse"):
                    key = (fold, split, row["case_id"])
                    need(key in p1 and row["reuse"] == p1[key], "unexpected inherited P1 record")
                    reused.add(key)
            need(len(grouped) == size // 5 and all(types == defect_types for types in grouped.values()),
                 "five defect types per source")
            parts[split] = grouped.keys()
        need(not parts["train"] & parts["development"], "fold source overlap")
        split_sources[fold] = parts
    need(not split_sources["C"]["development"] & split_sources["D"]["development"],
         "development source overlap across folds")
    need(reused == set(p1) and len(reused) == 4, "exact inherited P1 set")
    return rows, input_records.values()


def write_cached(target, cache):
    local, neighbors, scale = coarse_geometry(cache.q)
    need(tuple(cache.h.shape) == (1, 256, 384), "P1-measured FC width")
    arrays = {key: value[0].detach().cpu().contiguous().numpy()
              for key, value in dict(Q=cache.q, H=cache.h, P0=cache.p0, geometry=local,
                                     neighbors=neighbors, scale=scale).items()}
    with target.open("xb") as file:
        np.savez_compressed(file, **arrays)
        file.flush()
        os.fsync(file.fileno())


def copy_inherited(target, ref):
    with Path(ref["path"]).open("rb") as file:
        data = file.read(ref["bytes"] + 1)
    need(len(data) == ref["bytes"] and hashlib.sha256(data).hexdigest() == ref["sha256"],
         "P1 capture identity changed")
    with target.open("xb") as file:
        file.write(data)
        file.flush()
        os.fsync(file.fileno())


def run_p3(rows, output, builder, sample, assert_numeric):
    device = torch.device("cuda:0")
    journal = output / "p3_forward_attempts.jsonl"
    manifest = output / "p3_cache_manifest.jsonl"
    for path in (journal, manifest):
        path.open("x").close()
    attempted = 0
    completed = 0
    reused = 0
    states = {}
    try:
        for fold in ("C", "D"):
            model = builder(fold).eval().requires_grad_(False).to(device)
            model.enable_full_instrumentation(False)
            torch.cuda.synchronize(device)
            before = _snapshot(model)
            sample("fold_start_" + fold, attempted)
            for row in (r for r in rows if r["fold"] == fold):
                target = output / capture_name(row)
                inherit = row.get("reuse")
                if inherit:
                    copy_inherited(target, inherit)
                    reused += 1
                else:
                    rec = row["input"]
                    x = torch.from_numpy(load_partial(rec["path"], rec["bytes"], rec["sha256"]))
                    x = x.unsqueeze(0).to(device)
                    assert_numeric(torch)
                    need(attempted < COUNTS["donor_forward"], "too many donor calls")
                    attempted += 1
                    emit(journal, dict(index=attempted, fold=fold, case_id=row["case_id"],
                                       status="CLAIMED_BEFORE_FORWARD"), append=True)
                    cache = capture_fc(model, x)
                    torch.cuda.synchronize(device)
                    write_cached(target, cache)
                    del x, cache
                emit(manifest, dict(fold=fold, split=row["split"], case_id=row["case_id"],
                                    source_id=row["source_id"], normalization=row["normalization"],
                                    input_sha256=row["input"]["sha256"],
                                    checkpoint_sha256=row["checkpoint_sha256"], reused_p1=bool(inherit),
                                    capture={"file": target.name, **readback(target)}), append=True)
                completed += 1
                if completed % 16 == 0:
                    sample("cache_progress", attempted)
            after = _snapshot(model)
            need(before == after, "frozen donor, mode or RNG changed")
            states[fold] = {"before_after_equal": True,
                            "snapshot_sha256": hashlib.sha256(repr(before).encode()).hexdigest()}
            sample("fold_end_" + fold, attempted)
            del model
            gc.collect()
            torch.cuda.empty_cache()
        need((attempted, completed, reused) == (836, 840, 4), "P3 cardinality mismatch")
        sample("complete", attempted)
        emit(output / "p3_completion.json", dict(status="AWAITING_READ_ONLY_HISTORY_AND_FREEZE_AUDIT",
                                                 counts=COUNTS, states=states, manifest=readback(manifest),
                                                 journal=readback(journal)))
    except BaseException as exc:
        emit(output / "p3_failure.json", dict(status="FAILED_STOP_NO_RETRY", attempted=attempted,
                                             complete_rows=completed, reused_p1=reused, error=repr(exc)))
        raise
