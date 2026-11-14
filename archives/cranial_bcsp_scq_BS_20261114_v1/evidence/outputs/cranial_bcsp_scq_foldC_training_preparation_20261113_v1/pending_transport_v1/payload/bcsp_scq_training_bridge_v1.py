"""Thin SCQ caller bridge. Delegates the unchanged3900-step runtime."""
import hashlib
from pathlib import Path

def train_lifecycle(parent_runtime,parent_sha256,model,*args,admission,device,**kwargs):
    if admission['status']!='SCQ_NATIVE_CUDA_ADMISSION_PASS' or model.f0_evidence['artificial_fixture']:
        raise ValueError('Native SCQ admission and real model required')
    if str(device) not in ('cuda','cuda:0'):raise ValueError('Production CUDA only')
    if hashlib.sha256(Path(parent_runtime.__file__).read_bytes()).hexdigest()!=parent_sha256:raise ValueError('Frozen original runtime required')
    return parent_runtime.train_lifecycle(model,*args,device=device,**kwargs)
