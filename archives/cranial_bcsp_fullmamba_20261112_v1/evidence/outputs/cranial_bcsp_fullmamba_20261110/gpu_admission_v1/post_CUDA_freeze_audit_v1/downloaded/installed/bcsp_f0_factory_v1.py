"""Isolated installation after complete frozen M0 initialization."""
import torch
from torch import nn
import bcsp_p1_model_factory_v1 as parent
from bcsp_f0_decoder_v1 import F0Decoder, require

DECODER_SEED = 20261110


def shared_fingerprint(model):
    def removed(n):
        return n.startswith('base_model.decoder.blocks.blocks.') and any('.' + key + '.' in n for key in ['self_attn', 'cross_attn'])
    return {n: parent.tensor_sha(t) for n, t in model.state_dict().items() if not removed(n)}


def no_attention_inventory(model):
    forbidden = []
    for name, m in model.named_modules():
        typ = type(m).__name__
        if isinstance(m, nn.MultiheadAttention) or ('attention' in typ.lower() and typ != 'DynamicGraphAttention'):
            forbidden.append((name, typ))
    require(not forbidden, 'remaining attention modules: ' + repr(forbidden))
    return dict(forbidden_registered_modules=forbidden, dynamic_kernel_audit_pending=True)


def _install(model, evidence, mixer_builder, artificial_fixture):
    base = model.base_model
    require(isinstance(base.mem_link, nn.Identity), 'fixed memory width')
    require(not getattr(model, 'coarse_geometry_guard_enabled', False), 'H1 disabled')
    require(not getattr(base, 'rim_query_enabled', False), 'rim disabled')
    require(getattr(base, 'scqr_local_geometry', None) is None and getattr(base, 'scqr_query_conditioner', None) is None, 'SCQR disabled')
    require(not hasattr(model, 'h2_head') and not hasattr(base, 'h2_head'), 'no H2 head')
    old = base.decoder
    # Reused module identities are compared explicitly because their paths change.
    old_common = {n: parent.tensor_sha(t) for n, t in old.state_dict().items()
                  if not any('.' + k + '.' in n for k in ['self_attn', 'cross_attn'])}
    outer_before = {n: parent.tensor_sha(t) for n, t in model.state_dict().items() if not n.startswith('base_model.decoder.')}
    rng = torch.random.get_rng_state().clone()
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(DECODER_SEED)
        decoder = F0Decoder(old, mixer_builder)
    require(torch.equal(rng, torch.random.get_rng_state()), 'new decoder consumed common RNG')
    # old blocks.blocks.i -> new blocks.i, everything except attention retained exactly.
    new_state = decoder.state_dict()
    for name, fingerprint in old_common.items():
        target = name.replace('blocks.blocks.', 'blocks.', 1)
        require(target in new_state and parent.tensor_sha(new_state[target]) == fingerprint, 'common decoder state changed: '+name)
    base.decoder = decoder
    require(outer_before == {n: parent.tensor_sha(t) for n,t in model.state_dict().items() if not n.startswith('base_model.decoder.')}, 'outside decoder changed')
    inventory = no_attention_inventory(model)
    model.f0_evidence = dict(version='F0-P-v2-implementation-v1', artificial_fixture=artificial_fixture,
        parent=evidence, shared_decoder_tensors=len(old_common), decoder_seed=DECODER_SEED,
        new_mamba_mixers=16, shared_coordinate_pe_parameters=1152, expected_decoder_native_calls=24,
        expected_total_native_calls=36, inventory=inventory, common_initialization_preserved=True)
    return model, model.f0_evidence


def build_model(legacy_builder, seed=0):
    model, evidence = parent.build_model(legacy_builder, 'M0', seed)
    return _install(model, evidence, parent.native_mixer, False)


def build_artificial_fixture(legacy_builder, mixer_builder):
    model, evidence = parent._build(legacy_builder, 'M0', 0, mixer_builder, artificial_fixture=True)
    return _install(model, evidence, mixer_builder, True)
