"""P3 adapter derived from the admitted P1 path. Full zero-update cache collection."""

import argparse
import gc
import hashlib
import importlib
import importlib.util
import json
import os
import shutil
import socket
import sys
import traceback
from pathlib import Path


def need(value, message):
    if not value:
        raise RuntimeError(message)


def clean(path):
    value = Path(path)
    need(value.is_absolute() and ".." not in value.parts, "absolute canonical path")
    need(not any(p.is_symlink() for p in (value, *value.parents)), f"link path: {value}")
    return value


def checked(path, digest):
    data = clean(path).read_bytes()
    need(hashlib.sha256(data).hexdigest() == digest, f"bound bytes: {path}")
    return data


def load_native(record):
    path = clean(record["path"])
    raw = checked(path, record["sha256"])
    need(len(raw) == record["bytes"], "native source size")
    spec = importlib.util.spec_from_file_location("fcsp_bound_native", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def main():
    parser = argparse.ArgumentParser()
    for key in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime", "runtime-sha256"):
        parser.add_argument("--" + key, required=True)
    a = parser.parse_args()
    q = json.loads(checked(a.request, a.request_sha256))
    auth = json.loads(checked(a.authorization, a.authorization_sha256))
    runtime = json.loads(checked(a.runtime, a.runtime_sha256))
    need(q["schema"] == "bcsp-fcsp-p3-execution-v1" and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION"
         and q["execution_authorized"] is False, "request state")
    launch = q["launch"]
    need((a.request, a.authorization, a.runtime) == (
        launch["request"], launch["authorization"], launch["runtime"]), "control paths")
    need(set(auth) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
         and auth["schema"] == "bcsp-fcsp-p3-authorization-v1"
         and auth["request_sha256"] == a.request_sha256
         and auth["explicit_user_authorization"] is True and bool(auth["user_authorization_text"].strip()),
         "explicit execution authorization")
    need(runtime == dict(schema="bcsp-fcsp-p3-runtime-v1", request_sha256=a.request_sha256,
                         authorization_sha256=a.authorization_sha256), "one-way runtime binding")
    need(json.loads(clean(launch["claim"]).read_bytes()) ==
         {"status": "CLAIMED_BEFORE_TMUX", "request_sha256": a.request_sha256}, "single attempt")
    ident = q["identity"]
    need(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         "Linux -I -S -B required")
    need((socket.gethostname(), os.getuid(), str(Path(sys.executable).resolve()), sys.version.split()[0]) ==
         (ident["hostname"], ident["uid"], ident["python_realpath"], ident["python_version"]), "runtime identity")
    root, output = clean(q["model_root"]), clean(q["output"])
    need(Path.cwd().resolve() == clean(ident["project"]) and
         output.parent == clean(ident["project"]) / "logs/cranial_bcsp_fullmamba", "work directory binding")
    parent_args = Path(f"/proc/{os.getppid()}/cmdline").read_bytes().decode().rstrip("\0").split("\0")
    need(parent_args[:4] == ["/usr/bin/timeout", "--signal=TERM", "--kill-after=5s",
                            f"{q['limits']['wall_seconds']}s"], "external wall timeout")
    need(Path(__file__).resolve() == clean(q["entry"]["path"]), "exact entry path")
    need(output.is_dir() and {p.name for p in output.iterdir()} == {"launch.log"}, "fresh launcher output")
    need(shutil.disk_usage(output).free >= q["startup_free_disk_bytes"], "startup disk availability")
    for key, value in q["environment"].items():
        need(os.environ.get(key) == value.replace("<owned_output>", str(output)), f"environment: {key}")
    native = load_native(q["native_entry"])
    native.exact(q["entry"])
    parent = native.bound(q["native_request"])
    need(root == clean(parent["model_root"]), "SPCG donor root")
    source_files = {**parent["implementation"], **q["modules"], "fcsp_native": q["native_entry"]}
    source_conf = {**parent, "implementation": source_files, "entry": q["entry"]}
    index = native.bound(q["cache_index"])
    parent_p1 = native.bound(q["p1_request"])
    completion = native.bound(q["p1_completion"])
    need(parent_p1["identity"] == q["identity"] and parent_p1["checkpoints"] == q["checkpoints"]
         and completion["counts"] == parent_p1["counts"], "exact P1 reuse parent")
    need(len(index["rows"]) == 840, "bounded cache index")
    rows = index["rows"]
    p1 = {(r["fold"], r["split"], r["case_id"]): r["capture"] for r in q["reuse_p1"]}
    need(len(p1) == 4 and set(q["checkpoints"]) == {"G2_C", "G2_D"}, "exact P1 and weight sets")
    returned_p1 = {(r["fold"], r["split"], r["case_id"]): r["capture"] for r in completion["captures"]}
    for key, rec in p1.items():
        need(returned_p1[key] == dict(file=Path(rec["path"]).name, bytes=rec["bytes"], sha256=rec["sha256"]),
             "P1 completion identity")
        native.exact(rec)
    for checkpoint in q["checkpoints"].values():
        native.exact(checkpoint)
    timezone = native.source_module("fcsp_exact_utc", parent["implementation"]["timezone"])
    utc = timezone.ExactUTCReader(timezone.UTC_RESOURCE)
    source_guard = None
    active_policy = None
    try:
        static = native.bound(parent["static_config"])
        scope = native.bound(parent["preflight_scope"])
        helper = native.source_module("fcsp_native_helper", parent["helper"])
        helper._MONITOR = None
        records = helper.source_map(scope)
        for relative, rec in records.items():
            helper.exact(root / relative, rec["sha256"], rec["bytes"])
        helper.exact(root / "base_model.yaml", scope["bindings"]["base_config"]["sha256"])
        for rec in scope["bindings"]["provider"] + scope["bindings"]["environment_metadata"]:
            helper.exact(rec["path"], rec["sha256"], rec["bytes"])
        gpu = [part.strip() for part in helper.smi("uuid,name,driver_version,memory.total,memory.used")[0].split(",")]
        need(gpu[:4] == [ident["gpu_uuid"], ident["gpu_name"], ident["driver_version"],
                         str(ident["nvidia_smi_memory_total_MiB"])] and int(gpu[4]) <= 256, "GPU identity or idle")
        (output / "tmp").mkdir()
        with (output / "worker.pid").open("x") as file:
            file.write(f"{os.getpid()}\n")
        source_guard = native.make_source_guard(source_conf)
        envroot = clean(ident["python_realpath"]).parent.parent
        provider = Path(scope["bindings"]["provider"][0]["path"]).parent.parent
        sys.path[:0] = [str(Path(parent["implementation"]["factory"]["path"]).parent),
                        str(provider), str(envroot / "lib/python3.10/site-packages")]
        helper.namespace_packages(root)
        sys.meta_path.insert(0, helper.FiniteProjectImports(root, records))
        inputs = []
        for row in rows:
            rec = row["input"]
            path = clean(rec["path"])
            case = row["case_id"]
            need(path.parent.as_posix() in q["input_roots"] and path.name == case + "_8192.npz"
                 and "/" not in case and case.startswith("train__") and ".." not in case
                 and row["fold"] in ("C", "D"), "fixed input and output scope")
            inputs.append(str(path))
        targets = [output / f"{row['fold']}__{row['case_id']}.npz" for row in rows]
        policy = native.make_policy(
            helper, [root, envroot, provider, Path(__file__).parent, "/usr/lib",
                     f"/proc/{os.getpid()}", "/dev/null", "/dev/urandom"], output,
            [*inputs, *(v["path"] for v in p1.values())],
            [record["path"] for record in q["checkpoints"].values()], targets, utc, source_guard,
        )
        active_policy = policy
        sys.addaudithook(lambda event, args: active_policy.audit(event, args) if active_policy else None)
        import numpy as np
        import timm
        import torch
        import yaml
        from easydict import EasyDict

        need((torch.__version__, np.__version__, timm.__version__, torch.version.cuda) ==
             (ident["torch_version"], ident["numpy_version"], ident["timm_version"], ident["torch_cuda_version"]),
             "runtime package and CUDA identity")
        need(torch.cuda.is_available() and torch.cuda.device_count() == 1, "single visible CUDA device")
        torch.cuda.set_device(0)
        helper.configure_numeric(torch)
        chamfer = importlib.import_module("extensions.chamfer_dist")
        adapter = importlib.import_module("utils.pointnet2_utils")
        pointnet = importlib.import_module("pointnet2_ops.pointnet2_utils")
        extension = importlib.import_module("pointnet2_ops._ext")
        need(str(Path(pointnet.__file__).resolve()) == scope["bindings"]["provider"][1]["path"]
             and str(Path(extension.__file__).resolve()) == scope["bindings"]["provider"][2]["path"],
             "PointNet2 provider identity")
        helper.check_backend(chamfer, adapter, pointnet)
        transformer = importlib.import_module("models.Transformer_utils")
        model_class = importlib.import_module("models.AdaPoinTr").AdaPoinTr
        need(static["model"] == yaml.safe_load((root / "base_model.yaml").read_text())["model"], "donor config")
        transformer.enable_bcsp_knn()
        factory = native.load_spcg_builder(parent["implementation"])
        for name in ("bcsp_fcsp_head_v1", "bcsp_fcsp_capture_v1", "bcsp_fcsp_p3_capture_v1"):
            core = native.source_module(name, q["modules"][name])
        need(core.COUNTS == q["counts"], "P3 count contract")
        rows, point_files = core.validate_index(index, q["checkpoints"], q["input_roots"], p1)
        for point in point_files:
            native.exact(point)

        def builder(fold):
            label = "G2_" + fold
            run = {**native.FROZEN_MODELS[label], "checkpoint": q["checkpoints"][label]}
            model, evidence = native.build_spcg_model(factory, lambda: model_class(EasyDict(static["model"])),
                                                       run, parent)
            native.validate_model(model, evidence)
            native.load_checkpoint(torch, model, run)
            return model

        budget = native.Budget(q, output, torch, helper)
        budget.sample("start", 0)
        core.run_p3(rows, output, builder, budget.sample, helper.assert_numeric)
        gc.collect()
        budget.sample("final", q["counts"]["donor_forward"])
    except BaseException as exc:
        detail = traceback.format_exc()
        native.emit(output / "p3_error_traceback.json", {"error": repr(exc), "traceback": detail})
        raise
    finally:
        active_policy = None
        if source_guard is not None:
            source_guard.close()
        utc.close()


if __name__ == "__main__":
    main()
