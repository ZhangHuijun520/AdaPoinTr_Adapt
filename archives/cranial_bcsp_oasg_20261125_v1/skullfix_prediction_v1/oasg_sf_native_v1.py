"""Frozen Fold D OASG Native prediction. No execution on import."""
import argparse
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

ARMS = ("B", "A")
SEED = 2026112102
CASES = 90
TOTAL = 180
STATUS = "AWAITING_EXPLICIT_USER_AUTHORIZATION"
SCHEMA = "bcsp-oasg-sf-native-v1"
CALLS = dict(optimizer_steps=0, backward=0, loss=0, BNCal=0, warmup=0, TTA=0, scoring=0)


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def identity(arm):
    need(arm in ARMS, "registered OASG arm")
    return dict(variant=arm, fold="D", seed=SEED)


def authorize(q, req_sha, auth, auth_sha, rt):
    need(q["schema"] == SCHEMA and q["status"] == STATUS and q["execution_authorized"] is False,
         "pending frozen request")
    need(q["science"] == dict(dataset="SkullFix", fold="D", seed=SEED, arms=list(ARMS), cases=CASES, sources=CASES,
                             forward=TOTAL, n_input=8192, n_output=8192, batch=1)
         and q["no_calls"] == CALLS, "exact Native scope")
    need(set(auth) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
         and auth["schema"] == "bcsp-development-authorization-v1"
         and auth["request_sha256"] == req_sha and auth["explicit_user_authorization"] is True
         and bool(auth["user_authorization_text"].strip()), "explicit execution authorization")
    need(rt == dict(schema="bcsp-development-runtime-v1", request_sha256=req_sha, authorization_sha256=auth_sha),
         "one-way runtime authorization")


def select_inputs(q, manifest):
    cases = manifest["cases"]
    ids = [row["case_id"] for row in cases]
    sources = [row["source_id"] for row in cases]
    need(manifest["schema"] == "oasg-sf-partial-only-v1" and manifest["dataset"] == "SkullFix"
         and ids == q["case_ids"] and len(ids) == len(set(ids)) == CASES
         and len(sources) == len(set(sources)) == CASES, "exact ordered 90-case SkullFix cohort")
    for row in cases:
        cid = row["case_id"]
        need(set(row) == {"case_id", "source_id", "n_input", "normalization", "input"}
             and len(cid) == 3 and cid.isascii() and cid.isdecimal()
             and row["source_id"] == "SkullFix:" + cid and row["n_input"] == 8192,
             "SkullFix case identity")
        n = row["normalization"]
        need(set(n) == {"center", "scale"} and len(n["center"]) == 3
             and all(map(math.isfinite, n["center"])) and math.isfinite(n["scale"]) and n["scale"] > 0,
             "defective-only physical frame")
        b = row["input"]
        need(set(b) == {"path", "bytes", "sha256"}
             and b["path"] == str(PurePosixPath(q["input_root"]) / (cid + "_partial_8192.npz"))
             and 0 < b["bytes"] <= 128 * 1024 and len(b["sha256"]) == 64
             and all(c in "0123456789abcdef" for c in b["sha256"]), "exact partial-only file")
    return cases


def load_partial(np, row):
    b = row["input"]
    p = Path(b["path"])
    need(p.is_file() and p.resolve() == p and p.stat().st_size == b["bytes"], "input path and size")
    from io import BytesIO
    raw = p.read_bytes()
    need(len(raw) == b["bytes"] and hashlib.sha256(raw).hexdigest() == b["sha256"], "input bytes")
    with np.load(BytesIO(raw), allow_pickle=False) as archive:
        need(archive.files == ["partial"], "partial-only NPZ")
        points = archive["partial"]
    need(points.shape == (8192, 3) and points.dtype == np.float32 and np.isfinite(points).all(),
         "finite partial FP32 coordinates")
    return points


