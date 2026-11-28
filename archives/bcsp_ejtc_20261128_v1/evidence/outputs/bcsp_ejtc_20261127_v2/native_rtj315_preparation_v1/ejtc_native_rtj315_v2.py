"""EJTC R/T/J Native inference only. No training entry or label/loss attachment."""
import argparse
from contextlib import ExitStack
import gc
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import shutil
import socket
import sys
import tarfile
import time
import types

ARMS = ('R', 'T', 'J')
SEEDS = (2026112801, 2026112803)
COUNTS = dict(forward=315, loss=0, backward=0, optimizer_steps=0,
              BNCal=0, warmup=0, TTA=0, scoring=0)
SCOPE_SHA = 'e70eeff89284e009b9ada79c9675884cc925da0d51ebb7ccaf77e7d30b0573fd'
STATUSES = dict(R='FORMAL_READ_ONLY_R_D_V3_POST_TRAINING_FREEZE_AUDIT_PASS',
                T='FORMAL_READ_ONLY_T_D_POST_TRAINING_AND_R_T_PAIR_FREEZE_PASS',
                J='FORMAL_READ_ONLY_J_D_POST_TRAINING_AND_R_T_J_PAIR_FREEZE_PASS')


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def bound(record):
    p = Path(record['path'])
    need(p.is_absolute() and p.resolve(strict=True) == p and not p.is_symlink(), 'exact file path')
    mark = p.stat()
    need(mark.st_size == record['bytes'] and mark.st_size <= 262144, 'bounded source/control size')
    raw = p.read_bytes()
    after = p.stat()
    need((mark.st_ino, mark.st_size, mark.st_mtime_ns) ==
         (after.st_ino, after.st_size, after.st_mtime_ns) and sha(raw) == record['sha256'], 'exact file bytes')
    return raw


def control(path, digest):
    p = Path(path)
    need(p.resolve(strict=True) == p and not p.is_symlink() and p.stat().st_size <= 262144, 'control path/size')
    raw = p.read_bytes()
    need(sha(raw) == digest, 'control SHA256')
    return json.loads(raw)


def source(record):
    module = types.ModuleType(Path(record['path']).stem)
    module.__file__ = record['path']
    exec(compile(bound(record), record['path'], 'exec', dont_inherit=True), module.__dict__)
    return module


