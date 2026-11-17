"""SPCG same-forward observations, partial-only access and bounded call accounting."""
import hashlib
from pathlib import Path
import torch
from bcsp_spcg_head_v1 import need

SCIENCE=dict(full_forward=11,full_loss=3,full_backward=3,optimizer_steps=0,synthetic_forward=6,real_D_forward=5)
LOG_STEPS=(1,39,390,1950,3900)

def read_partial(np, record):
    p=Path(record['path'])
    need(not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file(),'partial path')
    need(p.stat().st_size==record['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'],'partial file binding')
    # Hashing the fixed container file is not accessing individual GT arrays.
    with np.load(p,allow_pickle=False) as archive:
        x=archive['partial'].copy()
    need(x.shape==(8192,3) and x.dtype==np.float32 and bool(np.isfinite(x).all()),'D-only partial')
    return x

def geometry(Q):
    with torch.no_grad():
        d=torch.pdist(Q[0])
        q=Q.detach();c=q.mean(1)
        return dict(centroid=c.cpu().tolist(),rms_radius=(q-c[:,None]).square().sum(-1).mean(1).sqrt().cpu().tolist(),first_batch_pair_min=float(d.min()),first_batch_pair_median=float(d.median()),first_batch_exact_duplicates=256-len(torch.unique(q[0],dim=0)))

def gradients(model):
    rows={n:float(p.grad.detach().double().norm()) for n,p in model.named_parameters() if p.grad is not None and bool(torch.isfinite(p.grad).all())}
    need(all(p.grad is None or bool(torch.isfinite(p.grad).all()) for p in model.parameters()),'nonfinite parameter gradient')
    return rows

def Q_gradient_record(Q):
    need(Q.grad is not None and bool(torch.isfinite(Q.grad).all()),'total-loss Q gradient')
    g=Q.grad.detach()
    return dict(origin='TOTAL_LOSS_NOT_ISOLATED_COARSE',L2=float(g.double().norm()),max_abs=float(g.abs().max()))

def optimizer_groups(model):
    decay=[];no=[]
    for n,p in model.named_parameters():
        if p.requires_grad:(no if p.ndim==1 or n.endswith('.bias') or getattr(p,'_no_weight_decay',False) else decay).append(p)
    return [dict(params=decay,weight_decay=.0005),dict(params=no,weight_decay=0.)]

def output_estimate(model, log_bytes=96*1024**2, extra_bytes=64*1024**2):
    # FP32 parameters + two Adam moments + buffers, conservative serialization allowance.
    param=sum(p.numel()*p.element_size() for p in model.parameters())
    buffers=sum(b.numel()*b.element_size() for b in model.buffers())
    result=3*param+buffers+log_bytes+extra_bytes
    need(result<=1024**3,'1GiB run output estimate exceeded')
    return dict(model_parameter_bytes=param,buffer_bytes=buffers,model_and_Adam_estimate_bytes=3*param+buffers,log_and_control_allowance_bytes=log_bytes,serialization_and_tmp_allowance_bytes=extra_bytes,total_bytes=result,cap_bytes=1024**3,actual_runtime_enforcement_required=True)

class CallBudget:
    def __init__(self):self.counts={k:0 for k in SCIENCE}
    def claim(self,key,event=lambda x:None):
        need(key!='optimizer_steps' and key in self.counts and self.counts[key]<SCIENCE[key],'call budget '+key)
        self.counts[key]+=1
        event(dict(operation=key,counts=dict(self.counts)))
    def finish(self):need(self.counts==SCIENCE,'exact calls');return dict(self.counts)
