"""Frozen Fold D CISC R/U/I Native prediction. No execution on import."""
import argparse
from collections import Counter
from contextlib import ExitStack
import gc
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import sys
import time

ARMS = ("R", "U", "I")
SEED = 2026112601
TOTAL = 315
STATUS = "AWAITING_EXPLICIT_USER_AUTHORIZATION"
SCHEMA = "bcsp-cisc-rui-d-native-v1"
CALLS = dict(optimizer_steps=0, backward=0, loss=0, BNCal=0, warmup=0, TTA=0, scoring=0)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def identity(arm):
    need(arm in ARMS, "registered CISC arm")
    return dict(variant=arm, fold="D", seed=SEED)


def authorize(q, req_sha, auth, auth_sha, rt):
    need(q["schema"] == SCHEMA and q["status"] == STATUS and q["execution_authorized"] is False,
         "pending frozen request")
    need(q["science"] == dict(fold="D", seed=SEED, arms=list(ARMS), cases=105, sources=21,
                             forward=TOTAL, n_input=8192, n_output=8192, batch=1)
         and q["no_calls"] == CALLS, "exact Native scope")
    need(set(auth) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
         and auth["schema"] == "bcsp-development-authorization-v1"
         and auth["request_sha256"] == req_sha and auth["explicit_user_authorization"] is True
         and bool(auth["user_authorization_text"].strip()), "explicit execution authorization")
    need(rt == dict(schema="bcsp-development-runtime-v1", request_sha256=req_sha, authorization_sha256=auth_sha),
         "one-way runtime authorization")


def select_inputs(q, fold, manifest):
    f = fold["folds"]["D"]
    ids, sources = f["dev_case_ids"], f["dev_sources"]
    need(len(ids) == len(set(ids)) == 105 and len(sources) == len(set(sources)) == 21
         and not set(ids) & set(f["train_case_ids"]) and not set(sources) & set(f["train_sources"]),
         "Fold D development split")
    index = {r["case_id"]: r for r in manifest}
    need(len(index) == len(manifest) == 420, "frozen point manifest")
    rows = []
    for cid in ids:
        row = index[cid]
        relative = f"points/{cid}_8192.npz"
        norm = row["normalization"]
        need(row["point_path"] == relative and PurePosixPath(relative).name == cid + "_8192.npz"
             and row["normalization_source"] == "defective_bbox" and row["schema"] == "BCSP-normalized-v1"
             and len(norm["center"]) == 3 and all(map(math.isfinite, norm["center"]))
             and math.isfinite(norm["scale"]) and norm["scale"] > 0
             and row["n_input"] == row["n_target"] == 8192, f"development metadata: {cid}")
        rows.append(dict(case_id=cid, source_id=row["source_id"], n_input=8192, normalization=norm,
                         input=dict(path=str(PurePosixPath(q["development_root"]) / relative), sha256=row["sha256"],
                                    bytes=q["development_sizes"][cid])))
    need(Counter(r["source_id"] for r in rows) == Counter({s: 5 for s in sources})
         and set(q["development_sizes"]) == set(ids), "21 sources and five cases each")
    return rows


def mechanism_cases(rows):
    used = set()
    selected = []
    by_type = {}
    for row in rows:
        kind = row["case_id"].split("__")[-1]
        by_type.setdefault(kind, []).append(row)
    need(set(by_type) == {"bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"}
         and all(len(group) == 21 for group in by_type.values()), "five defect types")
    for kind in sorted(by_type):
        group = sorted(by_type[kind], key=lambda row: hashlib.sha256(row["case_id"].encode()).hexdigest())
        count = 0
        for row in group:
            if row["source_id"] in used:
                continue
            selected.append(row["case_id"])
            used.add(row["source_id"])
            count += 1
            if count == 3:
                break
        need(count == 3, f"three fixed mechanism cases: {kind}")
    return selected


