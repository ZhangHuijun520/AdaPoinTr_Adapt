"""Generate P5 predictions from frozen P3 development caches, without the donor."""

import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import time
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fcsp_p5_common_v1 as common
from fcsp_p5_common_v1 import append, clean, file_record, read, require, sha, write_json


ARMS = ("B0-Global", "B1-Local")
DEFECTS = {"bilateral", "frontoorbital", "parietotemporal", "random_1", "random_2"}
COUNTS = dict(cases=210, head_forward=420, shared_native=210, donor_forward=0, optimizer_step=0)


def validate_index(idx, manifest):
    require(idx["schema"] == "fcsp-p5-server-head-index-v1" and idx["counts"] == COUNTS, "frozen prediction counts")
    models = {(r["fold"], r["arm"]): r for r in idx["models"]}
    expected = {(f, a) for f in "CD" for a in ARMS}
    require(set(models) == expected and len(idx["models"]) == 4, "four distinct models")
    for f in "CD":
        a, b = (models[f, arm] for arm in ARMS)
        require(a["seed"] == b["seed"] == 0
                and all(a[k] == b[k] for k in ("scale", "initial_state_sha256", "order", "train_selection_sha256")),
                f"frozen model pairing: {f}")
    dev = {(m["fold"], m["case_id"]): m for m in manifest if m["split"] == "development"}
    require(len(manifest) == 840 and len(dev) == len(idx["cases"]) == 210, "cache manifest count")
    root = PurePosixPath(idx["cache_manifest"]["path"]).parent
    cases = set()
    sources = {f: {} for f in "CD"}
    for r in idx["cases"]:
        f, k, s = (r[key] for key in ("fold", "case_id", "source_id"))
        case = k.split("__")
        require(f in "CD" and len(f) == 1 and len(case) == 3 and case[0] == "train"
                and re.fullmatch("[0-9]{3}", case[1]) and case[2] in DEFECTS and s == "train:" + case[1],
                f"case identity: {k}")
        require((f, k) not in cases and (f, k) in dev, f"development pairing: {k}")
        cases.add((f, k))
        group = sources[f].setdefault(s, set())
        group.add(case[2])
        old = dev[f, k]
        name = f"{f}__{k}.npz"
        require(old["capture"]["file"] == name and r["cache"] ==
                dict(path=str(root/name), bytes=old["capture"]["bytes"], sha256=old["capture"]["sha256"])
                and all(r[key] == old[key] for key in ("source_id", "normalization", "input_sha256"))
                and r["donor_checkpoint_sha256"] == old["checkpoint_sha256"], f"exact cache member: {k}")
        require(len(r["normalization"]["center"]) == 3
                and all(math.isfinite(x) for x in r["normalization"]["center"])
                and math.isfinite(r["normalization"]["scale"]) and r["normalization"]["scale"] > 0,
                f"normalization: {k}")
    require(set(dev) == cases and not (sources["C"].keys() & sources["D"].keys())
            and all(len(groups) == 21 and all(v == DEFECTS for v in groups.values())
                    for groups in sources.values()), "balanced source sets")
    return models


def arrays(blob, shapes, expected=None):
    with np.load(io.BytesIO(blob), allow_pickle=False) as z:
        require(len(z.files) == len(set(z.files)) and set(z.files) == set(expected or shapes), "exact NPZ schema")
        ret = {k: z[k] for k in shapes}
    for k, shape in shapes.items():
        a = ret[k]
        require(a.dtype == np.dtype("<f4") and a.shape == shape and np.isfinite(a).all(), f"FP32 array: {k}")
    return ret


def read_cache(row):
    keys = ("Q","H","P0","geometry","neighbors","scale")
    c = arrays(read(row["cache"], 1048576),
               dict(Q=(256, 3), H=(256, 384), P0=(256, 32, 3), geometry=(256, 10)), keys)
    require(all(sha(c[k].tobytes(order="C")) == row[k+"_sha256"] for k in ("Q","P0")), "ordered anchor")
    return c


def state_sha(model):
    digest = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        digest.update(repr((name, str(value.dtype), tuple(value.shape))).encode())
        digest.update(value.detach().cpu().numpy().tobytes())
    return digest.hexdigest()


def snapshot(model):
    n = np.random.get_state()
    items = (state_sha(model), tuple(m.training for m in model.modules()),
             tuple(p.requires_grad for p in model.parameters()), torch.get_rng_state().numpy().tobytes(),
             tuple(x.cpu().numpy().tobytes() for x in torch.cuda.get_rng_state_all()) if torch.cuda.is_initialized() else (),
             random.getstate(), (n[0], n[1].tobytes(), *n[2:]))
    return sha(repr(items).encode())


