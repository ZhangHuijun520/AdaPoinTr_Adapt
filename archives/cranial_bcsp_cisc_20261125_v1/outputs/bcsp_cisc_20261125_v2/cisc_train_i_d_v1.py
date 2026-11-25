"""Single Fold D spatial CISC run, paired to frozen R_D and U_D."""

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
from types import ModuleType


RUN = dict(variant="I", fold="D", seed=2026112601)
COUNTS = dict(batch=8, cases=315, sources=63, epochs=100, batches_per_epoch=39,
              updates=3900, exposures=31200, drop_slots=300)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def authorize(q, sha, auth, auth_sha, runtime):
    need(q["schema"] == "bcsp-cisc-p2-i-d-train-v1" and q["run"] == RUN and q["counts"] == COUNTS
         and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["execution_authorized"] is False
         and q["boundary"] == dict(retry=False, resume=False, development=False, BNCal=False),
         "exact pending I_D contract")
    need(set(auth) == {"request_sha256", "explicit_user_authorization", "authorization_text"}
         and auth["request_sha256"] == sha and auth["explicit_user_authorization"] is True
         and isinstance(auth["authorization_text"], str) and auth["authorization_text"].strip(),
         "explicit I_D full-hash authorization")
    need(runtime == dict(request_sha256=sha, authorization_sha256=auth_sha), "I_D runtime binding")


def verify_predecessor(q, common, reference, completion):
    need(common["runs"][2] == RUN and common["arm_order"] == ["R", "U", "I"]
         and common["counts"] == COUNTS and common["identity"] == q["identity"]
         and all(common[k] == q[k] for k in ("order", "fold", "point_manifest", "static_config",
                                              "coarse_initializer", "shared_initial_sha256", "seeds")),
         "frozen CISC I_D common contract")
    need(common["label_contract"]["weight"] == dict(R=0, U=.05, I=.05)
         and common["label_contract"]["load_by_arm"] == dict(R=False, U=True, I=True)
         and common["label_contract"]["prior"] == q["prior"], "matched U/I auxiliary contract")
    order = reference["complete_order"]
    need(reference["status"] == "FORMAL_CISC_R_D_POST_TRAINING_FREEZE_AUDIT_PASS"
         and reference["run"] == common["runs"][0] and reference["identity"] == q["identity"]
         and reference["request_sha256"] == q["reference_request_sha256"]
         and reference["common_contract_sha256"] == q["common_contract"]["sha256"]
         and reference["shared_initial_sha256"] == q["shared_initial_sha256"]
         and reference["starting_rng"] == q["starting_rng"]
         and reference["exit_code"] == 0 and reference["artifacts_stable"] is True
         and order["byte_identical"] is True and order["verified_batches"] == 3900
         and order["sha256"] == q["order"]["sha256"]
         and reference["counts"] == dict(updates=3900, epochs=100, cases=315, sources=63, exposures=31200, dropped=300)
         and completion["checkpoint_sha256"] == reference["checkpoint"]["sha256"]
         and completion["order_sha256"] == order["canonical_sha256"]
         and completion["scq_prime_run_identity"] == reference["run"], "formally frozen R_D predecessor")


class LabelledDataset:
    """Wrap the existing byte-verified dataset and validate a sidecar once per case."""

    def __init__(self, dataset, sidecars, verify, as_tensor):
        self.dataset = dataset
        self.records = dataset.records
        self.sidecars = sidecars
        self.verify = verify
        self.as_tensor = as_tensor
        self.labels = {}

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, index):
        x, target, cid, source = self.dataset[index]
        need(cid == self.records[index]["case_id"] and source == self.records[index]["source_id"],
             "label join requires exact case and source")
        if cid not in self.labels:
            binding = self.sidecars[cid]
            values = self.verify(Path(binding["path"]).read_bytes(), x.numpy(),
                                 label_sha256=binding["sha256"], partial_sha256=binding["partial_array_sha256"])
            self.labels[cid] = self.as_tensor(values)
        return x, target, cid, source, self.labels[cid]


