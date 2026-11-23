"""Fold D B/F admission and startup for the existing PRIME training lifecycle."""

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import socket
import sys


PROJECT = "/home/jovyan/adapointr_work/PoinTr"
SCHEMA = "bcsp-scq-fv-foldD-bf-training-request-v1"
PAIR_STATUS = "FROZEN_SCQ_FV_D_BF_SEED1_NOT_AUTHORIZATION"
AUDIT_STATUS = "FORMAL_SCQ_FV_D_BF_POST_TRAINING_FREEZE_AUDIT_PASS"
P3_STATUS = "SCQ_FV_D_BF_TRAIN_ENTRY_LOCAL_CPU_PASS"
STAGE = "CRANIAL_BCSP_SCQ_FV_D_BF"
SEED = 2026112101
ARMS = ("B", "F")
COUNTS = dict(cases=315, sources=63, batch=8, epochs=100, batches_per_epoch=39, updates=3900, exposures=31200)
STATIC_SHA = "86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647"
ORDER_SHA = "4f68edd55912be0dccfb3d2a1cc72e499d3d499a36aa5f3788550145b3095720"
ORDER_CANONICAL_SHA = "2c9f3e9afb2cfe9ae46c0566bdbced465c64acc2a564654914d2163d74e5e838"
ALLOWLIST_SHA = "682067ea877e8370e5c3d0ac7b2cdd7ae3b2b372a146829b42491899aa1c0aa1"
INIT_SHA = "330e52d581f4122c578cde9787eaa7471137bf1f35eedfb777cb403ad76a6ca7"
PARENT_SHA = "158efb375acb7dc46c40a407c288a9108acdaaa6d89bb94cd31b8ff3eb0ad8d3"
HOST_FIELDS = ("hostname", "gpu_uuid", "driver_version")
PAIR_FIELDS = ("fold", "seed", "identity", "environment", "implementation", "prime_worker", "static_config", "QC",
               "order_plan", "data_root", "initialization", "admission", "preflight_scope", "dependencies", "model_root")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def safe_path(value):
    p = Path(value)
    require(p.is_absolute() and ".." not in p.parts and not any(x.is_symlink() for x in (p, *p.parents)), "bound path")
    require(not {".ssh", ".aws", ".git", ".credentials"}.intersection(p.parts)
            and p.name not in {".env", ".netrc", "auth.json"}, "secret path")
    return p


def raw_record(rec):
    require(set(rec) == {"path", "bytes", "sha256"}, "binding fields")
    path = safe_path(rec["path"])
    require(path.is_file() and path.stat().st_size == rec["bytes"], f"binding size: {path}")
    data = path.read_bytes()
    require(len(data) == rec["bytes"] and hashlib.sha256(data).hexdigest() == rec["sha256"], f"binding SHA256: {path}")
    return data


def run_paths(arm):
    require(arm in ARMS, "registered B/F arm")
    root = PurePosixPath(PROJECT)
    run = f"SCQ_FV_{arm}_D_seed2026112101_train_20261123_v1"
    install = root / "third_party/scq_fv_foldD_bf_training_20261123_v1"
    out = root / "logs/cranial_bcsp_fullmamba" / run
    control = install / f"control_{arm}_D_v1"
    return dict(run_id=run, output=str(out), launch_attempt=str(control / "launch_attempt.json"), launch_contract=dict(
        request_path=str(install / f"{run}_request.json"), authorization_path=str(control / "authorization.json"),
        runtime_path=str(control / "runtime.json"), launcher_path=str(control / "launch_once.sh"),
        tmux_session=f"bcsp_scq_fv_{arm}_D_seed1_20261123_v1", log=str(out / "launch.log"),
        PID=str(out / "worker.pid"), exit_code=str(out / "exit_code.txt"),
        exclusive_single_attempt=True, automatic_retry=False, resume=False))


def check_request(q):
    require(q["schema"] == SCHEMA and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION"
            and q["execution_authorized"] is False and q["stage"] == STAGE and q["variant"] in ARMS
            and q["fold"] == "D" and type(q["seed"]) is int and q["seed"] == SEED
            and q["n_input"] == q["n_output"] == 8192, "fixed Fold D B/F seed and point counts")
    require(q["order_plan"]["sha256"] == ORDER_SHA and q["static_config"]["sha256"] == STATIC_SHA
            and q["initialization"]["sha256"] == INIT_SHA and q["initialization"]["seed"] == SEED,
            "frozen Fold D order, static configuration and initializer")
    require(q["data_root"] == f"{PROJECT}/data/bcsp_geov1_foldd_8192_seed0_v1", "Fold D training data root")
    require(all(q[k] == v for k, v in run_paths(q["variant"]).items()), "registered exclusive run and control paths")


