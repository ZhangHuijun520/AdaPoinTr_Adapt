"""Read the three one-way authorization records, then run the frozen OASG P2 scope."""

import argparse
import hashlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading


def require(condition, message):
    if not condition:
        raise ValueError(message)


def clean(path):
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "absolute normalized path required")
    require(not any(p.is_symlink() for p in (path, *path.parents)), "linked path: " + str(path))
    return path


def file_hash(path):
    with path.open("rb") as f:
        digest = hashlib.sha256()
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def exact(record):
    p = clean(record["path"])
    require(p.is_file() and p.stat().st_size == record["bytes"]
            and file_hash(p) == record["sha256"], "file binding: " + str(p))
    return p


def control(path, expected):
    p = clean(path)
    require(p.stat().st_size <= 128 * 1024, "control size cap")
    raw = p.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, "control hash: " + str(p))
    return json.loads(raw)


def source(name, binding):
    p = exact(binding)
    require(name not in sys.modules, "preloaded module: " + name)
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(p.read_bytes(), str(p), "exec", dont_inherit=True), module.__dict__)
    return module


def validate(args):
    q = control(args.request, args.request_sha256)
    a = control(args.authorization, args.authorization_sha256)
    r = control(args.runtime, args.runtime_sha256)
    require(q["schema"] == "bcsp-oasg-p2-cuda-execution-v1"
            and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION"
            and q["execution_authorized"] is False, "frozen pending request")
    require([args.request, args.authorization, args.runtime]
            == [q["controls"][key] for key in ("request", "authorization", "runtime")], "control paths")
    require(set(a) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
            and a["schema"] == "bcsp-oasg-p2-authorization-v1"
            and a["request_sha256"] == args.request_sha256 and a["explicit_user_authorization"] is True
            and bool(a["user_authorization_text"].strip()), "separate explicit execution authorization")
    require(r == dict(schema="bcsp-oasg-p2-runtime-v1", request_sha256=args.request_sha256,
                      authorization_sha256=args.authorization_sha256), "one-way runtime binding")
    require(q["science"] == dict(fold="D", seed=2026112101, arms=["B", "A"], batch=8,
                                forward=2, loss=2, backward=2, optimizer_step=0), "P2 call contract")
    identity = q["identity"]
    require(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
            "isolated Linux Python required")
    require(socket.gethostname() == identity["hostname"] and os.getuid() == identity["uid"]
            and str(Path(sys.executable).resolve()) == identity["python_realpath"]
            and sys.version.split()[0] == identity["python_version"], "runtime identity")
    require(Path.cwd() == clean(q["project"]) and Path(__file__) == exact(q["worker"]), "worker identity")
    require(exact(q["launcher"]) == clean(args.launcher), "launcher identity")
    require(all(os.environ.get(k) == v for k, v in q["environment"].items()), "environment binding")
    return q


def gpu_query(q, fields, compute=False):
    flag = "--query-compute-apps=" if compute else "--query-gpu="
    argv = ["/usr/bin/nvidia-smi", "--id=" + q["identity"]["gpu_uuid"], flag + fields,
            "--format=csv,noheader,nounits"]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=q["resources"]["smi_timeout_seconds"])
    require(result.returncode == 0, "SMI failed: " + result.stderr.strip())
    return result.stdout.strip()