def verify_training(q, receipts):
    need(set(receipts) == set(q["checkpoints"]) == set(q["training_receipts"]) == set(ARMS),
         "exact prediction arms")
    b, a = (receipts[arm] for arm in ARMS)
    for arm, receipt, checkpoint in ((arm, receipts[arm], q["checkpoints"][arm]) for arm in ARMS):
        completion = receipt["completion"]
        state = receipt["model_construction"]
        matches = [row for row in receipt["artifacts"] if Path(row["path"]).name == "ckpt-last.pth"]
        expected_status = ("FORMAL_POST_TRAINING_READ_ONLY_FREEZE_AUDIT_PASS" if arm == "B" else
                           "FORMAL_POST_TRAINING_READ_ONLY_PAIR_FREEZE_AUDIT_PASS")
        need(receipt["status"] == expected_status and receipt["run"] == identity(arm)
             and receipt["request_sha256"] == q["training_request_sha256"][arm]
             and receipt["exit_code"] == 0 and receipt["artifact_rehash_agrees"] is True
             and matches == [checkpoint] and completion["checkpoint_sha256"] == checkpoint["sha256"]
             and completion["scq_prime_run_identity"] == identity(arm)
             and (completion["optimizer_updates"], completion["traversals"], completion["case_exposures"])
             == (3900, 100, 31200)
             and all(completion[key] is False for key in ("bncal_executed", "evaluation_executed", "resume"))
             and state["run_identity"] == identity(arm) and state["shared_tensors"] == 410
             and state["shared_initial_state_SHA256"] == q["shared_initial_state_sha256"],
             f"{arm} frozen training evidence")
    pair = a["pairing"]
    need(a["identity"] == q["identity"]
         and (b["hostname"], b["uid"]) == (q["identity"]["hostname"], q["identity"]["uid"])
         and a["paired_B_request_sha256"] == b["request_sha256"]
         and a["baseline_receipt"]["sha256"] == q["training_receipts"]["B"]["sha256"]
         and a["paired_B_checkpoint"] == q["checkpoints"]["B"]
         and pair["baseline_checkpoint_sha256"] == q["checkpoints"]["B"]["sha256"]
         and pair["shared_state"] == q["shared_initial_state_sha256"]
         and pair["all_actual_batches_match_B"] == 3900 and pair["numeric_schedule_matches_B"] == 3900
         and pair["all_rng_streams_equal"] is True and pair["order_and_exposure_bytes_equal"] is True
         and a["training_start_rng"]["rng"] == b["training_start_rng"]["rng"]
         and a["model_construction"]["initializer_sha256"] == q["initialization"]["sha256"]
         and b["model_construction"]["initializer_sha256"] is None, "paired training freeze")


class ForwardBudget:
    def __init__(self, ids):
        need(len(ids) == len(set(ids)) == CASES, "90 distinct cases")
        self.schedule = [(arm, cid) for arm in ARMS for cid in ids]
        self.calls = 0

    def claim(self, arm, cid):
        need(self.calls < TOTAL and self.schedule[self.calls] == (arm, cid), "frozen forward order/budget")
        self.calls += 1
        return self.calls

    def finish(self, saved):
        need(self.calls == saved == TOTAL, "180 successful predictions")


def payload(np, arm, coarse, dense, relative, head=None):
    def valid(v, shape):
        return v.shape == shape and v.dtype == np.float32 and np.isfinite(v).all()

    need(valid(coarse, (1, 256, 3)) and valid(dense, (1, 8192, 3))
         and valid(relative, (1, 256, 32, 3)), "finite FP32 FC outputs")
    need(np.array_equal((relative + coarse[:, :, None, :]).reshape(1, 8192, 3), dense),
         "native FC parent-major expansion identity")
    index = np.arange(256, dtype=np.int64)
    out = dict(coarse=coarse[0], prediction=dense[0], parent_index=np.repeat(index, 32))
    if arm == "A":
        need(head is not None, "A coarse head trace")
        anchors, used, delta = head
        need(all(valid(x, (1, 256, 3)) for x in head) and np.array_equal(used, coarse)
             and np.array_equal(anchors + delta, used), "actual consumed Q equals S + Delta")
        out.update(S=anchors[0], delta=delta[0], token_index=index)
    else:
        need(head is None and arm == "B", "B scope")
    return out


