"""Authorized first CISC reference run using the admitted CISC construction."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
from types import ModuleType


RUN = dict(variant="R", fold="D", seed=2026112601)
COUNTS = dict(batch=8, cases=315, sources=63, epochs=100, batches_per_epoch=39,
              updates=3900, exposures=31200, drop_slots=300)
RUNTIME_SHA = "09973e15bfebe820f39bed550b809e814a4b14c022b22863946ad25f3c5dd292"


def need(ok, message):
    if not ok:
        raise ValueError(message)


def authorize(q, request_sha, auth, auth_sha, runtime):
    need(q["schema"] == "bcsp-cisc-p2-r-d-train-v1" and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION"
         and q["execution_authorized"] is False and q["run"] == RUN and q["counts"] == COUNTS
         and q["boundary"] == dict(retry=False, resume=False, development=False, BNCal=False),
         "exact pending R_D contract")
    need(set(auth) == {"request_sha256", "explicit_user_authorization", "authorization_text"}
         and auth["request_sha256"] == request_sha and auth["explicit_user_authorization"] is True
         and isinstance(auth["authorization_text"], str) and auth["authorization_text"].strip(),
         "explicit R_D full-hash authorization")
    need(runtime == dict(request_sha256=request_sha, authorization_sha256=auth_sha),
         "R_D runtime binding")


def check_admission(receipt, q):
    need(receipt["status"] == "FORMAL_CISC_P1_CUDA_POST_FREEZE_AUDIT_PASS"
         and receipt["request_sha256"] == q["admission_request_sha256"]
         and receipt["host"] == q["identity"]["hostname"]
         and receipt["shared_initial_sha256"] == q["shared_initial_sha256"]
         and receipt["counts"] == dict(validation_forward=6, loss=3, backward=3, optimizer_step=0, timing_forward=75),
         "frozen CISC admission")


def verify_common(q, common):
    need(common["runs"][0] == RUN and common["arm_order"] == ["R", "U", "I"]
         and common["counts"] == COUNTS and common["identity"] == q["identity"]
         and all(common[k] == q[k] for k in ("order", "fold", "point_manifest", "static_config",
                                              "coarse_initializer", "shared_initial_sha256", "seeds")),
         "first arm must match common CISC contract")


def check_run(**run):
    need(run == RUN, "only first CISC R_D may train")


def bind_lifecycle(training, oasg, claim):
    original = training.train_lifecycle
    path, tree = oasg._source(original, RUNTIME_SHA)
    [node] = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "train_lifecycle"]
    guard = node.body[1]
    old = """require(set(run_identity) == {'variant', 'fold', 'seed'} and run_identity['variant'] in ('B', 'F', 'S')
            and run_identity['fold'] in ('C', 'D') and type(run_identity['seed']) is int
            and run_identity['seed'] in (2026112101, 2026112102), 'SCQ-PRIME runtime identity')"""
    need(node.lineno == original.__code__.co_firstlineno and oasg._same_statement(guard, old),
         "exact inherited optimizer loop identity guard")
    node.body[1] = ast.copy_location(ast.parse("_cisc_run(**run_identity)").body[0], guard)
    return oasg._compile(node, path, {**original.__globals__, "_cisc_run": check_run, "claim_output": claim})


def initial_digest(model, parent):
    fingerprints = {name: parent.tensor_sha(value) for name, value in model.state_dict().items()}
    return hashlib.sha256(json.dumps(fingerprints, sort_keys=True).encode()).hexdigest()


def train_native(q, out, support, sample, append, old):
    import importlib
    import random

    p1 = support.source("cisc_p1_model_builder", q["cisc_p1_worker"])
    native = support.source("cisc_reference_model_loader", q["native_model_loader"])
    torch, np, helper, _ = native.prepare_models(q, support)
    support.source("bcsp_cisc_head_v1", q["cisc_sources"]["head"])
    cisc = support.source("bcsp_cisc_entry_v1", q["cisc_sources"]["entry"])
    impl, names = q["implementation"], q["module_names"]
    support.source(names["contract"], impl["contract"])
    training = support.source(names["training_runtime"], impl["training_runtime"])
    fold = json.loads(support.exact(q["fold"]).read_bytes())
    order = json.loads(support.exact(q["order"]).read_bytes())
    records = [json.loads(line) for line in support.exact(q["point_manifest"]).read_bytes().splitlines()]
    rows, sources = old.select_training(fold, records, order)
    for row in rows:
        path = support.clean(str(Path(q["data_root"]) / row["point_path"]))
        need(support.file_hash(path) == row["sha256"], "training input hash " + row["case_id"])
    model = p1.build_arm(q, support, torch, helper, cisc, "R")
    parent = sys.modules[names["prime_seeded_parent"]]
    digest = initial_digest(model, parent)
    need(digest == q["shared_initial_sha256"], "P1 and R_D native common tensor identity")
    random.seed(RUN["seed"])
    np.random.seed(RUN["seed"])
    torch.manual_seed(RUN["seed"])
    train_rng = {
        "python": hashlib.sha256(repr(random.getstate()).encode()).hexdigest(),
        "numpy": hashlib.sha256(np.random.get_state()[1].tobytes()).hexdigest(),
        "torch_cpu": parent.tensor_sha(torch.random.get_rng_state()),
        "torch_cuda": parent.tensor_sha(torch.cuda.get_rng_state(0)),
    }
    evidence = dict(run_identity=RUN, shared_initial_sha256=digest, starting_rng=train_rng,
                    total_parameters=sum(p.numel() for p in model.parameters()),
                    auxiliary_loss_weight=0.0, labels_loaded=False)
    with (out / "model_construction.json").open("x", encoding="ascii") as stream:
        json.dump(evidence, stream, allow_nan=False)
    resources = old.TrainingResources(out, torch, helper, sample,
                                      lambda row: append("p3_resources.jsonl", row), q["resources"]["torch_peak_bytes"])
    dataset = training.BCSPDataset(q["data_root"], rows, sources, 8192)
    oasg = sys.modules[names["oasg_entry"]]
    lifecycle = bind_lifecycle(training, oasg, old.claim_owned_training_output)
    knn = importlib.import_module("models.Transformer_utils").enable_bcsp_knn
    # This uses the existing observer only. Its historical arm identity is
    # internal to the choice of hooks and never reaches the training lifecycle.
    with oasg.observe_training(model, oasg.identity("A", "D", oasg.TRAIN_SEED),
                               resources, lambda row: append("OASG_geometry.jsonl", row)) as observer:
        return lifecycle(model, lambda epoch: training.make_loader(dataset, order, epoch),
                         rows, order, q["output"], device="cuda:0", numeric_check=helper.assert_numeric,
                         resources=observer, knn_enable=knn, state_fingerprint=helper.state_sha, run_identity=RUN)


def main():
    parser = argparse.ArgumentParser()
    for name in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime",
                 "runtime-sha256", "launcher"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    need(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         "isolated Linux runtime")

    def control(path, expected):
        p = Path(path)
        need(p.is_absolute() and p.resolve(strict=True) == p and p.stat().st_size <= 131072, "control file path")
        data = p.read_bytes()
        need(hashlib.sha256(data).hexdigest() == expected, "control SHA256")
        return json.loads(data)

    q = control(args.request, args.request_sha256)
    authorize(q, args.request_sha256, control(args.authorization, args.authorization_sha256),
              args.authorization_sha256, control(args.runtime, args.runtime_sha256))
    need([args.request, args.authorization, args.runtime] == [q["controls"][k]
         for k in ("request", "authorization", "runtime")], "exact control paths")
    i = q["identity"]
    need((socket.gethostname(), os.getuid(), str(Path(sys.executable).resolve()), sys.version.split()[0])
         == (i["hostname"], i["uid"], i["python_realpath"], i["python_version"])
         and Path.cwd() == Path(q["project"]), "native training identity")
    need(all(os.environ.get(k) == v for k, v in q["environment"].items()), "training environment")
    rec = q["p2_support"]
    source = Path(rec["path"])
    need(source.resolve(strict=True) == source, "support path")
    raw = source.read_bytes()
    need(len(raw) == rec["bytes"] and hashlib.sha256(raw).hexdigest() == rec["sha256"], "support SHA256")
    support = ModuleType("cisc_frozen_resource_support")
    exec(compile(raw, str(source), "exec"), support.__dict__)
    need(Path(__file__) == support.exact(q["worker"]) and Path(args.launcher) == support.exact(q["launcher"]),
         "exact worker and launcher")
    receipt = json.loads(support.exact(q["admission_receipt"]).read_bytes())
    check_admission(receipt, q)
    verify_common(q, json.loads(support.exact(q["common_contract"]).read_bytes()))
    out = support.clean(q["output"])
    need(out.parent == Path(q["project"]) / "logs/cranial_bcsp_fullmamba", "exact output parent")
    if args.check:
        need(not out.exists() and out.parent.is_dir(), "fresh output path")
        resources = support.resources(q, out, initial=True)
        need(resources["disk_free_bytes"] >= q["minimum_free_bytes_prelaunch"], "training disk start threshold")
        return
    old = support.source("cisc_inherited_oasg_training", q["inherited_training"])
    old.check_admission = check_admission
    old.train_native = lambda *a: train_native(*a, old)
    old.launch_training(q, support, receipt)


if __name__ == "__main__":
    main()