def resources(q, out, initial=False):
    lim, identity = q["resources"], q["identity"]
    line = gpu_query(q, "uuid,name,driver_version,memory.total,memory.used,memory.free")
    fields = [x.strip() for x in line.split(",")]
    require(len(fields) == 6 and fields[:4] == [identity[k] for k in
            ("gpu_uuid", "gpu_name", "driver_version", "total_MiB")], "GPU identity/resource query")
    used, free = map(int, fields[4:])
    if initial:
        require(used <= lim["idle_used_MiB"] and free >= lim["minimum_start_free_MiB"]
                and not gpu_query(q, "pid", compute=True), "GPU startup capacity or occupancy")
    rss = next(int(x.split()[1]) * 1024 for x in Path("/proc/self/status").read_text().splitlines()
               if x.startswith("VmRSS:"))
    vfs = os.statvfs(out if out.exists() else out.parent)
    disk_free = vfs.f_bavail * vfs.f_frsize
    output_bytes = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) if out.exists() else 0
    require(used <= lim["device_used_MiB"] and rss <= lim["rss_bytes"]
            and disk_free >= lim["minimum_disk_bytes"] and output_bytes <= lim["output_bytes"],
            f"resource cap: used_MiB={used}, rss_bytes={rss}, free_disk={disk_free}, output_bytes={output_bytes}")
    return dict(used_MiB=used, free_MiB=free, rss_bytes=rss, disk_free_bytes=disk_free, output_bytes=output_bytes)


