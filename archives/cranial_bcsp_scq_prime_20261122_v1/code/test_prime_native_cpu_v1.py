"""Local CPU checks with synthetic tensors and checkpoints, plus frozen metadata."""
import ast
import copy
import json
from pathlib import Path, PurePosixPath
import sys
from types import SimpleNamespace

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bcsp_scq_prime_BFS_C_native_v1 as native

SCOPE = HERE / "SCQ_PRIME_BFS_C_native_pending_scope_v1.json"
INDEX = HERE / "SCQ_PRIME_BFS_C_development_index_v1.json"
ENTRY = HERE / "bcsp_scq_prime_BFS_C_native_v1.py"
FIXTURE = HERE / "cpu_contract_v1"


def record(path, remote=None):
    return dict(path=str(remote or path), bytes=path.stat().st_size, sha256=native.sha(path))


def load(path):
    return json.loads(path.read_bytes())


def rejection(call, exc=ValueError):
    try:
        call()
    except exc:
        return True
    return False


def launch_contract(scope):
    install = PurePosixPath(scope["candidate_install_dir"])
    out = PurePosixPath(scope["candidate_output"])
    control = install / "control_v1"
    return dict(request_path=str(install / "SCQ_PRIME_BFS_C_native_execution_request_v1.json"),
                authorization=str(control / "authorization.json"), runtime=str(control / "runtime.json"),
                launcher=str(control / "launch_once.sh"), tmux_session=scope["tmux_session"],
                log=str(out / "launch.log"), PID=str(out / "worker.pid"), exit_code=str(out / "exit_code.txt"),
                single_attempt=True, automatic_retry=False)


def pending(scope):
    keys = ("identity", "implementation", "dependencies", "static_config", "preflight_scope", "model_root",
            "initialization", "environment", "limits", "source_manifest", "fold_binding", "model_records", "no_calls",
            "fold", "seed", "n_input", "n_output", "batch_size", "forward_budget")
    root = PurePosixPath(scope["candidate_install_dir"])
    historical = Path(scope["requires_new_entry"]["historical_parent"]["path"])
    return dict({k: scope[k] for k in keys}, schema="bcsp-scq-prime-BFS-C-native-prediction-v1",
                status="AWAITING_EXPLICIT_USER_AUTHORIZATION", execution_authorized=False,
                entry=record(ENTRY, root / ENTRY.name), scope=record(SCOPE, root / SCOPE.name),
                input_index=record(INDEX, root / INDEX.name), legacy_helpers=record(historical, root / historical.name),
                launch_contract=launch_contract(scope), launch_attempt=str(root / "control_v1/launch_attempt.json"),
                output=scope["candidate_output"])


class Toy(torch.nn.Module):
    def __init__(self, arm):
        super().__init__()
        self.arm = arm
        self.weight = torch.nn.Parameter(torch.zeros(1))
        self.register_buffer("running", torch.zeros(3))
        self.base_model = SimpleNamespace()
        if arm != "B":
            self.base_model.scq = SimpleNamespace(variant=arm)
        self.calls = 0

    def forward(self, x):
        assert torch.is_inference_mode_enabled() and not self.training
        self.calls += 1
        raw = x[:, :256].clone()
        offset = torch.full_like(raw, .125)
        used = raw if self.arm == "B" else raw + offset
        if self.arm != "B":
            self.base_model._scq_last_info = dict(Q0=raw, Qused=used, delta=offset,
                indices=torch.arange(8, dtype=torch.int64)[None, None].expand(1, 256, 8))
        return used, x


