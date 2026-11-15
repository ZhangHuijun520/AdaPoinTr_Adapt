"""Minimal caller bridge; no CLI, data access or automatic execution."""
import hashlib
from pathlib import Path
import torch
from bcsp_lqi_decoder_v1 import require
from bcsp_lqi_factory_v1 import no_attention_inventory

COUNTS = dict(batch=8, updates=3900, traversals=100, exposures=31200, drops=300)


def forward_loss(model, partial, target, epoch):
    require(getattr(model, 'f0_evidence', {}).get('version') == 'F0-LQI-implementation-v1', 'F0 model required')
    require(partial.shape == target.shape and partial.ndim == 3 and partial.shape[1:] == (8192,3), '8k fixed points')
    require(partial.dtype == target.dtype == torch.float32 and bool(torch.isfinite(partial).all()) and bool(torch.isfinite(target).all()), 'finite FP32 inputs')
    require(0 <= epoch < 100, 'epoch')
    ret = model(partial)  # target is never passed to the prediction path
    sparse, reconstruction = model.get_loss(ret, target, epoch, partial=partial)
    loss = sparse + reconstruction
    require(loss.numel() == 1 and bool(torch.isfinite(loss)), 'finite scalar loss')
    return ret, loss


def lightweight_geometry(q, p):
    require(q.shape[1:] == (256,3) and p.shape[1:] == (8192,3), 'geometry shape')
    with torch.no_grad():
        result = {}
        for name,t in [('coarse',q),('dense',p)]:
            center=t.mean(1)
            result[name]=dict(centroid=center.detach(), radius=((t-center[:,None])**2).sum(-1).mean(1).sqrt().detach())
        return result


def train_lifecycle(parent_runtime, parent_sha256, model, *args, admission, **kwargs):
    # Delegates the unchanged real 3900-step lifecycle; never execute with fixtures.
    require(not model.f0_evidence['artificial_fixture'], 'artificial fixture cannot enter real training')
    require(admission.get('status') == 'LQI_NATIVE_CUDA_ADMISSION_PASS', 'separate CUDA admission required')
    require(hashlib.sha256(Path(parent_runtime.__file__).read_bytes()).hexdigest() == parent_sha256, 'parent runtime hash')
    require(kwargs.get('device') == 'cuda' or str(kwargs.get('device')) == 'cuda:0', 'production CUDA only')
    no_attention_inventory(model)
    return parent_runtime.train_lifecycle(model, *args, **kwargs)
