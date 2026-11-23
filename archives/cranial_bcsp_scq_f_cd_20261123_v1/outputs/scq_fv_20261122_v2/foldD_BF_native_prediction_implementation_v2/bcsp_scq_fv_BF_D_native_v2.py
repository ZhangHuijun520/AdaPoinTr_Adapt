"""SCQ-PRIME: 210 fixed Fold D Native predictions. Import is inert."""
import argparse
from collections import Counter
import gc
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath
import shutil
import socket
import sys
import time

SEED = 2026112101
ARMS = ("B", "F")
TOTAL = 210
LEGACY_SHA = "c74e0da099d170dca3f4d1e002998ad0ce634aae702f0d2e6b324cc469ef5d81"
TIMING = dict(first_cases_per_arm=5, timed_cases_per_arm=100,
              boundary="device_input_ready_to_synchronized_dense_excluding_CPU_transfer")
DEV_ROOT = PurePosixPath("/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1")
MODEL_KEYS = ("encoder", "factory", "lqi_decoder", "lqi_factory", "scq_residual", "scq_factory", "prime_entry",
              "prime_seeded_parent", "timezone", "cuda_entry", "preflight_helper")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def clean(value):
    p = Path(value).absolute()
    require(not any(x.is_symlink() for x in (p, *p.parents)), f"linked path: {p}")
    require(not {".ssh", ".aws", ".credentials", ".git"}.intersection(p.parts)
            and p.name not in (".env", ".netrc", "auth.json"), "secret path")
    return p


def sha(path):
    with clean(path).open("rb") as stream:
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact(record):
    require(set(record) == {"path", "bytes", "sha256"}, "exact record fields")
    p = clean(record["path"])
    require(p.is_file() and p.stat().st_size == record["bytes"] and sha(p) == record["sha256"], f"file identity: {p}")
    return p


def read(record):
    return json.loads(exact(record).read_bytes())


def source(name, record):
    p = exact(record)
    require(name not in sys.modules, f"module already registered: {name}")
    spec = importlib.util.spec_from_file_location(name, p)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        exec(compile(p.read_bytes(), str(p), "exec", dont_inherit=True), module.__dict__)
    except BaseException:
        del sys.modules[name]
        raise
    return module


def identity(arm):
    require(arm in ARMS, "registered arm")
    return dict(variant=arm, fold="D", seed=SEED)


def validate_scope(q, scope):
    require(q["schema"] == "bcsp-scq-fv-BF-D-native-prediction-v1"
            and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["execution_authorized"] is False,
            "pending PRIME request")
    require((q["fold"], q["seed"], q["n_input"], q["n_output"], q["batch_size"], q["forward_budget"])
            == ("D", SEED, 8192, 8192, 1, TOTAL), "fixed inference budget")
    require(scope["arm_order"] == list(ARMS) and scope["per_arm"] == 105 and scope["scoring"] is False
            and q["no_calls"] == scope["no_calls"] == dict(optimizer_steps=0, backward=0, loss=0, BNCal=0, warmup=0, TTA=0),
            "Native only")
    for key in ("identity", "implementation", "dependencies", "static_config", "preflight_scope", "model_root",
                "initialization", "environment", "limits", "source_manifest", "fold_binding", "model_records"):
        require(q[key] == scope[key], f"frozen scope binding: {key}")
    require(set(q["implementation"]) == set(MODEL_KEYS), "exact implementation set")
    require(q["input_index"] == scope["input_index"] and q["training_audits"] == scope["training_audits"]
            and q["legacy_helpers"] == scope["legacy_helpers"] and q["legacy_helpers"]["sha256"] == LEGACY_SHA
            and q["timing"] == scope["timing"] == TIMING, "frozen index, audits, helper and timing")
    output = PurePosixPath(scope["candidate_output"])
    install = PurePosixPath(scope["candidate_install_dir"])
    control = install / "control_v1"
    require(q["output"] == str(output) and q["launch_attempt"] == str(control / "launch_attempt.json"),
            "frozen output and claim")
    require(q["launch_contract"] == dict(
        request_path=str(install / "SCQ_FV_BF_D_native_execution_request_v1.json"),
        authorization=str(control / "authorization.json"),
        runtime=str(control / "runtime.json"), launcher=str(control / "launch_once.sh"),
        tmux_session=scope["tmux_session"], log=str(output / "launch.log"),
        PID=str(output / "worker.pid"), exit_code=str(output / "exit_code.txt"),
        single_attempt=True, automatic_retry=False,
    ), "frozen launch map")


