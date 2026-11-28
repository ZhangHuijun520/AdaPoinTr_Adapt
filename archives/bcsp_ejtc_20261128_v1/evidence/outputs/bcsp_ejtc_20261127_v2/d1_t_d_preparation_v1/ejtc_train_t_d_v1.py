"""T_D isolated adapter: same OASG model, frozen R initial state and global target-tail supervision."""

import argparse
import ast
import hashlib
import importlib
import json
import os
from pathlib import Path
import random
import socket
import sys


SEED, HEAD_SEED = 2026112801, 2026112803
INITIAL = "81687ab7d797592e056e683b82dfead3e82aa318327151aa9315c13dfe1a855c"
COUNTS = dict(steps=3900, epochs=100, exposures=31200, drops=300)
LAMBDA = 0.027474069997873135


def need(ok, text):
    if not ok:
        raise ValueError(text)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def bound(path, expected, size=None):
    p = Path(path)
    need(p.is_file() and p.resolve(strict=True) == p and not p.is_symlink(), "exact path " + str(p))
    if size is not None:
        need(p.stat().st_size == size, "exact size " + str(p))
    else:
        need(p.stat().st_size <= 262144, "control size " + str(p))
    raw = p.read_bytes()
    need(sha(raw) == expected, "exact bytes " + str(p))
    return raw


def lifecycle(runtime, digest, claim, components):
    original = runtime.train_lifecycle
    path = Path(original.__code__.co_filename)
    raw = path.read_bytes()
    need(sha(raw) == digest, "exact lifecycle bytes")
    [node] = [v for v in ast.parse(raw).body if isinstance(v, ast.FunctionDef) and v.name == original.__name__]
    need(node.lineno == original.__code__.co_firstlineno and
         "SCQ-PRIME runtime identity" in ast.unparse(node.body[1]), "frozen guard node")
    node.body[1] = ast.copy_location(ast.parse(
        "require(run_identity == dict(variant='T', fold='D', seed=_seed), 'EJTC T identity')"
    ).body[0], node.body[1])
    [event] = [v for v in ast.walk(node) if isinstance(v, ast.Assign)
               and any(isinstance(n, ast.Name) and n.id == "event" for n in v.targets)]
    need(isinstance(event.value, ast.Dict) and "loss_reconstruction" in
         [v.value for v in event.value.keys if isinstance(v, ast.Constant)], "frozen event node")
    # Replace only the loss call/sum and add explicit scalar loss evidence.
    call_pattern = ast.parse('sparse, dense = model.get_loss(ret, target, epoch, partial=partial)').body[0]
    sum_pattern = ast.parse('loss = sparse + dense').body[0]
    calls = [v for v in ast.walk(node) if isinstance(v, ast.Assign)
             and ast.dump(v) == ast.dump(call_pattern)]
    sums = [v for v in ast.walk(node) if isinstance(v, ast.Assign)
            and ast.dump(v) == ast.dump(sum_pattern)]
    need(len(calls) == len(sums) == 1, 'exact frozen loss insertion nodes')
    calls[0].targets = ast.parse('sparse, dense, ejtc_auxiliary = None').body[0].targets
    calls[0].value = ast.parse('_components(model, ret, target, epoch, partial)', mode='eval').body
    sums[0].value = ast.parse('sparse + dense + _lambda * ejtc_auxiliary', mode='eval').body
    fields = dict(ejtc_auxiliary='float(ejtc_auxiliary.detach())',
                  ejtc_applied_lambda='_lambda',
                  ejtc_weighted_auxiliary='float((_lambda * ejtc_auxiliary).detach())')
    for field, expression in fields.items():
        event.value.keys.append(ast.Constant(field))
        event.value.values.append(ast.parse(expression, mode='eval').body)
    env = dict(original.__globals__, claim_output=claim, _seed=SEED,
               _components=components, _lambda=LAMBDA)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), env)
    return env[original.__name__]


