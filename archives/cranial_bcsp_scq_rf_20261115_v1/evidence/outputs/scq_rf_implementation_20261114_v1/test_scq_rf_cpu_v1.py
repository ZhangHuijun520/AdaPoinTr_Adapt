"""Single retained artificial CPU batch. No native Mamba, data, checkpoint or optimizer."""
from pathlib import Path
import ast
import gc
import hashlib
import json
import sys
import time
import traceback
import types
from functools import partial
import torch
from torch import nn

O = Path(__file__).resolve().parent
R = O.parents[1]
S = R / 'outputs/cranial_bcsp_scq_implementation_20261113_v1'
L = R / 'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1'
P = R / 'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'
SNAP = R / 'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot'
sys.path[:0] = [str(O), str(S), str(L), str(P)]
import bcsp_scq_rf_factory_v1 as factory
from bcsp_scq_rf_residual_v1 import RFResidual, load_initialization, initialization_values


def fingerprint(model):
    return {k: factory.parent.parent.parent.tensor_sha(v) for k, v in model.state_dict().items()}


def main():
    out = O / 'cpu_batch_v1'
    out.mkdir()
    checks, start = [], time.monotonic()
    def check(name, value=True):
        assert bool(value), name
        checks.append(name)
    def reject(name, fn):
        try:
            fn()
        except (ValueError, RuntimeError, TypeError):
            checks.append(name)
            return
        raise AssertionError('unexpected acceptance: ' + name)
    try:
        torch.set_num_threads(2)
        static = json.loads((O / 'static_review_v1.json').read_bytes())
        for row in static['frozen_files']:
            assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest() == row['sha256']
        check('all bound candidate and inherited source identities unchanged')
        init = json.loads((O / 'initialization_manifest_v1.json').read_bytes())
        scq_init = json.loads((S / 'initialization_manifest_v1.json').read_bytes())
        values = load_initialization(init)
        check('fixed private seed and exact initialization values', all(torch.equal(values[k], initialization_values()[k]) for k in values))
        # Exact inherited batched KNN, not a new tie-breaking implementation.
        adapter = {}
        tree = ast.parse((SNAP / 'tools/bcsp_adapter.py').read_text(encoding='utf-8'))
        nodes = [x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name in ('_shape_check', 'torch_knn')]
        exec(compile(ast.Module(nodes, []), str(SNAP / 'tools/bcsp_adapter.py'), 'exec'), adapter)
        knn = adapter['torch_knn']
        gen = torch.Generator().manual_seed(118)
        M = torch.randn(1, 256, 3, generator=gen)
        F = torch.randn(1, 256, 384, generator=gen)
        z = torch.randn(1, 1024, generator=gen)
        Q0 = torch.randn(1, 256, 3, generator=gen)
        N0 = knn(8, M, Q0)
        rng = torch.random.get_rng_state().clone()
        a, b = [RFResidual(v, knn, init) for v in ('RF-Static', 'RF-Requery')]
        check('construction preserves common RNG', torch.equal(rng, torch.random.get_rng_state()))
        check('both arms exactly same persistent initial state', fingerprint(a) == fingerprint(b))
        check('exact231171 parameters no extra buffers', sum(p.numel() for p in a.parameters()) == 231171 and not list(a.buffers()))
        h0, i0 = a.describe(M, F, z, Q0, N0)
        h1, i1 = b.describe(M, F, z, Q0, N0)
        check('Q1 equals Qraw gives same native neighbors and descriptor', torch.equal(h0, h1) and torch.equal(i0['indices'], i1['indices']))
        # A nonzero coordinate shift with unchanged nearest set, found deterministically.
        Qsmall = Q0 + 1e-7
        hs, _ = a.describe(M, F, z, Qsmall, N0)
        hr, ir = b.describe(M, F, z, Qsmall, N0)
        check('nonzero tiny Q1 shift same selected sets', torch.equal(ir['indices'].sort(-1).values, N0.sort(-1).values))
        check('Static recomputes Q1 geometry even when neighbors unchanged', not torch.equal(hs[..., -7:], h0[..., -7:]) and torch.allclose(hs, hr, atol=2e-6, rtol=2e-6))
        Q1 = Q0 + torch.tensor([2., -.8, .7])
        hs, si = a.describe(M, F, z, Q1, N0)
        hr, ri = b.describe(M, F, z, Q1, N0)
        check('changed-neighbor fixture proves mechanism distinction', not torch.equal(N0.sort(-1).values, ri['indices'].sort(-1).values) and not torch.equal(hs, hr))
        check('Static preserves N0 while Requery uses native Q1 KNN', torch.equal(si['indices'], N0) and torch.equal(ri['indices'], knn(8, M, Q1)))
        check('z and current Q1 descriptor channels common', torch.equal(hs[..., :1024], hr[..., :1024]) and torch.equal(hs[..., 1792:1795], Q1) and torch.equal(hr[..., 1792:1795], Q1))
        batch = torch.arange(1)[:, None, None]
        selected = F.double()[batch, N0]
        nf = (selected - selected.mean(-1, keepdim=True)) / ((selected - selected.mean(-1, keepdim=True)).square().mean(-1, keepdim=True) + 1e-5).sqrt()
        d = M.double()[batch, N0] - Q1.double()[:, :, None]
        dm = d.mean(2)
        geometry = torch.cat((dm, ((d - dm[:, :, None]).square().mean(2) + 1e-6).sqrt(), d.norm(dim=-1).mean(2, keepdim=True)), -1)
        expected = torch.cat((z.double()[:, None].expand(-1, 256, -1), nf.mean(2), nf.max(2).values, Q1.double(), geometry), -1)
        check('independent float64 descriptor formula LN before aggregation', torch.allclose(hs.double(), expected, atol=2e-6, rtol=2e-5))
        check('zero output exactly Q2 equals Q1 both arms', torch.equal(a(M, F, z, Q1, N0)[0], Q1) and torch.equal(b(M, F, z, Q1, N0)[0], Q1))
        inputs = [x.clone().requires_grad_() for x in (M, F, z, Q1)]
        a(*inputs, N0)[0].square().mean().backward()
        check('initial V2 effective gradients V1 zero expected', a.V2.weight.grad.abs().sum() > 0 and a.V2.bias.grad.abs().sum() > 0 and a.V1.weight.grad.abs().sum() == 0 and a.V1.bias.grad.abs().sum() == 0)
        a.zero_grad(set_to_none=True)
        with torch.no_grad():
            a.V2.weight.copy_(torch.sin(torch.arange(384).reshape(3, 128)) * .002)
        inputs = [x.clone().requires_grad_() for x in (M, F, z, Q1)]
        a(*inputs, N0)[0].square().mean().backward()
        check('nonzero diagnostic V2 gradient reaches all continuous inputs', all(x.grad is not None and torch.isfinite(x.grad).all() and x.grad.abs().sum() > 0 for x in inputs))
        check('nonzero diagnostic V2 gradient reaches V1', all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0 for p in a.parameters()))
        check('indices nondifferentiable diagnostics detached', not ri['indices'].requires_grad and all(not x.requires_grad for x in a(*inputs, N0)[1].values()))
        arrays = [x.expand(8, *x.shape[1:]).clone() for x in (M, F, z, Q1)]
        arrays[0][1:] += 20
        arrays[3][1:] += 20
        arrays[1][1:] *= 2
        idx8 = N0.expand(8, -1, -1).clone()
        h8, _ = b.describe(*arrays, idx8)
        check('B8 shape and batch independence', h8.shape == (8, 256, 1802) and torch.allclose(h8[:1], hr, atol=2e-6))
        tied = M.clone(); tied[:, 1] = tied[:, 0]
        _, ti = b.describe(tied, F, z, Q1, knn(8, tied, Q0))
        check('duplicate and equal-distance ties exactly inherited', torch.equal(ti['indices'], knn(8, tied, Q1)))
        perm = torch.randperm(256, generator=gen)
        ph, _ = b.describe(M[:, perm], F[:, perm], z, Q1, knn(8, M[:, perm], Q0))
        check('synchronous Memory permutation unique-distance consistency', torch.allclose(ph, hr, atol=3e-6, rtol=2e-6))
        reject('wrong dtype rejected', lambda: b(M.double(), F, z, Q1, N0))
        reject('wrong shape rejected', lambda: b(M[:, :255], F, z, Q1, N0))
        reject('invalid N0 rejected', lambda: a(M, F, z, Q1, N0 + 256))
        bad = F.clone(); bad[0, 0, 0] = float('nan')
        reject('nonfinite rejected', lambda: b(M, bad, z, Q1, N0))
        reject('GT not a model argument', lambda: b(M, F, z, Q1, N0, gt=Q1))
        reject('wrong initialization SHA rejected', lambda: load_initialization({**init, 'sha256': '0' * 64}))
        # Reuse only the exact retained artificial constructor and class setup, not its old tests.
        old_test = S / 'test_scq_cpu_v1.py'
        old = old_test.read_text(encoding='utf-8')
        setup = old[old.index('  env=dict(torch='):old.index('  rng=torch.random.get_rng_state().clone();mix=')]
        import textwrap
        scope = dict(torch=torch, nn=nn, partial=partial, ast=ast, types=types,
                     SNAP=SNAP, R=R, knn=knn, sys=sys)
        exec(compile(textwrap.dedent(setup), str(old_test) + ':fixture_setup', 'exec'), scope)
        legacy, mixer = scope['legacy'], scope['env']['ArtificialCausalMixer']
        rng = torch.random.get_rng_state().clone()
        reference, _ = factory.parent.build_artificial_fixture(legacy, mixer, 'S', scq_init)
        models = [factory.build_artificial_fixture(legacy, mixer, v, scq_init, init)[0] for v in ('RF-Static', 'RF-Requery')]
        check('complete factory construction preserves caller RNG', torch.equal(rng, torch.random.get_rng_state()))
        ref_state = fingerprint(reference)
        check('all inherited parameters and BN buffers preserved exactly', all(all(fingerprint(m)[k] == v for k, v in ref_state.items()) for m in models))
        check('full Static Requery state exact same initialization', fingerprint(models[0]) == fingerprint(models[1]))
        totals = [sum(p.numel() for p in m.parameters()) for m in [reference, *models]]
        check('actual artificial parameter deltas231171', totals[1] == totals[2] == totals[0] + 231171)
        check('no registered attention added', all(factory.parent.parent.no_attention_inventory(m)['forbidden_registered_modules'] == [] for m in models))
        inp = torch.randn(1, 8192, 3, generator=gen) * .5
        for m in [reference, *models]: m.eval()
        with torch.inference_mode():
            initial = [m(inp) for m in [reference, *models]]
        check('zero RF exact full8192 predictions equal S reference', all(all(torch.equal(x, y) for x, y in zip(initial[0], ret)) for ret in initial[1:]))
        del reference, initial; gc.collect()
        model = models[1]
        before = fingerprint(model)
        clone, _ = factory.build_artificial_fixture(legacy, mixer, 'RF-Requery', scq_init, init)
        clone.load_state_dict(model.state_dict(), strict=True)
        check('strict state roundtrip same registered keys values', fingerprint(clone) == before)
        del clone; gc.collect()
        for m in models:
            with torch.no_grad():
                m.base_model.scq.W2.bias.copy_(torch.tensor([.18, -.1, .07]))
                m.base_model.rf.V2.weight.copy_(torch.sin(torch.arange(384).reshape(3, 128)) * .002)
                m.base_model.rf.V2.bias.copy_(torch.tensor([-.09, .04, .02]))
        tracked = {}; base = model.base_model; dec = base.decoder; old_knn = dec.knn
        def track_knn(k, source, query):
            tracked.setdefault('knn', []).append((source.detach().clone(), query.detach().clone()))
            return old_knn(k, source, query)
        dec.knn = track_knn
        hooks = [base.mlp_query.register_forward_pre_hook(lambda m, args: tracked.update(mlp=args[0].detach().clone())),
                 dec.register_forward_pre_hook(lambda m, args, kw: tracked.update(dec_q=kw['q_pos'].detach().clone()), with_kwargs=True),
                 dec.coordinate_pe.register_forward_pre_hook(lambda m, args: tracked.setdefault('pe', []).append(args[0].detach().clone())),
                 dec.blocks[0].register_forward_pre_hook(lambda m, args: tracked.update(order=args[6].detach().clone())),
                 model.reduce_map.register_forward_pre_hook(lambda m, args: tracked.update(rebuild=args[0].detach().clone())),
                 model.decode_head.register_forward_hook(lambda m, args, val: tracked.update(relative=val.detach().clone()))]
        with torch.inference_mode(): ret = model(inp)
        for handle in hooks: handle.remove()
        dec.knn = old_knn
        diag = base._scq_last_info
        check('original SCQ preserved Qraw plus delta0 then RF Q1 plus delta1', torch.equal(diag['Q1'], diag['Q0'] + diag['delta0']) and torch.equal(ret[0], diag['Q1'] + diag['delta1']))
        check('Q2 consumed by actual query MLP decoder coordinate PE', torch.equal(tracked['mlp'][..., -3:], ret[0]) and torch.equal(tracked['dec_q'], ret[0]) and torch.equal(tracked['pe'][0], ret[0]))
        check('actual downstream self cross KNN use Q2', len(tracked['knn']) == 2 and all(torch.equal(q, ret[0]) for _, q in tracked['knn']))
        order, _ = sys.modules['bcsp_mamba_encoder_v1'].lexicographic_order(ret[0])
        check('actual decoder sort uses Q2', torch.equal(tracked['order'], order))
        check('actual FC condition dense center and returned coarse use Q2', torch.equal(tracked['rebuild'][..., -3:], ret[0]) and torch.equal(ret[1], (tracked['relative'] + ret[0][:, :, None]).reshape(1, 8192, 3)))
        # Same state, sole branch is the second neighbor selection.
        with torch.inference_mode(): rs = models[0](inp)
        check('active RF heads produce different predictions after neighbors change', not torch.equal(rs[0], ret[0]) and not torch.equal(rs[1], ret[1]))
        check('first stage Q1 identical between arms at same state', torch.equal(models[0].base_model._scq_last_info['Q1'], diag['Q1']))
        ids = {id(p) for p in [*base.scq.parameters(), *base.rf.parameters()]}
        common = [p for p in model.parameters() if id(p) not in ids]
        parent_groups = [dict(params=[p for p in common if p.ndim > 1], weight_decay=5e-4), dict(params=[p for p in common if p.ndim <= 1], weight_decay=0.)]
        groups = factory.optimizer_groups(model, parent_groups)
        grouped = [p for g in groups for p in g['params']]
        check('optimizer complete unique partition parent groups unchanged', groups[0] is parent_groups[0] and groups[1] is parent_groups[1] and len(grouped) == len({id(p) for p in grouped}) == len(list(model.parameters())))
        check('both heads weights decay biases no decay', [g['weight_decay'] for g in groups[-4:]] == [5e-4, 0., 5e-4, 0.])
        reject('duplicate shared optimizer partition rejected', lambda: factory.optimizer_groups(model, [dict(params=common + common)]))
        reject('double RF installation rejected', lambda: factory.install(model, 'RF-Requery', init))
        # Full inherited loss on8192 artificial points; not a reduced synthetic replacement loss.
        del models[0]; gc.collect()
        model.train(); buffers = {k: v.clone() for k, v in model.named_buffers()}
        params = fingerprint(model)
        model.zero_grad(set_to_none=True)
        ret = model(inp)
        ret[0].retain_grad()
        check('original no-denoise train tuple8192 preserved', len(ret) == 4 and ret[0].shape == (1, 256, 3) and ret[1].shape == (1, 0, 3) and ret[3].shape == (1, 8192, 3))
        target = torch.randn(1, 8192, 3, generator=gen) * .5 + torch.tensor([.8, .2, -.3])
        calls = []
        handles = [model.loss_func.register_forward_pre_hook(lambda m, args: calls.append(('coarse', tuple(args[0].shape)))), model.fine_loss_func.register_forward_pre_hook(lambda m, args: calls.append(('dense', tuple(args[0].shape))))]
        zero, loss = model.get_loss(ret, target)
        for handle in handles: handle.remove()
        check('original coarse dense loss once each no denoise auxiliary loss', zero.item() == 0 and calls == [('coarse', (1, 256, 3)), ('dense', (1, 8192, 3))] and torch.isfinite(loss))
        loss.backward()
        check('original complete loss reaches Q2 and both full heads', ret[0].grad is not None and ret[0].grad.abs().sum() > 0 and all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0 for p in [*base.scq.parameters(), *base.rf.parameters()]))
        with torch.no_grad():
            for k, v in model.named_buffers(): v.copy_(buffers[k])
        check('no optimizer step persistent parameters unchanged BN restored', fingerprint(model) == params)
        result = dict(status='RF_ARTIFICIAL_CPU_CONTRACT_PASS', checks=checks, count=len(checks), seconds=time.monotonic() - start,
                      torch=torch.__version__, initialization_sha256=init['sha256'], artificial_parameter_totals=totals,
                      loss=float(loss.detach()), CUDA=False, real_data=False, real_checkpoint=False, optimizer_steps=0,
                      limitations=['Actual mother forward, LQI decoder, FC head and original8192 cdist loss exercised with retained artificial constructors, grouper/FPS and causal surrogate Mamba.',
                                   'CPU tests do not validate native Mamba/PointNet2 CUDA, batch8 full loss, GPU memory or RF scientific efficacy.',
                                   'Parent optimizer policy retained as supplied; synthetic CPU grouping does not certify native SSM no-decay classification.',
                                   'Artifact/state_dict reconstruction supported; copying or whole-model pickling of dynamically installed methods is not an approved serialization route.'])
        (out / 'result_v1.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
        print(json.dumps(dict(status=result['status'], count=len(checks), seconds=result['seconds'])))
    except BaseException as exc:
        (out / 'failure_v1.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY', checks=checks, error=repr(exc), traceback=traceback.format_exc()), indent=2), encoding='utf-8')
        raise


if __name__ == '__main__':
    main()
