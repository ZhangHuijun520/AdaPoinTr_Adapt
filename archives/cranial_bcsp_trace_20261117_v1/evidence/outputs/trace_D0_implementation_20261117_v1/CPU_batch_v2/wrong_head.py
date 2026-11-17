"""SPCG v2 formula only. D/S/F/z input; no data access, GT, residual or attention."""
import torch
from torch import nn

HEAD_SEED = 2026111600
HEAD_PARAMETERS = 1845763
HEAD_NAMES = ('net.0.weight','net.0.bias','net.2.weight','net.2.bias','net.4.weight','net.4.bias')

def need(ok, message):
    if not ok:
        raise ValueError(message)

def head_bytes(head):
    return b''.join(head.state_dict()[n].detach().cpu().contiguous().numpy().tobytes() for n in HEAD_NAMES)

def from_bytes(blob, shape):
    need(len(blob) == 4 * __import__('math').prod(shape), 'raw FP32 byte length')
    return torch.frombuffer(bytearray(blob), dtype=torch.float32).clone().reshape(shape)

class SPCGHead(nn.Module):
    def __init__(self, arm, U, initialization=None):
        super().__init__()
        need(arm in ('G1','G2'), 'G1/G2 only')
        need(U.shape == (256,3) and U.dtype == torch.float32 and bool(torch.isfinite(U).all()) and bool(((U>=0)&(U<=1)).all()), 'U asset')
        self.arm = arm
        self.register_buffer('U', U.detach().cpu().clone())
        # Initialization bytes, if supplied, are authoritative; no seed regeneration comparison.
        with torch.random.fork_rng(devices=[]):
            torch.random.default_generator.manual_seed(HEAD_SEED)
            self.net = nn.Sequential(nn.Linear(1416,1024),nn.GELU(),nn.Linear(1024,384),nn.GELU(),nn.Linear(384,3))
        if initialization is not None:
            need(len(initialization) == HEAD_PARAMETERS*4, 'H initialization length')
            flat = from_bytes(initialization,(HEAD_PARAMETERS,)); offset = 0
            with torch.no_grad():
                for n,p in self.named_parameters():
                    need(n in HEAD_NAMES,'unexpected head state')
                    p.copy_(flat[offset:offset+p.numel()].reshape_as(p)); offset += p.numel()
            need(offset == HEAD_PARAMETERS,'H count')
        self.capture = False
        self.last = None
        self.last_q = None

    def probes(self, D):
        need(D.ndim == 3 and D.shape[1:] == (8192,3) and D.dtype == torch.float32 and bool(torch.isfinite(D).all()), 'D8192 FP32 finite')
        low, high = D.amin(1), D.amax(1)
        need(bool(((high-low)>=1e-6).all()), 'degenerate D bbox')
        return low[:,None]+(high-low)[:,None]*self.U[None]

    def describe(self, D, S, F, z):
        b = D.shape[0]
        for t,shape in ((S,(b,256,3)),(F,(b,256,384)),(z,(b,1024))):
            need(tuple(t.shape)==shape and t.dtype==torch.float32 and t.device==D.device and bool(torch.isfinite(t).all()), 'Memory/global shape dtype device finite')
        A = self.probes(D)
        normalized = torch.nn.functional.layer_norm(F,(384,),weight=None,bias=None,eps=1e-5)
        delta = S[:,None]-A[:,:,None]
        if self.arm == 'G2':
            index = torch.argsort(delta.detach().square().sum(-1),dim=-1,stable=True)[...,:8]
            batch = torch.arange(b,device=S.device)[:,None,None]
            selected = delta.gather(2,index[...,None].expand(-1,-1,-1,3))
            f = normalized[batch,index].mean(2)
            mu = selected.mean(2)
            rho = torch.linalg.vector_norm(selected,dim=-1).mean(2,keepdim=True)
            tau = ((selected-mu[:,:,None]).square().sum(-1).mean(2,keepdim=True)+1e-6).sqrt()
        else:
            index = None
            f = normalized.mean(1)[:,None].expand(-1,256,-1)
            center = S.mean(1)
            mu = center[:,None]-A
            rho = torch.linalg.vector_norm(delta,dim=-1).mean(2,keepdim=True)
            tau = ((S-center[:,None]).square().sum(-1).mean(1,keepdim=True)+1e-6).sqrt()[:,:,None].expand(-1,256,-1)
        x = torch.cat((z[:,None].expand(-1,256,-1),f,A,mu,rho,tau),-1)
        return x,dict(A=A,mu=mu,rho=rho,tau=tau,index=index)

    def forward(self, D, S, F, z):
        x, detail = self.describe(D,S,F,z)
        Q = self.net(x)
        need(Q.shape == (D.shape[0],256,3) and bool(torch.isfinite(Q).all()),'finite Q256')
        if self.capture:
            self.last = {k:(v.detach().clone() if torch.is_tensor(v) else v) for k,v in dict(S=S,F=F,z=z,**detail).items()}
            self.last_q = Q
            if Q.requires_grad:
                Q.retain_grad()
        return Q

