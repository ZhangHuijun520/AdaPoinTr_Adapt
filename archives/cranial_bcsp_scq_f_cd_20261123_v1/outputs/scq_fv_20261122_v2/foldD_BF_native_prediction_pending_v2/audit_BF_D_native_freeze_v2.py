"""Read-only archive and execution audit for SCQ-FV Fold D B/F Native predictions."""
from collections import Counter
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile

import numpy as np

import runpy
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "authorized_prediction_execution_v1"
KEY = "4a5eee455d20025369f13c6e5b1a568e60acb394bee6bc65908e3094aaf08005"
probe_path = HERE.parents[1] / "scq_prime_cuda_preparation_20261122_v1/probe_readonly_v1.py"
assert hashlib.sha256(probe_path.read_bytes()).hexdigest()=="f3085e0f5b302575b9a526c0314c33d13ff420e0ddb4e3b875d2ae2d4b97c568"
probe=SimpleNamespace(**runpy.run_path(str(probe_path)))
scope=json.loads((HERE/"BF_D_native_pending_install_scope_v1.json").read_bytes())
assert hashlib.sha256((HERE/"BF_D_native_pending_install_scope_v1.json").read_bytes()).hexdigest()=="b84c8b2d8ddbbfe16a7ff21feaadff56507f6ec95dddcf3c9bc7b99b4ae05f39"
r,=(x for x in scope["install_files"] if x["path"].endswith("bcsp_scq_fv_BF_D_native_v2.py"))
entry_path=Path(r["local_path"])
assert hashlib.sha256(entry_path.read_bytes()).hexdigest()==r["sha256"]
entry=SimpleNamespace(**runpy.run_path(str(entry_path)))

ROOT = HERE / "post_prediction_freeze_v2"
ARCHIVE = "development_predictions_v1.tar.gz"
SIDECARS = (ARCHIVE + ".sha256", ARCHIVE + ".bytes", ARCHIVE + ".contents.sha256")
PACKED_LOGS = {"forward_attempts.jsonl", "geometry_summary.jsonl", "inference_complete.json",
               "inference_manifest.jsonl", "resources.jsonl"}
TOP = PACKED_LOGS | set(SIDECARS) | {ARCHIVE, "completion.json", "launch.log", "exit_code.txt", "worker.pid"}
CLIENT = ["wsl.exe", "-d", "Ubuntu-20.04", "--exec", "/home/zhj/.local/bin/hpc5000"]
INVENTORY = """o=Path(out);assert o.resolve(strict=True)==o and o.is_dir()
assert set(x.name for x in o.iterdir())==set(top)|{'predictions','tmp'}
for n in ('predictions','tmp'):
 p=o/n;assert p.resolve(strict=True)==p and p.is_dir()
assert not any((o/'tmp').iterdir())
ps=sorted((o/'predictions').iterdir());assert len(ps)==210
pid=int((o/'worker.pid').read_text())
assert not Path('/proc',str(pid)).exists() and (o/'exit_code.txt').read_text().strip()=='0'
s=subprocess.run(['tmux','has-session','-t','='+session],capture_output=True,text=True,timeout=5)
assert s.returncode==1 and any(x in s.stderr for x in ('not found','no server running','No such file or directory','Connection refused'))
def row(p,limit):
 assert p.resolve(strict=True)==p
 with os.fdopen(os.open(p,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as f:
  a=os.fstat(f.fileno());assert stat.S_ISREG(a.st_mode) and 0<a.st_size<=limit
  h=hashlib.sha256()
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
  z=os.fstat(f.fileno());assert (a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns,z.st_ctime_ns)
 return [a.st_size,h.hexdigest()]
rows=[['predictions/'+p.name,*row(p,262144)] for p in ps]
files={n:row(o/n,41943040 if n.endswith('.tar.gz') else 2097152) for n in top}
output(dict(pid=pid,predictions=len(rows),prediction_bytes=sum(r[1] for r in rows),predictions_digest=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),files=files,exit_code=0,worker_absent=True,tmux_absent=True))
"""


