"""Admission control-flow CPU contracts: artificial model, no real Mamba/AdaPoinTr."""
import ast,hashlib,importlib.util,json,random,sys
from pathlib import Path
import numpy as np
import torch
from torch import nn
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('p1_admission',HERE/'bcsp_p1_gpu_admission_v1.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
OUT=HERE/'CPU_contracts_v1'


def tensor_sha(t):
    return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def state_sha(model):
    h=hashlib.sha256()
    for n,t in model.state_dict().items():h.update(n.encode());h.update(tensor_sha(t).encode())
    return h.hexdigest()


class Helper:
    tensor_sha=staticmethod(tensor_sha)
    state_sha=staticmethod(state_sha)


class ArtificialAdmissionModel(nn.Module):
    def __init__(self,drift=False,rng_drift=False,fail=False):
        super().__init__();self.calls=0;self.recording=False;self.drift=drift;self.rng_drift=rng_drift;self.fail=fail
        self.base_model=nn.Module();self.base_model.coarse_pred=nn.Linear(3,768)
        self.base_model.encoder=nn.Module();self.base_model.encoder.blocks=nn.Module()
        blocks=[]
        for i in range(6):
            b=nn.Module();b.attn=nn.Module();b.attn.mixer=nn.Linear(3,3);blocks.append(b)
        self.base_model.encoder.blocks.blocks=nn.ModuleList(blocks)
        self.offset=nn.Parameter(torch.randn(1,256,32,3)*.01);self.bn=nn.BatchNorm1d(3)
    def enable_full_instrumentation(self,v):self.recording=v
    def pop_full_instrumentation(self):return dict(backbone={})
    def forward(self,x):
        self.calls+=1
        if self.fail:raise RuntimeError('synthetic forward failure')
        if self.rng_drift:torch.rand(1)
        h=self.bn(x.mean(1))
        for b in self.base_model.encoder.blocks.blocks:h=torch.tanh(b.attn.mixer(h))
        coarse=self.base_model.coarse_pred(h).reshape(len(x),256,3)
        dense=(coarse[:,:,None,:]+self.offset).reshape(len(x),8192,3)
        if self.drift and self.calls==2:dense=dense+.001
        return (coarse,coarse[:,:0],dense[:,:0],dense) if self.training else (coarse,dense)
    def get_loss(self,ret,target,epoch,partial):return ret[-1].new_zeros(()),(ret[-1]-target).square().mean()+ret[0].square().mean()


def main():
    OUT.mkdir(exist_ok=False);checks=[]
    def check(n,v):assert v,n;checks.append(n)
    def rejects(n,fn):
        try:fn()
        except RuntimeError:checks.append(n)
        else:raise AssertionError(n)
    torch.set_num_threads(2);torch.manual_seed(1);random.seed(1);np.random.seed(1)
    x=torch.randn(8,8192,3);target=torch.randn_like(x);events=[];samples=[];counts=entry.counters()
    try:
        for variant in ('T0','M0'):
            model=ArtificialAdmissionModel().eval();before=state_sha(model);bn=model.bn.momentum;rng=torch.get_rng_state().clone()
            result=entry.admit_model(torch,np,model,x,target,variant,counts,Helper,events.append,lambda p,c:samples.append(p),cuda=False)
            check(variant+' exact six model calls and phase returns',model.calls==6 and result['phases']==6)
            check(variant+' state/mode/RNG/BN momentum restored',state_sha(model)==before and not model.training and model.bn.momentum==bn and torch.equal(torch.get_rng_state(),rng))
            check(variant+' all gradients cleared',all(p.grad is None for p in model.parameters()))
            phase=result['events']
            check(variant+' eval OFF/ON/roundtrip exact',all(r['dense_comparison']['exact_equal'] for r in phase[:4]))
            check(variant+' train outputs loss gradients repeated exactly',phase[-1]['gradient_exact_equal'] and phase[-1]['loss_exact_equal'] and phase[-1]['dense_comparison']['exact_equal'])
        check('exact two-arm 12 forward / 4 backward / zero steps',counts==dict(forward_attempts=12,forward_returns=12,loss_calls=4,backward_attempts=4,backward_returns=4,optimizer_steps=0))
        check('budget counter persisted before every actual operation',sum(e.get('kind')=='FORWARD_ATTEMPT' for e in events)==12 and sum(e.get('kind')=='BACKWARD_ATTEMPT' for e in events)==4)
        for label,kwargs,expected_calls in [('forward_exception',dict(fail=True),1),('output_drift',dict(drift=True),2),('RNG_drift',dict(rng_drift=True),1)]:
            model=ArtificialAdmissionModel(**kwargs).eval();before=state_sha(model);c=entry.counters();e=[];rng=torch.get_rng_state().clone()
            rejects(label+' stops without further forward',lambda:entry.admit_model(torch,np,model,x,target,'T0',c,Helper,e.append,lambda *a:None,cuda=False))
            check(label+' counts and restoration preserved',model.calls==expected_calls and c['forward_attempts']==expected_calls and c['optimizer_steps']==0 and state_sha(model)==before and torch.equal(torch.get_rng_state(),rng) and not model.recording)
        model=ArtificialAdmissionModel().eval();c=entry.counters();c['forward_attempts']=12
        rejects('hard forward cap before call',lambda:entry.admit_model(torch,np,model,x,target,'T0',c,Helper,lambda *a:None,lambda *a:None,cuda=False))
        check('cap violation executes zero model calls',model.calls==0)
        model=ArtificialAdmissionModel();model.base_model.coarse_pred.weight.register_hook(lambda g:torch.full_like(g,float('nan')))
        c=entry.counters();rejects('nonfinite gradient stops',lambda:entry.admit_model(torch,np,model,x,target,'M0',c,Helper,lambda *a:None,lambda *a:None,cuda=False))
        check('nonfinite gradient no optimizer and no second train attempt',c['forward_attempts']==5 and c['backward_attempts']==1 and all(p.grad is None for p in model.parameters()))
        F=OUT/'fixtures';F.mkdir()
        def rec(name,v):
            p=F/name;p.write_text(json.dumps(v),encoding='utf-8');return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=entry.sha(p))
        qr=rec('q.json',dict(schema='bcsp-p1-gpu-admission-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',science=dict(forward_attempt_limit=12,backward_attempt_limit=4,optimizer_steps=0)))
        ar=rec('a.json',dict(schema='bcsp-p1-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY'))
        rr=rec('r.json',dict(schema='bcsp-p1-runtime-v1',request_sha256=qr['sha256'],authorization_sha256=ar['sha256']))
        check('complete authorize one-way hash contract',entry.authorize(qr,ar,rr)['science']['optimizer_steps']==0)
        bad=rec('bad_auth.json',dict(schema='bcsp-p1-authorization-v1',request_sha256='0'*64,explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_ONLY'))
        rejects('authorization mismatch rejected',lambda:entry.authorize(qr,bad,rr))
        badr=rec('bad_runtime.json',dict(schema='bcsp-p1-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64))
        rejects('runtime mismatch rejected',lambda:entry.authorize(qr,ar,badr))
        tree=ast.parse((HERE/'bcsp_p1_gpu_admission_v1.py').read_text(encoding='utf-8'))
        check('static no optimizer construction/step or torch.load call',not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ('step','AdamW','Adam','load') and isinstance(n.func.value,ast.Name) and n.func.value.id in ('optimizer','torch') for n in ast.walk(tree)))
        result=dict(status='ARTIFICIAL_CPU_ADMISSION_CONTRACTS_PASS',count=len(checks),checks=checks,torch_version=torch.__version__,native_Mamba_calls=0,actual_AdaPoinTr_calls=0,GPU_calls=0,optimizer_steps=0,real_payload_reads=0,warning='Tests execute synthetic model control flow; no native SSM/CUDA equivalence claim')
        with (OUT/'result_v1.json').open('x') as f:json.dump(result,f,indent=2)
        print(json.dumps(result))
    except BaseException as exc:
        with (OUT/'failure_v1.json').open('x') as f:json.dump(dict(status='FAILED_STOP',checks=checks,error=repr(exc)),f,indent=2)
        raise


if __name__=='__main__':main()
