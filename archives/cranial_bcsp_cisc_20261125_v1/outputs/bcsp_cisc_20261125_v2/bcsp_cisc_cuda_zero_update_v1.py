"""Single admitted CISC CUDA validation. No checkpoint loading or optimizer."""
import argparse
import ast
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import random
import socket
import sys
import time


COUNTS = dict(validation_forward=6, loss=3, backward=3, optimizer_step=0, timing_forward=75)
SEED, HEAD_SEED, AUX_SEED = 2026112601, 2026112603, 2026112605
ARMS = ("R", "U", "I")


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def control(path, sha):
    p = Path(path)
    need(p.resolve(strict=True) == p and p.stat().st_size <= 131072, "control path")
    raw = p.read_bytes()
    need(digest(raw) == sha, "control SHA256")
    return json.loads(raw)


def authorize(q, request_sha, auth, auth_sha, runtime):
    need(q["schema"] == "bcsp-cisc-p1-cuda-zero-update-v1"
         and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["counts"] == COUNTS,
         "pending P1 admission scope")
    need(set(auth) == {"request_sha256", "explicit_user_authorization", "authorization_text"}
         and auth["request_sha256"] == request_sha and auth["explicit_user_authorization"] is True
         and isinstance(auth["authorization_text"], str) and auth["authorization_text"].strip(), "full-hash authorization")
    need(runtime == {"request_sha256": request_sha, "authorization_sha256": auth_sha}, "runtime binding")


def seeded_builder(parent, oasg, expected_sha):
    fn = parent._build
    path, tree = oasg._source(fn, expected_sha)
    [node] = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_build"]
    need(node.lineno == fn.__code__.co_firstlineno, "seeded parent source")
    old = ast.parse("(2026112101, 2026112102)", mode="eval").body
    [condition] = [n for n in ast.walk(node.body[0].test) if ast.dump(n) == ast.dump(old)]
    condition.elts = [ast.Constant(SEED)]
    return oasg._compile(node, path, fn.__globals__)


def build_arm(q, support, torch, native_helper, cisc, arm):
    import importlib
    from easydict import EasyDict

    names = q["module_names"]
    parent = sys.modules[names["prime_seeded_parent"]]
    oasg = sys.modules[names["oasg_entry"]]
    head_module = sys.modules[names["oasg_head"]]
    raw = support.exact(q["coarse_initializer"]).read_bytes()
    need(len(raw) == head_module.INITIALIZER_BYTES, "coarse initializer length")
    cls = importlib.import_module("models.AdaPoinTr").AdaPoinTr
    config = json.loads(support.exact(q["static_config"]).read_bytes())["model"]
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(SEED)
        build = seeded_builder(parent, oasg, q["implementation"]["prime_seeded_parent"]["sha256"])
        model, evidence = build(lambda: cls(EasyDict(config)), "M0", SEED, parent.native_mixer,
                                artificial_fixture=False)
        model, _ = sys.modules[names["lqi_factory"]]._install(model, evidence, parent.native_mixer, False)
        model, _ = sys.modules[names["scq_factory"]].install(model, "B", None)
        base = model.base_model
        base.forward = oasg._oasg_forward(base)
        base.coarse_pred = head_module.ObservationAnchoredHead()
        values = torch.frombuffer(bytearray(raw), dtype=torch.float32)
        need(bool(torch.isfinite(values).all()), "finite coarse initializer")
        with torch.no_grad():
            offset = 0
            for param in base.coarse_pred.parameters():
                end = offset + param.numel()
                param.copy_(values[offset:end].view_as(param))
                offset = end
            need(offset == values.numel(), "complete coarse initializer")
        options = {} if arm == "R" else dict(prior=q["prior"]["value"], auxiliary_seed=AUX_SEED)
        model = cisc.attach(model, arm, **options)
    native_helper.validate_model(model)
    return model


def counter_call(observed, key, maximum):
    need(observed[key] < maximum, f"{key} budget")
    observed[key] += 1


def gradients(model, torch):
    rows = {}
    for name, value in model.named_parameters():
        if value.grad is not None:
            need(bool(torch.isfinite(value.grad).all()), f"nonfinite gradient {name}")
            rows[name] = bool(torch.count_nonzero(value.grad))
    return rows