def observe_once(torch, np, model, x, arm):
    captured = {}
    def fc_hook(module, inputs, result):
        need("fc" not in captured, "one FC invocation")
        captured["fc"] = result.detach()
    def head_hook(module, inputs, result):
        need("head" not in captured and len(inputs) == 3 and len(result) == 2, "one A coarse head invocation")
        captured["head"] = tuple(v.detach() for v in (inputs[2], *result))
    need(not any(m.training for m in model.modules()), "native eval mode")
    with ExitStack() as stack, torch.inference_mode():
        stack.callback(model.decode_head.register_forward_hook(fc_hook).remove)
        if arm == "A":
            stack.callback(model.base_model.coarse_pred.register_forward_hook(head_hook).remove)
        result = model(x)
    need(isinstance(result, (tuple, list)) and len(result) == 2 and "fc" in captured, "native eval tuple")
    def cpu(v):
        return v.detach().cpu().numpy().copy()
    return payload(np, arm, *map(cpu, result), cpu(captured["fc"]),
                   tuple(map(cpu, captured["head"])) if "head" in captured else None)


def data_boundary(q, rows, output):
    """Restrict payload and checkpoint opens to the exact Native inputs and two weights."""
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
    for binding in q["dependencies"] + q["provider"] + list(q["implementation"].values()):
        support.exact(binding)
    scope = json.loads(support.exact(q["parent_scope"]).read_bytes())
    root = support.clean(q["model_root"])
    impl = q["implementation"]
    sys.path[:0] = [str(support.clean(q["provider"][0]["path"]).parent.parent), q["site_packages"]]
    helper = support.source("oasg_p3_preflight", impl["preflight_helper"])
    sources = helper.source_map(scope)
    for rel, binding in sources.items():
        support.exact(dict(binding, path=str(root / rel)))
    cfg = support.exact(dict(scope["bindings"]["base_config"], path=str(root / "base_model.yaml")))
    helper.namespace_packages(root)
    sys.meta_path.insert(0, helper.FiniteProjectImports(root, sources))
    import importlib
    import numpy as np
    import torch
    import timm
    import yaml
    from easydict import EasyDict
    device_identity = q["identity"]
    need((torch.__version__, np.__version__, timm.__version__, torch.version.cuda)
         == tuple(device_identity[k] for k in ("torch_version", "numpy_version", "timm_version", "torch_cuda_version")),
         "native software versions")
    need(torch.cuda.is_available() and torch.cuda.device_count() == 1, "single native CUDA device")
    torch.cuda.set_device(0)
    helper.configure_numeric(torch)
    helper.check_backend(importlib.import_module("extensions.chamfer_dist"),
                         importlib.import_module("utils.pointnet2_utils"),
                         importlib.import_module("pointnet2_ops.pointnet2_utils"))
    need(str(Path(importlib.import_module("pointnet2_ops._ext").__file__).resolve()) == q["provider"][2]["path"],
         "native PointNet2 extension")
    static = json.loads(support.exact(q["static_config"]).read_bytes())
    need(static["model"] == yaml.safe_load(cfg.read_text())["model"], "frozen model configuration")
    loaded = {}
    for key in ("encoder", "factory", "lqi_decoder", "lqi_factory", "scq_residual", "scq_factory",
                "prime_entry", "prime_seeded_parent", "oasg_head", "oasg_entry"):
        loaded[key] = support.source(q["module_names"][key], impl[key])
    cls = importlib.import_module("models.AdaPoinTr").AdaPoinTr
    importlib.import_module("models.Transformer_utils").enable_bcsp_knn()
    def build(arm):
        return loaded["oasg_entry"].construct(
            identity(arm), lambda: cls(EasyDict(static["model"])), q["initialization"] if arm == "A" else None,
            np=np, prime=loaded["prime_entry"], seeded=loaded["prime_seeded_parent"],
            lqi=loaded["lqi_factory"], scq=loaded["scq_factory"])
    return torch, np, helper, build


