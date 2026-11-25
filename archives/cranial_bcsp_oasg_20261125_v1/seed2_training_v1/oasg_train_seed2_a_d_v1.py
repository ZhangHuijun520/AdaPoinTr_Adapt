"""Fold D A-arm training adapter. Importing this module does not start a run."""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import socket
import sys
import threading


RUN = dict(variant="A", fold="D", seed=2026112102)
COUNTS = dict(batch=8, cases=315, sources=63, epochs=100, batches_per_epoch=39,
              updates=3900, exposures=31200, drop_slots=300)
HISTORICAL_B = "c0fff56ab9209e587e59aaf0fd1a832cfb27623f7caebbb0e0ba83d4e2184361"
P2_SHARED = "0238e3fc6dba4fd74f47c0a7a7fdaf8e19293c3bf257485bf629c110a200487b"
SHARED = "44054d598cee5b192f87e17bfeee7ae2eae7afe9681f15d8eb50a6b6525f1ce8"
P2_SHA = "3cda2082e6de2de2a3b6557211e4d3fd44bb11e663df98c528aa7c4e1142c79b"
ORDER_SHA = "4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720"


BASELINE_SHA = "ff02807e6935ccb37b60ba3e8078f41de67a9010a7a7093b9aec8114c07fd29a"
HEAD = ("a445481a3400d4c8ef6d07af164d64430d9fc2c9ec30a80f0d339bb5a636966b", 2026112402, 7362572)
BASELINE_RUN = dict(RUN, variant="B")


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def authorize(q, request_sha, auth, auth_sha, runtime):
    need(q.get("schema") == "bcsp-oasg-seed2-a-d-train-v1"
         and q.get("status") == "AWAITING_EXPLICIT_USER_AUTHORIZATION"
         and q.get("execution_authorized") is False, "pending frozen request")
    need(q["run"] == RUN and q["counts"] == COUNTS and q["order"]["sha256"] == ORDER_SHA
         and q["p2_receipt"]["sha256"] == P2_SHA and q["shared_initial_state_sha256"] == SHARED
         and q["baseline_receipt"]["sha256"] == BASELINE_SHA
         and tuple(q["initialization"][k] for k in ("sha256", "seed", "bytes")) == HEAD
         and q["boundary"] == dict(retry=False, resume=False, development=False, BNCal=False),
         "frozen OASG B_D science contract")
    need(set(auth) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
         and auth["schema"] == "bcsp-oasg-seed2-a-d-authorization-v1"
         and auth["request_sha256"] == request_sha and auth["explicit_user_authorization"] is True
         and bool(auth["user_authorization_text"].strip()), "separate full-hash execution authorization")
    need(runtime == dict(schema="bcsp-oasg-seed2-a-d-runtime-v1", request_sha256=request_sha,
                         authorization_sha256=auth_sha), "one-way training runtime binding")


def select_training(fold, manifest, order):
    f = fold["folds"]["D"]
    ids, sources = f["train_case_ids"], f["train_sources"]
    need(len(ids) == len(set(ids)) == 315 and len(sources) == len(set(sources)) == 63
         and not set(ids).intersection(f["dev_case_ids"])
         and not set(sources).intersection(f["dev_sources"]), "Fold D training allowlist")
    need(hashlib.sha256(("\n".join(ids) + "\n").encode()).hexdigest() == f["train_allowlist_sha256"],
         "ordered Fold D allowlist hash")
    need(len(manifest) == 420, "complete frozen point manifest")
    index = {r["case_id"]: r for r in manifest}
    need(len(index) == 420 and all(cid in index for cid in ids), "manifest case identity")
    rows = [index[cid] for cid in ids]
    need(Counter(r["source_id"] for r in rows) == Counter({s: 5 for s in sources}), "exact train sources")
    for r in rows:
        cid = r["case_id"]
        need(re.fullmatch(r"train__\d{3}__(bilateral|frontoorbital|parietotemporal|random_[12])", cid)
             and r["point_path"] == f"points/{cid}_8192.npz"
             and r["schema"] == "BCSP-normalized-v1" and r["normalization_source"] == "defective_bbox"
             and r["n_input"] == r["n_target"] == 8192
             and re.fullmatch("[a-f0-9]{64}", r["sha256"]), "fixed train point record")
    need(order["case_ids"] == ids and len(order["epochs"]) == 100, "Fold D order identity")
    for i, row in enumerate(order["epochs"]):
        batches, dropped = row["batches"], row["dropped"]
        flattened = [cid for batch in batches for cid in batch]
        need(row["epoch"] == i and len(batches) == 39 and all(len(b) == 8 for b in batches)
             and len(dropped) == 3 and sorted(flattened + dropped) == sorted(ids), "complete Fold D epoch")
    return rows, sources


