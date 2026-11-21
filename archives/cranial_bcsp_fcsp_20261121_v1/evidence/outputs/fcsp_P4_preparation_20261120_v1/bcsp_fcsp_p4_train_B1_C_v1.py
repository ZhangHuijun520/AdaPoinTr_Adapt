"""Fixed-cache FCSP head training. The donor and development data are outside this entry."""

import argparse
import ast
import hashlib
import io
import json
import math
import os
import re
import socket
import stat
import subprocess
import sys
import time
from pathlib import Path

ARM = "B1-Local"
PROJECT = Path("/home/jovyan/adapointr_work/PoinTr")
COUNTS = dict(batch=8, epochs=100, batches_per_epoch=39, updates=3900,
              exposures=31200, drops=300)
CACHE_FIELDS = dict(Q=(256, 3), H=(256, 384), P0=(256, 32, 3),
                    geometry=(256, 10), neighbors=(256, 8), scale=(256,))
CASE_ID = re.compile(r"train__[0-9]{3}__(bilateral|frontoorbital|parietotemporal|random_1|random_2)")
CHAMFER_SHA = "6456934164750c2d326236effe4827dc37c77a7d6d915d3c28fa65a90a9b1c50"


def require(value, message):
    if not value:
        raise ValueError(message)


def load_numeric(site_packages=None):
    global np, torch
    if site_packages is not None:
        packages = clean(site_packages)
        require(packages.is_dir(), "exact numeric site-packages")
        sys.path.insert(0, str(packages))
    import numpy as np
    import torch


def sha(data):
    return hashlib.sha256(data).hexdigest()


def clean(path):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, f"absolute path: {path}")
    require(not any(item.is_symlink() for item in (path, *path.parents)), f"link: {path}")
    return path


