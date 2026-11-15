"""Build the fully initialized parent first, then replace exactly six global branches."""
import ctypes
import hashlib
import torch
from bcsp_mamba_encoder_v1 import BidirectionalSpatialMamba, MambaEncoderBlock

PREFIX = 'base_model.encoder.blocks.blocks.'
MAMBA_CONFIG = dict(d_model=384, d_state=16, d_conv=4, expand=2, use_fast_path=True)


def tensor_sha(value):
    t = value.detach().cpu().contiguous()
    return hashlib.sha256(ctypes.string_at(t.data_ptr(), t.numel() * t.element_size())).hexdigest()


def common_state(model):
    def replaced(name):
        return any(name.startswith(PREFIX + str(i) + '.attn.') for i in range(6))
    return {n: dict(shape=list(v.shape), dtype=str(v.dtype), sha256=tensor_sha(v))
            for n, v in model.state_dict().items() if not replaced(n)}


def native_mixer():
    from mamba_ssm.modules.mamba_simple import Mamba
    if Mamba.__module__ != 'mamba_ssm.modules.mamba_simple':
        raise RuntimeError('unexpected Mamba implementation')
    mixer = Mamba(**MAMBA_CONFIG)
    if not getattr(mixer.dt_proj.bias, '_no_reinit', False):
        raise RuntimeError('Mamba dt initialization marker missing')
    if not all(getattr(p, '_no_weight_decay', False) for p in (mixer.A_log, mixer.D)):
        raise RuntimeError('Mamba no-weight-decay markers missing')
    return mixer


def _build(legacy_builder, variant, seed, mixer_builder, *, artificial_fixture):
    if variant not in ('T0', 'M0') or seed != 0:
        raise ValueError('first pair only: T0/M0, seed0')
    # No CUDA RNG initialization/device query. Build shared CPU modules in a private stream.
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(seed)
        model = legacy_builder()
    if any(p.device.type != 'cpu' or p.dtype != torch.float32 for p in model.parameters()):
        raise ValueError('fully initialized FP32 CPU parent required')
    blocks = model.base_model.encoder.blocks.blocks
    if len(blocks) != 6:
        raise ValueError('exact six encoder blocks required')
    for i, block in enumerate(blocks):
        if block.attn is None or block.combine_style != 'concat':
            raise ValueError('frozen global/concat structure')
        if block.block_length != (2 if i == 0 else 1):
            raise ValueError('frozen graph placement')
        if (block.local_attn is not None) != (i == 0):
            raise ValueError('frozen graph placement')
        if tuple(block.norm1.normalized_shape) != (384,):
            raise ValueError('frozen feature width')
    before = common_state(model)
    initialized = []
    if variant == 'M0':
        # Parent apply(_init_weights) has FINISHED. Never apply it to the SSM.
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(20261104)
            for i in range(6):
                mixer = mixer_builder()
                fingerprints = {n: tensor_sha(p) for n, p in mixer.named_parameters()}
                block = MambaEncoderBlock(blocks[i], BidirectionalSpatialMamba(mixer))
                if fingerprints != {n: tensor_sha(p) for n, p in block.attn.mixer.named_parameters()}:
                    raise RuntimeError('mixer initialization changed during installation')
                blocks[i] = block
                initialized.append(dict(block=i, mixer_class=type(mixer).__module__ + '.' + type(mixer).__name__, parameter_fingerprints=fingerprints))
    if before != common_state(model):
        raise RuntimeError('shared parent state changed')
    evidence = dict(variant=variant, seed=seed, common_state=before,
                    common_state_unchanged=True, replaced_global_branches=6 if variant == 'M0' else 0,
                    native_attention_retained=variant == 'T0', old_adapter_added=False,
                    mamba_config=MAMBA_CONFIG if variant == 'M0' else None,
                    shared_bidirectional_scans_per_forward=12 if variant == 'M0' else 0,
                    initialized_mixers=initialized, artificial_fixture=artificial_fixture,
                    total_parameters=sum(p.numel() for p in model.parameters()))
    return model, evidence


def build_model(legacy_builder, variant, seed=0):
    """Caller supplies the frozen B0 constructor/config; no dependency fallback allowed."""
    return _build(legacy_builder, variant, seed, native_mixer, artificial_fixture=False)
