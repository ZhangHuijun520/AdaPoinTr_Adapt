"""SCQ-v2 fixed local-feature/relative-geometry coarse residual. No GT argument."""
import hashlib
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as functional

SHAPES={'W1.weight':(384,1802),'W1.bias':(384,),'W2.weight':(3,384),'W2.bias':(3,),'Pfix':(7,384)}

def require(ok,message):
    if not ok:raise ValueError(message)

def load_initialization(record):
    p=Path(record['path']);raw=p.read_bytes()
    require(len(raw)==record['bytes']==sum(__import__('math').prod(s) for s in SHAPES.values())*4,'initialization bytes')
    require(hashlib.sha256(raw).hexdigest()==record['sha256'],'initialization SHA256')
    data=torch.frombuffer(bytearray(raw),dtype=torch.float32);result={};offset=0
    for name,shape in SHAPES.items():
        size=__import__('math').prod(shape);result[name]=data[offset:offset+size].reshape(shape).clone();offset+=size
    require(all(bool(torch.isfinite(t).all()) for t in result.values()),'initialization finite')
    require(torch.equal(result['W2.weight'],torch.zeros_like(result['W2.weight'])) and torch.equal(result['W2.bias'],torch.zeros_like(result['W2.bias'])),'zero output initialization')
    require(torch.allclose(result['Pfix']@result['Pfix'].T,torch.eye(7),atol=1e-6,rtol=1e-6),'orthogonal projection rows')
    return result

class SCQResidual(nn.Module):
    def __init__(self,variant,knn,initialization):
        super().__init__();require(variant in ('F','S'),'SCQ F/S only')
        self.variant=variant;self.knn=knn
        # Existing parent CPU RNG is unchanged, including temporary Linear construction.
        with torch.random.fork_rng(devices=[]):
            self.W1=nn.Linear(1802,384);self.W2=nn.Linear(384,3)
        values=load_initialization(initialization)
        self.register_buffer('Pfix',values.pop('Pfix'))
        self.load_state_dict({**values,'Pfix':self.Pfix},strict=True)

    def describe(self,S,F,z,Q0):
        b=Q0.shape[0]
        require(Q0.shape==(b,256,3) and S.shape==(b,256,3) and F.shape==(b,256,384) and z.shape==(b,1024) and b>0,'fixed SCQ tensor shapes')
        require(all(t.dtype==torch.float32 and t.device==Q0.device and bool(torch.isfinite(t).all()) for t in (S,F,z,Q0)),'finite FP32 shared device')
        with torch.no_grad():idx=self.knn(8,S,Q0)
        require(idx.shape==(b,256,8) and idx.dtype==torch.int64 and idx.device==S.device and bool((idx>=0).all()) and bool((idx<256).all()),'SCQ indices')
        batch=torch.arange(b,device=S.device)[:,None,None]
        nf=functional.layer_norm(F,(384,),eps=1e-5)[batch,idx]
        fa=nf.mean(2);fm=nf.max(2).values
        d=S[batch,idx]-Q0[:,:,None,:];mean=d.mean(2)
        sigma=((d-mean[:,:,None,:]).square().mean(2)+1e-6).sqrt()
        rho=torch.linalg.vector_norm(d,dim=-1).mean(2,keepdim=True)
        g=torch.cat((mean,sigma,rho),-1)
        channel=g if self.variant=='S' else functional.layer_norm(fa,(384,),eps=1e-5)@self.Pfix.T
        head_input=torch.cat((z[:,None,:].expand(-1,256,-1),fa,fm,Q0,channel),-1)
        return head_input,dict(indices=idx,fa=fa,fm=fm,geometry=g,channel=channel)

    def forward(self,S,F,z,Q0):
        head_input,info=self.describe(S,F,z,Q0)
        delta=self.W2(functional.gelu(self.W1(head_input),approximate='none'));Qused=Q0+delta
        require(bool(torch.isfinite(Qused).all()),'nonfinite SCQ output')
        # Diagnostics cannot hold an autograd graph or influence the computation.
        record={k:v.detach() for k,v in dict(Q0=Q0,Qused=Qused,delta=delta,**info).items()}
        return Qused,record