def check_admission(r, q):
    need(r["status"] == "FORMAL_P2_READ_ONLY_FREEZE_AUDIT_PASS" and r["identity"] == q["identity"]
         and r["counts"]["counts"] == dict(forward=2, loss=2, backward=2, optimizer_step=0)
         and r["gradient_checks"]["restoration"] is True
         and r["gradient_checks"]["shared"] == P2_SHARED, "audited same-device P2")


def check_cpu_evidence(receipt, q):
    b, a = receipt["models"]
    need(receipt["status"] == "NATIVE_CPU_INITIALIZATION_PAIR_VERIFIED"
         and receipt["identity"] == q["identity"]
         and receipt["entry_sha256"] == q["implementation"]["oasg_entry"]["sha256"]
         and b["run_identity"] == BASELINE_RUN and a["run_identity"] == RUN
         and all(x["shared_initial_state_SHA256"] == SHARED
                 and x["historical_B_initial_state_SHA256"] == HISTORICAL_B
                 and x["shared_tensors"] == 410 and x["artificial_fixture"] is False for x in (b, a))
         and b["training_start_rng"] == a["training_start_rng"]
         and b["training_start_rng"]["torch_cuda"] is None
         and b["initializer_sha256"] is None and a["initializer_sha256"] == q["initialization"]["sha256"],
         "frozen seed-2 CPU initialization pair")
    return a


def check_baseline(receipt, q, expected):
    completion, order = receipt["completion"], receipt["fold_order"]
    model = receipt["model_construction"]
    rng = receipt["training_start_rng"]
    need(receipt["status"] == "FORMAL_POST_TRAINING_READ_ONLY_FREEZE_AUDIT_PASS"
         and receipt["run"] == BASELINE_RUN
         and (receipt["hostname"], receipt["uid"]) == (q["identity"]["hostname"], q["identity"]["uid"])
         and receipt["request_sha256"] == q["paired_B_request_sha256"]
         and receipt["exit_code"] == 0 and receipt["artifact_rehash_agrees"] is True
         and receipt["tmux_absent"] is True and receipt["recorded_pids_not_live"] is True,
         "matching formally frozen seed-2 B_D")
    need(order["byte_identical_to_bound_order"] and order["case_source_drop_counters_verified"]
         and order["sha256"] == q["order"]["sha256"]
         and order["canonical"] == completion["order_sha256"]
         and tuple(order[k] for k in ("steps", "case_count", "sources", "exposures", "drop_slots"))
         == (3900, 315, 63, 31200, 300)
         and tuple(completion[k] for k in ("optimizer_updates", "traversals", "case_exposures"))
         == (3900, 100, 31200)
         and all(completion[k] is False for k in ("bncal_executed", "evaluation_executed", "resume")),
         "B_D batch schedule and exposure binding")
    checkpoints = [a for a in receipt["artifacts"] if Path(a["path"]).name == "ckpt-last.pth"]
    need(checkpoints == [q["paired_B_checkpoint"]]
         and completion["checkpoint_sha256"] == checkpoints[0]["sha256"]
         and model["shared_initial_state_SHA256"] == SHARED
         and model["historical_B_initial_state_SHA256"] == HISTORICAL_B
         and model["shared_tensors"] == 410 and model["initializer_sha256"] is None,
         "B_D checkpoint identity and paired initialization")
    need(rng["run_identity"] == BASELINE_RUN and rng["cuda_initial_seed"] == RUN["seed"]
         and re.fullmatch("[a-f0-9]{64}", rng["rng"]["torch_cuda"])
         and {**rng["rng"], "torch_cuda": None} == expected["training_start_rng"],
         "B_D paired start RNG")
    return rng["rng"]