def authorizations(qr, ar, rr):
    a, r = read(ar), read(rr)
    require(set(a) == {"schema", "request_sha256", "explicit_user_authorization", "user_authorization_text"}
            and a["schema"] == "bcsp-development-authorization-v1" and a["request_sha256"] == qr["sha256"]
            and a["explicit_user_authorization"] is True and bool(a["user_authorization_text"].strip()),
            "explicit request authorization")
    require(r == dict(schema="bcsp-development-runtime-v1", request_sha256=qr["sha256"],
                      authorization_sha256=ar["sha256"]), "one-way runtime authorization")


def validate_index(index, binding, manifest):
    require((index["fold"], index["seed"], index["arms"], index["cases"], index["sources"])
            == ("D", SEED, list(ARMS), 105, 21), "fixed development index")
    rows = index["inputs"]
    fold = binding["folds"]["D"]
    ids = [r["case_id"] for r in rows]
    require(ids == fold["dev_case_ids"] and len(ids) == len(set(ids)) == 105, "ordered 105 development cases")
    require(not set(ids) & set(fold["train_case_ids"]) and not set(fold["dev_sources"]) & set(fold["train_sources"]),
            "training/development separation")
    source_counts = Counter(r["source_id"] for r in rows)
    require(set(source_counts) == set(fold["dev_sources"]) and len(source_counts) == 21
            and set(source_counts.values()) == {5}, "21 sources and five defects per source")
    original = {r["case_id"]: r for r in manifest}
    require(len(original) == len(manifest) == 420, "original manifest identity")
    for row in rows:
        cid = row["case_id"]
        m = original[cid]
        rel = PurePosixPath("points") / (cid + "_8192.npz")
        require((row["n_input"], row["n_output"], m["n_input"], m["n_target"]) == (8192, 8192, 8192, 8192)
                and rel.as_posix() == m["point_path"] and row["input"]["path"] == str(DEV_ROOT / rel)
                and row["input"]["sha256"] == m["sha256"], f"development input identity: {cid}")
        require(cid == f"train__{row['source_id'].removeprefix('train:')}__{row['defect_type']}"
                and row["source_id"] == m["source_id"]
                and row["defect_type"] in {"bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"},
                f"case metadata: {cid}")
        norm = row["normalization"]
        require(row["normalization_source"] == m["normalization_source"] == "defective_bbox"
                and norm == m["normalization"] and len(norm["center"]) == 3 and all(map(math.isfinite, norm["center"]))
                and math.isfinite(norm["scale"]) and norm["scale"] > 0, f"D-only normalization: {cid}")
    return rows


def training_evidence(q):
    require(set(q["training_audits"]) == set(q["model_records"]) == set(ARMS), "both audited models")
    audits = {}
    for arm in ARMS:
        pin = q["model_records"][arm]
        rec = q["training_audits"][arm]
        require(rec["sha256"] == pin["training_audit_SHA256"], "audit byte binding")
        a = read(rec)
        require(a["status"] == "FORMAL_SCQ_FV_D_BF_POST_TRAINING_FREEZE_AUDIT_PASS" and a["exit_code"] == 0
                and a["stable_inventory"] and a["request_sha256"] == pin["training_request_SHA256"]
                and a["run_identity"] == pin["run_identity"] == identity(arm) and a["checkpoint"] == pin["checkpoint"],
                f"{arm} frozen weight identity")
        require(all(a[k] == q["identity"][k] for k in ("hostname", "gpu_uuid", "driver_version"))
                and (a["updates"], a["traversals"], a["exposures"], a["drop_events"]) == (3900, 100, 31200, 300)
                and not any(a[k] for k in ("bncal_executed", "development_evaluation_executed", "resume")), f"{arm} training contract")
        audits[arm] = a
    require(all(len({a[key] for a in audits.values()}) == 1 for key in
                ("common_initial_state_SHA256", "pair_contract_sha256", "actual_order_canonical_sha256")), "two-arm paired training")
    pair = audits["F"]["pairing"]
    require(pair["matching_batches"] == 3900 and pair["common_initial_state_equal"] is True
            and pair["exposure_histograms_equal"] is True and pair["same_gpu_driver"] is True
            and pair["B_D_receipt_sha256"] == q["training_audits"]["B"]["sha256"]
            and pair["B_D_checkpoint_sha256"] == audits["B"]["checkpoint"]["sha256"], "formal Fold D pair verification")
    return audits