def checked_zip(left, right):
    assert len(left) == len(right)
    return zip(left, right)


def save(name, data):
    with (ROOT / name).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def get(src, dest, expected):
    assert not dest.exists()
    wsl = "/mnt/" + dest.drive[0].lower() + dest.as_posix()[2:]
    result = subprocess.run(CLIENT + ["get", src, wsl], capture_output=True, timeout=55)
    assert result.returncode == 0, (src, result.returncode, result.stderr[-400:])
    assert [dest.stat().st_size, entry.sha(dest)] == expected, dest


def json_lines(raw):
    assert raw.endswith(b"\n")
    return [json.loads(line) for line in raw.splitlines()]


def file_sha(raw):
    return hashlib.sha256(raw).hexdigest()


def arrays(raw, arm):
    fields = {"coarse", "prediction"}
    if arm == "F":
        fields |= {"Qraw", "Qused", "delta"}
    with np.load(io.BytesIO(raw), allow_pickle=False) as z:
        assert len(z.files) == len(fields) and set(z.files) == fields
        for key in fields:
            value=z[key]
            assert value.dtype==np.float32 and value.shape==(8192 if key=="prediction" else 256,3)
            assert np.isfinite(value).all(),key
        if arm=="F":
            assert np.array_equal(z["Qused"],z["coarse"])
            assert np.allclose(z["Qraw"]+z["delta"],z["Qused"],rtol=2e-6,atol=2e-7)
    return sorted(fields)