def verify_training(q, receipts):
    need(set(receipts) == set(q["checkpoints"]) == set(ARMS), "exact R/U/I receipts")
    expected = {
        "R": "FORMAL_CISC_R_D_POST_TRAINING_FREEZE_AUDIT_PASS",
        "U": "FORMAL_CISC_U_D_POST_TRAINING_FREEZE_AND_PAIRED_AUDIT_PASS",
        "I": "FORMAL_CISC_I_D_POST_TRAINING_FREEZE_AND_THREE_ARM_PAIRED_AUDIT_PASS",
    }
    for arm in ARMS:
        receipt = receipts[arm]
        checkpoint = {k: receipt["checkpoint"][k] for k in ("path", "bytes", "sha256")}
        need(receipt["status"] == expected[arm] and receipt["run"] == identity(arm)
             and receipt["identity"] == q["identity"] and receipt["exit_code"] == 0
             and receipt["common_contract_sha256"] == q["common_contract_sha256"]
             and checkpoint == q["checkpoints"][arm], f"{arm} frozen training evidence")
    paired = receipts["I"]
    need(paired["reference_audit_sha256"] == q["training_receipts"]["R"]["sha256"]
         and paired["uniform_audit_sha256"] == q["training_receipts"]["U"]["sha256"]
         and all(paired["paired"].values()) and len(paired["paired"]) == 6,
         "three-arm pairing evidence")
    need(paired["completion"]["optimizer_updates"] == 3900
         and paired["completion"]["case_exposures"] == 31200
         and paired["counts"]["batch_count"] == 3900, "I completed training counts")


class ForwardBudget:
    def __init__(self, ids):
        need(len(ids) == len(set(ids)) == 105, "105 distinct cases")
        self.schedule = [(arm, cid) for arm in ARMS for cid in ids]
        self.calls = 0

    def claim(self, arm, cid):
        need(self.calls < TOTAL and self.schedule[self.calls] == (arm, cid), "frozen forward order/budget")
        self.calls += 1
        return self.calls

    def finish(self, saved):
        need(self.calls == saved == TOTAL, "315 successful predictions")


def observe_once(torch, np, model, x, arm):
    captured = {}

    def retain(key, value):
        need(key not in captured, f"one actual {key} call")
        captured[key] = value

    def head_hook(_module, args, result):
        expected_args = 3 if arm == "R" else 4
        need(len(args) == expected_args and len(result) == 2, "head signature")
        retain("head", (args[2].detach(), result[0].detach(), result[1].detach()))

    def condition_hook(_module, args, condition):
        points, anchors, _ = args
        weights = condition.descriptor[..., 0].gather(1, condition.index)
        alpha = weights / weights.sum(dim=1, keepdim=True)
        center = (alpha[..., None] * points).sum(dim=1)
        covariance = condition.descriptor[:, 0, 5:]
        retain("condition", (condition.logits, condition.logits.sigmoid(),
                             condition.index, condition.counts, center, covariance,
                             condition.descriptor[..., 0], condition.descriptor[..., 1]))

    need(not any(m.training for m in model.modules()), "native eval mode")
    with ExitStack() as stack, torch.inference_mode():
        head = model.base_model.coarse_pred
        stack.callback(model.decode_head.register_forward_hook(
            lambda _module, _args, result: retain("fc", result.detach())).remove)
        stack.callback(head.register_forward_hook(head_hook).remove)
        if arm in ("U", "I"):
            need(head.conditioner.arm == arm, "conditioner arm")
            stack.callback(head.conditioner.register_forward_hook(condition_hook).remove)
        result = model(x)
    need(isinstance(result, (tuple, list)) and len(result) == 2, "native eval tuple")
    need(set(captured) == ({"head", "fc"} if arm == "R" else {"head", "fc", "condition"}),
         "exact observed model calls")

    def cpu(value):
        return value.detach().cpu().numpy().copy()

    coarse, dense = map(cpu, result)
    relative = cpu(captured["fc"])
    anchors, used, delta = map(cpu, captured["head"])

    def finite(a, shape):
        return a.shape == shape and a.dtype == np.float32 and np.isfinite(a).all()

    need(all(finite(v, (1, 256, 3)) for v in (coarse, anchors, used, delta))
         and finite(dense, (1, 8192, 3)) and finite(relative, (1, 256, 32, 3)),
         "finite FP32 native geometry")
    need(np.array_equal(used, coarse) and np.array_equal(anchors + delta, used)
         and np.array_equal((relative + coarse[:, :, None, :]).reshape(1, 8192, 3), dense),
         "native query and FC parent-slot identities")
    slots = np.arange(256, dtype=np.int64)
    arrays = dict(coarse=coarse[0], prediction=dense[0], parent_index=np.repeat(slots, 32),
                  S=anchors[0], delta=delta[0], token_index=slots)
    if arm != "R":
        logits, probability, index, counts, center, covariance, support, uniform = (
            cpu(value)[0] for value in captured["condition"])
        need(all(finite(v, (256,)) for v in (logits, probability, support, uniform))
             and finite(center, (3,)) and finite(covariance, (6,)), "finite interface condition")
        need(index.shape == (8192,) and counts.shape == (256,)
             and index.dtype == counts.dtype == np.int64 and index.min() >= 0 and index.max() < 256
             and np.array_equal(np.bincount(index, minlength=256), counts), "exact token assignment")
        need(((probability >= 0) & (probability <= 1)).all()
             and ((support > 0) & (support < 1)).all()
             and np.all(uniform == uniform[0]), "interface probability and uniform field")
        need(np.array_equal(support, uniform) if arm == "U"
             else np.array_equal(support[counts == 0], uniform[counts == 0]), "effective support field")
        arrays.update(logits=logits, p=probability, v=index, n=counts, c=center, V=covariance,
                      r=support, uniform_r=uniform)
    return arrays


