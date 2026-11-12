"""Three isolated, offline decoder interventions. No whole-model forward or GT."""
import torch
from bcsp_mamba_encoder_v1 import gather_tokens, lexicographic_order

CONDITIONS = ('prefix_feature_null', 'prefix_donor', 'local_graph_donor')
TRACE_KEYS = ('input', 'after_self', 'prefix_suffix', 'after_cross', 'output')


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def validate_context(c):
    require(set(c) == {'F', 'S', 'z', 'Q', 'X'}, 'five cached contexts only')
    shapes = {'F': (1, 256, 384), 'S': (1, 256, 3), 'z': (1, 1024),
              'Q': (1, 256, 3), 'X': (1, 256, 384)}
    for k, shape in shapes.items():
        t = c[k]
        require(tuple(t.shape) == shape and t.dtype == torch.float32 and
                bool(torch.isfinite(t).all()) and not t.requires_grad, 'context ' + k)
        require(t.device == c['X'].device, 'context device')


def dense_head(model, q, positions):
    """Exact mother FC inference path, including both global max pool operations."""
    require(model.decoder_type == 'fc' and model.factor == 32, 'frozen FC head')
    global_feature = model.increase_dim(q.transpose(1, 2)).transpose(1, 2)
    global_feature = torch.max(global_feature, dim=1)[0]
    feature = torch.cat([global_feature.unsqueeze(1).expand(-1, 256, -1), q, positions], dim=-1)
    relative = model.decode_head(model.reduce_map(feature))
    require(tuple(relative.shape) == (1, 256, 32, 3), 'head offsets')
    dense = (relative + positions.unsqueeze(-2)).reshape(1, 8192, 3)
    require(bool(torch.isfinite(dense).all()), 'finite dense')
    return dense