def authorize(q, req_sha, auth, auth_sha, runtime):
    need(q["schema"] == "bcsp-ejtc-foldD-t-training-v1" and q["arm"] == "T"
         and q["status"] == "AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["execution_authorized"] is False
         and q["counts"] == COUNTS and q["seeds"] == [SEED, HEAD_SEED]
         and q["initial_state_sha256"] == INITIAL and q["lambda"] == 0.027474069997873135,
         "exact T request")
    need(q['pairing']['initial_state']['sha256'] ==
         '3e319c532e53efc613db8051d5f9035b45f0669f596b0c5426aea1b9707e0fa9'
         and q['pairing']['initial_state']['bytes'] == 159797106
         and q['pairing']['initial_state']['path'] ==
         '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/EJTC_D1_R_D_h7vvrr_v3/common_initial_state.pth'
         and q['pairing']['tensor_fingerprint'] == INITIAL
         and q['pairing']['start_rng'] == dict(
             python='b629d1ef225d6090293aefdb55d2fab7f5e5043718143caa0658f3df6e95cde1',
             numpy='f206bfef0f79900eab8246ac3ef75674c6b75ca51137725a0c794d699f6ba708',
             cpu='7a0f3c61b01b133202c617a6d507e5fe79a2abda7207bbb132ad115b8fc69db4',
             cuda='1b9e102c06ad4ad7464b83fc2215d3e4b3c1f1a856a7b16feebbedf0b2a0f2a0'),
         'frozen R pairing identity')
    need(auth == dict(schema="bcsp-development-authorization-v1", request_sha256=req_sha,
                      explicit_user_authorization=True, user_authorization_text=auth.get("user_authorization_text"))
         and isinstance(auth["user_authorization_text"], str) and req_sha in auth["user_authorization_text"]
         and runtime == dict(schema="bcsp-development-runtime-v1", request_sha256=req_sha,
                             authorization_sha256=auth_sha), "single use authorization chain")


def loss_components(ch, candidate, model, ret, target, epoch, partial):
    layer = model.fine_loss_func
    need('forward' not in vars(layer), 'unpatched dense layer')
    captured = []
    def wrapped(prediction, reference):
        need(not captured, 'one dense loss call per batch')
        value, distance = candidate.dense_loss_and_target_distances(ch, layer, prediction, reference)
        captured.append(distance)
        return value
    layer.forward = wrapped
    try:
        sparse, dense = model.get_loss(ret, target, epoch, partial=partial)
    finally:
        del layer.forward
    need(len(captured) == 1 and float(sparse.detach()) == 0.0, 'one frozen reconstruction branch')
    aux = candidate.auxiliary(captured[0], 'T')
    return sparse, dense, aux


def load_common_state(torch, helper, model, record, tensor_hash, parameter_hash):
    path = Path(record['path'])
    need(path.name == 'common_initial_state.pth' and not path.is_symlink()
         and path.resolve(strict=True) == path, 'frozen untrained state path')
    def digest():
        mark = path.stat()
        need(mark.st_size == record['bytes'], 'frozen initial state size')
        value = hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda: stream.read(4194304), b''):
                value.update(block)
        need(value.hexdigest() == record['sha256'], 'frozen initial state bytes')
        return mark.st_ino, mark.st_size, mark.st_mtime_ns
    before = digest()
    state = torch.load(path, map_location='cpu', weights_only=True)
    need(isinstance(state, dict) and state and
         all(isinstance(k, str) and torch.is_tensor(v) for k, v in state.items()),
         'initial state dict only; trained checkpoint forbidden')
    model.load_state_dict(state, strict=True)
    del state
    need(digest() == before, 'initial state changed while loading')
    need(helper.state_sha(model) == tensor_hash and helper.state_sha(model, True) == parameter_hash,
         'loaded parameter and buffer fingerprints')


def seed_pair_rng(torch, np, helper, expected):
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    rng = dict(python=sha(repr(random.getstate()).encode()),
               numpy=sha(np.random.get_state()[1].tobytes()),
               cpu=helper.tensor_sha(torch.get_rng_state()), cuda=helper.tensor_sha(torch.cuda.get_rng_state(0)))
    need(rng == expected, 'exact R starting RNG')
    return rng


