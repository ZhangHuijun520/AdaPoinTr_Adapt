"""RBSS P0b native encoder-prefix observation. No full forward or training."""
import argparse
import ast
from contextlib import ExitStack
import hashlib
import io
import json
import math
import os
from pathlib import Path
import random
import shutil
import socket
import subprocess
import sys
import time
import types


FOCAL = ("train__102__bilateral", "train__034__bilateral")
FILLERS = ("train__084__bilateral", "train__047__frontoorbital", "train__018__frontoorbital",
           "train__067__frontoorbital", "train__082__parietotemporal", "train__072__parietotemporal",
           "train__041__parietotemporal")
INITIALIZATIONS = ((2026112701, 2026112703), (2026112801, 2026112803))
TARGET = "base_model.encoder.blocks.blocks.5.attn"
PARENT_SHA = "ad34d559e1c0604fe065d24d32077e78d95c4e99314007eb81dbaa7e11d38fa6"
NATIVE_SHA = "0d1f30ac43fb6b5002429100bafd54e117156f9a40989e153aaf3da4c7c9a3d5"
PLAN_SHA = "96ea381c31f4f29f872d6b7e29ef0b8d95b60f579b335fe7ac522ef33fa35036"
PILOT_SHA = "cd7a65a805b0dcf4f940a7fcbc9e35cdabe2dc42bc2ee4b86357426625002608"
PILOT_SCOPE_SHA = "6232f8a751f60360c0bb0cca9e509702dba005be275cb98182c62c13a44a94a8"
COUNTS = dict(prefix=16, target_mixer=0, full_forward=0, coarse=0, dense=0,
              loss=0, backward=0, optimizer_steps=0)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def order_plan():
    rows = []
    for i, (seed, head_seed) in enumerate(INITIALIZATIONS):
        for m, mode in enumerate(("eval", "train")):
            for j, cid in enumerate(FOCAL):
                for b, layout in enumerate(("single", "batch8")):
                    slot = 0 if b == 0 else (1, 6)[j]
                    cases = [cid] if b == 0 else [*FILLERS[:slot], cid, *FILLERS[slot:]]
                    rows.append(dict(call=len(rows) + 1, case=cid, model_seed=seed, head_seed=head_seed,
                                     mode=mode, layout=layout, batch=cases, slot=slot,
                                     rng_seed=(2026112709, 2026112710)[i ^ m ^ b]))
    return rows


def validate_scope(q):
    need(q["schema"] == "bcsp-rbss-p0b-prefix16-v1" and q["plan_sha256"] == PLAN_SHA
         and q["pilot_result_sha256"] == PILOT_SHA and q["pilot_scope_sha256"] == PILOT_SCOPE_SHA,
         "frozen plan and pilot")
    need(q["counts"] == COUNTS and q["target"] == TARGET and q["schedule"] == order_plan(), "fixed diagnostic schedule")
    need(list(q["inputs"]) == [*FOCAL, *FILLERS] and list(q["historical"]) == list(FOCAL), "fixed input list")
    for cid, rec in q["inputs"].items():
        need(rec["relative_path"] == f"points/{cid}_8192.npz"
             and all(is_digest(rec[key]) for key in ("sha256", "partial_sha256")), "input identity")
    for rec in q["historical"].values():
        need(set(rec) == {"anchor_sha256", "order_sha256", "inverse_sha256"}
             and all(is_digest(v) for v in rec.values()), "historical native reference")


def is_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def authorize(q, request_sha, auth, auth_sha, runtime):
    validate_scope(q)
    need(q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["execution_authorized"] is False,
         "final request with fresh server binding required")
    need(auth == dict(schema="bcsp-development-authorization-v1", request_sha256=request_sha,
                      explicit_user_authorization=True, user_authorization_text=auth.get("user_authorization_text"))
         and bool((auth.get("user_authorization_text") or "").strip()), "single-use hash authorization")
    need(runtime == dict(schema="bcsp-development-runtime-v1", request_sha256=request_sha,
                         authorization_sha256=auth_sha), "one-way runtime proof")


class PrefixStop(Exception):
    pass


