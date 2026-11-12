"""BCSP-only candidate interfaces. No imports of models and no auto-execution."""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
import hashlib
import numpy as np

_ACTIVE = ContextVar('bcsp_knn_active', default=False)

@contextmanager
def bcsp_knn_scope():
    token = _ACTIVE.set(True)
    try:
        yield
    finally:
        _ACTIVE.reset(token)

def knn_dispatch(legacy, k, xyz, query):
    if not _ACTIVE.get():
        return legacy(k, xyz, query)
    return torch_knn(k, xyz, query)

def _shape_check(k, xyz, query, chunk):
    if type(k) is not int or type(chunk) is not int or chunk < 1:
        raise ValueError('integer k/chunk required')
    if len(xyz.shape) != 3 or len(query.shape) != 3:
        raise ValueError('B,N,3 required')
    if xyz.shape[0] != query.shape[0] or xyz.shape[0] < 1 or xyz.shape[2] != 3 or query.shape[2] != 3:
        raise ValueError('shape mismatch')
    if not 1 <= k <= xyz.shape[1]:
        raise ValueError('invalid k')

def numpy_knn(k, xyz, query, chunk=256):
    """CPU reference. Ties use first index; production torch ties remain topk."""
    _shape_check(k, xyz, query, chunk)
    if xyz.dtype != query.dtype or xyz.dtype not in (np.float32,np.float64):
        raise ValueError('matching floating dtype required')
    if not np.isfinite(xyz).all() or not np.isfinite(query).all():
        raise ValueError('nonfinite coordinates')
    result=[]
    for start in range(0,query.shape[1],chunk):
        q=query[:,start:start+chunk]
        d=-2*np.matmul(q,xyz.transpose(0,2,1))
        d+=np.sum(q*q,axis=-1)[...,None]
        d+=np.sum(xyz*xyz,axis=-1)[:,None,:]
        result.append(np.argsort(d,axis=-1,kind='stable')[...,:k])
    return np.concatenate(result,axis=1) if result else np.empty((xyz.shape[0],0,k),np.int64)

def torch_knn(k, xyz, query, chunk=256):
    """Full-key, query-chunked parent distance formula; no approximate search."""
    import torch
    _shape_check(k, xyz, query, chunk)
    if xyz.dtype != query.dtype or xyz.dtype not in (torch.float32,torch.float64) or xyz.device != query.device:
        raise ValueError('matching device/floating dtype required')
    if not torch.isfinite(xyz).all().item() or not torch.isfinite(query).all().item():
        raise ValueError('nonfinite coordinates')
    if query.shape[1] == 0:
        return torch.empty((xyz.shape[0],0,k),dtype=torch.long,device=xyz.device)
    result=[]
    with torch.no_grad():
        for start in range(0,query.shape[1],chunk):
            q=query[:,start:start+chunk]
            d=-2*torch.matmul(q,xyz.permute(0,2,1))
            d+=torch.sum(q**2,dim=-1).view(q.shape[0],q.shape[1],1)
            d+=torch.sum(xyz**2,dim=-1).view(xyz.shape[0],1,xyz.shape[1])
            result.append(torch.topk(d,k,dim=-1,largest=False,sorted=False)[1])
    return torch.cat(result,dim=1)

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def load_case(root, record, allowed_sources, n_input, training=False):
    """Versioned normalized partial/implant schema; xyz pilot NPZ is rejected."""
    if n_input not in (8192,16384):raise ValueError('unsupported input count')
    if record.get('source_id') not in allowed_sources:raise ValueError('source not allowed')
    rel=Path(record['point_path'])
    if rel.is_absolute() or '..' in rel.parts:raise ValueError('relative path required')
    root=Path(root).resolve();path=root/rel
    current=root
    for part in rel.parts:
        current=current/part
        if current.is_symlink():raise ValueError('symbolic link forbidden')
    if not path.resolve().is_relative_to(root):raise ValueError('outside root')
    if record.get('schema')!='BCSP-normalized-v1' or record.get('normalization_source')!='defective_bbox':
        raise ValueError('wrong geometry schema/frame')
    expected=record.get('sha256')
    if not expected or sha256(path)!=expected:raise ValueError('file hash mismatch')
    with np.load(path,allow_pickle=False) as z:
        # Do not enumerate/read GT arrays to construct inference input.
        partial=z['partial'].copy()
        if partial.dtype!=np.float32 or partial.shape!=(n_input,3) or not np.isfinite(partial).all():raise ValueError('invalid partial')
        target=None
        if training:
            target=z['implant'].copy()
            if target.dtype!=np.float32 or target.shape!=(8192,3) or not np.isfinite(target).all():raise ValueError('invalid target')
    if sha256(path)!=expected:raise ValueError('source changed during read')
    return partial,target

@dataclass(frozen=True)
class Contract:
    cases:int=315
    batch:int=8
    epochs:int=100
    step_per_update:int=1
    drop_last:bool=True
    stage:str='BCSP_INPUT_DENSITY_V1'
    def __post_init__(self):
        if (self.cases,self.batch,self.epochs,self.step_per_update,self.drop_last,self.stage)!=(315,8,100,1,True,'BCSP_INPUT_DENSITY_V1'):
            raise ValueError('frozen BCSP contract mismatch')
    @property
    def batches(self):return self.cases//self.batch
    @property
    def updates(self):return self.epochs*self.batches

class UpdateGuard:
    """Counts commits, latches failures; never invokes training by itself."""
    def __init__(self, contract=Contract()):
        self.c=contract;self.steps=0;self.epoch=-1;self.batch=0;self.open=False;self.pending=False;self.failed=False
    def _require(self, ok):
        if self.failed or not ok:
            self.failed=True
            raise RuntimeError('BCSP counter contract failed; no retry/resume')
    def begin_epoch(self, epoch, loader_batches):
        self._require(not self.open and not self.pending and type(epoch) is int and epoch==self.epoch+1 and epoch<self.c.epochs and loader_batches==self.c.batches)
        self.epoch=epoch;self.batch=0;self.open=True
    def before_step(self, batch_size):
        self._require(self.open and not self.pending and self.batch<self.c.batches and self.steps<self.c.updates and batch_size==self.c.batch)
        self.pending=True
    def after_step(self):
        self._require(self.pending);self.pending=False;self.batch+=1;self.steps+=1
    def end_epoch(self):
        self._require(self.open and not self.pending and self.batch==self.c.batches);self.open=False
    def abort(self):self.failed=True
    def finish(self):
        self._require(not self.open and not self.pending and self.steps==3900 and self.epoch==99)
        return {'stage':self.c.stage,'optimizer_updates':self.steps,'traversals':100,'case_exposures':self.steps*8}

def run_epoch(loader, epoch, optimizer, compute_gradients, guard):
    """Explicit new-path hook. compute_gradients must not call optimizer.step."""
    guard.begin_epoch(epoch,len(loader))
    try:
        for batch in loader:
            partial,target=batch
            guard.before_step(len(partial))
            if len(target)!=len(partial):raise ValueError('batch target mismatch')
            optimizer.zero_grad()
            with bcsp_knn_scope():compute_gradients(partial,target)
            optimizer.step()
            guard.after_step()
        guard.end_epoch()
    except BaseException:
        guard.abort();raise