def execute(q, out, initial_sample):
    for name in ("tmp", "cache", "mplconfig", "triton", "hf"):
        (out / name).mkdir()
    journal = out / "events.jsonl"
    with journal.open("x", encoding="ascii"):
        pass
    lock = threading.Lock()
    stop = threading.Event()

    def event(payload):
        with lock, journal.open("a", encoding="ascii") as f:
            f.write(json.dumps(payload, allow_nan=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def sample(arm, stage):
        event(dict(kind="resources", arm=arm, stage=stage, **resources(q, out)))

    def watch():
        while not stop.wait(q["resources"]["monitor_interval_seconds"]):
            try:
                sample(None, "monitor")
            except Exception as error:
                try:
                    event(dict(kind="monitor_failure", error=repr(error)))
                finally:
                    os.kill(os.getpid(), signal.SIGTERM)
                return

    event(dict(kind="initial_resources", **initial_sample))
    monitor = threading.Thread(target=watch, daemon=True)
    monitor.start()
    try:
        result = run_models(q, event, sample)
        with (out / "completion.json").open("x", encoding="ascii") as f:
            json.dump(dict(status="P2_NATIVE_ZERO_UPDATE_PASS", counts=result), f, allow_nan=False)
    finally:
        stop.set()
        monitor.join(timeout=q["resources"]["smi_timeout_seconds"] * 2 + 1)
        require(not monitor.is_alive(), "monitor did not terminate")


def run_models(q, event, sample):
    for binding in q["dependencies"] + q["provider"] + list(q["implementation"].values()):
        exact(binding)
    model_root = clean(q["model_root"])
    scope = json.loads(exact(q["parent_scope"]).read_bytes())
    impl = q["implementation"]
    provider_root = str(clean(q["provider"][0]["path"]).parent.parent)
    sys.path[:0] = [provider_root, q["site_packages"]]
    helper = source("oasg_inherited_preflight", impl["preflight_helper"])
    sources = helper.source_map(scope)
    for rel, binding in sources.items():
        exact(dict(binding, path=str(model_root / rel)))
    static = json.loads(exact(q["static_config"]).read_bytes())
    base_config = exact(dict(scope["bindings"]["base_config"], path=str(model_root / "base_model.yaml")))
    helper.namespace_packages(model_root)
    sys.meta_path.insert(0, helper.FiniteProjectImports(model_root, sources))
    import numpy as np
    import timm
    import torch
    import yaml
    from easydict import EasyDict

    identity = q["identity"]
    require((torch.__version__, np.__version__, timm.__version__, torch.version.cuda)
            == tuple(identity[k] for k in ("torch_version", "numpy_version", "timm_version", "torch_cuda_version")),
            "native software versions")
    helper.configure_numeric(torch)
    helper.check_backend(importlib.import_module("extensions.chamfer_dist"),
                         importlib.import_module("utils.pointnet2_utils"),
                         importlib.import_module("pointnet2_ops.pointnet2_utils"))
    require(str(Path(importlib.import_module("pointnet2_ops._ext").__file__).resolve()) == q["provider"][2]["path"],
            "native PointNet2 extension origin")
    require(static["model"] == yaml.safe_load(base_config.read_text())["model"], "frozen model configuration")
    order = json.loads(exact(q["order"]).read_bytes())
    ids = [row["case_id"] for row in q["inputs"]]
    require(order["epochs"][0]["epoch"] == 0 and order["epochs"][0]["batches"][0] == ids, "frozen first batch")
    require(len(set(ids)) == len({row["path"] for row in q["inputs"]}) == 8, "eight distinct inputs")
    for name in ("encoder", "factory", "lqi_decoder", "lqi_factory", "scq_residual", "scq_factory",
                 "prime_entry", "prime_seeded_parent", "oasg_head", "oasg_entry", "oasg_core"):
        source(q["module_names"][name], impl[name])
    core = sys.modules[q["module_names"]["oasg_core"]]
    entry = sys.modules[q["module_names"]["oasg_entry"]]
    torch.cuda.set_device(0)
    importlib.import_module("models.Transformer_utils").enable_bcsp_knn()
    model_type = importlib.import_module("models.AdaPoinTr").AdaPoinTr
    init = q["initialization"]
    exact(init)

    def load_batch():
        x, y = [], []
        for row in q["inputs"]:
            raw = clean(row["path"]).read_bytes()
            require(len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"], "input hash")
            with np.load(io.BytesIO(raw), allow_pickle=False) as f:
                partial, target = f["partial"], f["implant"]
            require(hashlib.sha256(target.tobytes()).hexdigest() == row["target_array_sha256"], "training target identity")
            require(partial.shape == target.shape == (8192, 3) and partial.dtype == target.dtype == np.float32,
                    "input geometry schema")
            x.append(partial)
            y.append(target)
        return ids, torch.from_numpy(np.stack(x)), torch.from_numpy(np.stack(y))

    def construct(run):
        names = q["module_names"]
        model, evidence = entry.construct(run, lambda: model_type(EasyDict(static["model"])),
                                           init if run["variant"] == "A" else None, np=np,
                                           prime=sys.modules[names["prime_entry"]],
                                           seeded=sys.modules[names["prime_seeded_parent"]],
                                           lqi=sys.modules[names["lqi_factory"]], scq=sys.modules[names["scq_factory"]])
        helper.validate_model(model)
        return model, evidence

    def numeric_sample(arm, stage):
        helper.assert_numeric(torch)
        sample(arm, stage)

    return core.run_cuda(ordered_case_ids=ids, load_batch=load_batch, construct=construct,
                         initializer_sha=init["sha256"], emit=event, sample=numeric_sample,
                         peak_limit=q["resources"]["torch_peak_bytes"])


def main():
    parser = argparse.ArgumentParser()
    for key in ("request", "request-sha256", "authorization", "authorization-sha256",
                "runtime", "runtime-sha256", "launcher"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    q = validate(args)
    out = clean(q["output"])
    require(out.parent == Path(q["project"]) / "logs/cranial_bcsp_fullmamba", "exact output parent")
    if args.check:
        require(not out.exists() and out.parent.is_dir(), "fresh output and existing parent required")
        resources(q, out, initial=True)
        return
    require(out.is_dir() and {p.name for p in out.iterdir()} == {"launch.log", "launcher.pid"}
            and int((out / "launcher.pid").read_text()) > 0, "exclusive launch output")
    parent = Path(f"/proc/{os.getppid()}")
    command = (parent / "cmdline").read_bytes().decode().rstrip("\0").split("\0")
    require(command[:4] == ["/usr/bin/timeout", "--signal=TERM", "--kill-after=10s",
                            str(q["resources"]["wall_seconds"]) + "s"], "frozen wall timeout")
    shell_pid = int((parent / "stat").read_text().rsplit(")", 1)[1].split()[1])
    require(shell_pid == int((out / "launcher.pid").read_text()), "worker must descend from launch owner")
    execute(q, out, resources(q, out, initial=True))


if __name__ == "__main__":
    main()