def run(q, support, event, sample):
    from statistics import median
    loader = support.source("cisc_frozen_oasg_native", q["native_model_loader"])
    torch, np, helper, _ = loader.prepare_models(q, support)
    support.source("bcsp_cisc_head_v1", q["cisc_sources"]["head"])
    cisc = support.source("bcsp_cisc_entry_v1", q["cisc_sources"]["entry"])
    helper.assert_numeric(torch)
    fold = json.loads(support.exact(q["fold"]).read_bytes())["folds"]["D"]
    rows = q["inputs"]
    ids = [row["case_id"] for row in rows]
    expected_ids = sorted(fold["train_case_ids"], key=lambda cid: digest(cid.encode()))[:8]
    need(ids == expected_ids and not set(ids) & set(fold["dev_case_ids"]), "fixed Fold D eight-case batch")
    x, y, labels = [], [], []
    for row in rows:
        with np.load(io.BytesIO(support.exact(row["points"]).read_bytes()), allow_pickle=False) as data:
            partial, target = data["partial"], data["implant"]
        sidecar = support.exact(row["labels"]).read_bytes()
        label = cisc.verified_labels(sidecar, partial, label_sha256=row["labels"]["sha256"],
                                     partial_sha256=row["partial_array_sha256"])
        need(partial.shape == target.shape == (8192, 3) and target.dtype == np.float32
             and np.isfinite(partial).all() and np.isfinite(target).all()
             and digest(target.tobytes()) == row["target_array_sha256"], "fixed training target")
        x.append(partial)
        y.append(target)
        labels.append(label)
    x, y, labels = (torch.from_numpy(np.stack(v)).to("cuda:0") for v in (x, y, labels))
    parent = sys.modules[q["module_names"]["prime_seeded_parent"]]
    counts = dict.fromkeys(COUNTS, 0)
    results, baseline = {}, None
    common_prefix = "base_model.coarse_pred."
    extra = tuple(common_prefix + name for name in ("conditioner.", "condition_map."))
    shared = None
    r_grad = None
    i_state = None
    for arm in ARMS:
        sample(arm, "before_arm")
        model = build_arm(q, support, torch, helper, cisc, arm)
        model.to("cuda:0")
        snapshot = {name: value.detach().cpu().clone() for name, value in model.state_dict().items()}
        fingerprints = {name: parent.tensor_sha(value) for name, value in snapshot.items()}
        current = {k: v for k, v in fingerprints.items() if not k.startswith(extra)}
        if shared is None:
            shared = current
        need(current == shared, "native common initialization")
        novel = {k: v for k, v in fingerprints.items() if k.startswith(extra)}
        if arm == "U":
            i_state = novel
        if arm == "I":
            need(novel == i_state, "native U/I auxiliary initialization")
        need(sum(p.numel() for p in model.parameters()) == (39907012 if arm == "R" else 39968069),
             "frozen parameter count")
        cpu_rng, gpu_rng = torch.random.get_rng_state(), torch.cuda.get_rng_state()
        python_rng, numpy_rng = random.getstate(), np.random.get_state()
        torch.cuda.reset_peak_memory_stats()
        model.eval()
        with torch.inference_mode():
            counter_call(counts, "validation_forward", 6)
            q0, p0 = model(x)
            need(q0.shape == (8, 256, 3) and p0.shape == (8, 8192, 3)
                 and q0.isfinite().all() and p0.isfinite().all(), "finite batch8 eval shape")
            pair = (q0.cpu(), p0.cpu())
            if baseline is None:
                baseline = pair
            errors = [float((a - b).abs().max()) for a, b in zip(pair, baseline)]
            need(all(torch.allclose(a, b, atol=1e-6, rtol=1e-5) for a, b in zip(pair, baseline)),
                 "zero-map batch8 reconstruction equivalence")
        del q0, p0
        model.train()
        counter_call(counts, "validation_forward", 6)
        counter_call(counts, "loss", 3)
        loss = cisc.training_losses(model, x, y, 0, None if arm == "R" else labels)
        need(all(bool(v.isfinite()) for v in loss), "nonfinite training loss")
        counter_call(counts, "backward", 3)
        loss.total.backward()
        grad = gradients(model, torch)
        current_grad = set(grad) - {k for k in grad if k.startswith(extra)}
        if arm == "R":
            r_grad = current_grad
        else:
            need(current_grad == r_grad and grad[common_prefix + "condition_map.weight"]
                 and grad[common_prefix + "conditioner.last.weight"], "common or new gradient coverage")
        train_peak = torch.cuda.max_memory_allocated()
        need(train_peak <= q["resources"]["torch_peak_bytes"], "batch8 peak budget")
        event(dict(kind="batch8", arm=arm, errors=errors, loss=[float(v.detach()) for v in loss],
                   grads=grad, peak_allocated_bytes=train_peak))
        del loss
        sample(arm, "after_backward")
        model.zero_grad(set_to_none=True)
        model.load_state_dict(snapshot, strict=True)
        model.eval()
        torch.cuda.synchronize()
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        measurements = []
        with torch.inference_mode():
            for index in range(25):
                counter_call(counts, "timing_forward", 75)
                batch = x[index % 8:index % 8 + 1]
                torch.cuda.synchronize()
                start = time.perf_counter_ns()
                model(batch)
                torch.cuda.synchronize()
                if index >= 5:
                    measurements.append((time.perf_counter_ns() - start) / 1_000_000)
        peak = torch.cuda.max_memory_allocated()
        torch.random.set_rng_state(cpu_rng)
        torch.cuda.set_rng_state(gpu_rng)
        random.setstate(python_rng)
        np.random.set_state(numpy_rng)
        need(all(parent.tensor_sha(value) == fingerprints[name] for name, value in model.state_dict().items())
             and torch.equal(cpu_rng, torch.random.get_rng_state())
             and torch.equal(gpu_rng, torch.cuda.get_rng_state())
             and random.getstate() == python_rng
             and all(np.array_equal(a, b) for a, b in zip(np.random.get_state(), numpy_rng)),
             "parameter, buffer or RNG restoration")
        results[arm] = dict(p50_ms=median(measurements), timings_ms=measurements,
                            peak_allocated_bytes=peak, batch8_peak_allocated_bytes=train_peak, restored=True,
                            initial_sha256=digest(json.dumps(fingerprints, sort_keys=True).encode()))
        event(dict(kind="timing", arm=arm, **results[arm]))
        del model, snapshot
        gc.collect()
        torch.cuda.empty_cache()
    need(counts == COUNTS, "complete counters")
    r = results["R"]
    ratios = {arm: {key: results[arm][key] / r[key] for key in ("p50_ms", "peak_allocated_bytes")}
              for arm in ("U", "I")}
    event(dict(kind="ratios", ratios=ratios))
    need(all(value <= 1.5 for row in ratios.values() for value in row.values()), "relative resource gate")
    return dict(status="CISC_P1_CUDA_ZERO_UPDATE_PASS", counts=counts, results=results, ratios=ratios,
                shared_initial_sha256=digest(json.dumps(shared, sort_keys=True).encode()))