def observe(torch, prefix, mixer, x, row):
    captured = []

    def stop_before_mix(_module, inputs):
        need(not captured and len(inputs) == 2, "one target mixer input")
        z, xyz = inputs
        n = len(row["batch"])
        need(tuple(z.shape) == (n, 256, 384) and tuple(xyz.shape) == (n, 256, 3)
             and z.dtype == xyz.dtype == torch.float32 and z.device == xyz.device == x.device
             and mixer.training == (row["mode"] == "train"), "actual target mixer input contract")
        need(bool(torch.isfinite(z).all() and torch.isfinite(xyz).all()), "finite actual mixer inputs")
        slot = row["slot"]
        # The prefix is interrupted before the target branch, leaving order computation explicit.
        native = mixer.forward.__func__.__globals__["lexicographic_order"]
        order, inverse = native(xyz[slot:slot + 1])
        captured.append(tuple(v.detach().cpu().contiguous().numpy().copy()
                              for v in (xyz[slot], order[0], inverse[0])))
        raise PrefixStop()

    with ExitStack() as stack, torch.no_grad():
        stack.callback(mixer.register_forward_pre_hook(stop_before_mix).remove)
        try:
            prefix(x)
        except PrefixStop:
            pass
        else:
            raise ValueError("prefix escaped target stop point")
    need(len(captured) == 1, "one prefix observation")
    return captured[0]


def array_hashes(np, values):
    coords, order, inverse = values
    ids = np.arange(256)
    need(coords.shape == (256, 3) and coords.dtype == np.float32 and np.isfinite(coords).all(), "native coordinates")
    need(order.shape == inverse.shape == (256,) and order.dtype == inverse.dtype == np.int64
         and np.array_equal(np.sort(order), ids) and np.array_equal(np.sort(inverse), ids)
         and np.array_equal(order[inverse], ids) and np.array_equal(inverse[order], ids), "native permutation inverse")
    x, y, z = coords.T
    need(np.array_equal(order, np.lexsort((ids, z, y, x))), "observed ordering equals frozen XYZ rule")
    return dict(anchor_sha256=digest(coords.astype("<f4", copy=False).tobytes()),
                order_sha256=digest(order.astype("<i8", copy=False).tobytes()),
                inverse_sha256=digest(inverse.astype("<i8", copy=False).tobytes()))


def decide(rows, historical):
    need([row["condition"] for row in rows] == order_plan(), "exact complete prefix record")
    need(all(row["buffers_restored"] and row["rng_restored"] for row in rows), "restoration evidence")
    groups = {}
    for cid in FOCAL:
        subset = [r for r in rows if r["condition"]["case"] == cid]
        equal = all(r["hashes"] == subset[0]["hashes"] for r in subset)
        hist = all(r["hashes"] == historical[cid] for r in subset)
        groups[cid] = dict(conditions=len(subset), invariant=equal, historical_equal=hist)
    if not all(v["invariant"] for v in groups.values()):
        outcome = "DISABLE_PERMUTATION_CACHE_ONLINE_ONLY_PENDING"
    elif not all(v["historical_equal"] for v in groups.values()):
        outcome = "HISTORICAL_ANCHOR_MISMATCH_REVALIDATE_BEFORE_P0C"
    else:
        outcome = "CONDITIONAL_CONTENT_KEYED_CACHE_PASS"
    return dict(outcome=outcome, cases=groups)


def seed_builder(parent, oasg, source_sha):
    old = parent._build
    path, tree = oasg._source(old, source_sha)
    [node] = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_build"]
    need(node.lineno == old.__code__.co_firstlineno, "frozen constructor source")
    prior = ast.dump(ast.parse("(2026112101, 2026112102)", mode="eval").body)
    [guard] = [n for n in ast.walk(node.body[0].test) if ast.dump(n) == prior]
    guard.elts = [ast.Constant(seed) for seed, _ in INITIALIZATIONS]
    return oasg._compile(node, path, old.__globals__)