def record_rng(path, entry, np, torch, expected_rng):
    need(torch.cuda.initial_seed() == RUN["seed"], "native CUDA seed did not reach training")
    rng = entry.rng_fingerprints(np, "cuda:0")
    need(rng == expected_rng, "runtime RNG differs from frozen seed-2 B_D")
    need(re.fullmatch("[a-f0-9]{64}", rng["torch_cuda"]), "missing native CUDA RNG fingerprint")
    with path.open("x", encoding="ascii") as f:
        json.dump(dict(run_identity=RUN, cuda_initial_seed=RUN["seed"], rng=rng), f, allow_nan=False)


def claim_owned_training_output(path):
    path = Path(path)
    files = {"worker.pid", "launcher.pid", "launch.log", "model_construction.json", "p3_resources.jsonl"}
    folders = {"tmp", "cache", "mplconfig", "triton", "hf"}
    need(path.is_dir() and not any(p.is_symlink() for p in (path, *path.parents))
         and {p.name for p in path.iterdir()} == files | folders, "fresh training output members")
    need(all((path / n).is_file() and not (path / n).is_symlink() for n in files)
         and all((path / n).is_dir() and not (path / n).is_symlink() for n in folders)
         and int((path / "worker.pid").read_text()) == os.getpid(), "training output owner")
    return path


def dispatch(q, model, evidence, entry, training, rows, sources, order, resources, helper, knn, emit, device):
    need(str(device) == "cuda:0" and evidence["artificial_fixture"] is False
         and evidence["run_identity"] == RUN and evidence["initializer_sha256"] == HEAD[0]
         and evidence["historical_B_initial_state_SHA256"] == HISTORICAL_B
         and evidence["shared_initial_state_SHA256"] == q["shared_initial_state_sha256"],
         "native A construction and paired initial state")
    dataset = training.BCSPDataset(q["data_root"], rows, sources, 8192)
    lifecycle = entry.bind_training_lifecycle(training)
    # The isolated lifecycle owns the new launcher/monitor evidence layout.
    lifecycle.__globals__["claim_output"] = claim_owned_training_output
    with entry.observe_training(model, RUN, resources, emit) as watched:
        return lifecycle(model, lambda epoch: training.make_loader(dataset, order, epoch),
                         rows, order, q["output"], device=device, numeric_check=helper.assert_numeric,
                         resources=watched, knn_enable=knn, state_fingerprint=helper.state_sha, run_identity=RUN)


class TrainingResources:
    def __init__(self, out, torch, helper, sample, emit, peak, on_first_step):
        self.out, self.torch, self.helper = out, torch, helper
        self.sample, self.emit, self.peak = sample, emit, peak
        self.on_first_step = on_first_step

    def check(self, stage, step=None):
        self.helper.assert_numeric(self.torch)
        reserved = self.torch.cuda.max_memory_reserved(0)
        allocated = self.torch.cuda.max_memory_allocated(0)
        need(max(allocated, reserved) <= self.peak, "PyTorch peak memory cap")
        self.emit(dict(stage=stage, step=step, peak_allocated=allocated, peak_reserved=reserved,
                       **self.sample()))

    def before_step(self, step):
        self.helper.assert_numeric(self.torch)
        if step == 0:
            self.check("before_first_step", step)
            self.on_first_step()

    def after_step(self, step):
        need(self.torch.cuda.max_memory_reserved(0) <= self.peak, "PyTorch peak memory cap")
        if step % 39 == 0:
            self.check("epoch_end", step)

    def before_final(self):
        self.check("before_checkpoint")

    def after_final(self):
        self.check("after_checkpoint")


