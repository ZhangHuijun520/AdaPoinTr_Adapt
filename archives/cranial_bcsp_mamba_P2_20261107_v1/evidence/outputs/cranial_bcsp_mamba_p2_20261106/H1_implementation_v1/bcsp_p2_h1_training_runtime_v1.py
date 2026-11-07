# P2 H1 derivative: only detached H1 diagnostics added; loss/update lifecycle unchanged.
# Isolated P1 derivative of bcsp_training_runtime_v5.py.
# Parent SHA256: 55ad69b0e87f3fc4ecac68a5ebcc4cdd560c4825ff01363ba9868de5875f0847
# Same lifecycle; respect SSM no-decay flags and label existing loss values accurately.
"""Fixed BCSP training lifecycle; no runner/package initializer or auto-execution."""
from collections import Counter
import json
import os
from pathlib import Path
import time

import torch
from torch.utils.data import Dataset, DataLoader
from tools.bcsp_adapter import Contract, UpdateGuard, load_case
from bcsp_training_contract_v1 import require, no_links, emit, sha, canonical_sha, validate_order


class BCSPDataset(Dataset):
    def __init__(self, root, records, sources, n_input):
        require(n_input in (8192, 16384), 'input count')
        require(len(records) == 315 and len(sources) == len(set(sources)) == 63, 'dataset counts')
        require(len({r['case_id'] for r in records}) == 315, 'duplicate case')
        counts = Counter(r['source_id'] for r in records)
        require(set(counts) == set(sources) and set(counts.values()) == {5}, 'fixed sources/five defects')
        self.root = no_links(root)
        self.records, self.sources, self.n_input = tuple(records), frozenset(sources), n_input

    def __len__(self):
        return 315

    def __getitem__(self, i):
        r = self.records[i]
        x, y = load_case(self.root, r, self.sources, self.n_input, training=True)
        return torch.from_numpy(x), torch.from_numpy(y), r['case_id'], r['source_id']


def make_order(case_ids):
    """Preserve the prior shuffle generator's permutation, including base-seed draw."""
    require(len(case_ids) == len(set(case_ids)) == 315, '315 fixed ordered case IDs')
    epochs = []
    for epoch in range(100):
        generator = torch.Generator(device='cpu').manual_seed(epoch)
        loader = DataLoader(list(range(315)), batch_size=315, shuffle=True, drop_last=False,
                            num_workers=0, generator=generator)
        indices = next(iter(loader)).tolist()
        order = [case_ids[i] for i in indices]
        epochs.append({'epoch': epoch, 'batches': [order[i:i + 8] for i in range(0, 312, 8)],
                       'dropped': order[312:]})
    return validate_order({'schema': 'bcsp-shared-order-v1', 'case_ids': list(case_ids), 'epochs': epochs},
                          list(case_ids))


def make_loader(dataset, plan, epoch):
    ids = [r['case_id'] for r in dataset.records]
    lookup = {cid: i for i, cid in enumerate(ids)}
    require(plan['case_ids'] == ids and 0 <= epoch < 100, 'loader order identity')
    batches = [[lookup[cid] for cid in batch] for batch in plan['epochs'][epoch]['batches']]
    generator = torch.Generator(device='cpu').manual_seed(epoch)
    return DataLoader(dataset, batch_sampler=batches, num_workers=0, generator=generator)


def optimizer_groups(model):
    decay, no_decay, records = [], [], []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        flagged = bool(getattr(p, '_no_weight_decay', False))
        exempt = flagged or p.ndim == 1 or name.endswith('.bias')
        (no_decay if exempt else decay).append(p)
        records.append({'name': name, 'shape': list(p.shape), 'weight_decay': 0. if exempt else .0005,
                        'reason': 'explicit_no_weight_decay' if flagged else
                        'one_dimensional_or_bias' if exempt else 'matrix_default'})
    require(len({id(p) for p in decay + no_decay}) == len(decay + no_decay), 'duplicate optimizer parameters')
    return [{'params': no_decay, 'weight_decay': 0.}, {'params': decay, 'weight_decay': .0005}], records


def make_optimizer(model):
    groups, _ = optimizer_groups(model)
    return torch.optim.AdamW(groups, lr=.0001, betas=(.9, .999), eps=1e-8,
                             amsgrad=False, foreach=None, fused=None)