def verify_uniform(q, reference, uniform, completion):
    need(uniform["status"] == "FORMAL_CISC_U_D_POST_TRAINING_FREEZE_AND_PAIRED_AUDIT_PASS"
         and uniform["run"] == dict(variant="U", fold=RUN["fold"], seed=RUN["seed"])
         and uniform["identity"] == q["identity"]
         and uniform["request_sha256"] == q["uniform_request_sha256"]
         and uniform["common_contract_sha256"] == q["common_contract"]["sha256"]
         and uniform["reference_audit_sha256"] == q["reference_receipt"]["sha256"]
         and uniform["reference_request_sha256"] == reference["request_sha256"]
         and uniform["shared_initial_sha256"] == reference["shared_initial_sha256"] == q["shared_initial_sha256"]
         and uniform["uniform_initial_sha256"] == q["uniform_initial_sha256"]
         and uniform["starting_rng"] == reference["starting_rng"] == q["starting_rng"]
         and uniform["complete_order"] == reference["complete_order"]
         and uniform["counts"] == reference["counts"]
         and uniform["paired"] == dict(verified_batches=3900, byte_identical_order=True, exposure_identical=True,
                                       rng_identical=True, shared_initial_identical=True)
         and uniform["exit_code"] == 0 and uniform["artifacts_stable"] is True
         and uniform["labels_sidecars_verified"] == 315 and uniform["auxiliary_loss_weight"] == .05
         and completion["scq_prime_run_identity"] == uniform["run"]
         and completion["checkpoint_sha256"] == uniform["checkpoint"]["sha256"]
         and completion["order_sha256"] == uniform["complete_order"]["canonical_sha256"],
         "formally frozen and paired U_D predecessor")


def check_run(**run):
    need(run == RUN, "only CISC I_D may train")


def bind_lifecycle(training, oasg, original_r, claim, loss_step):
    original = training.train_lifecycle
    path, tree = oasg._source(original, original_r.RUNTIME_SHA)
    [node] = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "train_lifecycle"]
    guard = node.body[1]
    old = """require(set(run_identity) == {'variant', 'fold', 'seed'} and run_identity['variant'] in ('B', 'F', 'S')
            and run_identity['fold'] in ('C', 'D') and type(run_identity['seed']) is int
            and run_identity['seed'] in (2026112101, 2026112102), 'SCQ-PRIME runtime identity')"""
    need(node.lineno == original.__code__.co_firstlineno and oasg._same_statement(guard, old), "inherited loop guard")
    node.body[1] = ast.copy_location(ast.parse("_cisc_run(**run_identity)").body[0], guard)
    expected = "for batch_index, (partial, target, batch_ids, batch_sources) in enumerate(loader):\n pass"
    target = ast.parse(expected).body[0]
    [loop] = [x for x in ast.walk(node) if isinstance(x, ast.For) and ast.dump(x.target) == ast.dump(target.target)
              and ast.dump(x.iter) == ast.dump(target.iter)]
    loop.target.elts[1].elts.append(ast.Name(id="labels", ctx=ast.Store()))
    old_step = ast.parse("""ret = model(partial)
counts['forward'] += 1
sparse, dense = model.get_loss(ret, target, epoch, partial=partial)
loss = sparse + dense""").body
    [idx] = [i for i in range(len(loop.body)) if [ast.dump(x) for x in loop.body[i:i+4]]
             == [ast.dump(x) for x in old_step]]
    new_step = ast.parse("""parts = _cisc_loss_step(model, partial, target, epoch, labels.to(device))
counts['forward'] += 1
sparse, dense, auxiliary, loss = parts""").body
    loop.body[idx:idx+4] = [ast.copy_location(x, loop.body[idx]) for x in new_step]
    [event] = [x for x in loop.body if isinstance(x, ast.Assign) and isinstance(x.value, ast.Dict)
               and any(isinstance(k, ast.Constant) and k.value == "optimizer_step_committed" for k in x.value.keys)]
    event.value.keys.extend([ast.Constant("loss_aux"), ast.Constant("loss_aux_weighted")])
    event.value.values.extend([ast.parse(x, mode="eval").body for x in ("float(auxiliary.detach())", "float(.05 * auxiliary.detach())")])
    return oasg._compile(node, path, {**original.__globals__, "_cisc_run": check_run,
                                    "claim_output": claim, "_cisc_loss_step": loss_step})