def run(q, support, legacy, rows, receipts, out, request_sha):
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
        model, construction = build(arm)
        need(construction == receipts[arm]["model_construction"], "model construction matches training receipt")
        helper.validate_model(model)
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
        rng = legacy.rng_state(torch, np, helper, True)
        for r in rows:
            cid = r["case_id"]
            helper.assert_numeric(torch)
            monitor.sample("before_forward", budget.calls)
            x = torch.from_numpy(load_partial(np, r)).unsqueeze(0).to("cuda:0")
            call = budget.claim(arm, cid)
            legacy.append_event(journal, dict(forward_index=call, run=f"{arm}_D", case_id=cid,
                                               status="CLAIMED_BEFORE_FORWARD"))
            arrays = observe_once(torch, np, model, x, arm)
            path = out / f"predictions/{arm}_D__{cid}.npz"
            with path.open("xb") as stream:
                np.savez_compressed(stream, **arrays)
            saved.append(path)
            legacy.append_event(manifest, dict(
                run=f"{arm}_D", dataset="SkullFix", variant=arm, fold="D", seed=SEED, case_id=cid, source_id=r["source_id"],
                n_input=8192, n_output=8192, input_sha256=r["input"]["sha256"], normalization=r["normalization"],
                frame="native_D_only_normalized", checkpoint_sha256=record["sha256"], forward_index=call,
                diagnostic_fields=sorted(arrays), native_fc_parent_major_verified=True,
                prediction=dict(name=path.relative_to(out).as_posix(), bytes=path.stat().st_size,
                                sha256=support.file_hash(path))))
            helper.assert_numeric(torch)
            monitor.sample("after_forward", budget.calls)
            del x, arrays
        after, rng_after = helper.state_sha(model), legacy.rng_state(torch, np, helper, True)
        need(state == after and rng == rng_after, f"{arm} parameters, buffers and RNG unchanged")
        states.append(dict(run=f"{arm}_D", identity=identity(arm), forwards=len(rows),
                           state_before=state, state_after=after, RNG_before=rng, RNG_after=rng_after))
        del model
        gc.collect()
        torch.cuda.empty_cache()
    budget.finish(len(saved))
    monitor.sample("all_complete", budget.calls)
    done = out / "inference_complete.json"
    legacy.emit(done, dict(status="OASG_SF_NATIVE_180_COMPLETE", forwards=TOTAL,
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
    support = types.ModuleType("oasg_p4_support")
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
    initial = support.resources(q, out, initial=True)
    need(initial["disk_free_bytes"] >= q["execution_policy"]["minimum_free_bytes_prelaunch"],
         "frozen minimum startup disk")
    leg = support.source("oasg_p4_frozen_helpers", q["legacy_helpers"])
    audit = {k: json.loads(support.exact(v).read_bytes()) for k, v in q["training_receipts"].items()}
    verify_training(q, audit)
    for p in [*q["checkpoints"].values(), q["initialization"]]:
        support.exact(p)
    rows = select_inputs(q, json.loads(support.exact(q["input_manifest"]).read_bytes()))
    for row in rows:
        support.exact(row["input"])
    with (out / "worker.pid").open("x", encoding="ascii") as f:
        f.write(str(os.getpid()) + "\n")
    for name in ("predictions", "tmp", "cache", "mplconfig", "triton", "hf"):
        (out / name).mkdir()
    try:
        run(q, support, leg, rows, audit, out, args.request_sha256)
    except BaseException as exc:
        leg.emit(out / "failure.json", dict(status="FAILED_STOP_NO_RETRY", error=repr(exc)))
        raise


if __name__ == "__main__":
    main()