def set_bn_momentum(model, epoch):
    value = max(.9 * .5 ** (epoch / 21), .01)
    for module in model.modules():
        if isinstance(module, torch.nn.modules.batchnorm._BatchNorm):
            require(module.track_running_stats, 'ordinary training BN tracking required')
            module.momentum = value
    return value


def claim_output(out):
    out = no_links(out)
    if out.exists():
        names = {p.name for p in out.iterdir()}
        require(out.is_dir() and 'worker.pid' in names
                and names <= {'worker.pid', 'launch.log', 'tmp', 'resources.jsonl'}, 'fresh owned output only')
        require((out / 'worker.pid').read_text().strip() == str(os.getpid()), 'output PID owner')
        require(all(not p.is_symlink() and (p.is_file() or p.name == 'tmp' and p.is_dir())
                    for p in out.iterdir()), 'output file type')
        require(not (out / 'resources.jsonl').exists() or (out / 'resources.jsonl').stat().st_size == 0,
                'resource attempt already used')
    else:
        out.mkdir()
        with (out / 'worker.pid').open('x', encoding='ascii') as stream:
            stream.write(str(os.getpid()) + '\n')
    return out



def h1_log_components(model, ret, target, total_loss):
    """Detached O(N) diagnostics; never adds loss or recomputes Chamfer/forward."""
    enabled = model.coarse_geometry_guard_enabled
    with torch.no_grad():
        if enabled:
            require(model.coarse_geometry_guard_mode == 'centroid_radius'
                    and model.coarse_geometry_guard_weight == .1
                    and model.coarse_geometry_guard_beta == .1
                    and model.coarse_geometry_guard_eps == 1e-6, 'unique H1 formula')
            fn = model.get_loss.__func__.__globals__['coarse_geometry_guard_components']
            c = fn(ret[0], target, smooth_l1_beta=.1, cvar_fraction=.1,
                   eps=1e-6, requested_mode='centroid_radius')
            raw = c['centroid_radius']
            center, radius = c['centroid'], c['radius']
        else:
            raw = center = radius = total_loss.new_zeros(())
        weighted = raw * .1 if enabled else raw
        values = {'H1_enabled': bool(enabled), 'H1_centroid': float(center),
                  'H1_radius': float(radius), 'H1_raw': float(raw),
                  'H1_weighted': float(weighted),
                  'loss_without_H1_derived': float(total_loss.detach() - weighted),
                  'H1_log_is_detached_recomputation': True}
        require(all(__import__('math').isfinite(v) for v in values.values()
                    if type(v) is float), 'finite H1 diagnostic')
        return values