def loss_adapter(cisc):
    def loss_step(model, partial, target, epoch, labels):
        parts = cisc.training_losses(model, partial, target, epoch, labels)
        # The inherited, verified configuration disables denoising.
        return parts.original.new_zeros(()), parts.original, parts.interface, parts.total
    return loss_step


def train_native(q, out, support, sample, append, old, original_r, common):
    import importlib
    import random

    p1 = support.source("cisc_p1_model_builder", q["cisc_p1_worker"])
    native = support.source("cisc_spatial_model_loader", q["native_model_loader"])
    torch, np, helper, _ = native.prepare_models(q, support)
    support.source("bcsp_cisc_head_v1", q["cisc_sources"]["head"])
    cisc = support.source("bcsp_cisc_entry_v1", q["cisc_sources"]["entry"])
    impl, names = q["implementation"], q["module_names"]
    support.source(names["contract"], impl["contract"])
    training = support.source(names["training_runtime"], impl["training_runtime"])
    fold = json.loads(support.exact(q["fold"]).read_bytes())
    order = json.loads(support.exact(q["order"]).read_bytes())
    records = [json.loads(s) for s in support.exact(q["point_manifest"]).read_bytes().splitlines()]
    rows, sources = old.select_training(fold, records, order)
    label_root = support.clean(q["label_root"])
    universe = common["label_contract"]["rows"]
    need(set(universe) == {r["case_id"] for r in rows}, "315 frozen label joins")
    need({f.name for f in label_root.iterdir()} == {f"{cid}_labels.npz" for cid in universe}, "exact label directory members")
    sidecars = {}
    for row in rows:
        cid = row["case_id"]
        point = support.clean(str(Path(q["data_root"]) / row["point_path"]))
        entry = universe[cid]
        need(entry["point_file_sha256"] == row["sha256"] == support.file_hash(point), "training input identity")
        record = dict(entry, path=str(label_root / f"{cid}_labels.npz"))
        support.exact(record)
        sidecars[cid] = record
    model = p1.build_arm(q, support, torch, helper, cisc, "I")
    parent = sys.modules[names["prime_seeded_parent"]]
    full = original_r.initial_digest(model, parent)
    init = {name: parent.tensor_sha(value) for name, value in model.state_dict().items()
            if not name.startswith(("base_model.coarse_pred.conditioner.", "base_model.coarse_pred.condition_map."))}
    shared = hashlib.sha256(json.dumps(init, sort_keys=True).encode()).hexdigest()
    need(shared == q["shared_initial_sha256"] and full == q["uniform_initial_sha256"]
         and model.base_model.coarse_pred.conditioner.arm == "I", "admitted I construction")
    random.seed(RUN["seed"])
    np.random.seed(RUN["seed"])
    torch.manual_seed(RUN["seed"])
    rng = dict(python=hashlib.sha256(repr(random.getstate()).encode()).hexdigest(),
               numpy=hashlib.sha256(np.random.get_state()[1].tobytes()).hexdigest(),
               torch_cpu=parent.tensor_sha(torch.random.get_rng_state()),
               torch_cuda=parent.tensor_sha(torch.cuda.get_rng_state(0)))
    need(rng == q["starting_rng"], "paired R_D/U_D/I_D starting RNG")
    params = sum(p.numel() for p in model.parameters())
    need(params == 39968069, "matched U/I parameter count")
    evidence = dict(run_identity=RUN, shared_initial_sha256=shared, uniform_initial_sha256=full,
                    starting_rng=rng, total_parameters=params, carrier="spatial_mass_field",
                    labels_sha256_verified=315, auxiliary_loss_weight=.05)
    with (out / "model_construction.json").open("x", encoding="ascii") as stream:
        json.dump(evidence, stream, allow_nan=False)
    dataset = LabelledDataset(training.BCSPDataset(q["data_root"], rows, sources, 8192),
                              sidecars, cisc.verified_labels, torch.from_numpy)
    resources = old.TrainingResources(out, torch, helper, sample,
                                      lambda row: append("p3_resources.jsonl", row), q["resources"]["torch_peak_bytes"])
    oasg = sys.modules[names["oasg_entry"]]
    lifecycle = bind_lifecycle(training, oasg, original_r, old.claim_owned_training_output, loss_adapter(cisc))
    knn = importlib.import_module("models.Transformer_utils").enable_bcsp_knn
    with oasg.observe_training(model, oasg.identity("A", "D", oasg.TRAIN_SEED),
                               resources, lambda row: append("OASG_geometry.jsonl", row)) as observer:
        return lifecycle(model, lambda epoch: training.make_loader(dataset, order, epoch),
                         rows, order, q["output"], device="cuda:0", numeric_check=helper.assert_numeric,
                         resources=observer, knn_enable=knn, state_fingerprint=helper.state_sha, run_identity=RUN)