def load_model(record, head, device):
    result = torch.load(io.BytesIO(read(record["checkpoint"], 1048576)), map_location="cpu", weights_only=True)
    weights = result.pop("state_dict")
    require(result == dict(request_sha256=record["request_sha256"], fold=record["fold"],
                          arm=record["arm"], seed=0, step=3900), "checkpoint identity")
    with torch.random.fork_rng(devices=[]):
        model = head["PlacementHead"](384, record["scale"]["b_train_fp64"])
    expected = model.state_dict()
    require(set(weights) == set(expected)
            and all(w.dtype == expected[k].dtype and w.shape == expected[k].shape
                    and bool(torch.isfinite(w).all()) for k, w in weights.items()), "exact finite head tensors")
    model.load_state_dict(weights, strict=True)
    require(state_sha(model) == record["final_state_sha256"]
            and model.b_train.numpy().tobytes().hex() == record["scale"]["b_train_float32_bytes"], "frozen trained state")
    return model.eval().requires_grad_(False).to(device)


def head_forward(model, head, arm, cache, device):
    h, g, p0 = (torch.from_numpy(cache[k]).unsqueeze(0).to(device) for k in ("H","geometry","P0"))
    logits = []
    hook = model.net[-1].register_forward_hook(lambda _, __, v: logits.append(v.detach()))
    try:
        with torch.inference_mode(), torch.autocast(device_type=device.type, enabled=False):
            p = model(h, head["geometry_condition"](g, arm), p0)
    finally:
        hook.remove()
    require(len(logits) == 1, "one head call")
    result = p[0].cpu().numpy()
    delta = np.abs(result.astype(np.float64) - cache["P0"])
    scale = float(model.b_train)
    margin = np.finfo(np.float32).eps * (np.abs(cache["P0"].astype(np.float64)) + scale)
    require(result.shape == (256,32,3) and result.dtype == np.float32 and np.isfinite(result).all()
            and np.all(delta <= scale + margin), "bounded ordered prediction")
    norm = np.linalg.norm(delta, axis=-1)
    return result, dict(max_component_norm=float(delta.max()), max_euclidean_norm=float(norm.max()),
                        mean_euclidean_norm=float(norm.mean()),
                        saturation_fraction=float((logits[0].tanh().abs() >= .99).float().mean()))


def run_predictions(idx, models, head, device, out, monitor, claim_sha):
    snapshots = {k: snapshot(v) for k, v in models.items()}
    counts = dict(cases=0, head_forward=0, shared_native=0, donor_forward=0, optimizer_step=0)
    files = []
    folder = out / "predictions"
    folder.mkdir()
    with (out/"prediction_manifest.jsonl").open("x", encoding="utf-8", newline="\n") as manifest, (
            out/"head_forward_journal.jsonl").open("x", encoding="utf-8", newline="\n") as journal:
        for row in idx["cases"]:
            cache = read_cache(row)
            f, case = row["fold"], row["case_id"]
            for arm in ("N", *ARMS):
                if arm == "N":
                    data = dict(Q=cache["Q"], P0=cache["P0"])
                    counts["shared_native"] += 1
                    diagnostic = None
                else:
                    counts["head_forward"] += 1
                    append(journal, dict(index=counts["head_forward"], fold=f, case_id=case, arm=arm,
                                         status="CLAIMED_BEFORE_HEAD_FORWARD"))
                    p, diagnostic = head_forward(models[f,arm], head, arm, cache, device)
                    data = dict(prediction=p)
                name = f"{f}__{case}__{arm}.npz"
                path = folder/name
                with path.open("xb") as file:
                    np.savez_compressed(file, **data)
                files.append(path)
                append(manifest, dict(fold=f,case_id=case,arm=arm,cache_sha256=row["cache"]["sha256"],
                                      diagnostics=diagnostic,member=f"predictions/{name}",**file_record(path)))
            counts["cases"] += 1
            if counts["cases"] % 16 == 0:
                monitor(counts["cases"])
    require(counts == COUNTS, "exact final prediction inventory")
    require(all(snapshot(m) == snapshots[k] for k,m in models.items()), "head or RNG state changed")
    monitor(210)
    files += [out/"prediction_manifest.jsonl", out/"head_forward_journal.jsonl"]
    complete = out/"completion.json"
    write_json(complete, dict(status="AWAITING_READ_ONLY_PREDICTION_FREEZE_AUDIT",counts=counts,
                              request_sha256=claim_sha, state_and_rng_equal=True,
                              snapshots={"/".join(k):v for k,v in snapshots.items()}))
    files.append(complete)
    pack_outputs(out, files)
    monitor(210)


def pack_outputs(out, files):
    archive = out/"P5_predictions_v1.tar.gz"
    records = [(p, p.relative_to(out).as_posix(), file_record(p)) for p in files]
    with archive.open("xb") as f, tarfile.open(fileobj=f, mode="w:gz", format=tarfile.USTAR_FORMAT) as t:
        for path, name, _ in records:
            t.add(path, arcname=name, recursive=False)
    with tarfile.open(archive, "r:gz") as t:
        entries = t.getmembers()
        require(len(entries) == len(records), "archive record count")
        for item, (_, name, v) in zip(entries, records):
            require(item.isfile() and item.name == name and item.size == v["bytes"]
                    and sha(t.extractfile(item).read()) == v["sha256"], f"archive readback: {name}")
    v = file_record(archive)
    for suffix, data in ((".bytes", f"{v['bytes']}\n"), (".sha256", f"{v['sha256']}  {archive.name}\n"),
                         (".contents.sha256", "".join(f"{r['sha256']}  {n}\n" for _,n,r in records))):
        with archive.with_name(archive.name+suffix).open("x", encoding="ascii", newline="\n") as f:
            f.write(data)


