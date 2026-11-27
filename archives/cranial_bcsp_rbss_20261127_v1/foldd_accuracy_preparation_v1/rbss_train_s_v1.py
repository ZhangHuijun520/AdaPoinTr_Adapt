"""RBSS training adapter over the frozen OASG lifecycle."""
import argparse
import ast
from contextlib import ExitStack
import hashlib
import importlib
import json
import os
from pathlib import Path
import random
import socket
import sys
import time


SEED = 2026112701
HEAD = 2026112703
ARMS = ('R', 'C', 'S')
INITIAL = '66e1ce594074e8c0521d0b4748b198db5ef9a528bf327a69121dbccea1e023f7'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def lifecycle(runtime, frozen, claim):
    fn = runtime.train_lifecycle
    f = Path(fn.__code__.co_filename)
    raw = f.read_bytes()
    need(sha(raw) == frozen, 'runtime bytes')
    [node] = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == fn.__name__]
    need(node.lineno == fn.__code__.co_firstlineno and isinstance(node.body[1], ast.Expr)
         and 'SCQ-PRIME runtime identity' in ast.unparse(node.body[1]), 'exact historical identity guard')
    guard = ast.parse("require(run_identity == dict(variant=_arm, fold='D', seed=_seed), 'RBSS identity')").body[0]
    node.body[1] = ast.copy_location(guard, node.body[1])
    def bind(arm):
        need(arm in ARMS, 'RBSS arm')
        env = dict(fn.__globals__, claim_output=claim, _arm=arm, _seed=SEED)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(f), 'exec'), env)
        return env[fn.__name__]
    return bind


class CheckedLoader:
    def __init__(self, loader, planned, assets, model, target, torch, lib, arm, geometry_sha):
        self.loader, self.planned, self.assets = loader, planned, assets
        self.target, self.torch, self.lib = target, torch, lib
        self.model = model
        self.arm, self.geo = arm, geometry_sha
        need(arm in ARMS and len(loader) == len(planned) == 39, 'epoch binding')

    def __len__(self):
        return len(self.loader)

    def __iter__(self):
        for index, batch in enumerate(self.loader):
            partial, _gt, ids, _sources = batch
            ids = list(ids)
            need(ids == self.planned[index] and len(ids) == 8, 'ordered batch IDs')
            # The contract supplies CPU tensors from its zero-worker DataLoader.
            x = [v.contiguous().numpy() for v in partial]
            specs = [self.assets[cid] for cid in ids]
            need(all(sha(v.tobytes()) == a['input_sha256'] for v, a in zip(x, specs)), 'batch input bytes')
            calls = 0

            def choose(pos, native, inv0):
                nonlocal calls
                calls += 1
                need(calls == 1 and tuple(pos.shape) == (8, 256, 3), 'one actual mixer invocation')
                xyz = pos.detach().cpu().contiguous().numpy()
                ranks = native.detach().cpu().contiguous().numpy()
                inverse = inv0.detach().cpu().contiguous().numpy()
                orders, inverses = [], []
                for slot, s in enumerate(specs):
                    need(self.lib.content_key(x[slot], s['frame'], xyz[slot], ranks[slot], self.geo, 'RBSS-v2') == s['key']
                         and ranks[slot].tolist() == s['order']['R'] and inverse[slot].tolist() == s['inverse']['R'],
                         'live anchor/key mismatch ' + ids[slot])
                    arm = self.arm if s['active'] else 'R'
                    orders.append(s['order'][arm]); inverses.append(s['inverse'][arm])
                if self.arm == 'R' or not any(s['active'] for s in specs):
                    return None
                return tuple(self.torch.tensor(v, dtype=self.torch.long, device=pos.device) for v in (orders, inverses))

            def verify_consumed(*_args):
                need(calls == 1, 'target mixer observation missing before loss')

            with ExitStack() as stack:
                stack.enter_context(self.lib.temporary_order(self.target, self.torch, choose))
                stack.callback(self.model.register_forward_hook(verify_consumed).remove)
                yield batch
                need(calls == 1, 'target mixer observation missing')


