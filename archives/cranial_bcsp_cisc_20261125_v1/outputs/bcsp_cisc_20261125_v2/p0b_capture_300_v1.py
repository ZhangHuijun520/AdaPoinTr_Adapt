"""Capture the frozen OASG prefix only for the 300 nonpilot Fold D training cases."""
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import types


ROOT = Path("/home/jovyan/adapointr_work/PoinTr")
HOST = "shu-common-25721452-notebook-zrtpob-0"
GPU = "GPU-e763d389-b4c2-4dc8-9571-d7343ec328b1"
PILOT_CASES = (
    "train__111__bilateral", "train__009__bilateral", "train__076__bilateral",
    "train__028__frontoorbital", "train__053__frontoorbital", "train__071__frontoorbital",
    "train__012__parietotemporal", "train__089__parietotemporal", "train__017__parietotemporal",
    "train__075__random_1", "train__045__random_1", "train__021__random_1",
    "train__058__random_2", "train__102__random_2", "train__019__random_2",
)


def bound(path, sha):
    assert path.resolve(strict=True) == path
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == sha, path
    return data


def module(path, sha, name):
    obj = types.ModuleType(name)
    obj.__file__ = str(path)
    sys.modules[name] = obj
    exec(compile(bound(path, sha), str(path), "exec"), obj.__dict__)
    return obj


def gpu_sample():
    result = subprocess.check_output([
        "nvidia-smi", "--id=" + GPU, "--query-gpu=uuid,memory.free,memory.used,driver_version,name",
        "--format=csv,noheader,nounits",
    ], text=True, timeout=8)
    uuid, free, used, driver, name = map(str.strip, result.strip().split(","))
    assert uuid == GPU
    return dict(uuid=uuid, free_mib=int(free), used_mib=int(used), driver=driver, name=name)