def train_lifecycle(model, loader_factory, records, plan, out, *, device, numeric_check, resources,
                    knn_enable, state_fingerprint):
    """Fixed real optimizer loop; CPU validation uses only a named artificial tiny model."""
    ids = [r['case_id'] for r in records]
    validate_order(plan, ids)
    source_by_id = {r['case_id']: r['source_id'] for r in records}
    require(len(source_by_id) == 315 and len(set(source_by_id.values())) == 63, 'lifecycle sources')
    out = claim_output(out)
    counts = {'forward': 0, 'backward': 0, 'clip': 0, 'step': 0, 'lr_scheduler': 0, 'bn_scheduler': 0}
    guard = UpdateGuard(Contract())
    case_exposure, source_exposure, dropped = Counter(), Counter(), Counter()
    metrics_path = out / 'metrics.jsonl'
    started = time.monotonic()
    try:
        emit(out / 'order_plan.json', plan)
        numeric_check(torch)
        emit(out / 'initialization.json', {'parameter_sha256': state_fingerprint(model, True),
                                          'persistent_state_sha256': state_fingerprint(model),
                                          'order_sha256': canonical_sha(plan), 'seed': 0})
        model.to(device)
        require(all(p.dtype == torch.float32 for p in model.parameters()), 'FP32 model')
        optimizer = make_optimizer(model)
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda e: max(.9 ** (e / 21), .02))
        emit(out / 'optimizer_actual_defaults.json', optimizer.defaults)
        emit(out / 'optimizer_parameter_groups.json', optimizer_groups(model)[1])
        knn_enable()
        with metrics_path.open('x', encoding='utf-8', newline='\n') as metrics:
            for epoch in range(100):
                numeric_check(torch)
                row = plan['epochs'][epoch]
                loader = loader_factory(epoch)
                guard.begin_epoch(epoch, len(loader))
                model.train()
                momentum = set_bn_momentum(model, epoch)
                counts['bn_scheduler'] += 1
                for batch_index, (partial, target, batch_ids, batch_sources) in enumerate(loader):
                    batch_ids, batch_sources = list(batch_ids), list(batch_sources)
                    require(batch_ids == row['batches'][batch_index]
                            and batch_sources == [source_by_id[cid] for cid in batch_ids], 'actual batch/order drift')
                    guard.before_step(len(partial))
                    require(len(target) == len(batch_ids) == 8, 'fixed batch8')
                    numeric_check(torch)
                    resources.before_step(counts['step'])
                    partial, target = partial.to(device), target.to(device)
                    optimizer.zero_grad(set_to_none=True)
                    ret = model(partial)
                    counts['forward'] += 1
                    sparse, dense = model.get_loss(ret, target, epoch, partial=partial)
                    loss = sparse + dense
                    h1_event = h1_log_components(model, ret, target, loss)
                    require(loss.numel() == 1 and torch.isfinite(loss).all().item(), 'finite scalar loss')
                    loss.backward()
                    counts['backward'] += 1
                    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 10, error_if_nonfinite=True)
                    counts['clip'] += 1
                    optimizer.step()
                    counts['step'] += 1
                    guard.after_step()
                    case_exposure.update(batch_ids)
                    source_exposure.update(batch_sources)
                    event = {'step': counts['step'], 'epoch': epoch, 'batch': batch_index,
                             'case_ids': batch_ids, 'source_ids': batch_sources,
                             'loss_sparse': float(sparse.detach()), 'loss_dense': float(dense.detach()),
                             'loss_denoise': float(sparse.detach()), 'loss_reconstruction': float(dense.detach()),
                             'loss': float(loss.detach()), 'LR': [g['lr'] for g in optimizer.param_groups],
                             'BN_momentum': momentum, 'grad_norm_before_clip': float(norm),
                             'clip_max_norm': 10, 'optimizer_step_committed': True}
                    event.update(h1_event)
                    metrics.write(json.dumps(event, allow_nan=False) + '\n')
                    metrics.flush()
                    numeric_check(torch)
                    resources.after_step(counts['step'])
                guard.end_epoch()
                dropped.update(row['dropped'])
                scheduler.step()
                counts['lr_scheduler'] += 1
        state = guard.finish()
        numeric_check(torch)
        require(counts == {'forward': 3900, 'backward': 3900, 'clip': 3900, 'step': 3900,
                           'lr_scheduler': 100, 'bn_scheduler': 100}, 'exact lifecycle counts')
        require(sum(case_exposure.values()) == sum(source_exposure.values()) == 31200
                and sum(dropped.values()) == 300, 'exact exposure/drop counts')
        emit(out / 'exposure.json', {'case': dict(case_exposure), 'source': dict(source_exposure),
                                    'dropped_case': dict(dropped), 'order_sha256': canonical_sha(plan)})
        resources.before_final()
        final = out / 'ckpt-last.pth'
        with final.open('xb') as stream:
            torch.save({'base_model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                        'scheduler': scheduler.state_dict(), 'epoch': 99,
                        'stage': 'BCSP_INPUT_DENSITY_V1', 'updates': 3900}, stream)
        resources.after_final()
        receipt = {**state, 'counts': counts, 'checkpoint_sha256': sha(final),
                   'order_sha256': canonical_sha(plan), 'elapsed_seconds': time.monotonic() - started,
                   'bncal_executed': False, 'evaluation_executed': False, 'resume': False}
        emit(out / 'completion.json', receipt)
        return receipt
    except BaseException as exc:
        guard.abort()
        emit(out / 'failure.json', {'status': 'FAILED_STOP_NO_RETRY', 'error': repr(exc),
                                   'counts': counts, 'committed_steps': guard.steps})
        raise