def monitor_factory(q, out):
    start = time.monotonic()
    limit = q["limits"]
    ident = q["identity"]
    def monitor(cases):
        smi = subprocess.check_output(["/usr/bin/nvidia-smi","-i",ident["gpu_uuid"],"--query-gpu=memory.used",
                                       "--format=csv,noheader,nounits"], timeout=10)
        rss = next(x for x in Path("/proc/self/status").read_text().splitlines() if x.startswith("VmRSS:"))
        values = dict(wall_seconds=time.monotonic()-start, device_MiB=int(smi), RSS_bytes=int(rss.split()[1])*1024,
                      torch_peak_bytes=torch.cuda.max_memory_reserved(),
                      output_bytes=sum(p.stat().st_size for p in out.rglob("*") if p.is_file()),
                      minimum_free_disk_bytes=shutil.disk_usage(out).free)
        checks = {k:(value >= limit[k] if k=="minimum_free_disk_bytes" else value <= limit[k])
                  for k,value in values.items()}
        with (out/"resources.jsonl").open("a",encoding="utf-8",newline="\n") as f:
            append(f,dict(cases=cases, values=values, checks=checks))
        require(all(checks.values()), "prediction resource limits")
    return monitor


def load_numeric(site=None):
    global np, torch
    if site is not None:
        sys.path.insert(0,str(clean(site)))
    import numpy as np
    import torch


def run(a):
    q = common.authorize(a,"predict")
    ident = q["identity"]
    require(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
            and (socket.gethostname(),os.getuid(),str(Path(sys.executable).resolve()),sys.version.split()[0]) ==
            (ident["hostname"],ident["uid"],ident["python_realpath"],ident["python_version"]), "frozen Linux identity")
    require(q["counts"] == COUNTS and Path.cwd() == clean(ident["project"])
            and clean(q["entry"]["path"]) == Path(__file__).resolve()
            and clean(q["common"]["path"]) == Path(common.__file__).resolve(), "frozen runtime paths")
    for record in (q["entry"],q["common"]):
        read(record,65536)
    out=clean(q["output"])
    require(out.parent == clean(ident["project"])/"logs/cranial_bcsp_fullmamba"
            and {p.name for p in out.iterdir()} == {"launch.log"}, "new prediction output")
    for k,v in q["environment"].items():
        require(os.environ.get(k)==v.replace("<owned_output>",str(out)),f"environment: {k}")
    p = Path(f"/proc/{os.getppid()}/cmdline").read_bytes().split(b"\0")
    require(p[:4]==[b"/usr/bin/timeout",b"--signal=TERM",b"--kill-after=5s",
                    f"{q['limits']['wall_seconds']}s".encode()], "external timeout")
    require(shutil.disk_usage(out).free >= q["startup_free_disk_bytes"], "starter free space")
    load_numeric(clean(ident["python_realpath"]).parent.parent/"lib/python3.10/site-packages")
    require(torch.__version__==ident["torch_version"] and torch.version.cuda==ident["torch_cuda_version"]
            and np.__version__==ident["numpy_version"] and torch.cuda.device_count()==1, "CUDA provider")
    torch.set_float32_matmul_precision("highest")
    torch.backends.cuda.matmul.allow_tf32=False
    torch.backends.cudnn.allow_tf32=False
    torch.use_deterministic_algorithms(True)
    require(not torch.backends.cuda.matmul.allow_tf32 and not torch.backends.cudnn.allow_tf32
            and torch.are_deterministic_algorithms_enabled(), "strict FP32 deterministic settings")
    idx=json.loads(read(q["input_index"],524288))
    require(idx["identity"]==ident,"index device binding")
    manifest=list(map(json.loads,read(idx["cache_manifest"],500000).splitlines()))
    specs=validate_index(idx,manifest)
    head={}
    exec(compile(read(idx["head"],16384),idx["head"]["path"],"exec"),head)
    device=torch.device("cuda:0")
    with (out/"worker.pid").open("x",encoding="ascii") as f:
        f.write(f"{os.getpid()}\n")
    try:
        monitor=monitor_factory(q,out)
        monitor(0)
        models={k:load_model(v,head,device) for k,v in specs.items()}
        run_predictions(idx,models,head,device,out,monitor,a.request_sha256)
    except Exception as exc:
        write_json(out/"failure.json",dict(status="FAILED_STOP_NO_RETRY",error=repr(exc)))
        raise


if __name__=="__main__":
    run(common.args())