def fingerprint(model):
    h = hashlib.sha256()
    for name, value in sorted(model.state_dict().items()):
        h.update(name.encode() + b"\0")
        h.update(value.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def main():
    out = Path(sys.argv[1])
    assert out.resolve() == out and out.parent == Path("/home/jovyan")
    assert (socket.gethostname(), os.getuid(), os.environ["CUDA_VISIBLE_DEVICES"]) == (HOST, 1000, GPU)
    startup = gpu_sample()
    assert startup["free_mib"] >= 20480 and startup["used_mib"] <= 256, startup
    out.mkdir()
    print("IDENTITY", startup, flush=True)
    q_path = ROOT / "third_party/bcsp_oasg_p3_a_d_20261124_v1/OASG_A_D_training_execution_request_v1.json"
    q = json.loads(bound(q_path, "ad34d559e1c0604fe065d24d32077e78d95c4e99314007eb81dbaa7e11d38fa6"))
    assert dict(variant="A", fold="D", seed=2026112101) == q["run"]
    assert sys.version.split()[0] == q["identity"]["python_version"]
    assert Path(sys.executable).resolve() == Path(q["identity"]["python_realpath"])
    for key, dirname in (("TMPDIR", "tmp"), ("XDG_CACHE_HOME", "cache"),
                         ("MPLCONFIGDIR", "mpl"), ("TRITON_CACHE_DIR", "triton"), ("HF_HOME", "hf")):
        p = out / dirname
        p.mkdir()
        os.environ[key] = str(p)
    for key, value in q["environment"].items():
        if key not in ("CUDA_VISIBLE_DEVICES", "TMPDIR", "XDG_CACHE_HOME",
                       "MPLCONFIGDIR", "TRITON_CACHE_DIR", "HF_HOME"):
            os.environ[key] = value
    support_rec = q["p2_support"]
    support = module(Path(support_rec["path"]), support_rec["sha256"], "cisc_oasg_support")
    fold = json.loads(support.exact(q["fold"]).read_bytes())["folds"]["D"]
    train = fold["train_case_ids"]
    assert len(train) == len(set(train)) == 315 and set(PILOT_CASES) <= set(train)
    assert hashlib.sha256(("\n".join(train) + "\n").encode()).hexdigest() == fold["train_allowlist_sha256"]
    cases = tuple(cid for cid in train if cid not in PILOT_CASES)
    assert len(cases) == 300 and not set(cases) & set(fold["dev_case_ids"])
    rows = {r["case_id"]: r for r in map(json.loads, support.exact(q["point_manifest"]).read_bytes().splitlines())}
    cp = ROOT / "logs/cranial_bcsp_fullmamba/OASG_A_D_seed2026112101_a7jkrj_v1/ckpt-last.pth"
    cp_sha = "e2c459cb59ec7c198df4daec9e80978c04bec45dad88ef53592e00d012ebd41b"
    support.exact(dict(path=str(cp), bytes=478859115, sha256=cp_sha))
    print("ASSETS_BOUND", flush=True)
    native = module(ROOT / "third_party/bcsp_oasg_sf_native_20261125_hwk2fy_v2/oasg_sf_native_v2.py",
                    "0d1f30ac43fb6b5002429100bafd54e117156f9a40989e153aaf3da4c7c9a3d5", "cisc_native_builder")
    native.SEED = 2026112101
    torch, np, helper, build = native.prepare_models(q, support)
    model, identity = build("A")
    helper.validate_model(model)
    checkpoint = torch.load(cp, map_location="cpu", weights_only=True)
    assert (checkpoint["epoch"], checkpoint["updates"], checkpoint["scq_prime_run_identity"]) == (99, 3900, q["run"])
    model.load_state_dict(checkpoint["base_model"], strict=True)
    del checkpoint
    model.eval().requires_grad_(False).to("cuda:0")
    base = model.base_model
    assert type(base.mem_link) is torch.nn.Identity
    before = fingerprint(model)
    cpu_rng = torch.random.get_rng_state().clone()
    cuda_rng = torch.cuda.get_rng_state().clone()
    torch.cuda.reset_peak_memory_stats()
    coords, memory, input_hashes = [], [], []
    with torch.inference_mode():
        for cid in cases:
            row = rows[cid]
            point_path = Path(q["data_root"]) / f"points/{cid}_8192.npz"
            assert row["point_path"] == f"points/{cid}_8192.npz"
            data = bound(point_path, row["sha256"])
            with np.load(io.BytesIO(data), allow_pickle=False) as z:
                x = z["partial"]
            assert x.shape == (8192, 3) and x.dtype == np.float32 and np.isfinite(x).all()
            x_gpu = torch.from_numpy(x).unsqueeze(0).to("cuda:0")
            s, _, _, f = base.encode_rim_proxy_tokens(x_gpu)
            f = base.mem_link(f)
            assert tuple(s.shape) == (1, 256, 3) and tuple(f.shape) == (1, 256, 384)
            assert s.dtype == f.dtype == torch.float32
            assert torch.isfinite(s).all() and torch.isfinite(f).all()
            coords.append(s[0].cpu().numpy())
            memory.append(f[0].cpu().numpy())
            input_hashes.append(hashlib.sha256(x.tobytes()).hexdigest())
            assert torch.cuda.max_memory_allocated() <= q["resources"]["torch_peak_bytes"]
            if len(coords) % 30 == 0:
                assert gpu_sample()["used_mib"] <= q["resources"]["device_used_MiB"]
                print("PREFIX", len(coords), cid, flush=True)
    assert len(coords) == len(memory) == len(cases) == 300
    assert fingerprint(model) == before
    assert torch.equal(cpu_rng, torch.random.get_rng_state())
    assert torch.equal(cuda_rng, torch.cuda.get_rng_state())
    final = gpu_sample()
    assert final["used_mib"] <= q["resources"]["device_used_MiB"], final
    meta = dict(host=HOST, checkpoint_sha256=cp_sha, model_state_sha256=before, state_rng_unchanged=True,
                calls=dict(prefix=300, coarse=0, dense=0, loss=0, backward=0, optimizer_steps=0),
                gpu_before=startup, gpu_after=final, peak_allocated_bytes=torch.cuda.max_memory_allocated())
    shards = []
    for start in range(0, len(cases), 30):
        end = start + 30
        result = out / f"prefix_{start // 30 + 1:02}.npz"
        with result.open("xb") as stream:
            np.savez_compressed(stream, case_ids=np.asarray(cases[start:end]),
                                S=np.stack(coords[start:end]), F=np.stack(memory[start:end]),
                                input_sha256=np.asarray(input_hashes[start:end]))
        shards.append(dict(name=result.name, count=30, bytes=result.stat().st_size,
                           sha256=hashlib.sha256(result.read_bytes()).hexdigest()))
    receipt = out / "capture_receipt.json"
    with receipt.open("x", encoding="utf-8") as stream:
        json.dump(dict(metadata=meta, shards=shards, case_ids=list(cases)), stream, indent=2)
    print("CAPTURED", len(cases), len(shards), hashlib.sha256(receipt.read_bytes()).hexdigest(), flush=True)


if __name__ == "__main__":
    main()