def load_checkpoint(torch, model, record, arm):
    data = torch.load(exact(record), map_location="cpu", weights_only=True)
    require(isinstance(data, dict) and data.get("scq_prime_run_identity") == identity(arm)
            and data.get("stage") == "BCSP_INPUT_DENSITY_V1" and data.get("epoch") == 99
            and data.get("updates") == 3900 and isinstance(data.get("base_model"), dict), f"{arm} checkpoint payload identity")
    model.load_state_dict(data["base_model"], strict=True)


class ForwardBudget:
    def __init__(self, ids):
        require(len(ids) == len(set(ids)) == 105, "exact 105-case call schedule")
        self.schedule = [(arm, cid) for arm in ARMS for cid in ids]
        self.attempts = 0

    def claim(self, arm, cid):
        require(self.attempts < TOTAL and self.schedule[self.attempts] == (arm, cid), "forward limit or frozen call order")
        self.attempts += 1
        return self.attempts

    def finish(self, successful):
        require(self.attempts == successful == TOTAL, "exactly 210 successful native predictions")


def prediction_payload(np, model, arm, coarse, dense):
    arrays = dict(coarse=coarse[0], prediction=dense[0])
    inner = model.base_model
    if arm == "B":
        require(not hasattr(inner, "scq"), "B has no SCQ head")
        return arrays
    require(inner.scq.variant == arm and isinstance(inner._scq_last_info, dict), "actual arm diagnostic")
    info = inner._scq_last_info
    inner._scq_last_info = None
    raw, used, delta = (info[key].detach().cpu().numpy() for key in ("Q0", "Qused", "delta"))
    require(raw.shape == used.shape == delta.shape == coarse.shape == (1, 256, 3)
            and raw.dtype == delta.dtype == used.dtype == np.float32
            and np.isfinite(raw).all() and np.isfinite(delta).all()
            and np.array_equal(used, coarse) and np.allclose(raw + delta, used, rtol=2e-6, atol=2e-7), "Qraw/Qused/delta consistency")
    arrays.update(Qraw=raw[0].copy(), Qused=used[0].copy(), delta=delta[0].copy())
    return arrays


def timed_native_forward(torch, model, x, synchronize, clock):
    require(not model.training and not any(m.training for m in model.modules()), "eval mode required")
    with torch.inference_mode():
        synchronize()
        start = clock()
        result = model(x)
        synchronize()
        elapsed_ns = clock() - start
        require(elapsed_ns > 0, "positive synchronized latency")
        require(isinstance(result, (tuple, list)) and len(result) == 2, "native eval output tuple")
        coarse, dense = result
        for tensor, shape in ((coarse, (1, 256, 3)), (dense, (1, 8192, 3))):
            require(tuple(tensor.shape) == shape and tensor.dtype == torch.float32
                    and bool(torch.isfinite(tensor).all()), "finite FP32 prediction")
        return coarse.detach().cpu().numpy().copy(), dense.detach().cpu().numpy().copy(), elapsed_ns


def latency_summary(np, timings):
    warmup = TIMING["first_cases_per_arm"]
    require(len(timings) == warmup + TIMING["timed_cases_per_arm"] and all(t > 0 for t in timings),
            "105 positive timings with first five excluded")
    p50, p95 = np.percentile(timings[warmup:], [50, 95]) / 1e6
    return dict(P50_ms=float(p50), P95_ms=float(p95), warmup=warmup, measured=len(timings)-warmup)


def predict_case(torch, np, legacy, model, x, arm, row, budget, journal, synchronize, clock):
    cid = row["case_id"]
    call = budget.claim(arm, cid)
    legacy.append_event(journal, dict(forward_index=call, run=f"{arm}_D", case_id=cid, status="CLAIMED_BEFORE_FORWARD"))
    coarse, dense, elapsed_ns = timed_native_forward(torch, model, x, synchronize, clock)
    arrays = prediction_payload(np, model, arm, coarse, dense)
    return call, coarse, dense, arrays, elapsed_ns