def main():
    parser = argparse.ArgumentParser()
    for k in ('request', 'request-sha256', 'authorization', 'authorization-sha256', 'runtime', 'runtime-sha256'):
        parser.add_argument('--' + k, required=True)
    a = parser.parse_args()
    def bound(path, expected):
        p = Path(path)
        need(p.is_file() and p.resolve() == p, 'exact path ' + str(p))
        data = p.read_bytes()
        need(sha(data) == expected, 'exact bytes ' + str(p))
        return data
    q = json.loads(bound(a.request, a.request_sha256))
    auth = json.loads(bound(a.authorization, a.authorization_sha256))
    rt = json.loads(bound(a.runtime, a.runtime_sha256))
    need(q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and not q['execution_authorized']
         and q['schema'] == 'bcsp-rbss-foldD-training-v1' and q['arm'] == 'S'
         and q['seeds'] == [SEED, HEAD] and q['initial_state_sha256'] == INITIAL
         and q['counts'] == dict(steps=3900, epochs=100, exposures=31200, drops=300), 'exact frozen request')
    need(auth.get('schema') == 'bcsp-development-authorization-v1' and auth.get('request_sha256') == a.request_sha256
         and auth.get('explicit_user_authorization') is True and bool(auth.get('user_authorization_text','').strip())
         and rt == dict(schema='bcsp-development-runtime-v1', request_sha256=a.request_sha256,
                        authorization_sha256=a.authorization_sha256), 'explicit single-run authorization')
    b = q['binding']; i = b['identity']; out = Path(b['output'])
    need(sys.platform == 'linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
         and (socket.gethostname(), os.getuid(), os.environ.get('CUDA_VISIBLE_DEVICES'), str(Path(sys.executable).resolve()), sys.version.split()[0])
         == (i['hostname'],i['uid'],i['gpu_uuid'],i['python_realpath'],i['python_version']), 'runtime identity')
    need(Path(q['files']['worker']['path']) == Path(__file__).resolve(), 'worker path')
    for rec in q['files'].values():
        need(len(bound(rec['path'], rec['sha256'])) == rec['bytes'], 'bound file size')
    def source(name):
        import types
        rec = q['files'][name]
        module = types.ModuleType('rbss_' + name)
        module.__file__ = rec['path']
        exec(compile(bound(rec['path'], rec['sha256']), rec['path'], 'exec'), module.__dict__)
        return module
    prefix, lib, old = (source(n) for n in ('prefix', 'order_adapter', 'oasg_train'))
    parent = json.loads(bound(b['historical_request'], prefix.PARENT_SHA))
    parent.update(identity={**parent['identity'], **i}, resources=b['resources'])
    support = prefix.load_support(parent)
    need(out.resolve() == out and not os.path.lexists(out), 'fresh output')
    support.resources(parent, out, initial=True)
    out.mkdir()
    for k, n in (('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('MPLCONFIGDIR','mpl'),('TRITON_CACHE_DIR','triton'),('HF_HOME','hf')):
        (out/n).mkdir(); os.environ[k] = str(out/n)
    for key, value in parent['environment'].items():
        if key not in {'CUDA_VISIBLE_DEVICES','TMPDIR','XDG_CACHE_HOME','MPLCONFIGDIR','TRITON_CACHE_DIR','HF_HOME'}:
            os.environ[key] = value
    native = support.source('rbss_train_native_loader', q['files']['native_loader'])
    torch, np, helper, _ = native.prepare_models(parent, support)
    helper._MONITOR = None
    names, impl = parent['module_names'], parent['implementation']
    support.source(names['contract'], impl['contract'])
    runtime = support.source(names['training_runtime'], impl['training_runtime'])
    reader = lambda key: json.loads(support.exact(parent[key]).read_bytes())
    order = reader('order')
    manifest = [json.loads(k) for k in support.exact(parent['point_manifest']).read_bytes().splitlines()]
    rows, sources = old.select_training(reader('fold'), manifest, order)
    assets = json.loads(support.exact(q['files']['train_keys']).read_bytes())['cases']
    need(set(assets) == {r['case_id'] for r in rows}, 'exact training cache cases')
    model, target = prefix.build_model(parent, support, torch, helper, SEED, HEAD)
    need(helper.state_sha(model) == INITIAL, 'P1 frozen common parameter/buffer state')
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    rng = dict(python=sha(repr(random.getstate()).encode()), numpy=sha(np.random.get_state()[1].tobytes()),
               cpu=helper.tensor_sha(torch.get_rng_state()), cuda=helper.tensor_sha(torch.cuda.get_rng_state(0)))
    paired = q['paired_R_start']
    reference = json.loads(bound(paired['path'], paired['sha256']))
    need(reference['arm'] == 'R' and reference['request_sha256'] == paired['request_sha256']
         and reference['state_sha256'] == INITIAL and reference['rng'] == rng,
         'R_D shared initial state and four starting RNG streams')

    paired_c = q['paired_C_start']
    control = json.loads(bound(paired_c['path'], paired_c['sha256']))
    need(control['arm'] == 'C' and control['request_sha256'] == paired_c['request_sha256']
         and control['state_sha256'] == INITIAL and control['rng'] == rng,
         'C_D shared initial state and four starting RNG streams')

    prefix.emit(out/'rbss_start.json', dict(state_sha256=INITIAL, rng=rng, request_sha256=a.request_sha256, arm=q['arm']), 'x')
    dataset = runtime.BCSPDataset(parent['data_root'], rows, sources, 8192)
    def loader(epoch):
        return CheckedLoader(runtime.make_loader(dataset, order, epoch), order['epochs'][epoch]['batches'],
                             assets, model, target, torch, lib, q['arm'], q['geometry_sha256'])
    def claim(path):
        need(Path(path) == out and (out/'rbss_start.json').is_file(), 'owned output')
        return out
    start = time.monotonic()
    def sample():
        need(time.monotonic() - start <= b['resources']['wall_seconds'], 'wall cap')
        return support.resources(parent, out)
    resources = old.TrainingResources(out, torch, helper, sample,
                 lambda row: prefix.emit(out/'p3_resources.jsonl', row, 'a'), b['resources']['torch_peak_bytes'])
    knn = importlib.import_module('models.Transformer_utils').enable_bcsp_knn
    lifecycle(runtime, impl['training_runtime']['sha256'], claim)(q['arm'])(
        model, loader, rows, order, str(out), device='cuda:0', numeric_check=helper.assert_numeric,
        resources=resources, knn_enable=knn, state_fingerprint=helper.state_sha,
        run_identity=dict(variant=q['arm'], fold='D', seed=SEED))


if __name__ == '__main__':
    main()
