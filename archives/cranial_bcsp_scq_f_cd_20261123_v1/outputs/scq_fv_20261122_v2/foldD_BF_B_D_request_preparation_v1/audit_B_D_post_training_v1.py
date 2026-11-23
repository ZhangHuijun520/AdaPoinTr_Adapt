"""Read-only checkpoint and training-evidence audit for SCQ-FV B_D."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import subprocess

import runpy
from types import SimpleNamespace

HERE = Path("outputs/scq_fv_20261122_v2/foldD_BF_B_D_request_preparation_v1").resolve()
HISTORY = HERE.parents[1] / "scq_prime_foldC_training_preparation_20261122_v1"
EVIDENCE = HERE / "authorized_B_D_execution_v1"
ROOT = HERE / "B_D_post_training_freeze_v1"
AUTHORIZED = "b0387bf71ce225842b3d4624fb1c3c72cb81fad5594345f613f7b7ae6babdfc6"
probe_path = HISTORY.parent / "scq_prime_cuda_preparation_20261122_v1/probe_readonly_v1.py"
assert hashlib.sha256(probe_path.read_bytes()).hexdigest() == "f3085e0f5b302575b9a526c0314c33d13ff420e0ddb4e3b875d2ae2d4b97c568"
probe = SimpleNamespace(**runpy.run_path(str(probe_path)))
CLIENT = ["wsl.exe", "-d", "Ubuntu-20.04", "--exec", "/home/zhj/.local/bin/hpc5000"]
CHECKPOINT = "ckpt-last.pth"
OUTPUT_MEMBERS = {
    "SCQ_geometry.jsonl", CHECKPOINT, "completion.json", "exposure.json", "initialization.json",
    "metrics.jsonl", "model_construction.json", "optimizer_actual_defaults.json",
    "optimizer_parameter_groups.json", "order_plan.json", "resources.jsonl", "run_identity.json",
}
OUTPUT_FILES = OUTPUT_MEMBERS | {"launch.log", "exit_code.txt", "worker.pid", "payload_manifest.json"}
INVENTORY = """p=Path(out)
assert p.resolve(strict=True)==p and p.is_dir()
assert {x.name for x in p.iterdir()}==set(names)|{'tmp'}
temp=p/'tmp'
assert temp.is_dir() and not temp.is_symlink() and not any(temp.iterdir())
s=subprocess.run(['tmux','has-session','-t','='+session],capture_output=True,text=True,timeout=4)
assert s.returncode==1 and any(x in s.stderr for x in ('not found','no server running','No such file or directory','Connection refused'))
pid=int((p/'worker.pid').read_text());assert not Path('/proc',str(pid)).exists()
assert (p/'exit_code.txt').read_text().strip()=='0'
files={}
for n,f in [(n,p/n) for n in names]+[(n,Path(v)) for n,v in controls.items()]:
 assert f.resolve(strict=True)==f
 with os.fdopen(os.open(f,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
  a=os.fstat(stream.fileno())
  limit=536870912 if n=='ckpt-last.pth' else 33554432
  assert stat.S_ISREG(a.st_mode) and 0<=a.st_size<=limit,str(f)
  h=hashlib.sha256()
  for block in iter(lambda:stream.read(4194304),b''):h.update(block)
  b=os.fstat(stream.fileno())
  assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns,b.st_ctime_ns),str(f)
  files[n]=dict(bytes=b.st_size,sha256=h.hexdigest(),inode=b.st_ino,mtime_ns=b.st_mtime_ns)
output(dict(files=files,pid=pid,directories=['tmp'],exit_code=0,worker_absent=True,tmux_absent=True))
"""


def read(path):
    return json.loads(path.read_bytes())


def save(name, data):
    with (ROOT / name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def lines(path):
    with path.open("rb") as stream:
        for line in stream:
            assert line.endswith(b"\n"), path
            yield json.loads(line)


def get(src, dest, meta):
    assert not dest.exists()
    wsl = "/mnt/" + dest.drive[0].lower() + dest.as_posix()[2:]
    result = subprocess.run(CLIENT + ["get", src, wsl], capture_output=True, timeout=45)
    assert result.returncode == 0, (src, result.returncode, result.stderr[-300:])
    assert dest.stat().st_size == meta["bytes"] and sha(dest) == meta["sha256"], src


def verify_training(d, q, remote, pair):
    manifest = read(d / "payload_manifest.json")["files"]
    assert len(manifest) == len(OUTPUT_MEMBERS) and {row["name"] for row in manifest} == OUTPUT_MEMBERS
    for row in manifest:
        measured = remote["files"][row["name"]]
        assert (row["bytes"], row["sha256"]) == (measured["bytes"], measured["sha256"]), row["name"]
    checkpoint = remote["files"][CHECKPOINT]
    done, init, model, run = (read(d / f"{name}.json") for name in
                               ("completion", "initialization", "model_construction", "run_identity"))
    expected_identity = {key: q[key] for key in ("fold", "seed", "variant")}
    assert all(run[key] == val for key, val in expected_identity.items()) and run["stage"] == q["stage"]
    assert run["native_admission_sha256"] == q["admission"]["audit"]["sha256"]
    assert run["SSM_gradient_non_bitwise_reproducibility_disclosed"] is True
    assert expected_identity == model["run_identity"] == done["scq_prime_run_identity"]
    common = pair["pair_common_sha256"]
    assert model["common_initial_state_SHA256"] == common
    assert model["pair_contract_sha256"] == q["pair_contract"]["sha256"]
    assert model["lqi"]["artificial_fixture"] is False
    head = model["scq"]
    assert head["variant"] == "B" and head["common_initialization_preserved"] is True
    assert head["new_parameters"] == 0 and head["total_parameters"] == 39903169 and head["initialization_sha256"] is None
    assert init["seed"] == q["seed"]
    assert all(len(init[key]) == 64 and all(c in "0123456789abcdef" for c in init[key])
               for key in ("parameter_sha256", "persistent_state_sha256"))
    historical = HISTORY / "B_C_post_training_freeze_v1"
    historical_receipt = read(historical / "B_C_post_training_freeze_receipt_v1.json")
    assert historical_receipt["status"] == "FORMAL_SCQ_PRIME_POST_TRAINING_FREEZE_AUDIT_PASS"
    assert historical_receipt["run_identity"] == {"fold":"C","variant":"B","seed":q["seed"]}
    assert all(historical_receipt[k] == q["identity"][k] for k in ("hostname","gpu_uuid","driver_version"))
    assert historical_receipt["common_initial_state_SHA256"] == common
    for key in ("parameter_sha256", "persistent_state_sha256"):
        assert init[key] == historical_receipt["initialization"][key], key
    assert done["checkpoint_sha256"] == checkpoint["sha256"]
    assert (done["optimizer_updates"], done["traversals"], done["case_exposures"]) == (3900, 100, 31200)
    assert done["counts"] == dict(forward=3900, backward=3900, clip=3900, step=3900, lr_scheduler=100, bn_scheduler=100)
    assert all(done[key] is False for key in ("bncal_executed", "evaluation_executed", "resume"))

    old = HISTORY.parent / "cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload"
    order = old / PurePosixPath(q["order_plan"]["path"]).name
    fold_path = old / PurePosixPath(q["QC"]["fold_binding"]["path"]).name
    manifest_path = old / PurePosixPath(q["QC"]["manifests"]["8192"]["path"]).name
    assert sha(order) == q["order_plan"]["sha256"] and sha(fold_path) == q["QC"]["fold_binding"]["sha256"]
    assert sha(manifest_path) == q["QC"]["manifests"]["8192"]["sha256"]
    fold = read(fold_path)["folds"]["D"]
    ids = set(fold["train_case_ids"])
    source = {row["case_id"]: row["source_id"] for row in lines(manifest_path) if row["case_id"] in ids}
    assert len(source) == 315 and set(source.values()) == set(fold["train_sources"]) and len(set(source.values())) == 63
    plan = read(d / "order_plan.json")
    assert plan == read(order) and plan["case_ids"] == fold["train_case_ids"]
    order_sha = canonical(plan)
    assert init["order_sha256"] == done["order_sha256"] == order_sha
    metrics = iter(lines(d / "metrics.jsonl"))
    geometry = iter(lines(d / "SCQ_geometry.jsonl"))
    case_count, source_count, drops = Counter(), Counter(), Counter()
    step = 0
    for epoch, spec in enumerate(plan["epochs"]):
        assert spec["epoch"] == epoch and len(spec["batches"]) == 39 and len(spec["dropped"]) == 3
        drops.update(spec["dropped"])
        lr = .0001 * max(.9 ** (epoch / 21), .02)
        bn = max(.9 * .5 ** (epoch / 21), .01)
        for batch, cases in enumerate(spec["batches"]):
            step += 1
            m, g = next(metrics), next(geometry)
            assert all((row["step"], row["epoch"], row["batch"], row["case_ids"]) == (step, epoch, batch, cases)
                       for row in (m, g))
            assert len(cases) == 8 and m["source_ids"] == [source[c] for c in cases]
            assert m["optimizer_step_committed"] is True and m["clip_max_norm"] == 10
            assert m["LR"] == [lr, lr] and m["BN_momentum"] == bn
            assert all(math.isfinite(m[k]) and m[k] >= 0 for k in ("loss", "loss_sparse", "loss_dense", "grad_norm_before_clip"))
            assert g["frame"] == "D-only normalized" and set(g["loss_components"]) == {"coarse_CD", "dense_CD"}
            assert math.isclose(g["reconstruction_sum"], sum(g["loss_components"].values()), abs_tol=1e-10)
            assert math.isclose(g["reconstruction_sum"], m["loss"], rel_tol=2e-7, abs_tol=1e-10)
            shapes = g["geometry"]
            assert set(shapes) == {"coarse", "dense", "Q0", "delta"}
            assert shapes["Q0"]["centroid"] == shapes["coarse"]["centroid"]
            assert all(v == 0 for v in shapes["delta"]["mean_norm"] + shapes["delta"]["max_norm"])
            case_count.update(cases)
            source_count.update(m["source_ids"])
    assert step == 3900 and next(metrics, None) is None and next(geometry, None) is None
    assert sum(case_count.values()) == sum(source_count.values()) == 31200 and sum(drops.values()) == 300
    assert read(d / "exposure.json") == dict(case=dict(case_count), source=dict(source_count),
                                            dropped_case=dict(drops), order_sha256=order_sha)
    resource_rows = list(lines(d / "resources.jsonl"))
    assert [(r["phase"], r["committed_step"]) for r in resource_rows] == (
        [("after_step", k) for k in range(1, 3901)] + [("before_final", 3900), ("after_final", 3900)])
    caps = pair["resources"]
    for row in resource_rows:
        assert row["limits"] == caps and row["resource_guard_passed"] and not row["failed_checks"]
        assert row["own_PID"] == remote["pid"]
        assert row["RSS"] <= caps["RSS_bytes"] and row["output_bytes"] <= caps["output_bytes"]
        assert row["elapsed_seconds"] <= caps["wall_seconds"] and row["device_MiB"] <= caps["device_MiB"]
        assert row["peak_allocated"] <= row["peak_reserved"] <= caps["torch_peak_bytes"]
    optimizer = read(d / "optimizer_actual_defaults.json")
    assert (optimizer["lr"], optimizer["betas"], optimizer["eps"], optimizer["amsgrad"]) == (.0001, [.9, .999], 1e-8, False)
    groups = read(d / "optimizer_parameter_groups.json")
    assert len(groups) == len({r["name"] for r in groups}) and groups
    assert all(r["weight_decay"] == (.0005 if r["reason"] == "matrix_default" else 0.) for r in groups)
    assert not any(r["name"].startswith("base_model.scq.") for r in groups)
    return dict(run_identity=expected_identity, common_initial_state_SHA256=common, initialization=init,
                checkpoint=dict(path=q["output"] + "/" + CHECKPOINT, bytes=checkpoint["bytes"], sha256=checkpoint["sha256"]),
                order_file_sha256=q["order_plan"]["sha256"], actual_order_canonical_sha256=order_sha,
                same_seed_B_C_initialization_matches=True, historical_B_C_receipt_sha256=sha(historical / "B_C_post_training_freeze_receipt_v1.json"),
                updates=step, traversals=100, exposures=31200, drop_events=300, sources=63, training_cases=315,
                optimizer_groups=len(groups), geometry_rows=step, resource_rows=len(resource_rows),
                resource_peak={key: max(r[key] for r in resource_rows)
                               for key in ("RSS", "peak_allocated", "peak_reserved", "device_MiB", "output_bytes")},
                elapsed_seconds=done["elapsed_seconds"], bncal_executed=False, development_evaluation_executed=False, resume=False)


def main():
    ROOT.mkdir()
    downloads = ROOT / "downloads"
    downloads.mkdir()
    stage = "request"
    try:
        request = HERE / "SCQ_FV_B_D_seed2026112101_train_20261123_v1_request.json"
        assert sha(request) == AUTHORIZED
        q = read(request)
        pair_path = HERE / PurePosixPath(q["pair_contract"]["path"]).name
        assert sha(pair_path) == q["pair_contract"]["sha256"]
        pair = read(pair_path)
        launch = q["launch_contract"]
        controls = {key: launch[key+"_path"] for key in ("request", "authorization", "runtime", "launcher")}
        controls["claim"] = q["launch_attempt"]
        identity = q["identity"]
        values = dict(host=identity["hostname"], project=identity["project"], out=q["output"],
                      names=sorted(OUTPUT_FILES), controls=controls, session=launch["tmux_session"])
        stage = "inventory_and_checkpoint_sha256"
        before = probe.query(INVENTORY, values, 40)
        save("server_inventory_before_v1.json", before)
        stage = "controls"
        local = {"request": request, "authorization": EVIDENCE/"authorization.json",
                 "runtime": EVIDENCE/"runtime.json", "launcher": EVIDENCE/"launch_once.sh"}
        for key, path in local.items():
            assert (before["files"][key]["bytes"], before["files"][key]["sha256"]) == (path.stat().st_size, sha(path))
        auth = read(local["authorization"])
        assert auth["schema"] == "bcsp-scq-fv-d-bf-training-authorization-v1" and auth["request_sha256"] == AUTHORIZED and auth["explicit_user_authorization"] is True
        assert isinstance(auth["user_authorization_text"], str) and auth["user_authorization_text"].strip()
        assert read(local["runtime"]) == dict(schema="bcsp-scq-fv-d-bf-training-runtime-v1", request_sha256=AUTHORIZED,
                                               authorization_sha256=sha(local["authorization"]))
        get(controls["claim"], downloads/"launch_attempt.json", before["files"]["claim"])
        assert read(downloads/"launch_attempt.json") == dict(status="CLAIMED_BEFORE_TMUX", request_sha256=AUTHORIZED)
        stage = "capture_exact_training_logs"
        for name in sorted(OUTPUT_FILES - {CHECKPOINT}):
            get(q["output"] + "/" + name, downloads/name, before["files"][name])
        stage = "parse_all_training_evidence"
        report = verify_training(downloads, q, before, pair)
        stage = "independent_final_inventory"
        after = probe.query(INVENTORY, values, 40)
        save("server_inventory_after_v1.json", after)
        assert before == after
        result = dict(status="FORMAL_SCQ_FV_D_BF_POST_TRAINING_FREEZE_AUDIT_PASS", request_sha256=AUTHORIZED,
                      pair_contract_sha256=q["pair_contract"]["sha256"], hostname=identity["hostname"],
                      gpu_uuid=identity["gpu_uuid"], driver_version=identity["driver_version"],
                      exit_code=after["exit_code"], process_absent=True, tmux_absent=True, stable_inventory=True,
                      output_files=len(OUTPUT_FILES), manifest_members=len(OUTPUT_MEMBERS), server_writes=0,
                      checkpoint_loaded=False, **report)
        save("B_D_post_training_freeze_receipt_v1.json", result)
        print(json.dumps(result))
    except BaseException as exc:
        save("audit_stopped_v1.json", dict(status="AUDIT_INCOMPLETE", stage=stage, error=repr(exc)))
        raise


if __name__ == "__main__":
    main()