def read_bound(record, max_bytes):
    path = clean(record["path"])
    length = record["bytes"]
    require(type(length) is int and 0 < length <= max_bytes, f"byte bound: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as file:
        info = os.fstat(file.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_size == length, f"regular exact size: {path}")
        raw = file.read(length + 1)
    require(len(raw) == length and sha(raw) == record["sha256"], f"bound bytes: {path}")
    return raw


def read_control(path, digest):
    path = clean(path)
    return json.loads(read_bound(dict(path=str(path), bytes=path.stat().st_size, sha256=digest), 16384))


def load_head(record):
    scope = {"__name__": "fcsp_bound_head"}
    exec(compile(read_bound(record, 16384), record["path"], "exec"), scope)
    return scope


def load_loss(record):
    require(record["sha256"] == CHAMFER_SHA, "P1-approved loss identity")
    nodes = ast.parse(read_bound(record, 65536)).body
    names = ("_torch_chamfer_forward", "ChamferDistanceL1Directional")
    selected = [node for node in nodes if getattr(node, "name", None) in names]
    require(tuple(node.name for node in selected) == names, "historical loss symbols")
    scope = {"torch": torch, "chamfer": None}
    exec(compile(ast.Module(body=selected, type_ignores=[]), record["path"], "exec"), scope)
    return scope[names[1]](1.0, 1.0)


def validate_order(order, allowed):
    require(order["schema"] == "bcsp-shared-order-v1", "order schema")
    require(len(allowed) == 315 and len(order["case_ids"]) == 315
            and set(order["case_ids"]) == allowed, "order allowlist")
    epochs = order["epochs"]
    require(len(epochs) == 100, "epoch count")
    for epoch, row in enumerate(epochs):
        batches, dropped = row["batches"], row["dropped"]
        require(row["epoch"] == epoch and len(batches) == 39
                and all(len(batch) == 8 for batch in batches) and len(dropped) == 3,
                f"batch/drop count at epoch {epoch}")
        traversal = [case for batch in batches for case in batch] + dropped
        require(len(traversal) == len(set(traversal)) and set(traversal) == allowed,
                f"case inventory at epoch {epoch}")
    return epochs


def bind_training(selection, manifest, cache_root, label_roots):
    require(selection["status"] == "TRAIN_ONLY_FROZEN_LOCAL_SELECTION"
            and selection["fold"] == "C", "Fold C selection")
    selected = selection["rows"]
    allowed = {row["case_id"] for row in selected}
    require(len(selected) == len(allowed) == 315
            and all(CASE_ID.fullmatch(case) for case in allowed), "315 distinct cases")
    require(len({row["source_id"] for row in selected}) == 63, "63 distinct sources")
    cache_rows = {row["case_id"]: row for row in manifest
                  if (row["fold"], row["split"]) == ("C", "train")}
    require(len(manifest) == 840 and len(cache_rows) == 315
            and set(cache_rows) == allowed
            and sum((row["fold"], row["split"]) == ("C", "train") for row in manifest) == 315,
            "exact train cache set")
    dev_sources = {row["source_id"] for row in manifest
                   if (row["fold"], row["split"]) == ("C", "development")}
    require(len(dev_sources) == 21, "21 development sources in frozen metadata")
    bindings = {}
    for row in selected:
        case, src = row["case_id"], row["source_id"]
        current = cache_rows[case]
        name = f"C__{case}.npz"
        cache = dict(current["capture"])
        label = row["label_npz"]
        require(src == "train:" + case.split("__")[1] == current["source_id"]
                and src not in dev_sources, f"source isolation: {case}")
        require(cache.pop("file") == name and Path(row["cache_file"]) == cache_root / name,
                f"fixed cache filename: {case}")
        path = Path(label["path"])
        require(path.parent in label_roots and path.name == f"{case}_8192.npz"
                and label["sha256"] == current["input_sha256"]
                and label["read_member"] == "implant"
                and label["member_shape"] == [8192, 3] and label["member_dtype"] == "float32"
                and re.fullmatch(r"[0-9a-f]{64}", label["member_sha256"]),
                f"fixed label identity: {case}")
        bindings[case] = (dict(path=row["cache_file"], **cache), label)
    return bindings


def load_row(cache, label):
    with np.load(io.BytesIO(read_bound(cache, 1048576)), allow_pickle=False) as packed:
        require(set(packed.files) == set(CACHE_FIELDS) and len(packed.files) == len(CACHE_FIELDS),
                f"cache member set: {cache['path']}")
        values = {}
        for field, shape in CACHE_FIELDS.items():
            array = packed[field]
            dtype = np.int64 if field == "neighbors" else np.float32
            require(array.dtype == dtype and array.shape == shape and np.isfinite(array).all(),
                    f"cache {field}: {cache['path']}")
            values[field] = torch.from_numpy(np.ascontiguousarray(array))
    neighbors = values["neighbors"]
    require(bool(((neighbors >= 0) & (neighbors < 256)).all())
            and not bool((neighbors == torch.arange(256).unsqueeze(1)).any())
            and bool((neighbors.sort(dim=1).values.diff(dim=1) != 0).all())
            and bool((values["scale"] >= 0).all()), f"cache geometry: {cache['path']}")
    with np.load(io.BytesIO(read_bound(label, 262144)), allow_pickle=False) as packed:
        require(sorted(packed.files) == ["implant", "partial"], "label container schema")
        target = packed["implant"]
    require(target.dtype == np.float32 and target.shape == (8192, 3)
            and np.isfinite(target).all() and sha(target.tobytes(order="C")) == label["member_sha256"],
            f"frozen implant member: {label['path']}")
    return {k: values[k] for k in ("Q", "H", "P0", "geometry")}, torch.from_numpy(target)


def learning_rate(step):
    require(1 <= step <= COUNTS["updates"], "step outside schedule")
    if step <= 200:
        return 0.001 * step / 200
    return 0.00001 + (0.001 - 0.00001) * (1 + math.cos(math.pi * (step - 200) / 3700)) / 2


def state_sha(model):
    digest = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        digest.update(repr((name, str(tensor.dtype), tuple(tensor.shape))).encode())
        digest.update(tensor.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def append(file, event):
    file.write(json.dumps(event, allow_nan=False) + "\n")
    file.flush()


def write_json(path, event):
    with path.open("x", encoding="utf-8") as file:
        append(file, event)


def build_training(head, dataset, device):
    train_q = torch.stack([cache["Q"] for cache, _ in dataset.values()])
    train_p0 = torch.stack([cache["P0"] for cache, _ in dataset.values()])
    scale = head["fit_residual_scale"](train_q, train_p0)
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(0)
        model = head["PlacementHead"](384, scale)
    return model.to(device), scale


def train_step(model, dataset, batch, device, condition, criterion, optimizer, step):
    examples = [dataset[case] for case in batch]
    h, g, p0 = (torch.stack([cache[key] for cache, _ in examples]).to(device)
                for key in ("H", "geometry", "P0"))
    target = torch.stack([label for _, label in examples]).to(device)
    lr = learning_rate(step)
    optimizer.param_groups[0]["lr"] = lr
    optimizer.zero_grad(set_to_none=True)
    logits = []
    hook = model.net[-1].register_forward_hook(lambda _, __, result: logits.append(result.detach()))
    try:
        output = model(h, condition(g, ARM), p0)
    finally:
        hook.remove()
    require(len(logits) == 1, f"head output call count at step {step}")
    with torch.no_grad():
        saturation = float((logits[0].tanh().abs() >= .99).float().mean())
        displacement = (output.detach().to(torch.float64) - p0).abs()
        scale = float(model.b_train)
        rounding = torch.finfo(torch.float32).eps * (p0.abs().to(torch.float64) + scale)
        require(bool((displacement <= scale + rounding).all()), f"residual bound at step {step}")
        magnitude = displacement.norm(dim=-1)
        diagnostics = dict(saturation_fraction=saturation, max_component=float(displacement.max()),
                           max_norm=float(magnitude.max()), mean_norm=float(magnitude.mean()))
    loss = criterion(output.flatten(1, 2), target)
    require(loss.ndim == 0 and loss.dtype == torch.float32 and bool(torch.isfinite(loss)),
            f"nonfinite or invalid loss at step {step}")
    loss.backward()
    require(all(param.grad is not None for param in model.parameters()),
            f"missing head gradient at step {step}")
    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 10.0, error_if_nonfinite=True)
    optimizer.step()
    require(all(bool(torch.isfinite(p).all()) for p in model.parameters()),
            f"nonfinite head parameter at step {step}")
    return dict(lr=lr, loss=float(loss.detach()), gradient_norm_pre_clip=float(norm),
                nonfinite=0, residual=diagnostics)


def train(head, criterion, dataset, epochs, device, output, request_sha, monitor, paired):
    model, scale = build_training(head, dataset, device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, betas=(0.9, 0.999),
                                  eps=1e-8, weight_decay=0.0001, foreach=False, fused=False)
    init = state_sha(model)
    initialization = dict(seed=0, state_sha256=init, b_train_fp64=scale,
                          b_train_float32_bytes=model.b_train.detach().cpu().numpy().tobytes().hex(),
                          trainable_parameters=sum(p.numel() for p in model.parameters()),
                          optimizer=optimizer.defaults)
    require(json.loads(json.dumps(initialization)) == paired, "B0_C initialization and optimizer mismatch")
    write_json(output / "initialization.json", initialization)
    step = exposures = drops = 0
    with (output / "metrics.jsonl").open("x", encoding="utf-8") as metrics:
        for row in epochs:
            drops += len(row["dropped"])
            for number, batch in enumerate(row["batches"]):
                step += 1
                outcome = train_step(model, dataset, batch, device, head["geometry_condition"],
                                     criterion, optimizer, step)
                exposures += len(batch)
                append(metrics, dict(step=step, epoch=row["epoch"], batch=number,
                                     case_ids=batch, **outcome))
                if step == 1 or step % 16 == 0:
                    monitor(step)
    require((step, exposures, drops) == (3900, 31200, 300), "exact completed counts")
    monitor(step)
    checkpoint = output / "B1_Local_C_seed0_step3900.pth"
    with checkpoint.open("xb") as file:
        torch.save(dict(request_sha256=request_sha, fold="C", arm=ARM, seed=0, step=step,
                        state_dict={k: v.detach().cpu() for k, v in model.state_dict().items()}), file)
    monitor(step)
    write_json(output / "completion.json", dict(status="AWAITING_READ_ONLY_FREEZE_AUDIT",
               request_sha256=request_sha, updates=step, epochs=len(epochs), exposures=exposures,
               drops=drops, initial_state_sha256=init, final_state_sha256=state_sha(model),
               checkpoint=dict(file=checkpoint.name, sha256=sha(checkpoint.read_bytes()),
                               bytes=checkpoint.stat().st_size),
               donor_forward=0, development_access=0, BNCal=False, resume=False))


def authorize(args):
    q = read_control(args.request, args.request_sha256)
    auth = read_control(args.authorization, args.authorization_sha256)
    runtime = read_control(args.runtime, args.runtime_sha256)
    require(q["schema"] == "bcsp-fcsp-p4-training-v1"
            and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION"
            and q["execution_authorized"] is False and (q["fold"], q["arm"], q["seed"]) == ("C", ARM, 0)
            and q["counts"] == COUNTS, "P4 B1_C frozen request")
    l = q["launch"]
    require((args.request, args.authorization, args.runtime) ==
            (l["request"], l["authorization"], l["runtime"]), "exact control paths")
    require(set(auth) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
            and auth["schema"] == "bcsp-fcsp-p4-authorization-v1"
            and auth["request_sha256"] == args.request_sha256
            and auth["explicit_user_authorization"] is True and auth["user_authorization_text"].strip(),
            "separate explicit authorization")
    require(runtime == dict(schema="bcsp-fcsp-p4-runtime-v1", request_sha256=args.request_sha256,
                            authorization_sha256=args.authorization_sha256), "one-way runtime")
    claim = json.loads(clean(l["claim"]).read_bytes())
    require(claim == dict(status="CLAIMED_BEFORE_TMUX", request_sha256=args.request_sha256), "single attempt")
    return q


def make_monitor(q, out, filename):
    start = time.monotonic()
    limits = q["limits"]
    def monitor(step):
        used = subprocess.check_output(
            ["/usr/bin/nvidia-smi", "-i", q["identity"]["gpu_uuid"], "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"], timeout=10).decode().strip()
        rss_kib = int(next(line.split()[1] for line in Path("/proc/self/status").read_text().splitlines()
                           if line.startswith("VmRSS:")))
        from shutil import disk_usage
        values = dict(wall_seconds=time.monotonic() - start, device_MiB=int(used),
                      RSS_bytes=rss_kib * 1024, torch_peak_bytes=torch.cuda.max_memory_reserved(0),
                      output_bytes=sum(p.stat().st_size for p in out.iterdir() if p.is_file()),
                      minimum_free_disk_bytes=disk_usage(out).free)
        checks = {key: (value >= limits[key] if key == "minimum_free_disk_bytes" else value <= limits[key])
                  for key, value in values.items()}
        with filename.open("a", encoding="utf-8") as file:
            append(file, dict(step=step, values=values, checks=checks))
        require(all(checks.values()), f"resource guard: {checks}")
    return monitor


def run(args):
    q = authorize(args)
    ident = q["identity"]
    require(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site
            and sys.dont_write_bytecode, "Linux isolated entry")
    require((socket.gethostname(), os.getuid(), str(Path(sys.executable).resolve()), sys.version.split()[0])
            == (ident["hostname"], ident["uid"], ident["python_realpath"], ident["python_version"]),
            "execution identity")
    require(Path.cwd() == PROJECT and clean(q["entry"]["path"]) == Path(__file__).resolve(), "working directory")
    read_bound(q["entry"], 65536)
    out = clean(q["output"])
    require(out.parent == PROJECT / "logs/cranial_bcsp_fullmamba" and out.is_dir()
            and {p.name for p in out.iterdir()} == {"launch.log"}, "fresh output")
    parent = Path(f"/proc/{os.getppid()}/cmdline").read_bytes().split(b"\0")
    require(parent[:4] == [b"/usr/bin/timeout", b"--signal=TERM", b"--kill-after=5s",
                           f"{q['limits']['wall_seconds']}s".encode()], "external wall guard")
    for k, v in q["environment"].items():
        require(os.environ.get(k) == v.replace("<owned_output>", str(out)), f"environment: {k}")
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == ident["gpu_uuid"]
            and os.environ.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", "CUDA binding")
    env = clean(ident["python_realpath"]).parent.parent
    load_numeric(env / "lib/python3.10/site-packages")
    require(torch.__version__ == ident["torch_version"] and torch.version.cuda == ident["torch_cuda_version"]
            and np.__version__ == ident["numpy_version"], "numeric provider identity")
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.backends.cudnn.benchmark = False
    torch.use_deterministic_algorithms(True)
    require(not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32
            and torch.are_deterministic_algorithms_enabled() and not torch.is_autocast_enabled()
            and torch.cuda.device_count() == 1,
            "strict CUDA FP32")
    selection = json.loads(read_bound(q["selection"], 524288))
    cache_root = clean(q["cache_root"])
    require(cache_root.parent == out.parent and q["cache_manifest"]["path"] ==
            str(cache_root / "p3_cache_manifest.jsonl"), "P3 manifest path")
    require(selection["bound_cache_manifest"] == q["cache_manifest"]
            and selection["recorded_order"] == q["order"], "frozen selection provenance")
    raw = read_bound(q["cache_manifest"], 500000)
    label_roots = {clean(p) for p in q["label_roots"]}
    require(len(label_roots) == 2 and all(p.name == "points" and p.parent.parent == PROJECT / "data"
                                         for p in label_roots), "point roots")
    pair = q["pair_B0_C"]
    require(pair["order_sha256"] == q["order"]["sha256"] and pair["selection_sha256"] == q["selection"]["sha256"]
            and pair["cache_manifest_sha256"] == q["cache_manifest"]["sha256"], "B0_C paired asset identity")
    paired = json.loads(read_bound(pair["initialization"], 4096))
    require(paired == pair["expected_initialization"], "B0_C frozen initialization evidence")
    bindings = bind_training(selection, list(map(json.loads, raw.splitlines())), cache_root, label_roots)
    epochs = validate_order(json.loads(read_bound(q["order"], 1300000)), set(bindings))
    with (out / "worker.pid").open("x", encoding="ascii") as file:
        file.write(f"{os.getpid()}\n")
    try:
        monitor = make_monitor(q, out, out / "resources.jsonl")
        monitor(0)
        head, criterion = load_head(q["head"]), load_loss(q["loss_source"])
        dataset = {case: load_row(*binding) for case, binding in bindings.items()}
        monitor(0)
        train(head, criterion, dataset, epochs, torch.device("cuda:0"), out, args.request_sha256, monitor, paired)
    except Exception as exc:
        write_json(out / "failure.json", dict(status="FAILED_STOP_NO_RETRY", error=repr(exc)))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for key in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime", "runtime-sha256"):
        parser.add_argument("--" + key, required=True)
    run(parser.parse_args())
