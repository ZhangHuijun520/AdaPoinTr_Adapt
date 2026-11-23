"""Single artificial CPU contract batch for the Fold D Native B/F entry."""
import ast
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
from types import SimpleNamespace

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bcsp_scq_fv_BF_D_native_v1 as native

ROOT = HERE.parent
SOURCE = HERE / "bcsp_scq_fv_BF_D_native_v1.py"
READINESS = ROOT / "foldD_BF_native_prediction_readiness_v1.json"
FIXTURE = HERE / "cpu_contract_v1"


def pin(path):
    data = path.read_bytes()
    return dict(path=path.as_posix(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def emit(path, data):
    with path.open("x", encoding="ascii", newline="\n") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def rejected(call, error=ValueError):
    try:
        call()
    except error:
        return True
    raise AssertionError("expected contract rejection")


class Toy(torch.nn.Module):
    def __init__(self, arm, events):
        super().__init__()
        self.arm = arm
        self.events = events
        self.calls = 0
        self.weight = torch.nn.Parameter(torch.zeros(1))
        self.register_buffer("running", torch.zeros(3))
        self.base_model = SimpleNamespace()
        if arm == "F":
            self.base_model.scq = SimpleNamespace(variant=arm)

    def forward(self, x):
        assert torch.is_inference_mode_enabled() and not self.training and x.device.type == "cpu"
        self.events.append("model")
        self.calls += 1
        raw = x[:, :256].clone()
        used = raw
        if self.arm == "F":
            delta = torch.full_like(raw, 0.125)
            used = raw + delta
            self.base_model._scq_last_info = dict(Q0=raw, Qused=used, delta=delta)
        return used, x


def check_contracts(checks):
    assert pin(READINESS)["sha256"] == "0fadf7abc5519e74f1e277fa95a69bf7c8e1778f587eb541385e7e2e31aabcc1"
    ready = json.loads(READINESS.read_bytes())
    bindings = ready["metadata_bindings"]
    folds = native.read(bindings["fold"])
    manifest = [json.loads(line) for line in native.exact(bindings["manifest_8192"]).read_bytes().splitlines()]
    original = {m["case_id"]:m for m in manifest}
    rows = []
    for case_id in ready["ordered_development_case_ids"]:
        m = original[case_id]
        rows.append(dict(case_id=case_id, source_id=m["source_id"], defect_type=case_id.rsplit("__",1)[1],
                         n_input=8192, n_output=8192, normalization=m["normalization"],
                         normalization_source=m["normalization_source"],
                         input=dict(path=str(native.DEV_ROOT / m["point_path"]),bytes=1,sha256=m["sha256"])))
    fixture_index = dict(fold="D",seed=native.SEED,arms=list(native.ARMS),cases=105,sources=21,inputs=rows)
    checks["105_cases_from_21_sources_and_frozen_D_only_coordinates"] = len(native.validate_index(fixture_index,folds,manifest)) == 105
    for key, val in (("path","/tmp/wrong"),("sha256","0"*64)):
        bad = copy.deepcopy(fixture_index)
        bad["inputs"][0]["input"][key] = val
        checks[f"wrong_input_{key}_rejected"] = rejected(lambda: native.validate_index(bad,folds,manifest))
    bad = copy.deepcopy(fixture_index)
    bad["inputs"][0]["normalization"]["scale"] *= 2
    checks["changed_normalization_rejected"] = rejected(lambda: native.validate_index(bad,folds,manifest))
    bad = {**fixture_index,"inputs":list(reversed(rows))}
    checks["changed_case_order_rejected"] = rejected(lambda: native.validate_index(bad,folds,manifest))

    audits = ready["training_audits"]
    evidence = {a:native.read(r) for a,r in audits.items()}
    model_records = {a:dict(training_audit_SHA256=audits[a]["sha256"], training_request_SHA256=e["request_sha256"],
                            run_identity=native.identity(a),checkpoint=e["checkpoint"]) for a,e in evidence.items()}
    train = native.read(ready["training_requests"]["F"])
    old = json.loads((ROOT.parent / "scq_prime_foldC_training_preparation_20261122_v1/BFS_C_native_prediction_preparation_v1/SCQ_PRIME_BFS_C_native_execution_request_v1.json").read_bytes())
    common = {k:old[k] for k in ("identity","implementation","dependencies","static_config","preflight_scope","model_root",
                                "initialization","environment","limits","source_manifest","fold_binding","legacy_helpers","no_calls")}
    common.update(model_records=model_records, training_audits=audits, input_index={"sha256":"1"*64}, timing=native.TIMING)
    scope = dict(**common,arm_order=list(native.ARMS),per_arm=105,scoring=False,
                 candidate_output="/home/jovyan/fake/out",candidate_install_dir="/home/jovyan/fake/install",tmux_session="fixture")
    install=PurePosixPath(scope["candidate_install_dir"])
    ctrl=install/"control_v1"
    out=PurePosixPath(scope["candidate_output"])
    launch=dict(request_path=str(install/"SCQ_FV_BF_D_native_execution_request_v1.json"),
        authorization=str(ctrl/"authorization.json"),runtime=str(ctrl/"runtime.json"),launcher=str(ctrl/"launch_once.sh"),
        tmux_session="fixture",log=str(out/"launch.log"),PID=str(out/"worker.pid"),exit_code=str(out/"exit_code.txt"),
        single_attempt=True,automatic_retry=False)
    q=dict(**common,schema="bcsp-scq-fv-BF-D-native-prediction-v1",status="AWAITING_EXPLICIT_USER_AUTHORIZATION",
           execution_authorized=False,fold="D",seed=native.SEED,n_input=8192,n_output=8192,batch_size=1,forward_budget=210,
           output=str(out),launch_attempt=str(ctrl/"launch_attempt.json"),launch_contract=launch)
    assert q["identity"]==train["identity"]
    native.validate_scope(q,scope)
    checks["scope_locks_fold_arms_budget_and_timing"] = all(rejected(lambda: native.validate_scope({**q,k:v},scope))
        for k,v in (("fold","C"),("forward_budget",211),("identity",{}),("timing",{})))
    checks["formal_B_D_F_D_audits_bind"] = set(native.training_evidence(q)) == set(native.ARMS)
    checks["swapped_audits_rejected"] = rejected(lambda: native.training_evidence({**q,"training_audits":{"B":audits["F"],"F":audits["B"]}}))
    synthetic = {"sha256":"a"*64}
    auth, runtime = FIXTURE/"auth_fixture.json", FIXTURE/"runtime_fixture.json"
    emit(auth,dict(schema="bcsp-development-authorization-v1",request_sha256=synthetic["sha256"],
                   explicit_user_authorization=True,user_authorization_text="artificial fixture"))
    emit(runtime,dict(schema="bcsp-development-runtime-v1",request_sha256=synthetic["sha256"],
                      authorization_sha256=pin(auth)["sha256"]))
    native.authorizations(synthetic,pin(auth),pin(runtime))
    checks["single_direction_authorization_hash"] = rejected(lambda: native.authorizations({"sha256":"b"*64},pin(auth),pin(runtime)))


def check_predictions(checks):
    events = []
    journal = []
    legacy = SimpleNamespace(append_event=lambda path, row: journal.append(row))
    ids = [f"toy_{k}" for k in range(105)]
    budget = native.ForwardBudget(ids)
    x = torch.zeros((1,8192,3),dtype=torch.float32)
    rng = torch.get_rng_state().clone()
    model_by_arm = {}
    for arm in native.ARMS:
        model = Toy(arm,events).eval()
        model_by_arm[arm] = model
        cp = FIXTURE / f"toy_{arm}.pth"
        torch.save(dict(base_model={"weight":torch.ones(1),"running":torch.ones(3)},
                        stage="BCSP_INPUT_DENSITY_V1",epoch=99,updates=3900,scq_prime_run_identity=native.identity(arm)),cp)
        native.load_checkpoint(torch,model,pin(cp),arm)
        checks[f"{arm}_strict_CPU_checkpoint_and_buffer"] = model.weight.item() == 1 and model.running.tolist() == [1,1,1]
        checks[f"{arm}_wrong_arm_checkpoint_rejected"] = rejected(lambda: native.load_checkpoint(torch,model,pin(cp),"F" if arm=="B" else "B"))
    checks["early_completion_rejected"] = rejected(lambda: budget.finish(0))
    checks["wrong_first_arm_blocked"] = rejected(lambda: budget.claim("F",ids[0]))
    for arm, model in model_by_arm.items():
        state = {k:v.clone() for k,v in model.state_dict().items()}
        for k, cid in enumerate(ids):
            events.clear()
            times = iter((100,120))
            def clock():
                events.append("clock")
                return next(times)
            def sync():
                events.append("sync")
            call, coarse, dense, arrays, ns = native.predict_case(
                torch,np,legacy,model,x,arm,{"case_id":cid},budget,None,sync,clock)
            assert call == (0 if arm=="B" else 105)+k+1 and ns==20
            assert events == ["sync","clock","model","sync","clock"]
            assert set(arrays)==({"coarse","prediction"} if arm=="B" else {"coarse","prediction","Qraw","Qused","delta"})
            assert coarse.shape==(1,256,3) and dense.shape==(1,8192,3)
            if arm=="F":
                assert np.array_equal(arrays["Qused"], arrays["coarse"])
                assert np.array_equal(arrays["Qraw"]+arrays["delta"],arrays["Qused"])
        assert all(torch.equal(v, model.state_dict()[k]) for k,v in state.items())
        assert model.calls==105
    budget.finish(210)
    checks["all_210_artificial_forwards_with_native_geometry_and_clock_boundaries"] = len(journal)==210 and torch.equal(rng,torch.get_rng_state())
    checks["211th_blocked_before_model"] = rejected(lambda: budget.claim("F",ids[-1]))
    summary=native.latency_summary(np,[10**9]*5+[10**6*k for k in range(1,101)])
    checks["exclude_first_five_samples_from_percentiles"] = summary["warmup"] == 5 and summary["measured"] == 100 and np.allclose([summary["P50_ms"],summary["P95_ms"]],[50.5,95.05])
    tree=ast.parse(SOURCE.read_bytes())
    calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
    checks["one_model_call_site_and_no_training_calls"] = sum(isinstance(n.func,ast.Name) and n.func.id=="model" for n in calls)==1 and not any(
        isinstance(n.func,ast.Attribute) and n.func.attr in {"backward","step","zero_grad","train"} for n in calls)
    return budget.attempts


def main():
    FIXTURE.mkdir()
    torch.set_num_threads(2)
    checks = {}
    try:
        check_contracts(checks)
        count = check_predictions(checks)
        assert all(checks.values()), checks
    except Exception as error:
        emit(FIXTURE/"result_v1.json",dict(status="ARTIFICIAL_CPU_FAILED",checks=checks,error=repr(error)))
        raise
    result=dict(status="ARTIFICIAL_CPU_PASS",checks=checks,artificial_forwards=count,real_forward_calls=0,
                real_arrays_loaded=0,CUDA_exercised=False,server_writes=0,torch_version=str(torch.__version__))
    emit(FIXTURE/"result_v1.json",result)
    print(json.dumps(result),flush=True)


if __name__ == "__main__":
    main()