def build_model(q, support, torch, helper, seed, head_seed):
    import importlib
    from easydict import EasyDict

    modules = {key: sys.modules[name] for key, name in q["module_names"].items() if name in sys.modules}
    parent, oasg = modules["prime_seeded_parent"], modules["oasg_entry"]
    constructor = seed_builder(parent, oasg, q["implementation"]["prime_seeded_parent"]["sha256"])
    cls = importlib.import_module("models.AdaPoinTr").AdaPoinTr
    config = json.loads(support.exact(q["static_config"]).read_bytes())["model"]
    with torch.random.fork_rng(devices=[]):
        model, info = constructor(lambda: cls(EasyDict(config)), "M0", seed, parent.native_mixer,
                                  artificial_fixture=False)
        model, _ = modules["lqi_factory"]._install(model, info, parent.native_mixer, False)
        model, _ = modules["scq_factory"].install(model, "B", None)
        base = model.base_model
        base.forward = oasg._oasg_forward(base)
        torch.random.default_generator.manual_seed(head_seed)
        # The head is seeded to make the diagnostic initializations distinct.
        # No head call is made, and these are not formal training initializer bytes.
        base.coarse_pred = modules["oasg_head"].ObservationAnchoredHead()
    helper.validate_model(model)
    need(info["seed"] == seed and sum(p.numel() for p in model.parameters()) == 39907012, "model identity")
    target = model.get_submodule(TARGET)
    need(type(target) is modules["encoder"].BidirectionalSpatialMamba, "native mixer type")
    return model, target


def bound(path, sha, cap=131072):
    p = Path(path)
    need(p.is_absolute() and p.resolve(strict=True) == p and p.stat().st_size <= cap, "exact bounded file")
    data = p.read_bytes()
    need(digest(data) == sha, f"binding mismatch: {p}")
    return data


def load_support(parent):
    rec = parent["p2_support"]
    raw = bound(rec["path"], rec["sha256"])
    need(len(raw) == rec["bytes"], "support size")
    mod = types.ModuleType("rbss_oasg_support")
    mod.__file__ = rec["path"]
    exec(compile(raw, rec["path"], "exec", dont_inherit=True), mod.__dict__)
    return mod


def gpu_sample(q, out, started, torch=None):
    r = q["binding"]["resources"]
    ident = q["binding"]["identity"]
    stdout = subprocess.check_output(
        ["nvidia-smi", "--id=" + ident["gpu_uuid"], "--query-gpu=uuid,driver_version,memory.used,memory.free",
         "--format=csv,noheader,nounits"], text=True, timeout=r["smi_timeout_seconds"])
    uuid, driver, used, free = map(str.strip, stdout.strip().split(","))
    need((uuid, driver) == (ident["gpu_uuid"], ident["driver_version"]), "GPU identity drift")
    peak = None if torch is None else torch.cuda.max_memory_allocated(0)
    need(time.monotonic() - started <= r["wall_seconds"] and shutil.disk_usage(out.parent).free >= r["minimum_disk_bytes"]
         and int(used) <= r["device_used_MiB"] and (peak is None or peak <= r["torch_peak_bytes"]), "resource limits")
    if torch is None:
        need(int(used) <= r["idle_used_MiB"] and int(free) >= r["minimum_start_free_MiB"], "startup GPU reserve")
    return dict(uuid=uuid, driver=driver, used_MiB=int(used), free_MiB=int(free), peak_allocated=peak)


def read_points(np, parent, q):
    project_data = Path(parent["data_root"])
    partials = {}
    for cid, rec in q["inputs"].items():
        raw = bound(project_data / rec["relative_path"], rec["sha256"], cap=512 * 1024)
        with np.load(io.BytesIO(raw), allow_pickle=False) as z:
            x = z["partial"]
        need(x.dtype == np.float32 and x.shape == (8192, 3) and np.isfinite(x).all()
             and digest(x.tobytes()) == rec["partial_sha256"], "ordered residual-only input")
        partials[cid] = x
    return partials


def emit(path, data, mode):
    with path.open(mode, encoding="utf-8") as f:
        f.write(json.dumps(data, allow_nan=False, separators=(",", ":")) + "\n")