def inspect_archive(q, index, local, remote):
    state = json.loads((local / "completion.json").read_bytes())
    assert state["status"] == "PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT" and state["request_sha256"] == KEY
    assert state["forwards"] == 210 and state["archive"]["path"] == q["output"] + "/" + ARCHIVE
    size, sha = remote["files"][ARCHIVE]
    assert (state["archive"]["bytes"], state["archive"]["sha256"]) == (size, sha)
    assert (local / SIDECARS[0]).read_text().strip() == f"{sha}  {ARCHIVE}"
    assert (local / SIDECARS[1]).read_text().strip() == str(size)
    declared = state["archive"]["members"]
    assert len(declared) == len({r["name"] for r in declared}) == 215
    expected_order = [(a, row) for a in entry.ARMS for row in index["inputs"]]
    expected_names = [f"predictions/{a}_D__{r['case_id']}.npz" for a, r in expected_order]
    assert len(expected_order) == len(expected_names) == len(set(expected_names)) == 210
    assert [r["name"] for r in declared[:210]] == expected_names and {r["name"] for r in declared[210:]} == PACKED_LOGS
    assert (local / SIDECARS[2]).read_text().splitlines() == [f"{r['sha256']}  {r['name']}" for r in declared]
    logs, observed, diagnostic_fields = {}, [], []
    timing = {a:[] for a in entry.ARMS}
    with tarfile.open(local / ARCHIVE, "r:gz") as stream:
        members = stream.getmembers()
        assert len(members) == 215
        for i, (member, rec) in enumerate(checked_zip(members, declared)):
            assert member.isfile() and member.name == rec["name"] and member.size == rec["bytes"]
            assert 0 < member.size <= (262144 if i < 210 else 2097152)
            raw = stream.extractfile(member).read(member.size + 1)
            assert len(raw) == member.size and file_sha(raw) == rec["sha256"], member.name
            if i < 210:
                arm, row = expected_order[i]
                fields = arrays(raw, arm)
                diagnostic_fields.append(fields)
                observed.append([member.name, member.size, rec["sha256"]])
            else:
                assert [rec["bytes"], rec["sha256"]] == remote["files"][member.name]
                logs[member.name] = raw
    observed.sort()
    observed_digest = file_sha(json.dumps(observed, separators=(",", ":")).encode())
    assert observed_digest == remote["predictions_digest"] and remote["predictions"] == 210
    assert sum(r[1] for r in observed) == remote["prediction_bytes"]

    journal, manifest, geometry = (json_lines(logs[n]) for n in
        ("forward_attempts.jsonl", "inference_manifest.jsonl", "geometry_summary.jsonl"))
    assert len(journal) == len(manifest) == len(geometry) == 210
    for i, (arm, row) in enumerate(expected_order):
        label, cid = f"{arm}_D", row["case_id"]
        assert journal[i] == dict(forward_index=i+1, run=label, case_id=cid, status="CLAIMED_BEFORE_FORWARD")
        m, g = manifest[i], geometry[i]
        for key, value in dict(run=label, variant=arm, case_id=cid, source_id=row["source_id"], fold="D",
                seed=entry.SEED, n_input=8192, n_output=8192, input_sha256=row["input"]["sha256"], normalization=row["normalization"],
                checkpoint_sha256=q["model_records"][arm]["checkpoint"]["sha256"], forward_index=i+1,
                diagnostic_fields=diagnostic_fields[i], prediction=declared[i]).items():
            assert m[key] == value, (i, key)
        assert type(m["synchronized_forward_ns"]) is int and m["synchronized_forward_ns"]>0
        assert m["timing_warmup"] is (len(timing[arm])<5)
        timing[arm].append(m["synchronized_forward_ns"])
        assert g["run"] == label and g["case_id"] == cid and g["frame"] == "native_D_only_normalized_no_GT"
        assert ("Qraw" in g) is (arm != "B")
        if arm != "B":
            assert 0 <= g["delta_mean_norm"] <= g["delta_max_norm"] and math.isfinite(g["delta_max_norm"])
    done = json.loads(logs["inference_complete.json"])
    assert done["status"] == "SCQ_FV_BF_D_NATIVE_210_COMPLETE" and done["request_sha256"] == KEY and done["forwards"] == 210
    assert all(done[k] == 0 for k in ("training_updates", "BNCal", "loss", "backward"))
    assert [model["run"] for model in done["models"]] == ["B_D", "F_D"]
    state_summary = {}
    efficiency = {}
    for arm, model in checked_zip(entry.ARMS, done["models"]):
        assert model["forwards"] == 105 and model["identity"] == entry.identity(arm)
        assert model["state_before"] == model["state_after"] and len(model["state_before"]) == 64
        rng = model["RNG_before"]
        assert model["RNG_after"] == rng and set(rng) == {"CPU", "CUDA", "Python", "numpy"}
        assert all(isinstance(v, str) and v for v in rng.values())
        state_summary[arm] = dict(model_fingerprint_equal=True, RNG_equal=True)
        measured=entry.latency_summary(np,timing[arm])
        e=model["efficiency"]
        assert all(e[k]==v for k,v in measured.items()) and 0<e["peak_allocated_bytes"]<=e["peak_reserved_bytes"]<=q["limits"]["torch_peak_bytes"]
        efficiency[arm]=e
    resource = json_lines(logs["resources.jsonl"])
    expected_resource = []
    for i, arm in enumerate(entry.ARMS):
        expected_resource.append((f"model_start:{arm}_D", i*105))
        for j in range(i*105, (i+1)*105):
            expected_resource.extend([("before_forward", j), ("after_forward", j+1)])
    expected_resource.append(("all_complete", 210))
    assert [(r["phase"], r["forwards"]) for r in resource] == expected_resource
    caps = q["limits"]
    for row in resource:
        v = row["values"]
        assert row["container_PID"] == remote["pid"] and row["failed_checks"] == [] and all(row["checks"].values())
        for key, limit in (("RSS_bytes", "RSS_bytes"), ("output_bytes", "output_bytes"), ("device_MiB", "device_MiB"),
                           ("peak_allocated", "torch_peak_bytes"), ("peak_reserved", "torch_peak_bytes"),
                           ("elapsed_seconds", "wall_seconds")):
            assert 0 <= v[key] <= caps[limit]
        assert v["free_disk_bytes"] >= caps["minimum_free_disk_bytes"]
    for arm in entry.ARMS:
        i=entry.ARMS.index(arm)
        values=[row["values"] for row in resource[211*i:211*(i+1)]]
        for metric in ("allocated","reserved"):
            assert max(v["peak_"+metric] for v in values)==efficiency[arm]["peak_"+metric+"_bytes"],(arm,metric)
    ratio={k:efficiency["F"][k]/efficiency["B"][k] for k in ("P50_ms","peak_allocated_bytes","peak_reserved_bytes")}
    return dict(archive_sha256=sha, archive_bytes=size, archive_members=215, prediction_files=210,
                matched_cases=105, sources=21, per_arm={"B":105, "F":105}, efficiency=efficiency, efficiency_F_over_B=ratio,
                resource_rows=len(resource), model_state_and_RNG=state_summary, predictions_digest=observed_digest)