def save_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    FIXTURE.mkdir()
    torch.set_num_threads(2)
    checks = {}
    scope = load(SCOPE)
    q = pending(scope)
    native.validate_scope(q, scope)
    checks["pending_scope_exact_hash_and_values"] = q["scope"]["sha256"] == native.SCOPE_SHA
    checks["budget_changed_rejected"] = rejection(lambda: native.validate_scope({**q, "forward_budget": 316}, scope))
    checks["changed_GPU_rejected"] = rejection(lambda: native.validate_scope({**q, "identity": {}}, scope))
    root = HERE.parents[1] / "cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload"
    fold = root / PurePosixPath(scope["fold_binding"]["path"]).name
    man = root / PurePosixPath(scope["source_manifest"]["path"]).name
    assert native.sha(man) == scope["source_manifest"]["sha256"] and native.sha(fold) == scope["fold_binding"]["sha256"]
    ix, binding = load(INDEX), load(fold)
    manifest = [json.loads(line) for line in man.read_bytes().splitlines()]
    cases = scope["traces"]["selected_case_ids"]
    rows = native.validate_index(ix, binding, manifest, cases)
    checks["frozen_exact_105_development_metadata"] = len(rows) == 105 and q["input_index"]["sha256"] == native.INDEX_SHA
    bad = copy.deepcopy(ix)
    bad["inputs"][0]["input"]["sha256"] = "0" * 64
    checks["changed_input_rejected"] = rejection(lambda: native.validate_index(bad, binding, manifest, cases))
    checks["changed_trace_list_rejected"] = rejection(lambda: native.validate_index(ix, binding, manifest, cases[:-1]))
    receipts = {arm: HERE.parent / f"{arm}_C_post_training_freeze_v1/{arm}_C_post_training_freeze_receipt_v1.json"
                for arm in native.ARMS}
    q["training_audits"] = {a: record(p) for a, p in receipts.items()}
    checks["all_three_formal_training_receipts_bound"] = set(native.training_evidence(q)) == set(native.ARMS)
    swapped = {**q, "training_audits": {**q["training_audits"], "B": q["training_audits"]["F"]}}
    checks["swapped_audit_rejected"] = rejection(lambda: native.training_evidence(swapped))
    historical_path = Path(scope["requires_new_entry"]["historical_parent"]["path"])
    legacy = native.source("legacy_cpu_test", record(historical_path))
    for p in (ENTRY, historical_path):
        ast.parse(p.read_bytes(), filename=str(p))
    fake_request = {"sha256": "a"*64}
    auth = FIXTURE / "fixture_auth.json"
    runtime = FIXTURE / "fixture_runtime.json"
    save_json(auth, dict(schema="bcsp-development-authorization-v1", request_sha256=fake_request["sha256"],
                        explicit_user_authorization=True, user_authorization_text="synthetic fixture"))
    save_json(runtime, dict(schema="bcsp-development-runtime-v1", request_sha256=fake_request["sha256"],
                            authorization_sha256=native.sha(auth)))
    native.authorizations(fake_request, record(auth), record(runtime))
    checks["one_way_authorization_and_bad_hash_rejection"] = rejection(
        lambda: native.authorizations({"sha256":"b"*64}, record(auth), record(runtime)))
    rendered = legacy.render_launcher(q, "1"*64, "2"*64, "3"*64)
    checks["frozen_paths_and_timeout_launcher"] = "7200s" in rendered and q["launch_contract"]["request_path"] in rendered
    models = {}
    model_records = {}
    for arm in native.ARMS:
        model = Toy(arm)
        sample = FIXTURE / f"synthetic_{arm}.pth"
        toy_state = dict(weight=torch.tensor([1.0]), running=torch.ones(3))
        payload = dict(base_model=toy_state, stage="BCSP_INPUT_DENSITY_V1", epoch=99, updates=3900,
                       scq_prime_run_identity=native.identity(arm))
        torch.save(payload, sample)
        model_records[arm] = record(sample)
        native.load_checkpoint(torch, model, model_records[arm], arm)
        checks[f"{arm}_safe_strict_checkpoint_and_buffer_load"] = model.running.tolist() == [1, 1, 1]
        checks[f"{arm}_wrong_arm_rejected"] = rejection(
            lambda: native.load_checkpoint(torch, model, model_records[arm], "F" if arm == "B" else "B"))
        models[arm] = model.eval()
    bad_checkpoint = FIXTURE / "wrong_dimensions.pth"
    payload["base_model"]["running"] = torch.zeros(4)
    torch.save(payload, bad_checkpoint)
    checks["strict_state_dict_mismatch_rejected"] = rejection(
        lambda: native.load_checkpoint(torch, models["S"], record(bad_checkpoint), "S"), RuntimeError)
    wrong_seed = FIXTURE / "wrong_seed.pth"
    payload["scq_prime_run_identity"]["seed"] = 0
    torch.save(payload, wrong_seed)
    checks["wrong_seed_rejected_before_load"] = rejection(
        lambda: native.load_checkpoint(torch, models["S"], record(wrong_seed), "S"))

    fake_rows = [dict(case_id=f"synthetic_{k}", selected_neighborhood_trace=k < 6) for k in range(105)]
    budget = native.ForwardBudget([r["case_id"] for r in fake_rows])
    journal = FIXTURE / "forward_attempts.jsonl"
    x = torch.arange(8192 * 3, dtype=torch.float32).reshape(1, 8192, 3) * 1e-4
    checks["wrong_first_call_stopped_before_model"] = rejection(
        lambda: native.predict_case(torch, np, legacy, models["F"], x, "F", fake_rows[0], budget, journal))
    checks["short_run_rejected"] = rejection(lambda: budget.finish(0))
    shape_counts = {"B": 0, "F": 0, "S": 0}
    for arm, model in models.items():
        for row in fake_rows:
            _, coarse, dense, arrays = native.predict_case(torch, np, legacy, model, x, arm, row, budget, journal)
            assert arrays["coarse"].shape == (256, 3) and arrays["prediction"].shape == (8192, 3)
            if arm == "B":
                assert set(arrays) == {"coarse", "prediction"}
            else:
                assert np.allclose(arrays["Qraw"] + arrays["delta"], arrays["coarse"])
                if "neighbor_indices" in arrays:
                    assert row["selected_neighborhood_trace"] and arrays["neighbor_indices"].shape == (256, 8)
                    shape_counts[arm] += 1
                assert model.base_model._scq_last_info is None
    budget.finish(sum(m.calls for m in models.values()))
    checks["three_arms_315_artificial_CPU_forwards"] = [m.calls for m in models.values()] == [105]*3
    checks["six_selected_each_F_S_and_B_has_no_SCQ_fields"] = shape_counts == dict(B=0,F=6,S=6)
    checks["316_blocked_before_forward"] = rejection(
        lambda: native.predict_case(torch, np, legacy, models["S"], x, "S", fake_rows[0], budget, journal))
    checks["exact_315_journal_claims"] = len(journal.read_bytes().splitlines()) == 315 and models["S"].calls == 105
    assert all(checks.values()), checks
    result = dict(status="PRIME_NATIVE_ARTIFICIAL_CPU_PASS", checks=checks, torch_version=str(torch.__version__),
                  device=str(x.device), artificial_forwards=315, real_forward_calls=0, real_array_loads=0,
                  entry_sha256=native.sha(ENTRY), predecessor_sha256=native.sha(historical_path),
                  test_sha256=native.sha(Path(__file__)))
    save_json(FIXTURE / "result_v1.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