def run(q, parent, out, sha):
    started = time.monotonic()
    b = q["binding"]
    ident = b["identity"]
    need((socket.gethostname(), os.getuid(), os.environ.get("CUDA_VISIBLE_DEVICES"),
          str(Path(sys.executable).resolve()), sys.version.split()[0]) ==
         (ident["hostname"], ident["uid"], ident["gpu_uuid"], ident["python_realpath"], ident["python_version"]),
         "fresh exact container, device and interpreter binding")
    need(out.is_absolute() and out.resolve() == out and out.parent.is_dir() and not out.exists(), "fresh output")
    initial = gpu_sample(q, out, started)
    out.mkdir()
    emit(out / "started.json", dict(request_sha256=sha, resources=initial), "x")
    for key, dirname in (("TMPDIR", "tmp"), ("XDG_CACHE_HOME", "cache"), ("MPLCONFIGDIR", "mpl"),
                         ("TRITON_CACHE_DIR", "triton"), ("HF_HOME", "hf")):
        (out / dirname).mkdir()
        os.environ[key] = str(out / dirname)
    for key in ("CUBLAS_WORKSPACE_CONFIG", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "CUDA_CACHE_DISABLE", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "MPLBACKEND"):
        os.environ[key] = parent["environment"][key]
    support = load_support(parent)
    need(b["native_loader"]["sha256"] == NATIVE_SHA, "frozen OASG loader identity")
    native = support.source("rbss_oasg_native_loader", b["native_loader"])
    torch, np, helper, _unused = native.prepare_models(parent, support)
    helper._MONITOR = None
    partials = read_points(np, parent, q)
    rows, model_hashes, arrays = [], {}, {}
    torch.cuda.reset_peak_memory_stats(0)
    for seed, head in INITIALIZATIONS:
        model, target = build_model(parent, support, torch, helper, seed, head)
        model.requires_grad_(False).to("cuda:0")
        state = helper.state_sha(model)
        model_hashes[str(seed)] = state
        for condition in (r for r in q["schedule"] if r["model_seed"] == seed):
            model.train(condition["mode"] == "train")
            helper.assert_numeric(torch)
            x = torch.from_numpy(np.stack([partials[c] for c in condition["batch"]])).to("cuda:0")
            before = {n: value.detach().clone() for n, value in model.named_buffers()}
            rng_evidence = {}
            emit(out / "attempts.jsonl", condition, "a")
            with helper.rng_preserved(torch, np, cuda=True, evidence=rng_evidence):
                try:
                    rng_seed = condition["rng_seed"]
                    random.seed(rng_seed)
                    np.random.seed(rng_seed)
                    torch.manual_seed(rng_seed)
                    observation = observe(torch, model.base_model.encode_rim_proxy_tokens, target, x, condition)
                finally:
                    with torch.no_grad():
                        for n, value in model.named_buffers():
                            value.copy_(before[n])
            restored = all(torch.equal(v, before[n]) for n, v in model.named_buffers())
            need(restored and rng_evidence.get("rng_restored") is True, "buffers and RNG restore")
            hashes = array_hashes(np, observation)
            for key, value in zip(("S", "order", "inverse"), observation):
                arrays[f"{condition['call']:02d}_{key}"] = value
            item = dict(condition=condition, hashes=hashes, buffers_restored=restored, rng_restored=True,
                        resources=gpu_sample(q, out, started, torch))
            rows.append(item)
            emit(out / "observations.jsonl", item, "a")
        need(helper.state_sha(model) == state, "model parameters and buffers unchanged")
        del model, target
        torch.cuda.empty_cache()
    need(len(set(model_hashes.values())) == 2, "distinct diagnostic initializations")
    verdict = decide(rows, q["historical"])
    with (out / "anchors.npz").open("xb") as output:
        np.savez_compressed(output, **arrays)
    emit(out / "completion.json", dict(request_sha256=sha, counts=COUNTS, states=model_hashes,
                                      buffers_and_rng_restored=True, verdict=verdict,
                                      anchors_sha256=support.file_hash(out / "anchors.npz")), "x")


def main():
    parser = argparse.ArgumentParser()
    for key in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime", "runtime-sha256"):
        parser.add_argument("--" + key, required=True)
    a = parser.parse_args()
    need(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,
         "isolated Linux interpreter")
    q = json.loads(bound(a.request, a.request_sha256))
    au = json.loads(bound(a.authorization, a.authorization_sha256))
    rt = json.loads(bound(a.runtime, a.runtime_sha256))
    authorize(q, a.request_sha256, au, a.authorization_sha256, rt)
    self_path = Path(__file__).resolve()
    need(str(self_path) == q["binding"]["worker"]["path"], "worker path")
    bound(self_path, q["binding"]["worker"]["sha256"])
    parent = json.loads(bound(q["binding"]["historical_request"], PARENT_SHA))
    # Only the verified runtime identity is rebound. The original science and source bindings stay in force.
    parent["identity"] = {**parent["identity"], **q["binding"]["identity"]}
    run(q, parent, Path(q["binding"]["output"]), a.request_sha256)


if __name__ == "__main__":
    main()