def main():
    ROOT.mkdir()
    local = ROOT / "audit_readback"
    local.mkdir()
    stage = "request_binding"
    try:
        request = HERE / "SCQ_FV_BF_D_native_execution_request_v1.json"
        assert entry.sha(request) == KEY
        q = json.loads(request.read_bytes())
        index_path = HERE / PurePosixPath(q["input_index"]["path"]).name
        assert entry.sha(index_path) == q["input_index"]["sha256"]
        index = json.loads(index_path.read_bytes())
        assert index["arms"]==["B","F"] and index["fold"]=="D" and index["cases"]==105 and index["sources"]==21
        ordered=index["inputs"]
        assert len(ordered)==len({r["case_id"] for r in ordered})==105
        assert set(Counter(r["source_id"] for r in ordered).values())=={5}
        ident, launch = q["identity"], q["launch_contract"]
        meta = dict(host=ident["hostname"], project=ident["project"])
        stage = "server_first_inventory"
        values = {**meta, "out": q["output"], "top": sorted(TOP), "session": launch["tmux_session"]}
        before = probe.query(INVENTORY, values, 45)
        save("server_inventory_before_v1.json", before)
        stage = "control_hashes"
        remote_controls = [launch["request_path"], launch["authorization"], launch["runtime"], launch["launcher"]]
        local_controls = [request, EVIDENCE / "authorization.json", EVIDENCE / "runtime.json", EVIDENCE / "launch_once.sh"]
        rows = [[p, f.stat().st_size, entry.sha(f)] for p, f in checked_zip(remote_controls, local_controls)]
        observed = probe.query(probe.HASHES, {**meta, "paths":[(p,n) for p,n,_ in rows]}, 25)
        assert observed == rows
        entry.authorizations({"sha256":KEY},
            {"path":str(local_controls[1]),"bytes":local_controls[1].stat().st_size,"sha256":entry.sha(local_controls[1])},
            {"path":str(local_controls[2]),"bytes":local_controls[2].stat().st_size,"sha256":entry.sha(local_controls[2])})
        save("server_control_hashes_v1.json", observed)
        claim_path = q["launch_attempt"]
        claim = probe.query("p=Path(claim);assert p.resolve(strict=True)==p and p.stat().st_size<=512\noutput(json.loads(p.read_bytes()))\n",
                            {**meta, "claim":claim_path}, 15)
        assert claim == dict(status="CLAIMED_BEFORE_TMUX", request_sha256=KEY)
        stage = "archive_download_and_check"
        for name in (ARCHIVE, *SIDECARS, "completion.json"):
            get(q["output"] + "/" + name, local / name, before["files"][name])
        result = inspect_archive(q, index, local, before)
        stage = "server_second_inventory"
        after = probe.query(INVENTORY, values, 45)
        save("server_inventory_after_v1.json", after)
        assert before == after
        receipt = dict(status="FORMAL_SCQ_FV_BF_D_NATIVE_POST_PREDICTION_FREEZE_PASS", request_sha256=KEY,
                       hostname=ident["hostname"], output=q["output"], exit_code=0, stable_remote_inventory=True,
                       server_writes=0, audit_added_forwards=0, scoring_executed=False,
                       local_archive_readback=str(local/ARCHIVE), **result)
        save("BF_D_post_prediction_freeze_receipt_v1.json", receipt)
        print(json.dumps(receipt))
    except BaseException as exc:
        save("audit_stopped_v1.json", dict(status="AUDIT_INCOMPLETE", stage=stage, error=repr(exc)))
        raise


if __name__ == "__main__":
    main()