def main():
    parser = argparse.ArgumentParser()
    for item in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime", "runtime-sha256"):
        parser.add_argument("--" + item, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    q = control(args.request, args.request_sha256)
    authorize(q, args.request_sha256, control(args.authorization, args.authorization_sha256),
              args.authorization_sha256, control(args.runtime, args.runtime_sha256))
    need([args.request, args.authorization, args.runtime] == [q["controls"][key]
         for key in ("request", "authorization", "runtime")], "frozen control paths")
    ident = q["identity"]
    need((socket.gethostname(), os.getuid(), str(Path(sys.executable).resolve()), sys.version.split()[0])
         == (ident["hostname"], ident["uid"], ident["python_realpath"], ident["python_version"])
         and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
         and Path.cwd() == Path(q["project"]), "launch identity")
    need(all(os.environ.get(k) == v for k, v in q["environment"].items()), "runtime environment")
    binding = q["p2_support"]
    path = Path(binding["path"])
    need(path.resolve(strict=True) == path, "support path")
    raw = path.read_bytes()
    need(len(raw) == binding["bytes"] and digest(raw) == binding["sha256"], "support SHA256")
    import types
    support = types.ModuleType("cisc_oasg_support")
    exec(compile(raw, str(path), "exec"), support.__dict__)
    need(Path(__file__) == support.exact(q["worker"]), "worker SHA256")
    support.exact(q["launcher"])
    out = support.clean(q["output"])
    need(out.parent == Path(q["project"]) / "logs/cranial_bcsp_fullmamba", "exclusive output root")
    initial = support.resources(q, out, initial=True)
    if args.check:
        need(out.parent.is_dir() and not out.exists(), "fresh output path")
        return
    need(out.is_dir() and {p.name for p in out.iterdir()} == {"launch.log", "launcher.pid"}, "exclusive launch")
    parent = Path(f"/proc/{os.getppid()}")
    argv = (parent / "cmdline").read_bytes().split(b"\0")
    need(argv[:4] == [b"/usr/bin/timeout", b"--signal=TERM", b"--kill-after=10s",
                     (str(q["resources"]["wall_seconds"]) + "s").encode()]
         and int((parent / "stat").read_text().rsplit(")", 1)[1].split()[1]) == int((out / "launcher.pid").read_text()),
         "worker must descend from the bounded launcher")
    for name in ("tmp", "cache", "mplconfig", "triton", "hf"):
        (out / name).mkdir()
    import threading
    import signal
    lock, stop = threading.Lock(), threading.Event()

    def event(row):
        with lock, (out / "events.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()

    def sample(arm, stage):
        event(dict(kind="resources", arm=arm, stage=stage, **support.resources(q, out)))

    def monitor():
        while not stop.wait(q["resources"]["monitor_interval_seconds"]):
            try:
                sample(None, "monitor")
            except Exception as error:
                try:
                    event(dict(kind="monitor_failure", error=repr(error)))
                finally:
                    os.kill(os.getpid(), signal.SIGTERM)
                return

    event(dict(kind="initial_resources", **initial))
    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    try:
        result = run(q, support, event, sample)
    finally:
        stop.set()
        watcher.join(timeout=q["resources"]["smi_timeout_seconds"] + 2)
        need(not watcher.is_alive(), "monitor shutdown")
    with (out / "completion.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
