"""RIVE caller only: retain the frozen runtime and admit either matched RF arm."""
import hashlib
from pathlib import Path


def train_lifecycle(parent_runtime, parent_sha256, model, *args,
                    admission, device, **kwargs):
    if admission.get('status') != 'RIVE_FROZEN_NATIVE_EVIDENCE_REUSED':
        raise ValueError('RIVE frozen native evidence required')
    if admission.get('fold') not in ('C', 'D') or admission.get('seed') != 0:
        raise ValueError('RIVE mode A seed0 C/D only')
    arm = admission.get('arm')
    if arm not in ('RF-Static', 'RF-Requery'):
        raise ValueError('RIVE RF arm required')
    if model.f0_evidence['artificial_fixture']:
        raise ValueError('Production bridge refuses artificial model')
    if not hasattr(model.base_model, 'rf') or model.base_model.rf.variant != arm:
        raise ValueError('RIVE model arm differs from authorized arm')
    if str(device) not in ('cuda', 'cuda:0'):
        raise ValueError('Production CUDA only')
    raw = Path(parent_runtime.__file__).read_bytes()
    if hashlib.sha256(raw).hexdigest() != parent_sha256:
        raise ValueError('Frozen original runtime required')
    return parent_runtime.train_lifecycle(model, *args, device=device, **kwargs)