def authorize(q, digest, auth, auth_digest, runtime):
    need(q['schema'] == 'bcsp-ejtc-rtj-native315-v1'
         and q['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
         and q['counts'] == COUNTS and q['seeds'] == list(SEEDS) and q['arms'] == list(ARMS)
         and q['files']['scope']['sha256'] == SCOPE_SHA, 'exact Native315 request')
    need(auth == dict(schema='bcsp-development-authorization-v1', request_sha256=digest,
                      explicit_user_authorization=True, user_authorization_text=auth.get('user_authorization_text'))
         and isinstance(auth['user_authorization_text'], str) and digest in auth['user_authorization_text']
         and runtime == dict(schema='bcsp-development-runtime-v1', request_sha256=digest,
                             authorization_sha256=auth_digest), 'single-use authorization chain')


def verify_training(scope, receipts):
    need(scope['arms'] == list(ARMS) and scope['seeds'] == list(SEEDS)
         and scope['counts'] == COUNTS and set(receipts) == set(ARMS), 'three-arm scope')
    states = []
    for arm in ARMS:
        receipt = receipts[arm]
        need(receipt['status'] == STATUSES[arm]
             and receipt['request_sha256'] == scope['training_freeze_receipts'][arm]['training_request_sha256']
             and receipt['counts'] == dict(steps=3900, epochs=100, exposures=31200, drops=300, cases=315, sources=63)
             and {k: receipt['checkpoint'][k] for k in ('path', 'bytes', 'sha256')} == scope['checkpoints'][arm]
             and receipt['checkpoint']['independently_hashed_twice'] is True
             and receipt['worker_and_session_absent'] is True, 'frozen checkpoint ' + arm)
        initial = receipt['initial_state']
        need(initial['recorded_tensor_fingerprint'] == scope['shared_initial_fingerprint'], 'shared initialization')
        states.append((initial['parameter_fingerprint'], initial['serialized_sha256'], initial['rng']))
    need(states[0] == states[1] == states[2], 'paired starting state and RNG')
    need(receipts['T']['R_T_pair_contract_verified'] is True
         and receipts['J']['R_T_J_pair_contract_verified'] is True
         and receipts['J']['T_formal_freeze_sha256'] == scope['training_freeze_receipts']['T']['sha256']
         and receipts['T']['R_freeze_index_sha256'] == receipts['J']['R_freeze_index_sha256'], 'three-arm freeze chain')


def select_inputs(scope, parent, fold, manifest):
    f = fold['folds']['D']
    ids, sources = f['dev_case_ids'], f['dev_sources']
    need(scope['fold'] == 'D' and ids == scope['case_ids'] and len(ids) == len(set(ids)) == 105
         and len(sources) == len(set(sources)) == 21
         and not set(ids) & set(f['train_case_ids']) and not set(sources) & set(f['train_sources']), 'development-only split')
    indexed = {r['case_id']: r for r in manifest}
    need(len(indexed) == len(manifest) == 420 and len(scope['inputs']) == 105, 'frozen manifest population')
    for cid, row in zip(ids, scope['inputs']):
        original = indexed[cid]
        norm = row['normalization']
        need(row['case_id'] == cid and row['source_id'] == original['source_id'] in sources
             and original['point_path'] == f'points/{cid}_8192.npz'
             and row['input']['path'] == str(PurePosixPath(scope['input_root']) / original['point_path'])
             and row['input']['sha256'] == original['sha256'] and row['input']['bytes'] > 0
             and row['normalization'] == original['normalization']
             and original['normalization_source'] == 'defective_bbox'
             and original['schema'] == 'BCSP-normalized-v1'
             and row['n_input'] == original['n_input'] == original['n_target'] == 8192
             and len(norm['center']) == 3 and all(map(math.isfinite, norm['center']))
             and math.isfinite(norm['scale']) and norm['scale'] > 0, 'frozen input/frame ' + cid)
    need(all(sum(r['source_id'] == s for r in scope['inputs']) == 5 for s in sources), 'five cases per source')
    return scope['inputs']


def load_partial(np, support, row):
    with np.load(io.BytesIO(support.exact(row['input']).read_bytes()), allow_pickle=False) as archive:
        x = archive['partial'].copy()
    need(x.shape == (8192, 3) and x.dtype == np.float32 and np.isfinite(x).all()
         and sha(x.tobytes()) == row['partial_array_sha256'], 'partial-only array identity')
    return x


class ForwardBudget:
    def __init__(self, ids):
        need(len(ids) == len(set(ids)) == 105, '105 unique inputs')
        self.schedule = [(arm, cid) for arm in ARMS for cid in ids]
        self.calls = 0

    def claim(self, arm, cid):
        need(self.calls < 315 and self.schedule[self.calls] == (arm, cid), 'forward order/budget')
        self.calls += 1
        return self.calls

    def finish(self, saved):
        need(self.calls == saved == 315, '315 complete predictions')


def construct_load(torch, helper, prefix, support, parent, scope, arm):
    need(arm in ARMS, 'known EJTC arm')
    model, _ = prefix.build_model(parent, support, torch, helper, *scope['seeds'])
    need(helper.state_sha(model) == scope['shared_initial_fingerprint'], 'same untrained model constructor')
    checkpoint = torch.load(support.exact(scope['checkpoints'][arm]), map_location='cpu', weights_only=True)
    need(isinstance(checkpoint, dict) and checkpoint.get('scq_prime_run_identity') ==
         dict(variant=arm, fold='D', seed=SEEDS[0]) and checkpoint.get('epoch') == 99
         and checkpoint.get('updates') == 3900 and checkpoint.get('stage') == 'BCSP_INPUT_DENSITY_V1'
         and isinstance(checkpoint.get('base_model'), dict), 'checkpoint run identity ' + arm)
    model.load_state_dict(checkpoint['base_model'], strict=True)
    del checkpoint
    need(all(p.dtype == torch.float32 for p in model.parameters()), 'FP32 parameters')
    return model


def snapshot(torch, np, helper, model):
    state = np.random.get_state()
    return dict(state=helper.state_sha(model), python=sha(repr(random.getstate()).encode()),
                numpy=sha(repr((state[0], *state[2:])).encode() + state[1].tobytes()),
                cpu=helper.tensor_sha(torch.get_rng_state()), cuda=helper.tensor_sha(torch.cuda.get_rng_state(0)))


def validate_payload(np, payload):
    need(set(payload) == {'coarse', 'prediction', 'S', 'delta', 'parent_index', 'token_index'}, 'Native diagnostic fields')
    for key, shape in [('coarse', (256, 3)), ('prediction', (8192, 3)), ('S', (256, 3)), ('delta', (256, 3))]:
        value = payload[key]
        need(value.shape == shape and value.dtype == np.float32 and np.isfinite(value).all(), 'finite FP32 ' + key)
    need(np.array_equal(payload['S'] + payload['delta'], payload['coarse']), 'consumed OASG coarse identity')
    need(payload['parent_index'].dtype == payload['token_index'].dtype == np.int64
         and np.array_equal(payload['parent_index'], np.repeat(np.arange(256, dtype=np.int64), 32))
         and np.array_equal(payload['token_index'], np.arange(256, dtype=np.int64)), 'parent/token indices')


def observe(torch, np, native, model, x):
    base = model.base_model
    mixers = [b.attn.mixer for b in base.encoder.blocks.blocks]
    mixers.extend(m for b in base.decoder.blocks for m in (b.self_ssm, b.cond_ssm))
    need(len({id(m) for m in mixers}) == 22 and not any(m.training for m in model.modules()), 'Native Mamba eval graph')
    calls = [0]
    def count(*_):
        calls[0] += 1
    with ExitStack() as stack:
        for m in mixers:
            stack.callback(m.register_forward_hook(count).remove)
        # A describes the common OASG head geometry only. The actual checkpoint,
        # budget and output manifest retain the real R/T/J arm throughout.
        result = native.observe_once(torch, np, model, x, 'A')
    need(calls[0] == 36, 'one complete Native SSM forward')
    validate_payload(np, result)
    return result


def data_boundary(scope, out):
    read = {Path(r['input']['path']) for r in scope['inputs']} | {Path(r['path']) for r in scope['checkpoints'].values()}
    owned = {out / f'predictions/{arm}_D__{cid}.npz' for arm in ARMS for cid in scope['case_ids']}
    def audit(event, args):
        if event != 'open' or isinstance(args[0], int):
            return
        p = Path(os.fsdecode(args[0])).absolute()
        write = bool(args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
        if write:
            need(p.resolve() == out or out in p.resolve().parents, 'Native write outside output')
        if p.suffix.lower() in {'.npz', '.npy', '.pt', '.pth', '.ckpt', '.nrrd', '.nii', '.stl', '.ply'} or p.name.endswith('.nii.gz'):
            need(not any(x.is_symlink() for x in (p, *p.parents))
                 and (p in owned or not write and p in read), 'out-of-scope Native payload')
    return audit


def pack(out, saved, file_hash):
    members = [*saved, *(out / n for n in ('started.json', 'attempts.jsonl', 'manifest.jsonl', 'inference_complete.json', 'resources.jsonl'))]
    need(len(members) == len(set(members)) == 320, '315 predictions plus five evidence members')
    rows = [dict(name=p.relative_to(out).as_posix(), bytes=p.stat().st_size, sha256=file_hash(p)) for p in members]
    archive = out / 'EJTC_RTJ_D_native315.tar.gz'
    with archive.open('xb') as stream, tarfile.open(fileobj=stream, mode='w:gz') as writer:
        for p in members:
            writer.add(p, arcname=p.relative_to(out).as_posix(), recursive=False)
    digest = file_hash(archive)
    with Path(str(archive) + '.sha256').open('x', encoding='ascii') as stream:
        stream.write(digest + '  ' + archive.name + '\n')
    listing = out / 'archive_members.json'
    with listing.open('x', encoding='utf-8') as stream:
        json.dump(rows, stream, indent=2)
    with Path(str(listing) + '.sha256').open('x', encoding='ascii') as stream:
        stream.write(file_hash(listing) + '  ' + listing.name + '\n')
    return dict(name=archive.name, bytes=archive.stat().st_size, sha256=digest, members=320,
                member_listing=listing.name, member_listing_sha256=file_hash(listing))


def run(q, scope, out, digest, prefix, native, parent, support, started):
    sys.addaudithook(data_boundary(scope, out))
    torch, np, helper, _ = native.prepare_models(parent, support)
    helper._MONITOR = None
    partials = {row['case_id']: load_partial(np, support, row) for row in scope['inputs']}
    budget = ForwardBudget(scope['case_ids'])
    saved, states = [], []
    for name in ('attempts.jsonl', 'manifest.jsonl', 'resources.jsonl'):
        (out / name).open('x').close()
    for arm in ARMS:
        model = construct_load(torch, helper, prefix, support, parent, scope, arm)
        model.eval().requires_grad_(False).to('cuda:0')
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats(0)
        before = snapshot(torch, np, helper, model)
        for row in scope['inputs']:
            helper.assert_numeric(torch)
            cid = row['case_id']
            index = budget.claim(arm, cid)
            prefix.emit(out / 'attempts.jsonl', dict(index=index, arm=arm, case_id=cid, status='CLAIMED_BEFORE_FORWARD'), 'a')
            x = torch.from_numpy(partials[cid]).unsqueeze(0).to('cuda:0')
            payload = observe(torch, np, native, model, x)
            path = out / f'predictions/{arm}_D__{cid}.npz'
            with path.open('xb') as stream:
                np.savez_compressed(stream, **payload)
            saved.append(path)
            prefix.emit(out / 'manifest.jsonl', dict(index=index, arm=arm, fold='D', seed=SEEDS[0], case_id=cid,
                        source_id=row['source_id'], n_input=8192, n_output=8192, frame='native_D_only_normalized',
                        normalization=row['normalization'], input_sha256=row['input']['sha256'],
                        partial_array_sha256=row['partial_array_sha256'], checkpoint_sha256=scope['checkpoints'][arm]['sha256'],
                        diagnostic_fields=sorted(payload), ssm_calls=36, native_fc_parent_major_verified=True,
                        member=path.relative_to(out).as_posix(), bytes=path.stat().st_size, sha256=support.file_hash(path)), 'a')
            if index % 15 == 0:
                prefix.emit(out / 'resources.jsonl', dict(index=index, **prefix.gpu_sample(q, out, started, torch)), 'a')
            del x, payload
        after = snapshot(torch, np, helper, model)
        need(before == after, 'model parameters/buffers or RNG changed during Native inference')
        states.append(dict(arm=arm, forwards=105, before=before, after=after))
        del model
        gc.collect()
        torch.cuda.empty_cache()
    budget.finish(len(saved))
    prefix.emit(out / 'resources.jsonl', dict(index=315, phase='all_complete', **prefix.gpu_sample(q, out, started, torch)), 'a')
    prefix.emit(out / 'inference_complete.json', dict(status='EJTC_RTJ_D_NATIVE315_COMPLETE', request_sha256=digest,
                counts=COUNTS, states=states, paired_cases=105), 'x')
    archive = pack(out, saved, support.file_hash)
    need(sum(p.stat().st_size for p in out.rglob('*') if p.is_file()) <= q['binding']['resources']['output_bytes']
         and shutil.disk_usage(out).free >= q['binding']['resources']['minimum_disk_bytes']
         and time.monotonic() - started <= q['binding']['resources']['wall_seconds'], 'final archive resource limits')
    prefix.emit(out / 'completion.json', dict(status='PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT',
                request_sha256=digest, counts=COUNTS, archive=archive), 'x')


def main():
    parser = argparse.ArgumentParser()
    for k in ('request', 'request-sha256', 'authorization', 'authorization-sha256', 'runtime', 'runtime-sha256'):
        parser.add_argument('--' + k, required=True)
    args = parser.parse_args()
    q = control(args.request, args.request_sha256)
    authorize(q, args.request_sha256, control(args.authorization, args.authorization_sha256),
              args.authorization_sha256, control(args.runtime, args.runtime_sha256))
    binding = q['binding'];i = binding['identity'];out = Path(binding['output'])
    need(sys.platform == 'linux' and sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
         and (socket.gethostname(), os.getuid(), os.environ.get('CUDA_VISIBLE_DEVICES'),
              str(Path(sys.executable).resolve()), sys.version.split()[0]) ==
         (i['hostname'], i['uid'], i['gpu_uuid'], i['python_realpath'], i['python_version']), 'bound runtime')
    need([args.request, args.authorization, args.runtime] == [q['launch'][k + '_path'] for k in
         ('request', 'authorization', 'runtime')] and q['files']['worker']['path'] == str(Path(__file__).resolve()), 'exact controls/worker')
    for rec in q['files'].values():
        bound(rec)
    scope = json.loads(bound(q['files']['scope']))
    receipts = {arm: json.loads(bound(q['files']['receipt_' + arm])) for arm in ARMS}
    verify_training(scope, receipts)
    prefix, native = source(q['files']['prefix']), source(q['files']['native_loader'])
    parent = json.loads(bound(q['files']['parent']))
    parent.update(identity={**parent['identity'], **i}, resources=binding['resources'])
    support = prefix.load_support(parent)
    select_inputs(scope, parent, json.loads(support.exact(parent['fold']).read_bytes()),
                  [json.loads(v) for v in support.exact(parent['point_manifest']).read_bytes().splitlines()])
    for row in scope['inputs']:
        support.exact(row['input'])
    for rec in scope['checkpoints'].values():
        support.exact(rec)
    need(out.is_absolute() and out.resolve() == out and out.parent.is_dir() and not os.path.lexists(out), 'new output')
    started = time.monotonic()
    initial = prefix.gpu_sample(q, out, started)
    out.mkdir();(out / 'predictions').mkdir()
    for k, v in parent['environment'].items():
        if k not in ('CUDA_VISIBLE_DEVICES', 'TMPDIR', 'XDG_CACHE_HOME', 'MPLCONFIGDIR', 'TRITON_CACHE_DIR', 'HF_HOME'):
            os.environ[k] = v
    for k in ('TMPDIR', 'XDG_CACHE_HOME', 'MPLCONFIGDIR', 'TRITON_CACHE_DIR', 'HF_HOME'):
        p = out / k;p.mkdir();os.environ[k] = str(p)
    prefix.emit(out / 'started.json', dict(request_sha256=args.request_sha256, resources=initial, counts=COUNTS), 'x')
    try:
        run(q, scope, out, args.request_sha256, prefix, native, parent, support, started)
    except BaseException as error:
        prefix.emit(out / 'failure.json', dict(status='FAILED_STOP_NO_RETRY', error=repr(error)), 'x')
        raise


if __name__ == '__main__':
    main()