def launch_training(q, support, receipt, expected_rng):
    out = support.clean(q["output"])
    check_admission(receipt, q)
    output_files = {"launch.log", "launcher.pid"}
    need(out.is_dir() and {p.name for p in out.iterdir()} == output_files, "exclusive launcher output")
    parent = Path(f"/proc/{os.getppid()}")
    command = (parent / "cmdline").read_bytes().decode().rstrip("\0").split("\0")
    need(command[:4] == ["/usr/bin/timeout", "--signal=TERM", "--kill-after=10s",
                         str(q["resources"]["wall_seconds"]) + "s"], "frozen training timeout")
    shell_pid = int((parent / "stat").read_text().rsplit(")", 1)[1].split()[1])
    need(shell_pid == int((out / "launcher.pid").read_text()), "one-shot launcher owner")
    with (out / "worker.pid").open("x", encoding="ascii") as f:
        f.write(str(os.getpid()) + "\n")
    for name in ("tmp", "cache", "mplconfig", "triton", "hf"):
        (out / name).mkdir()
    lock, stop = threading.Lock(), threading.Event()

    def append(name, value):
        with lock, (out / name).open("a", encoding="ascii") as stream:
            stream.write(json.dumps(value, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def sample():
        return support.resources(q, out)

    def watch():
        while not stop.wait(q["resources"]["monitor_interval_seconds"]):
            try:
                append("p3_resources.jsonl", dict(stage="monitor", **sample()))
            except Exception as error:
                try:
                    append("p3_resources.jsonl", dict(stage="monitor_failure", error=repr(error)))
                finally:
                    os.kill(os.getpid(), signal.SIGTERM)
                return

    initial = support.resources(q, out, initial=True)
    append("p3_resources.jsonl", dict(stage="initial", **initial))
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        train_native(q, out, support, sample, append, expected_rng)
    finally:
        stop.set()
        watcher.join(q["resources"]["smi_timeout_seconds"] + 2)
        need(not watcher.is_alive(), "training monitor did not terminate")


def train_native(q, out, support, sample, append, expected_rng):
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

    identity = q["identity"]
    need((torch.__version__, np.__version__, timm.__version__, torch.version.cuda)
         == tuple(identity[k] for k in ("torch_version", "numpy_version", "timm_version", "torch_cuda_version")),
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
                "prime_entry", "prime_seeded_parent", "oasg_head", "oasg_entry", "contract", "training_runtime"):
        loaded[key] = support.source(q["module_names"][key], impl[key])
    fold = json.loads(support.exact(q["fold"]).read_bytes())
    order = json.loads(support.exact(q["order"]).read_bytes())
    manifest = [json.loads(line) for line in support.exact(q["point_manifest"]).read_bytes().splitlines()]
    rows, train_sources = select_training(fold, manifest, order)
    for row in rows:
        path = support.clean(str(Path(q["data_root"]) / row["point_path"]))
        need(support.file_hash(path) == row["sha256"], "frozen train input " + row["case_id"])
    cls = importlib.import_module("models.AdaPoinTr").AdaPoinTr
    knn = importlib.import_module("models.Transformer_utils").enable_bcsp_knn
    entry = loaded["oasg_entry"]
    model, evidence = entry.construct(RUN, lambda: cls(EasyDict(static["model"])), q["initialization"], np=np,
                                      prime=loaded["prime_entry"], seeded=loaded["prime_seeded_parent"],
                                      lqi=loaded["lqi_factory"], scq=loaded["scq_factory"])
    helper.validate_model(model)
    expected = check_cpu_evidence(json.loads(support.exact(q["seed2_cpu_receipt"]).read_bytes()), q)
    need(evidence == {k: v for k, v in expected.items() if k != "training_start_rng"},
         "native construction matches frozen CPU evidence")
    need(entry.rng_fingerprints(np) == expected["training_start_rng"], "constructor CPU RNG")
    with (out / "model_construction.json").open("x", encoding="ascii") as f:
        json.dump(evidence, f, allow_nan=False)
    resources = TrainingResources(out, torch, helper, sample,
                                  lambda row: append("p3_resources.jsonl", row), q["resources"]["torch_peak_bytes"],
                                  lambda: record_rng(out / "training_start_rng.json", entry, np, torch,
                                                     expected_rng))
    dispatch(q, model, evidence, entry, loaded["training_runtime"], rows, train_sources, order, resources,
             helper, knn, lambda row: append("OASG_geometry.jsonl", row), "cuda:0")


def main():
    parser = argparse.ArgumentParser()
    for name in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime",
                 "runtime-sha256", "launcher"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--check", action="store_true")
    a = parser.parse_args()
    need(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         "isolated Linux Python")

    def read(path, digest):
        p = Path(path)
        need(p.is_absolute() and ".." not in p.parts and not any(x.is_symlink() for x in (p, *p.parents)),
             "exact control path")
        with p.open("rb") as f:
            data = f.read(128 * 1024 + 1)
        need(len(data) <= 128 * 1024 and hashlib.sha256(data).hexdigest() == digest, "control SHA256")
        return json.loads(data)

    q = read(a.request, a.request_sha256)
    auth = read(a.authorization, a.authorization_sha256)
    runtime = read(a.runtime, a.runtime_sha256)
    authorize(q, a.request_sha256, auth, a.authorization_sha256, runtime)
    need([a.request, a.authorization, a.runtime] == [q["controls"][k] for k in
         ("request", "authorization", "runtime")], "exact control locations")
    i = q["identity"]
    need(socket.gethostname() == i["hostname"] and os.getuid() == i["uid"]
         and sys.version.split()[0] == i["python_version"] and str(Path(sys.executable).resolve()) == i["python_realpath"],
         "current training identity")
    need(all(os.environ.get(k) == v for k, v in q["environment"].items()), "frozen training environment")
    # Load only the previously audited standard-library P2 support functions.
    item = q["p2_support"]
    path = Path(item["path"])
    need(not any(x.is_symlink() for x in (path, *path.parents)), "P2 support path")
    raw = path.read_bytes()
    need(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"], "P2 support bytes")
    import types
    support = types.ModuleType("oasg_p2_frozen_support")
    exec(compile(raw, str(path), "exec", dont_inherit=True), support.__dict__)
    need(Path.cwd() == support.clean(q["project"]) and Path(__file__) == support.exact(q["worker"])
         and support.exact(q["launcher"]) == support.clean(a.launcher), "training worker/launcher binding")
    out = support.clean(q["output"])
    need(out.parent == Path(q["project"]) / "logs/cranial_bcsp_fullmamba", "owned output root")
    receipt = json.loads(support.exact(q["p2_receipt"]).read_bytes())
    check_admission(receipt, q)
    expected = check_cpu_evidence(json.loads(support.exact(q["seed2_cpu_receipt"]).read_bytes()), q)
    expected_rng = check_baseline(json.loads(support.exact(q["baseline_receipt"]).read_bytes()), q, expected)
    support.exact(q["initialization"])
    if a.check:
        need(not out.exists() and out.parent.is_dir(), "fresh training output")
        sample = support.resources(q, out, initial=True)
        need(sample["disk_free_bytes"] >= q["execution_policy"]["minimum_free_bytes_prelaunch"],
             "frozen minimum startup disk")
        return
    launch_training(q, support, receipt, expected_rng)


if __name__ == "__main__":
    main()