def run_predictions(torch, np, helper, legacy, q, rows, out, monitor, build, audits):
    budget = ForwardBudget([r["case_id"] for r in rows])
    states, files = [], []
    manifest, journal, geometry = [out / name for name in
                                  ("inference_manifest.jsonl", "forward_attempts.jsonl", "geometry_summary.jsonl")]
    for path in (manifest, journal, geometry):
        path.open("x").close()
    saved = 0
    try:
        for arm in ARMS:
            model, construction = build(arm)
            require(construction["run_identity"] == identity(arm)
                    and construction["common_initial_state_SHA256"] == audits[arm]["common_initial_state_SHA256"],
                    "reproduced model construction")
            helper.validate_model(model)
            head = construction["scq"]
            require(head["variant"] == arm and head["new_parameters"] == (0 if arm == "B" else 693507)
                    and head["total_parameters"] == (39903169 if arm == "B" else 40596676)
                    and head["initialization_sha256"] == (None if arm == "B" else q["initialization"]["sha256"]), "actual SCQ construction")
            checkpoint = q["model_records"][arm]["checkpoint"]
            load_checkpoint(torch, model, checkpoint, arm)
            model.eval().to("cuda:0")
            model.enable_full_instrumentation(False)
            require(all(p.dtype == torch.float32 for p in model.parameters()), "FP32 checkpoint model")
            torch.cuda.synchronize()
            torch.cuda.reset_peak_memory_stats(0)
            state_before = helper.state_sha(model)
            rng_before = legacy.rng_state(torch, np, helper, True)
            monitor.sample(f"model_start:{arm}_D", budget.attempts)
            timings = []
            for case_offset, row in enumerate(rows):
                cid = row["case_id"]
                label = f"{arm}_D"
                helper.assert_numeric(torch)
                monitor.sample("before_forward", budget.attempts)
                x = torch.from_numpy(legacy.load_partial(np, row)).unsqueeze(0).to("cuda:0")
                call, coarse, dense, arrays, elapsed_ns = predict_case(
                    torch, np, legacy, model, x, arm, row, budget, journal,
                    torch.cuda.synchronize, time.perf_counter_ns)
                timings.append(elapsed_ns)
                path = out / f"predictions/{label}__{cid}.npz"
                with path.open("xb") as stream:
                    np.savez_compressed(stream, **arrays)
                files.append(path)
                saved += 1
                stats = legacy.geometry_summary(np, coarse, dense)
                if arm != "B":
                    stats["Qraw"] = legacy.geometry_summary(np, arrays["Qraw"][None], dense)["coarse"]
                    stats["delta_mean_norm"] = float(np.linalg.norm(arrays["delta"], axis=-1).mean())
                    stats["delta_max_norm"] = float(np.linalg.norm(arrays["delta"], axis=-1).max())
                legacy.append_event(geometry, dict(run=label, case_id=cid, **stats))
                legacy.append_event(manifest, dict(run=label, variant=arm, case_id=cid, source_id=row["source_id"],
                    fold="D", seed=SEED, n_input=8192, n_output=8192, input_sha256=row["input"]["sha256"],
                    checkpoint_sha256=checkpoint["sha256"], normalization=row["normalization"],
                    diagnostic_fields=sorted(arrays), forward_index=call,
                    synchronized_forward_ns=elapsed_ns, timing_warmup=case_offset < TIMING["first_cases_per_arm"],
                    prediction=dict(name=path.relative_to(out).as_posix(), bytes=path.stat().st_size, sha256=sha(path))))
                del x, coarse, dense, arrays
                helper.assert_numeric(torch)
                monitor.sample("after_forward", budget.attempts)
            state_after = helper.state_sha(model)
            rng_after = legacy.rng_state(torch, np, helper, True)
            require(state_before == state_after and rng_before == rng_after, f"{arm} parameter/buffer/RNG state")
            states.append(dict(run=f"{arm}_D", identity=identity(arm), forwards=len(rows), state_before=state_before,
                               state_after=state_after, RNG_before=rng_before, RNG_after=rng_after,
                               efficiency=dict(**latency_summary(np, timings),
                                   peak_allocated_bytes=int(torch.cuda.max_memory_allocated(0)),
                                   peak_reserved_bytes=int(torch.cuda.max_memory_reserved(0)))))
            del model
            gc.collect()
            torch.cuda.empty_cache()
        budget.finish(saved)
        monitor.sample("all_complete", budget.attempts)
        return files, [manifest, journal, geometry], states
    except BaseException as exc:
        legacy.emit(out / "failure.json", dict(status="FAILED_STOP_NO_RETRY", forward_attempts=budget.attempts,
                    saved_predictions=saved, error=repr(exc)))
        raise


