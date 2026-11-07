"""H2 v1: one zero-initialized residual range head; no GT in forward."""
import math
import torch
from torch import nn
from torch.nn import functional as F

CONTRACT=dict(version='H2-range-soft-coupling-v1',feature_dim=1024,coarse_points=256,
              head_parameters=1025,beta=.1,aux_weight=.1,maximum_scale=1.25,
              minimum_radius=1e-6,epsilon_added_to_radius=False,
              detach_Q_in_aux_target=True,detach_delta_in_coupling=True)
def require(ok,text):
    if not ok:raise ValueError(text)
def moments(points):
    require(points.ndim==3 and points.shape[-1]==3 and points.shape[1]>0 and bool(torch.isfinite(points).all()),'finite BxNx3 points')
    center=points.mean(1,keepdim=True)
    radius=((points-center).square().sum(-1).mean(1)).sqrt()
    require(bool(torch.isfinite(radius).all()) and bool((radius>1e-6).all()),'nonfinite/degenerate radius')
    return center,radius
def soft_couple(raw,delta):
    center,radius=moments(raw)
    require(delta.shape==(raw.shape[0],1) and bool(torch.isfinite(delta).all()),'finite Bx1 delta')
    a=math.log(1.25);scale=(a*torch.tanh(delta.detach()/a)).exp()
    used=raw+(scale[:,None,:]-1)*(raw-center)
    require(bool(torch.isfinite(used).all()),'finite coupled coarse')
    return used,scale,radius
def auxiliary(delta,raw,target):
    require(target.shape==(raw.shape[0],8192,3) and not target.requires_grad,'fixed detached GT8192')
    _,rq=moments(raw);_,rg=moments(target)
    t=rg.log()-rq.log().detach()
    require(delta.shape==(raw.shape[0],1) and bool(torch.isfinite(delta).all()),'finite delta')
    loss=F.smooth_l1_loss(delta[:,0],t,beta=.1,reduction='mean')
    require(bool(torch.isfinite(loss)),'finite auxiliary loss')
    return loss,t
class RangeHead(nn.Module):
    def __init__(self):
        super().__init__()
        # Do not instantiate nn.Linear and then zero it: that would consume RNG.
        self.weight=nn.Parameter(torch.zeros(1,1024,dtype=torch.float32))
        self.bias=nn.Parameter(torch.zeros(1,dtype=torch.float32))
    def forward(self,z):
        require(z.ndim==2 and z.shape[1]==1024 and bool(torch.isfinite(z).all()),'B1024 feature')
        delta=F.linear(z,self.weight,self.bias)
        require(bool(torch.isfinite(delta).all()),'finite range head output in every mode')
        return delta