def check_pair(q, pair, predecessors, common, prime_worker):
    require(pair["status"] == PAIR_STATUS and pair["arm_order"] == list(ARMS) and pair["counts"] == COUNTS
            and pair["resources"] == prime_worker.RESOURCES and pair["drop_events"] == 300
            and pair["pair_common_sha256"] == common and pair["audit_sha256"] == prime_worker.ADMISSION_SHA,
            "frozen B/D then F/D pair contract")
    require(all(pair[key] == q[key] for key in PAIR_FIELDS), "same paired inputs, implementation and device")
    want = {"B"} if q["variant"] == "F" else set()
    require(set(predecessors) == want, "F requires exactly one B_D formal predecessor")
    if q["variant"] == "B":
        return
    b = predecessors["B"]
    count_keys = ("updates", "traversals", "exposures", "drop_events", "sources", "training_cases")
    require(b["status"] == AUDIT_STATUS and b["exit_code"] == 0 and b["stable_inventory"] is True
            and b["run_identity"] == dict(variant="B", fold="D", seed=SEED)
            and tuple(b[k] for k in count_keys) == (3900, 100, 31200, 300, 63, 315)
            and all(b[k] is False for k in ("bncal_executed", "development_evaluation_executed", "resume")),
            "successful B_D formal training freeze and exact counts")
    require(b["pair_contract_sha256"] == q["pair_contract"]["sha256"] and b["common_initial_state_SHA256"] == common
            and b["order_file_sha256"] == ORDER_SHA and b["actual_order_canonical_sha256"] == ORDER_CANONICAL_SHA
            and all(b[key] == q["identity"][key] for key in HOST_FIELDS), "paired B_D initialization, order and device")
    checkpoint = b["checkpoint"]
    require(checkpoint["path"] == run_paths("B")["output"] + "/ckpt-last.pth" and checkpoint["bytes"] > 0
            and len(checkpoint["sha256"]) == 64 and all(c in "0123456789abcdef" for c in checkpoint["sha256"]),
            "bound B_D final checkpoint receipt")