def main():
    parser = argparse.ArgumentParser()
    for key in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime", "runtime-sha256"):
        parser.add_argument("--" + key, required=True)
    args = vars(parser.parse_args())
    def rec(key):
        p = clean(args[key])
        return dict(path=str(p), bytes=p.stat().st_size, sha256=args[key + "_sha256"])
    qr = rec("request")
    q = read(qr)
    authorizations(qr, rec("authorization"), rec("runtime"))
    scope = read(q["scope"])
    validate_scope(q, scope)
    launch = q["launch_contract"]
    require(qr["path"] == launch["request_path"] and args["authorization"] == launch["authorization"]
            and args["runtime"] == launch["runtime"], "exact control paths")
    gpu = q["identity"]
    out, root = clean(q["output"]), clean(q["model_root"])
    require(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode, "Linux -I -S -B")
    require(socket.gethostname() == gpu["hostname"] and os.getuid() == gpu["uid"]
            and str(Path(sys.executable).resolve()) == gpu["python_realpath"] and sys.version.split()[0] == gpu["python_version"],
            "current platform identity")
    require(Path.cwd().resolve() == Path(gpu["project"]) and out.parent == Path(gpu["project"]) / "logs/cranial_bcsp_fullmamba"
            and Path(__file__).absolute() == exact(q["entry"]), "project and entry origin")
    parent = Path(f"/proc/{os.getppid()}/cmdline").read_bytes().split(b"\0")
    require(parent[:4] == [b"/usr/bin/timeout", b"--signal=TERM", b"--kill-after=5s", b"7200s"], "external timeout")
    require(json.loads(clean(q["launch_attempt"]).read_bytes()) == dict(status="CLAIMED_BEFORE_TMUX", request_sha256=qr["sha256"]),
            "single launch claim")
    p3 = read(q["P3"])
    require(p3["status"] == "LOCAL_SCQ_FV_BF_D_NATIVE_P3_PASS" and p3["entry_sha256"] == q["entry"]["sha256"]
            and p3["checks"] and all(p3["checks"].values()) and p3["artificial_forwards"] == TOTAL
            and p3["real_forward_calls"] == 0, "local P3")
    rows = validate_index(read(q["input_index"]), read(q["fold_binding"]),
        [json.loads(line) for line in exact(q["source_manifest"]).read_bytes().splitlines()])
    audits = training_evidence(q)
    impl = q["implementation"]
    for record in [*q["dependencies"], *impl.values(), {k:q["initialization"][k] for k in ("path", "bytes", "sha256")}]:
        exact(record)
    for row in rows:
        exact(row["input"])
    legacy = source("scq_prime_native_legacy_helpers", q["legacy_helpers"])
    helper = source("scq_prime_native_helper", impl["preflight_helper"])
    helper._MONITOR = None
    frozen = read(q["preflight_scope"])
    sources = helper.source_map(frozen)
    for rel, r in sources.items():
        helper.exact(root / rel, r["sha256"], r["bytes"])
    bindings = frozen["bindings"]
    helper.exact(root / "base_model.yaml", bindings["base_config"]["sha256"])
    for r in bindings["provider"] + bindings["environment_metadata"]:
        helper.exact(r["path"], r["sha256"], r["bytes"])
    for key, val in q["environment"].items():
        require(os.environ.get(key) == val.replace("<owned_output>", str(out)), f"environment: {key}")
    smi = [x.strip() for x in helper.smi("uuid,name,driver_version,memory.total,memory.used")[0].split(",")]
    require(smi[:4] == [gpu["gpu_uuid"], gpu["gpu_name"], gpu["driver_version"], str(gpu["nvidia_smi_memory_total_MiB"])]
            and int(smi[4]) <= 256 and not helper.smi("pid", True), "same idle GPU")
    require(out.is_dir() and {p.name for p in out.iterdir()} == {"launch.log"}, "fresh launcher output")
    (out / "predictions").mkdir()
    (out / "tmp").mkdir()
    with (out / "worker.pid").open("x") as stream:
        stream.write(str(os.getpid()) + "\n")
    utc_module = source("scq_prime_native_utc", impl["timezone"])
    utc = utc_module.ExactUTCReader(utc_module.UTC_RESOURCE)
    guard = None
    try:
        reader = source("scq_prime_exact_reader", impl["cuda_entry"])
        guard = reader.ExactSCQReads(legacy.ExactSourceReads(impl),
            [impl[k] for k in ("scq_residual", "scq_factory", "prime_entry", "prime_seeded_parent")]
            + [{k:q["initialization"][k] for k in ("path", "bytes", "sha256")}])
        provider = Path(bindings["provider"][0]["path"]).parent.parent
        envroot = Path(gpu["python_realpath"]).parent.parent
        static = read(q["static_config"])
        sys.path[:0] = [str(provider), str(envroot / "lib/python3.10/site-packages")]
        helper.namespace_packages(root)
        sys.meta_path.insert(0, helper.FiniteProjectImports(root, sources))
        allowed = [out / f"predictions/{arm}_D__{row['case_id']}.npz" for arm in ARMS for row in rows]
        policy = legacy.make_policy(helper, [root, envroot, provider, Path(__file__).parent, "/usr/lib",
            f"/proc/{os.getpid()}", "/dev/null", "/dev/urandom"], out, [r["input"]["path"] for r in rows],
            [q["model_records"][a]["checkpoint"]["path"] for a in ARMS], allowed, utc, guard)
        sys.addaudithook(policy.audit)
        import numpy as np
        import timm
        import torch
        import yaml
        from easydict import EasyDict
        require((torch.__version__, np.__version__, timm.__version__, torch.version.cuda) ==
                (gpu["torch_version"], gpu["numpy_version"], gpu["timm_version"], gpu["torch_cuda_version"]), "admitted dependencies")
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1, "one native CUDA device")
        torch.cuda.set_device(0)
        helper.configure_numeric(torch)
        chamfer, adapter, pointnet, extension = (importlib.import_module(k) for k in
            ("extensions.chamfer_dist", "utils.pointnet2_utils", "pointnet2_ops.pointnet2_utils", "pointnet2_ops._ext"))
        require(str(Path(pointnet.__file__).resolve()) == bindings["provider"][1]["path"]
                and str(Path(extension.__file__).resolve()) == bindings["provider"][2]["path"], "PointNet2 origins")
        helper.check_backend(chamfer, adapter, pointnet)
        model_class = importlib.import_module("models.AdaPoinTr").AdaPoinTr
        importlib.import_module("models.Transformer_utils").enable_bcsp_knn()
        require(static["model"] == yaml.safe_load((root / "base_model.yaml").read_text())["model"], "unchanged model config")
        for name, key in (("bcsp_mamba_encoder_v1","encoder"), ("bcsp_p1_model_factory_v1","factory"),
                          ("bcsp_lqi_decoder_v1","lqi_decoder"), ("bcsp_lqi_factory_v1","lqi_factory"),
                          ("bcsp_scq_residual_v1","scq_residual")):
            source(name, impl[key])
        scq = source("bcsp_scq_factory_v1", impl["scq_factory"])
        prime = source("bcsp_scq_prime_entry_v1", impl["prime_entry"])
        seeded = source("bcsp_scq_prime_seeded_parent_v1", impl["prime_seeded_parent"])
        def build(arm):
            return prime.construct(identity(arm), lambda: model_class(EasyDict(static["model"])),
                None if arm == "B" else q["initialization"], torch=torch, np=np, parent=seeded, lqi=scq.parent, scq=scq)
        monitor = legacy.Budget(q, out, torch, helper)
        files, extras, states = run_predictions(torch, np, helper, legacy, q, rows, out, monitor, build, audits)
        done = out / "inference_complete.json"
        legacy.emit(done, dict(status="SCQ_FV_BF_D_NATIVE_210_COMPLETE", forwards=TOTAL, request_sha256=qr["sha256"],
                              models=states, training_updates=0, BNCal=0, loss=0, backward=0))
        archive = legacy.pack(out, files + extras + [done, monitor.path])
        require(sum(p.stat().st_size for p in out.rglob("*") if p.is_file()) <= q["limits"]["output_bytes"]
                and time.monotonic() - monitor.start <= q["limits"]["wall_seconds"]
                and shutil.disk_usage(out).free >= q["limits"]["minimum_free_disk_bytes"], "post-archive resource limits")
        legacy.emit(out / "completion.json", dict(status="PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT", forwards=TOTAL,
                                                 archive=archive, request_sha256=qr["sha256"]))
    except BaseException as exc:
        if not (out / "failure.json").exists():
            legacy.emit(out / "failure.json", dict(status="FAILED_STOP_NO_RETRY", error=repr(exc)))
        raise
    finally:
        if guard is not None:
            guard.close()
        utc.close()


if __name__ == "__main__":
    main()