def main():
    parser = argparse.ArgumentParser()
    for name in ("request", "request-sha256", "authorization", "authorization-sha256",
                 "runtime", "runtime-sha256", "launcher"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    need(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         "isolated Linux runtime")

    def control(path, sha):
        p = Path(path)
        need(p.is_absolute() and p.resolve(strict=True) == p and p.stat().st_size <= 131072, "control path")
        data = p.read_bytes()
        need(hashlib.sha256(data).hexdigest() == sha, "control SHA256")
        return json.loads(data)

    q = control(args.request, args.request_sha256)
    authorize(q, args.request_sha256, control(args.authorization, args.authorization_sha256),
              args.authorization_sha256, control(args.runtime, args.runtime_sha256))
    need([args.request, args.authorization, args.runtime] == [q["controls"][k]
         for k in ("request", "authorization", "runtime")], "exact control paths")
    i = q["identity"]
    need((socket.gethostname(), os.getuid(), str(Path(sys.executable).resolve()), sys.version.split()[0])
         == (i["hostname"], i["uid"], i["python_realpath"], i["python_version"])
         and Path.cwd() == Path(q["project"]), "native identity")
    need(all(os.environ.get(k) == v for k, v in q["environment"].items()), "runtime environment")
    r = q["p2_support"]
    path = Path(r["path"])
    need(path.resolve(strict=True) == path, "support path")
    raw = path.read_bytes()
    need(len(raw) == r["bytes"] and hashlib.sha256(raw).hexdigest() == r["sha256"], "support SHA256")
    support = ModuleType("cisc_frozen_resource_support")
    exec(compile(raw, str(path), "exec"), support.__dict__)
    need(Path(__file__) == support.exact(q["worker"]) and Path(args.launcher) == support.exact(q["launcher"]),
         "exact I worker and launcher")
    original_r = support.source("cisc_frozen_reference_adapter", q["reference_worker"])
    receipt = json.loads(support.exact(q["admission_receipt"]).read_bytes())
    original_r.check_admission(receipt, q)
    common = json.loads(support.exact(q["common_contract"]).read_bytes())
    reference = json.loads(support.exact(q["reference_receipt"]).read_bytes())
    completion = json.loads(support.exact(q["reference_completion"]).read_bytes())
    verify_predecessor(q, common, reference, completion)
    uniform = json.loads(support.exact(q["uniform_receipt"]).read_bytes())
    uniform_completion = json.loads(support.exact(q["uniform_completion"]).read_bytes())
    verify_uniform(q, reference, uniform, uniform_completion)
    admission = json.loads(support.exact(q["admission_completion"]).read_bytes())
    need(admission["results"]["U"]["initial_sha256"] == admission["results"]["I"]["initial_sha256"]
         == q["uniform_initial_sha256"], "P1 uniform initialization evidence")
    out = support.clean(q["output"])
    need(out.parent == Path(q["project"]) / "logs/cranial_bcsp_fullmamba", "exact output parent")
    if args.check:
        need(not out.exists() and out.parent.is_dir(), "fresh I output")
        resources = support.resources(q, out, initial=True)
        need(resources["disk_free_bytes"] >= q["minimum_free_bytes_prelaunch"], "disk start threshold")
        return
    old = support.source("cisc_inherited_oasg_training", q["inherited_training"])
    old.check_admission = original_r.check_admission
    old.train_native = lambda *args: train_native(*args, old, original_r, common)
    old.launch_training(q, support, receipt)


if __name__ == "__main__":
    main()