def load_parent(record):
    require(record["sha256"] == PARENT_SHA, "frozen PRIME entry origin")
    path = safe_path(record["path"])
    spec = importlib.util.spec_from_file_location("scq_fv_frozen_prime_training", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw_record(record), str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def authorize(qr, ar, rr):
    q, auth, runtime = (json.loads(raw_record(record)) for record in (qr, ar, rr))
    check_request(q)
    launch = q["launch_contract"]
    require(all(record["path"] == launch[f"{name}_path"]
                for name, record in (("request", qr), ("authorization", ar), ("runtime", rr))), "exact control paths")
    require(auth == dict(schema="bcsp-scq-fv-d-bf-training-authorization-v1", request_sha256=qr["sha256"],
                         explicit_user_authorization=True, user_authorization_text=auth.get("user_authorization_text"))
            and isinstance(auth.get("user_authorization_text"), str) and auth["user_authorization_text"].strip(),
            "separate full request SHA256 authorization")
    require(runtime == dict(schema="bcsp-scq-fv-d-bf-training-runtime-v1", request_sha256=qr["sha256"],
                            authorization_sha256=ar["sha256"]), "one-way authorization binding")
    parent = load_parent(q["prime_worker"])
    for key, record in q["implementation"].items():
        if key in parent.PINS:
            require(record["sha256"] == parent.PINS[key], "unchanged " + key)
        parent.exact(record)
    parent.exact({k: q["initialization"][k] for k in ("path", "bytes", "sha256")})
    # Check the historical admission's Fold C label without changing the actual Fold D request or model identity.
    admission, common = parent.validate_admission({**q, "fold": "C"})
    predecessors = {arm: parent.bound(r) for arm, r in q["predecessors"].items()}
    check_pair(q, parent.bound(q["pair_contract"]), predecessors, common, parent)
    p3 = parent.bound(q["P3"])
    require(p3["status"] == P3_STATUS and p3["entry_sha256"] == q["implementation"]["entry"]["sha256"]
            and p3["runtime_sha256"] == q["implementation"]["runtime"]["sha256"]
            and p3["prime_worker_sha256"] == PARENT_SHA and p3["checks"]
            and all(value is True for value in p3["checks"].values()), "Fold D local CPU evidence")
    metadata = parent.source_module("bcsp_training_contract_v1", q["implementation"]["contract"])
    static = metadata.validate_static(parent.bound(q["static_config"]))
    require(static["counts"] == COUNTS and static["resources"] == parent.RESOURCES, "unchanged counts and resources")
    qc = q["QC"]
    selected, fold = metadata.verify_qualified_receipt(parent.bound(qc["qualified_receipt"]), qc["verification"],
                                                       qc["manifests"], qc["fold_binding"], "D", 8192)
    plan = metadata.validate_order(parent.bound(q["order_plan"]), fold["train_case_ids"])
    require(fold["train_allowlist_sha256"] == ALLOWLIST_SHA and metadata.canonical_sha(plan) == ORDER_CANONICAL_SHA,
            "exact Fold D ordered allowlist and canonical batch plan")
    return q, static, selected, fold, plan, admission, common, parent


def run(q, static, selected, fold, plan, admission, common, parent, request_sha):
    ident, impl = q["identity"], q["implementation"]
    out, root = map(safe_path, (q["output"], q["model_root"]))
    require(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
            "Linux -I -S -B required")
    require(socket.gethostname() == ident["hostname"] and os.getuid() == ident["uid"]
            and str(Path(sys.executable).resolve()) == ident["python_realpath"]
            and sys.version.split()[0] == ident["python_version"] and Path.cwd().resolve() == Path(PROJECT)
            and parent.exact(impl["entry"]) == Path(__file__), "current execution identity and source")
    timeout = Path(f"/proc/{os.getppid()}/cmdline").read_bytes().split(b"\0")[:4]
    require(timeout == [b"/usr/bin/timeout", b"--signal=TERM", b"--kill-after=5s", b"86400s"], "external timeout")
    require(json.loads(safe_path(q["launch_attempt"]).read_bytes()) ==
            dict(status="CLAIMED_BEFORE_TMUX", request_sha256=request_sha), "single launch claim")
    for record in q["dependencies"]:
        parent.exact(record)
    allowed = parent.payload_paths(q["data_root"], selected)
    for path, digest in allowed.items():
        require(path.is_file() and parent.sha(path) == digest, f"training payload changed: {path}")
    helper = parent.source_module("scq_training_helper", impl["preflight_helper"])
    helper._MONITOR = None
    budget_parent = parent.source_module("scq_training_budget_parent", impl["budget_parent"])
    native = parent.source_module("scq_native_read_helper", impl["native_helper"])
    cuda_entry = parent.source_module("scq_read_guard_module", impl["cuda_entry"])
    scope = parent.bound(q["preflight_scope"])
    sources = helper.source_map(scope)
    bindings = scope["bindings"]
    for rel, record in sources.items():
        helper.exact(root / rel, record["sha256"], record["bytes"])
    helper.exact(root / "base_model.yaml", bindings["base_config"]["sha256"])
    for record in bindings["provider"] + bindings["environment_metadata"]:
        helper.exact(record["path"], record["sha256"], record["bytes"])
    require(all(os.environ.get(k) == v.replace("<owned_output>", str(out)) for k, v in q["environment"].items()),
            "unchanged numerical environment")
    gpu = [s.strip() for s in helper.smi("uuid,name,driver_version,memory.total,memory.used")[0].split(",")]
    require(gpu[:4] == [ident[k] for k in ("gpu_uuid", "gpu_name", "driver_version")]
            + [str(ident["nvidia_smi_memory_total_MiB"])] and int(gpu[4]) <= 256 and not helper.smi("pid", True),
            "frozen idle GPU")
    require(out.is_dir() and {p.name for p in out.iterdir()} == {"launch.log"}, "fresh run output")
    with (out / "worker.pid").open("x") as stream:
        stream.write(str(os.getpid()) + "\n")
    timezone = parent.source_module("scq_training_timezone", impl["timezone"])
    utc = timezone.ExactUTCReader(timezone.UTC_RESOURCE)
    guard = None
    try:
        init = {k: q["initialization"][k] for k in ("path", "bytes", "sha256")}
        guard = cuda_entry.ExactSCQReads(native.ExactSourceReads(impl),
            [impl[k] for k in ("scq_residual", "scq_factory", "prime_entry", "prime_seeded_parent", "runtime")]
            + [init, q["prime_worker"], impl["entry"]])
        envroot = Path("/opt/conda/envs/adapointr-mamba")
        provider = Path(bindings["provider"][0]["path"]).parent.parent
        entryroot = Path(__file__).parent
        sys.path[:0] = [str(entryroot), str(provider), str(envroot / "lib/python3.10/site-packages")]
        helper.namespace_packages(root)
        sys.meta_path.insert(0, helper.FiniteProjectImports(root, sources))
        (out / "tmp").mkdir()
        roots = [root, entryroot, envroot, provider, "/usr/lib", f"/proc/{os.getpid()}", "/dev/null", "/dev/urandom"]
        base_policy = budget_parent.make_training_policy(helper, roots, out, allowed, utc)

        class Policy(type(base_policy)):
            def check(self, filename, write=False):
                if isinstance(filename, int) or utc.allow(filename, write) or guard.allow(filename, write):
                    return
                return super().check(filename, write)

        sys.addaudithook(Policy(roots, out).audit)
        import numpy as np
        import timm
        import torch
        import yaml
        from easydict import EasyDict

        require((torch.__version__, np.__version__, timm.__version__, torch.version.cuda) ==
                tuple(ident[k] for k in ("torch_version", "numpy_version", "timm_version", "torch_cuda_version")),
                "admitted library versions")
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1, "one native CUDA device")
        torch.cuda.set_device(0)
        helper.configure_numeric(torch)
        chamfer, pn, pointnet, extension = (importlib.import_module(name) for name in
            ("extensions.chamfer_dist", "utils.pointnet2_utils", "pointnet2_ops.pointnet2_utils", "pointnet2_ops._ext"))
        helper.check_backend(chamfer, pn, pointnet)
        require(str(Path(pointnet.__file__).resolve()) == bindings["provider"][1]["path"]
                and str(Path(extension.__file__).resolve()) == bindings["provider"][2]["path"], "frozen provider origins")
        transformer = importlib.import_module("models.Transformer_utils")
        model_cls = importlib.import_module("models.AdaPoinTr").AdaPoinTr
        require(static["model"] == yaml.safe_load((root / "base_model.yaml").read_text())["model"], "same model config")
        for name, key in (("bcsp_mamba_encoder_v1", "encoder"), ("bcsp_p1_model_factory_v1", "factory"),
                          ("bcsp_lqi_decoder_v1", "lqi_decoder"), ("bcsp_lqi_factory_v1", "lqi_factory"),
                          ("bcsp_scq_residual_v1", "scq_residual")):
            parent.source_module(name, impl[key])
        factory = parent.source_module("bcsp_scq_factory_v1", impl["scq_factory"])
        prime = parent.source_module("bcsp_scq_prime_entry_v1", impl["prime_entry"])
        seeded = parent.source_module("bcsp_scq_prime_seeded_parent_v1", impl["prime_seeded_parent"])
        runtime = parent.source_module("scq_prime_training_runtime", impl["runtime"])
        budget = parent.make_budget(budget_parent, static["resources"], out, torch, helper, q, plan)
        parent.dispatch_training(q, selected, fold, plan, factory=factory, model_builder=lambda: model_cls(EasyDict(static["model"])),
            runtime=runtime, prime=prime, seeded=seeded, admission=admission, expected_common=common, helper=helper,
            budget=budget, torch=torch, np=np, knn_enable=transformer.enable_bcsp_knn)
        budget.local()
        payload = [dict(name=p.name, bytes=p.stat().st_size, sha256=parent.sha(p)) for p in sorted(out.iterdir())
                   if p.is_file() and p.name not in ("launch.log", "worker.pid")]
        parent.emit(out / "payload_manifest.json", dict(files=payload))
        return 0
    except BaseException as exc:
        if not (out / "failure.json").exists():
            parent.emit(out / "startup_failure.json", dict(status="FAILED_STOP_NO_RETRY", error=repr(exc)))
        return 1
    finally:
        if guard is not None:
            guard.close()
        utc.close()


def main():
    parser = argparse.ArgumentParser()
    for role in ("request", "authorization", "runtime"):
        parser.add_argument(f"--{role}", required=True)
        parser.add_argument(f"--{role}-sha256", required=True)
    args = vars(parser.parse_args())
    records = [dict(path=str(safe_path(args[role])), bytes=safe_path(args[role]).stat().st_size,
                    sha256=args[f"{role}_sha256"]) for role in ("request", "authorization", "runtime")]
    return run(*authorize(*records), request_sha=records[0]["sha256"])


if __name__ == "__main__":
    sys.exit(main())