def main():
    parser = argparse.ArgumentParser()
    for key in ("request", "request-sha256", "authorization", "authorization-sha256", "runtime", "runtime-sha256"):
        parser.add_argument("--" + key, required=True)
    a = parser.parse_args()
    q = json.loads(bound(a.request, a.request_sha256))
    auth = json.loads(bound(a.authorization, a.authorization_sha256))
    rt = json.loads(bound(a.runtime, a.runtime_sha256))
    authorize(q, a.request_sha256, auth, a.authorization_sha256, rt)
    binding = q["binding"]
    i, out = binding["identity"], Path(binding["output"])
    need(sys.platform == "linux" and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
         and (socket.gethostname(), os.getuid(), os.environ.get("CUDA_VISIBLE_DEVICES"),
              str(Path(sys.executable).resolve()), sys.version.split()[0]) ==
             (i["hostname"], i["uid"], i["gpu_uuid"], i["python_realpath"], i["python_version"]),
         "exact Linux runtime identity")
    need([a.request, a.authorization, a.runtime] == [q["launch"][k + "_path"] for k in
         ("request", "authorization", "runtime")], "exact control paths")
    need(q["files"]["worker"]["path"] == str(Path(__file__).resolve()), "exact worker")

    def records(rec):
        return bound(rec["path"], rec["sha256"], rec["bytes"])

    def source(name):
        import types
        rec = q["files"][name]
        module = types.ModuleType("ejtc_" + name)
        module.__file__ = rec["path"]
        exec(compile(records(rec), rec["path"], "exec", dont_inherit=True), module.__dict__)
        return module

    prefix, native, old = (source(key) for key in ("prefix", "native_loader", "oasg_train"))
    parent = json.loads(records(q["files"]["parent"]))
    parent.update(identity={**parent["identity"], **i}, resources=binding["resources"])
    support = prefix.load_support(parent)
    common = json.loads(records(q["files"]["common"]))
    need(common["initial_state_sha256"] == INITIAL and common["seeds"] == q["seeds"]
         and common["lambda"] == q["lambda"] and common["order"]["sha256"] == q["order_file_sha256"]
         and common["order"] == parent["order"], "common three-arm contract")
    need(out.is_absolute() and out.resolve() == out and out.parent.is_dir() and not os.path.lexists(out),
         "fresh output")
    support.resources(parent, out, initial=True)
    out.mkdir()
    cache = {"TMPDIR": "tmp", "XDG_CACHE_HOME": "cache", "MPLCONFIGDIR": "mpl",
             "TRITON_CACHE_DIR": "triton", "HF_HOME": "hf"}
    for key, name in cache.items():
        (out / name).mkdir()
        os.environ[key] = str(out / name)
    for key, value in parent["environment"].items():
        if key not in cache and key != "CUDA_VISIBLE_DEVICES":
            os.environ[key] = value
    torch, np, helper, _ = native.prepare_models(parent, support)
    helper._MONITOR = None
    names, impl = parent["module_names"], parent["implementation"]
    support.source(names["contract"], impl["contract"])
    runtime = support.source(names["training_runtime"], impl["training_runtime"])
    order = json.loads(support.exact(parent["order"]).read_bytes())
    fold = json.loads(support.exact(parent["fold"]).read_bytes())
    manifest = [json.loads(line) for line in support.exact(parent["point_manifest"]).read_bytes().splitlines()]
    rows, sources = old.select_training(fold, manifest, order)
    for row in rows:
        path = support.clean(str(Path(parent["data_root"]) / row["point_path"]))
        need(path.is_file() and support.file_hash(path) == row["sha256"], "frozen input " + row["case_id"])
    model, _ = prefix.build_model(parent, support, torch, helper, SEED, HEAD_SEED)
    need(helper.state_sha(model) == INITIAL, "P1 initial parameter and buffer bytes")
    pairing = q['pairing']
    rstart = json.loads(records(pairing['r_start']))
    need(rstart['request_sha256'] == pairing['r_request_sha256']
         and rstart['arm'] == 'R' and rstart['rng'] == pairing['start_rng']
         and rstart['state_sha256'] == INITIAL
         and rstart['serialized_initial_state_sha256'] == pairing['initial_state']['sha256'],
         'frozen R start evidence')
    load_common_state(torch, helper, model, pairing['initial_state'], INITIAL, pairing['parameter_fingerprint'])
    candidate = source('candidate')
    ch = importlib.import_module('extensions.chamfer_dist')
    rng = seed_pair_rng(torch, np, helper, pairing['start_rng'])
    prefix.emit(out / "ejtc_start.json", dict(state_sha256=helper.state_sha(model), rng=rng, arm="T",
                serialized_initial_state_sha256=pairing['initial_state']['sha256'],
                initial_state_path=pairing['initial_state']['path'],
                common_sha256=q['files']['common']['sha256'],
                r_request_sha256=pairing['r_request_sha256'], request_sha256=a.request_sha256), "x")
    dataset = runtime.BCSPDataset(parent["data_root"], rows, sources, 8192)

    def loader(epoch):
        return runtime.make_loader(dataset, order, epoch)

    def claim(path):
        need(Path(path) == out and (out / "ejtc_start.json").is_file(), "owned output")
        return out

    resources = old.TrainingResources(out, torch, helper, lambda: support.resources(parent, out),
                                      lambda row: prefix.emit(out / "p3_resources.jsonl", row, "a"),
                                      binding["resources"]["torch_peak_bytes"])
    lifecycle(runtime, impl["training_runtime"]["sha256"], claim,
              lambda m, ret, g, epoch, x: loss_components(ch, candidate, m, ret, g, epoch, x))(
        model, loader, rows, order, str(out), device="cuda:0", numeric_check=helper.assert_numeric,
        resources=resources, knn_enable=importlib.import_module("models.Transformer_utils").enable_bcsp_knn,
        state_fingerprint=helper.state_sha, run_identity=dict(variant="T", fold="D", seed=SEED))


if __name__ == "__main__":
    main()