def intervene(model, recipient, donor, condition):
    """One suffix call. Hooks isolate shared F/S arguments without editing frozen code."""
    require(condition in CONDITIONS, 'exact three conditions')
    require(not torch.is_grad_enabled(), 'inference context required')
    require(not any(m.training for m in model.modules()), 'all eval')
    validate_context(recipient); validate_context(donor)
    decoder = model.base_model.decoder
    require(len(decoder.blocks) == 8, 'eight blocks')
    original = {k: v.clone() for k, v in recipient.items()}
    donor_original = {k: v.clone() for k, v in donor.items()}
    handles = []
    counts = dict(decoder=0, head=0, self_ssm=0, cond_ssm=0, local_cross=0,
                  forbidden=0, donor_knn=0)
    prefix_logs = []

    def forbidden(*args, **kwargs):
        counts['forbidden'] += 1
        raise RuntimeError('whole model/encoder/coarse/query path forbidden')

    def count(key):
        def hook(*args):
            counts[key] += 1
        return hook

    try:
        for obj in [model, model.base_model]:
            handles.append(obj.register_forward_pre_hook(forbidden))
        for name in ('encoder', 'coarse_pred', 'mlp_query'):
            obj = getattr(model.base_model, name, None)
            if obj is not None:
                handles.append(obj.register_forward_pre_hook(forbidden))
        handles.append(decoder.register_forward_pre_hook(count('decoder')))
        handles.append(model.decode_head.register_forward_pre_hook(count('head')))
        for block in decoder.blocks:
            handles.append(block.self_ssm.register_forward_pre_hook(count('self_ssm')))
            handles.append(block.cond_ssm.register_forward_pre_hook(count('cond_ssm')))
        for i, block in enumerate(decoder.blocks):
            def prefix_hook(module, args, i=i, block=block):
                tokens, = args
                require(tuple(tokens.shape) == (1, 512, 384), 'prefix/suffix shape')
                c = donor if condition == 'prefix_donor' else recipient
                f = torch.zeros_like(c['F']) if condition == 'prefix_feature_null' else c['F']
                order, _ = lexicographic_order(c['S'])
                prefix = gather_tokens(block.norm_v(f) + decoder.coordinate_pe(c['S']), order)
                if condition == 'local_graph_donor':
                    require(torch.equal(prefix, tokens[:, :256]), 'recipient prefix unchanged')
                prefix_logs.append(dict(layer=i, prefix_source='donor' if condition == 'prefix_donor' else 'recipient',
                                        raw_feature_zero=condition == 'prefix_feature_null',
                                        local_source='donor' if condition == 'local_graph_donor' else 'recipient'))
                return (torch.cat([prefix, tokens[:, 256:]], dim=1).contiguous(),)
            handles.append(block.cond_ssm.register_forward_pre_hook(prefix_hook))
        local = decoder.blocks[0].local_cross_attn
        require(local is not None and all(b.local_cross_attn is None for b in decoder.blocks[1:]), 'one local graph')
        donor_idx = None
        if condition == 'local_graph_donor':
            donor_idx = decoder.knn(8, donor['S'], recipient['Q'])
            counts['donor_knn'] += 1

        def local_hook(module, args, kwargs):
            counts['local_cross'] += 1
            require(not args and set(kwargs) == {'q', 'v', 'q_pos', 'v_pos', 'idx'}, 'local kwargs')
            require(torch.equal(kwargs['q_pos'], recipient['Q']), 'fixed query coordinates')
            if condition == 'local_graph_donor':
                kwargs = dict(kwargs, v=decoder.blocks[0].norm_v(donor['F']),
                              v_pos=donor['S'], idx=donor_idx)
            else:
                require(torch.equal(kwargs['v_pos'], recipient['S']) and
                        torch.equal(kwargs['v'], decoder.blocks[0].norm_v(recipient['F'])),
                        'recipient local branch preserved')
            return args, kwargs
        handles.append(local.register_forward_pre_hook(local_hook, with_kwargs=True))
        q, layers = decoder(recipient['X'], recipient['F'], recipient['Q'], recipient['S'],
                            return_instrumentation=True)
        dense = dense_head(model, q, recipient['Q'])
        expected = dict(decoder=1, head=1, self_ssm=16, cond_ssm=8, local_cross=1,
                        forbidden=0, donor_knn=int(condition == 'local_graph_donor'))
        require(counts == expected and len(prefix_logs) == len(layers) == 8, 'suffix call counts')
        for c, before in [(recipient, original), (donor, donor_original)]:
            require(all(torch.equal(c[k], v) for k, v in before.items()), 'cached tensor mutated')
        return dense, layers, dict(counts=counts, isolation=prefix_logs,
                                  z_Q_X_unchanged=True, donor_unchanged=True)
    finally:
        for handle in reversed(handles):
            handle.remove()


def response(a, b):
    require(a.shape == b.shape and bool(torch.isfinite(a).all()) and bool(torch.isfinite(b).all()), 'finite comparison')
    a, b = a.double(), b.double()
    d = a - b
    return dict(max_abs=float(d.abs().max()), mean_abs=float(d.abs().mean()),
                RMSE=float(d.square().mean().sqrt()),
                relative_L2=float(d.norm() / b.norm().clamp_min(1e-12)),
                allclose=bool(torch.allclose(a, b, atol=1e-6, rtol=1e-5)))


def compare(layers, native_layers, dense, native_dense, recipient, scale):
    order, _ = lexicographic_order(recipient['Q'])
    rows = []
    for i, layer in enumerate(layers):
        for key in TRACE_KEYS:
            baseline = native_layers['layer_%d__%s' % (i, key)]
            rows.append(dict(layer=i, stage=key, group='all', **response(layer[key], baseline)))
            if key == 'prefix_suffix':
                a, b = gather_tokens(layer[key], order), gather_tokens(baseline, order)
                for name, lo, hi in [('early', 0, 86), ('middle', 86, 171), ('late', 171, 256)]:
                    rows.append(dict(layer=i, stage=key, group=name, **response(a[:, lo:hi], b[:, lo:hi])))
    require(torch.allclose(layers[0]['after_self'], native_layers['layer_0__after_self'], atol=1e-6, rtol=1e-5),
            'first self branch differs from saved Native')
    return rows, dict(normalized=response(dense, native_dense),
                      world_mm=response(dense * scale, native_dense * scale),
                      interpretation='slot-wise diagnostic response, NOT registered accuracy or Native performance')
