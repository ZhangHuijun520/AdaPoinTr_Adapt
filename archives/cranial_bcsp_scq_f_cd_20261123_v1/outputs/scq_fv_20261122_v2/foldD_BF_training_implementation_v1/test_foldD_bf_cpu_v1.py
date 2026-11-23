"""Artificial authorization and dispatch fixtures. Only frozen text assets are read."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import bcsp_scq_prime_foldD_bf_train_v1 as entry


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(v):
    return (json.dumps(v, sort_keys=True, separators=(",", ":")) + "\n").encode()


def run(checks):
    fv = ROOT / "outputs/scq_fv_20261122_v2"
    prime = ROOT / "outputs/scq_prime_cuda_preparation_20261122_v1/post_CUDA_freeze_audit_v1"
    manifest_pin = fv / "P1_implementation_plan_lock_v1/SCQ_FV_P1_plan_lock_v1.json"
    frozen = manifest_pin.read_bytes()
    assert digest(frozen) == "da0b91759db281ef944a216131b53d9a5e65ac951f694fe15465b06252f00861"
    lock = json.loads(frozen)
    previous = json.loads(entry.raw_record(lock["frozen_prime_lineage"]["B"]["training_request"]))
    impl = lock["original_implementation_bindings"]
    parent = entry.load_parent(impl["entry"])
    metadata = parent.source_module("_test_frozen_training_metadata", impl["contract"])
    local_paths = {}
    memory = {}

    def check(name, fn):
        fn()
        checks[name] = True

    def deny(fn, reason):
        try:
            fn()
        except ValueError as exc:
            assert reason in str(exc), str(exc)
        else:
            raise AssertionError("unexpected acceptance: " + reason)

    def store(path, value):
        data = encode(value)
        rec = dict(path=str(path), bytes=len(data), sha256=digest(data))
        memory[(str(path), rec["sha256"])] = data
        return rec

    def local(record):
        path = local_paths[record["path"]]
        data = path.read_bytes()
        assert len(data) == record["bytes"] and digest(data) == record["sha256"], path
        return path

    def bound(record):
        key = record["path"], record["sha256"]
        return json.loads(memory[key] if key in memory else local(record).read_bytes())

    def abstract_bytes(record):
        data = memory[record["path"], record["sha256"]]
        assert len(data) == record["bytes"] and digest(data) == record["sha256"]
        return data

    q0 = deepcopy(previous)
    q0.update(schema=entry.SCHEMA, stage=entry.STAGE, fold="D", data_root=entry.PROJECT + "/data/bcsp_geov1_foldd_8192_seed0_v1",
              prime_worker=impl["entry"])
    for key, r in q0["implementation"].items():
        local_paths[r["path"]] = Path(impl[key]["path"])
    new_path = entry.run_paths("B")["launch_contract"]["request_path"].rsplit("/", 1)[0] + "/" + Path(entry.__file__).name
    own = Path(entry.__file__).read_bytes()
    q0["implementation"]["entry"] = dict(path=new_path, bytes=len(own), sha256=digest(own))
    local_paths[new_path] = Path(entry.__file__)
    q0["order_plan"] = {**lock["inputs"]["fold_D_order"], "path": entry.PROJECT + "/third_party/shared_order_foldD_seed0_v1.json"}
    local_paths[q0["order_plan"]["path"]] = Path(lock["inputs"]["fold_D_order"]["path"])
    local_paths[q0["initialization"]["path"]] = Path(lock["inputs"]["seed_A_residual_initialization"]["path"])
    local_paths[q0["static_config"]["path"]] = Path(lock["inputs"]["static_training_config"]["path"])
    local_paths[q0["admission"]["audit"]["path"]] = prime / "formal_post_cuda_freeze_receipt_v1.json"
    local_paths[q0["admission"]["construction"]["path"]] = prime / "downloads/construction.json"
    train_req = Path(lock["frozen_prime_lineage"]["B"]["training_request"]["path"])
    local_paths[q0["admission"]["request"]["path"]] = train_req.parent / "SCQ_PRIME_cuda_execution_request_v1.json"
    qualified = lock["inputs"]["qualified_fold_D"]
    qual_body = json.loads(entry.raw_record(qualified))
    base = Path(qualified["path"]).parent
    q0["QC"] = {k: qual_body[k] for k in ("verification", "manifests", "fold_binding")}
    q0["QC"]["qualified_receipt"] = {**qualified, "path": entry.PROJECT + "/third_party/qualified_D.json"}
    for rec in (q0["QC"]["verification"], *q0["QC"]["manifests"].values(), q0["QC"]["fold_binding"]):
        local_paths[rec["path"]] = base / rec["path"].rsplit("/", 1)[-1]
    local_paths[q0["QC"]["qualified_receipt"]["path"]] = Path(qualified["path"])
    q0["P3"] = store(entry.PROJECT + "/third_party/synthetic_cpu_receipt.json", dict(status=entry.P3_STATUS,
        entry_sha256=digest(own), runtime_sha256=impl["runtime"]["sha256"], prime_worker_sha256=entry.PARENT_SHA,
        checks={"synthetic": True}))

    with patch.object(parent, "bound", bound), patch.object(parent, "exact", local), patch.object(metadata, "exact", local), \
            patch.object(parent, "source_module", return_value=metadata), patch.object(entry, "load_parent", return_value=parent), \
            patch.object(entry, "raw_record", abstract_bytes):
        _, common = parent.validate_admission(previous)
        pair = {k: q0[k] for k in entry.PAIR_FIELDS}
        pair.update(status=entry.PAIR_STATUS, arm_order=list(entry.ARMS), counts=entry.COUNTS,
                    resources=parent.RESOURCES, drop_events=300, pair_common_sha256=common, audit_sha256=parent.ADMISSION_SHA)
        q0["pair_contract"] = store(entry.PROJECT + "/third_party/synthetic_pair.json", pair)
        b = {**{k: q0["identity"][k] for k in entry.HOST_FIELDS}, "status": entry.AUDIT_STATUS, "exit_code": 0,
             "stable_inventory": True, "run_identity": dict(variant="B", fold="D", seed=entry.SEED),
             "updates": 3900, "traversals": 100, "exposures": 31200, "drop_events": 300, "sources": 63,
             "training_cases": 315, "bncal_executed": False, "development_evaluation_executed": False, "resume": False,
             "pair_contract_sha256": q0["pair_contract"]["sha256"], "common_initial_state_SHA256": common,
             "order_file_sha256": entry.ORDER_SHA, "actual_order_canonical_sha256": entry.ORDER_CANONICAL_SHA,
             "checkpoint": dict(path=entry.run_paths("B")["output"] + "/ckpt-last.pth", bytes=123, sha256="b" * 64)}

        def q_for(arm, predecessor=None):
            refs = {} if predecessor is None else {"B": store(entry.PROJECT + "/third_party/synthetic_B_D.json", predecessor)}
            return {**q0, **entry.run_paths(arm), "variant": arm, "predecessors": refs}

        def apply(q, *, auth_change=None, runtime_change=None, change_path=False):
            launch = q["launch_contract"]
            qr = store(launch["request_path"], q)
            auth = dict(schema="bcsp-scq-fv-d-bf-training-authorization-v1", request_sha256=qr["sha256"],
                        explicit_user_authorization=True, user_authorization_text="synthetic CPU only")
            auth.update(auth_change or {})
            ar = store(launch["authorization_path"] + (".wrong" if change_path else ""), auth)
            runtime = dict(schema="bcsp-scq-fv-d-bf-training-runtime-v1", request_sha256=qr["sha256"], authorization_sha256=ar["sha256"])
            runtime.update(runtime_change or {})
            rr = store(launch["runtime_path"], runtime)
            return entry.authorize(qr, ar, rr)

        authorized = {}
        for arm, predecessor in (("B", None), ("F", b)):
            def accept():
                result = apply(q_for(arm, predecessor))
                q, static, selected, fold, plan, admission, observed, original = result
                assert q["variant"] == arm and q["fold"] == "D" and q["seed"] == entry.SEED
                assert static["counts"] == entry.COUNTS and len(selected) == 315 and len(fold["dev_case_ids"]) == 105
                assert not set(fold["train_case_ids"]) & set(fold["dev_case_ids"])
                assert admission["status"] == "SCQ_PRIME_NATIVE_CUDA_ADMISSION_PASS" and observed == common
                assert metadata.canonical_sha(plan) == entry.ORDER_CANONICAL_SHA and original is parent
                authorized[arm] = result
            check(f"authorize_{arm}_D_with_real_metadata_and_historical_admission", accept)

        tests = {
            "unsupported_arm": (lambda: apply({**q_for("B"), "variant": "C0"}), "fixed Fold D"),
            "wrong_fold": (lambda: apply({**q_for("B"), "fold": "C"}), "fixed Fold D"),
            "wrong_seed": (lambda: apply({**q_for("B"), "seed": 0}), "fixed Fold D"),
            "changed_order": (lambda: apply({**q_for("B"), "order_plan": {"sha256": "0" * 64}}), "frozen Fold D order"),
            "wrong_data_root": (lambda: apply({**q_for("B"), "data_root": previous["data_root"]}), "Fold D training data root"),
            "request_hash_drift": (lambda: apply(q_for("B"), auth_change={"request_sha256": "0" * 64}), "full request SHA256"),
            "missing_user_authorization": (lambda: apply(q_for("B"), auth_change={"explicit_user_authorization": False}), "full request SHA256"),
            "different_control_path": (lambda: apply(q_for("B"), change_path=True), "exact control paths"),
            "runtime_hash_drift": (lambda: apply(q_for("B"), runtime_change={"authorization_sha256": "0" * 64}), "one-way authorization"),
            "different_gpu": (lambda: apply({**q_for("B"), "identity": {**q0["identity"], "gpu_uuid": "other"}}), "same admitted identity"),
            "B_unexpected_predecessor": (lambda: apply(q_for("B", b)), "exactly one B_D"),
            "F_missing_predecessor": (lambda: apply(q_for("F")), "exactly one B_D"),
            "F_rejects_C_predecessor": (lambda: apply(q_for("F", {**b, "run_identity": dict(variant="B", fold="C", seed=entry.SEED)})), "successful B_D"),
            "F_rejects_old_C0_evidence": (lambda: apply(q_for("F", {**b, "status": "FORMAL_P3_FAILURE_FREEZE_PASS"})), "successful B_D"),
            "F_rejects_predecessor_count_drift": (lambda: apply(q_for("F", {**b, "exposures": 31192})), "exact counts"),
            "F_rejects_predecessor_BNCal": (lambda: apply(q_for("F", {**b, "bncal_executed": True})), "successful B_D"),
            "F_rejects_predecessor_order_drift": (lambda: apply(q_for("F", {**b, "actual_order_canonical_sha256": "0" * 64})), "initialization, order and device"),
            "F_rejects_predecessor_init_drift": (lambda: apply(q_for("F", {**b, "common_initial_state_SHA256": "0" * 64})), "initialization, order and device"),
            "F_rejects_predecessor_pair_drift": (lambda: apply(q_for("F", {**b, "pair_contract_sha256": "0" * 64})), "initialization, order and device"),
            "F_rejects_predecessor_device_drift": (lambda: apply(q_for("F", {**b, "gpu_uuid": "other"})), "initialization, order and device"),
            "F_rejects_unrelated_checkpoint_path": (lambda: apply(q_for("F", {**b, "checkpoint": {**b["checkpoint"], "path": "/other/ckpt-last.pth"}})), "final checkpoint receipt"),
        }
        for name, (fn, reason) in tests.items():
            check(name, lambda: deny(fn, reason))
        for arm, result in authorized.items():
            def dispatch():
                q, _, selected, fold, plan, admission, _, _ = result
                class Hook:
                    def register_forward_hook(self, call):
                        return SimpleNamespace(remove=lambda: None)
                model = Hook()
                model.loss_func, model.fine_loss_func = Hook(), Hook()
                def fake_construct(run, _, init, **_kwargs):
                    assert run == dict(variant=arm, fold="D", seed=entry.SEED)
                    assert init == (None if arm == "B" else q["initialization"])
                    return model, {"run_identity":run}
                def fake_train(run, obj, construction, rt, runtime_sha, initial, proof, device, loader, rows, ordered,
                               output, **_kwargs):
                    assert run["fold"] == "D" and obj is model and device == "cuda:0"  # label only
                    assert construction == {"run_identity": run} and rt is runtime
                    assert rows is selected and ordered is plan and initial == common and proof == admission
                    assert loader(99) == plan["epochs"][99]["batches"]
                    assert runtime_sha == impl["runtime"]["sha256"] and output == entry.run_paths(arm)["output"]
                    return "artificial_dispatch_only"
                constructor = SimpleNamespace(identity=lambda variant, fold, seed: dict(variant=variant, fold=fold, seed=seed),
                                              construct=fake_construct, train_admitted=fake_train)
                runtime = SimpleNamespace(BCSPDataset=lambda *args: args, make_loader=lambda _, p, i:p["epochs"][i]["batches"])
                helper = SimpleNamespace(validate_model=lambda _: None, assert_numeric=None, state_sha=None)
                assert parent.dispatch_training(q, selected, fold, plan, factory=SimpleNamespace(parent=None), model_builder=None,
                    runtime=runtime, prime=constructor, seeded=None, admission=admission, expected_common=common,
                    helper=helper, budget=SimpleNamespace(), torch=None, np=None, knn_enable=None) == "artificial_dispatch_only"
            check(f"original_dispatch_routes_{arm}_D_with_shared_runtime_contract", dispatch)


if __name__ == "__main__":
    checks = {}
    try:
        run(checks)
    finally:
        print(json.dumps({"checks":checks, "torch_imported":"torch" in sys.modules, "numpy_imported":"numpy" in sys.modules}))