def data_boundary(q, rows, output):
    """Restrict payload and checkpoint opens to the exact Native inputs and three weights."""
    read = {Path(r["input"]["path"]) for r in rows} | {Path(r["path"]) for r in q["checkpoints"].values()}
    owned = {output / f"predictions/{arm}_D__{r['case_id']}.npz" for arm in ARMS for r in rows}
    roots = {Path(q["project"]) / name for name in ("data", "dataset", "datasets", "checkpoints", "sealed")}
    def audit(event, args):
        if event != "open" or isinstance(args[0], int):
            return
        p = Path(os.fsdecode(args[0])).absolute()
        write = bool(args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
        if write:
            resolved = p.resolve()
            need(resolved == output or output in resolved.parents, f"out-of-scope Native write: {p}")
        if (p.suffix.lower() in {".npz", ".npy", ".pt", ".pth", ".ckpt", ".nrrd", ".nii", ".stl", ".ply"}
                or p.name.endswith(".nii.gz") or any(r == p or r in p.parents for r in roots)):
            need(not any(x.is_symlink() for x in (p, *p.parents)), f"linked Native payload: {p}")
            need(p in owned or (not write and p in read), f"out-of-scope Native payload: {p}")
    return audit


def prepare_models(q, support):
    loader = support.source("cisc_frozen_prediction_model_loader", q["native_model_loader"])
    torch, np, helper, _ = loader.prepare_models(q, support)
    support.source("bcsp_cisc_head_v1", q["cisc_sources"]["head"])
    cisc = support.source("bcsp_cisc_entry_v1", q["cisc_sources"]["entry"])
    worker = support.source("cisc_frozen_prediction_builder", q["cisc_p1_worker"])

    def build(arm):
        model = worker.build_arm(q, support, torch, helper, cisc, arm)
        need(sum(p.numel() for p in model.parameters()) == (39907012 if arm == "R" else 39968069),
             f"{arm} parameter count")
        return model

    return torch, np, helper, build


def rng_hash(state):
    return {key: hashlib.sha256(value.encode("ascii")).hexdigest() for key, value in state.items()}


def run(q, support, legacy, rows, out, request_sha):
    sys.addaudithook(data_boundary(q, rows, out))
    torch, np, helper, build = prepare_models(q, support)
    helper._MONITOR = None
    budget = ForwardBudget([r["case_id"] for r in rows])
    monitor = legacy.Budget(q, out, torch, helper)
    manifest, journal = out / "inference_manifest.jsonl", out / "forward_attempts.jsonl"
    for p in (manifest, journal):
        p.open("x").close()
    saved, states = [], []
    for arm in ARMS:
        model = build(arm)
        record = q["checkpoints"][arm]
        checkpoint = torch.load(support.exact(record), map_location="cpu", weights_only=True)
        need(isinstance(checkpoint, dict) and checkpoint.get("scq_prime_run_identity") == identity(arm)
             and checkpoint.get("epoch") == 99 and checkpoint.get("updates") == 3900
             and checkpoint.get("stage") == "BCSP_INPUT_DENSITY_V1", "final checkpoint payload identity")
        model.load_state_dict(checkpoint["base_model"], strict=True)
        del checkpoint
        model.eval().to("cuda:0")
        need(all(p.dtype == torch.float32 for p in model.parameters()), "FP32 checkpoint model")
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats(0)
        state = helper.state_sha(model)
        rng = rng_hash(legacy.rng_state(torch, np, helper, True))
        for r in rows:
            cid = r["case_id"]
            helper.assert_numeric(torch)
            monitor.sample("before_forward", budget.calls)
            x = torch.from_numpy(legacy.load_partial(np, r)).unsqueeze(0).to("cuda:0")
            call = budget.claim(arm, cid)
            legacy.append_event(journal, dict(forward_index=call, run=f"{arm}_D", case_id=cid,
                                               status="CLAIMED_BEFORE_FORWARD"))
            arrays = observe_once(torch, np, model, x, arm)
            path = out / f"predictions/{arm}_D__{cid}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, **arrays)
            saved.append(path)
            legacy.append_event(manifest, dict(
                run=f"{arm}_D", variant=arm, fold="D", seed=SEED, case_id=cid, source_id=r["source_id"],
                n_input=8192, n_output=8192, input_sha256=r["input"]["sha256"], normalization=r["normalization"],
                frame="native_D_only_normalized", checkpoint_sha256=record["sha256"], forward_index=call,
                diagnostic_fields=sorted(arrays), native_fc_parent_major_verified=True,
                prediction=dict(name=path.relative_to(out).as_posix(), bytes=path.stat().st_size,
                                sha256=support.file_hash(path))))
            helper.assert_numeric(torch)
            monitor.sample("after_forward", budget.calls)
            del x, arrays
        after, rng_after = helper.state_sha(model), rng_hash(legacy.rng_state(torch, np, helper, True))
        need(state == after and rng == rng_after, f"{arm} parameters, buffers and RNG unchanged")
        states.append(dict(run=f"{arm}_D", identity=identity(arm), forwards=len(rows),
                           state_before=state, state_after=after, RNG_before=rng, RNG_after=rng_after))
        del model
        gc.collect()
        torch.cuda.empty_cache()
    budget.finish(len(saved))
    monitor.sample("all_complete", budget.calls)
    done = out / "inference_complete.json"
    legacy.emit(done, dict(status="CISC_RUI_D_NATIVE_315_COMPLETE", forwards=TOTAL,
                           request_sha256=request_sha, models=states, **CALLS))
    archive = legacy.pack(out, saved + [manifest, journal, done, monitor.path])
    limits = q["limits"]
    need(sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) <= limits["output_bytes"]
         and shutil.disk_usage(out).free >= limits["minimum_free_disk_bytes"]
         and time.monotonic() - monitor.start <= limits["wall_seconds"], "archive resource limits")
    legacy.emit(out / "completion.json", dict(status="PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT",
                                             forwards=TOTAL, archive=archive, request_sha256=request_sha))


def main():
    parser = argparse.ArgumentParser()
    for key in ("request", "request-sha256", "authorization", "authorization-sha256",
                "runtime", "runtime-sha256", "launcher"):
        parser.add_argument("--" + key, required=True)
    args = parser.parse_args()
    def control(path, sha):
        p = Path(path)
        need(p.is_absolute() and p.resolve() == p and not p.is_symlink(), "exact control path")
        with p.open("rb") as f:
            b = f.read(128 * 1024 + 1)
        need(len(b) <= 128 * 1024 and hashlib.sha256(b).hexdigest() == sha, "control SHA256")
        return json.loads(b)

    q = control(args.request, args.request_sha256)
    authorize(q, args.request_sha256, control(args.authorization, args.authorization_sha256),
              args.authorization_sha256, control(args.runtime, args.runtime_sha256))
    need([args.request, args.authorization, args.runtime] == [q["controls"][k]
         for k in ("request", "authorization", "runtime")], "exact launch controls")
    i = q["identity"]
    need(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
         and socket.gethostname() == i["hostname"] and os.getuid() == i["uid"]
         and str(Path(sys.executable).resolve()) == i["python_realpath"]
         and sys.version.split()[0] == i["python_version"], "runtime identity")
    need(all(os.environ.get(k) == v for k, v in q["environment"].items()), "frozen runtime environment")
    p = q["p2_support"]
    path = Path(p["path"])
    need(path.resolve() == path and not path.is_symlink(), "P2 support path")
    b = path.read_bytes()
    need(len(b) == p["bytes"] and hashlib.sha256(b).hexdigest() == p["sha256"], "P2 support binding")
    import types
    support = types.ModuleType("cisc_native_support")
    exec(compile(b, str(path), "exec", dont_inherit=True), support.__dict__)
    need(Path.cwd() == support.clean(q["project"]) and Path(__file__) == support.exact(q["worker"])
         and support.exact(q["launcher"]) == support.clean(args.launcher), "owned entry and project")
    out = support.clean(q["output"])
    need(out.parent == Path(q["project"]) / "logs/cranial_bcsp_fullmamba"
         and out.is_dir() and {p.name for p in out.iterdir()} == {"launcher.pid", "launch.log"},
         "exclusive prediction output")
    parent = Path(f"/proc/{os.getppid()}")
    data = (parent / "cmdline").read_bytes().split(b"\0")
    need(data[:4] == [b"/usr/bin/timeout", b"--signal=TERM", b"--kill-after=5s", b"7200s"]
         and int((parent / "stat").read_text().rsplit(")", 1)[1].split()[1]) == int((out / "launcher.pid").read_text()),
         "one-shot launcher parent")
    support.resources(q, out, initial=True)
    leg = support.source("cisc_frozen_native_helpers", q["legacy_helpers"])
    audit = {k: json.loads(support.exact(v).read_bytes()) for k, v in q["training_receipts"].items()}
    verify_training(q, audit)
    for p in [*q["checkpoints"].values(), q["coarse_initializer"]]:
        support.exact(p)
    rows = select_inputs(q, json.loads(support.exact(q["fold"]).read_bytes()),
                         [json.loads(s) for s in support.exact(q["point_manifest"]).read_bytes().splitlines()])
    need(q["mechanism_cases"] == mechanism_cases(rows), "fixed offline mechanism sample")
    for row in rows:
        support.exact(row["input"])
    with (out / "worker.pid").open("x", encoding="ascii") as f:
        f.write(str(os.getpid()) + "\n")
    for name in ("predictions", "tmp", "cache", "mplconfig", "triton", "hf"):
        (out / name).mkdir()
    try:
        run(q, support, leg, rows, out, args.request_sha256)
    except BaseException as exc:
        leg.emit(out / "failure.json", dict(status="FAILED_STOP_NO_RETRY", error=repr(exc)))
        raise


if __name__ == "__main__":
    main()
