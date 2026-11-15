"""One bounded artificial CPU check of the new entry, never its main/CUDA path."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import random
import sys
import traceback
from types import SimpleNamespace
import torch
import numpy as np
from torch import nn

O=Path(__file__).resolve().parent
R=O.parents[1]
D=O/'cpu_entry_batch_v1'


def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def main():
    D.mkdir();checks=[];torch.set_num_threads(2)
    def check(name,value=True):
        assert bool(value),name
        checks.append(name)
    def reject(name,fn):
        try:fn()
        except (ValueError,RuntimeError,KeyError,AssertionError):checks.append(name);return
        raise AssertionError('unexpected acceptance '+name)
    try:
        path=O/'bcsp_scq_rf_cuda_admission_v1.py'
        spec=importlib.util.spec_from_file_location('rf_entry_CPU',path)
        e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
        check('exact5F4loss4B0step and five batches',e.SCIENCE['full_forward']==5 and e.SCIENCE['full_loss']==e.SCIENCE['full_backward']==4 and e.SCIENCE['optimizer_steps']==0 and e.SCIENCE['full_batches']==[1,1,1,8,8])
        check('S reference forward only followed by matched RF phases',e.PHASES==[('S_ref_eval1','S-ref',1,False),('Static_eval1','RF-Static',1,False),('Requery_eval1','RF-Requery',1,False),('Static_train8','RF-Static',8,True),('Requery_train8','RF-Requery',8,True)])
        q=dict(schema='bcsp-scq-rf-artificial-cuda-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,science=e.SCIENCE,phases=[list(x) for x in e.PHASES],limits=e.LIMITS,fixture=e.FIXTURE,tolerances=e.TOLERANCE,readiness=dict(fresh_reverification_required=True))
        a=dict(schema='bcsp-scq-rf-cuda-authorization-v1',request_sha256='a'*64,explicit_user_authorization=True,user_authorization_text='ARTIFICIAL_CONTRACT_ONLY')
        r=dict(schema='bcsp-scq-rf-cuda-runtime-v1',request_sha256='a'*64,authorization_sha256='b'*64)
        check('actual authorize accepts one-way exact bindings',e.authorize(q,'a'*64,a,'b'*64,r) is q)
        mutations=[('science',dict(e.SCIENCE,full_forward=6)),('phases',[]),('limits',dict(e.LIMITS,wall_seconds=1801)),('fixture',dict(e.FIXTURE,input_seed=0)),('tolerances',dict(atol=.1,rtol=.1)),('status','AUTHORIZED'),('readiness',dict(fresh_reverification_required=False))]
        for key,value in mutations:
            bad=copy.deepcopy(q);bad[key]=value
            reject('request drift rejected '+key,lambda:e.authorize(bad,'a'*64,a,'b'*64,r))
        reject('reverse runtime hash in authorization rejected',lambda:e.authorize(q,'a'*64,dict(a,runtime_sha256='c'*64),'b'*64,r))
        reject('authorization false rejected',lambda:e.authorize(q,'a'*64,dict(a,explicit_user_authorization=False),'b'*64,r))
        reject('runtime hash drift rejected',lambda:e.authorize(q,'a'*64,a,'c'*64,r))
        c=e.counters();journal=[]
        for _ in range(5):e.claim(c,'full_forward',journal.append)
        for _ in range(4):e.claim(c,'full_loss',journal.append);e.claim(c,'full_backward',journal.append)
        check('attempt counters exact budgets',len(journal)==13 and c['full_forward']==5 and c['full_backward']==c['full_loss']==4)
        for key in ('full_forward','full_loss','full_backward','optimizer_steps','decoder_forward'):
            reject('extra claim rejected '+key,lambda:e.claim(c,key,journal.append))
        launch=dict(project='/home/jovyan/adapointr_work/PoinTr',output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_cuda_20261114_v1',launch_contract=dict(request_path='/tmp/q.json',authorization_path='/tmp/a.json',runtime_path='/tmp/r.json'),limits=e.LIMITS,identity=dict(python_realpath='/opt/conda/envs/adapointr-mamba/bin/python3.10'),entry=dict(path='/tmp/entry.py'),environment=dict(PYTHONDONTWRITEBYTECODE='1'))
        script=e.render_launcher(launch,'a'*64,'b'*64,'c'*64)
        check('POSIX launch parent precedes redirect and exit preserved','\\' not in script.replace('\\n','') and script.index('mkdir -p')<script.index(' >') and 'exit "$rc"' in script and max(len(s.encode()) for s in script.splitlines())<=2048)
        reject('truncated launcher hash rejected',lambda:e.render_launcher(launch,'a'*8,'b'*64,'c'*64))
        # Cheap stage fixture exercises the actual phase engine with a CPU CUDA facade.
        def tsha(t):return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
        def state(m,parameters_only=False):return hashlib.sha256(repr([(n,tsha(t)) for n,t in (m.named_parameters() if parameters_only else m.state_dict().items())]).encode()).hexdigest()
        helper=SimpleNamespace(state_sha=state)
        parent=SimpleNamespace(rng_state=lambda *args:dict(Python=repr(random.getstate()),numpy=repr(np.random.get_state()),CPU=tsha(torch.get_rng_state())))
        class Proxy:
            cuda=SimpleNamespace(get_rng_state=lambda _:torch.get_rng_state().clone(),set_rng_state=lambda s,_:torch.set_rng_state(s),synchronize=lambda:None)
            def __getattr__(self,name):return getattr(torch,name)
        class TinyHead(nn.Module):
            def __init__(self,rf=False):
                super().__init__();self.rf=rf
                if rf:self.V1=nn.Linear(3,3);self.V2=nn.Linear(3,3);nn.init.zeros_(self.V2.weight);nn.init.zeros_(self.V2.bias)
                else:self.W1=nn.Linear(3,3);self.W2=nn.Linear(3,3);nn.init.zeros_(self.W2.weight);nn.init.zeros_(self.W2.bias)
            def forward(self,q):
                first,last=(self.V1,self.V2) if self.rf else (self.W1,self.W2)
                delta=last(torch.nn.functional.gelu(first(q)))
                return q+delta,delta
        class Decoder(nn.Module):
            def __init__(self):super().__init__();self.coordinate_pe=nn.Linear(3,3)
            def forward(self,q_pos):return self.coordinate_pe(q_pos)
        class Fixture(nn.Module):
            def __init__(self,variant,fail=False):
                super().__init__();self.variant=variant;self.fail=fail;self.calls=0;self.loss_calls=0
                self.base_model=nn.Module();b=self.base_model;b.coarse_pred=nn.Linear(3,3);b.scq=TinyHead();b.mlp_query=nn.Identity();b.decoder=Decoder()
                self.bn=nn.BatchNorm1d(3);self.reduce_map=nn.Linear(6,3);self.decode_head=nn.Sequential(nn.Linear(3,96),nn.Unflatten(-1,(32,3)))
                if variant!='S-ref':b.rf=TinyHead(True)
            def forward(self,x):
                self.calls+=1
                if self.fail:raise RuntimeError('ARTIFICIAL_FAILURE')
                b=self.base_model;q0=b.coarse_pred(self.bn(x.transpose(1,2)).mean(-1))[:,None].expand(-1,256,-1)
                q1,d0=b.scq(q0);q2,d1=(q1,torch.zeros_like(q1)) if self.variant=='S-ref' else b.rf(q1)
                b._scq_last_info=dict(Q0=q0.detach(),Qused=q2.detach(),delta=(q2-q0).detach(),Q1=q1.detach(),delta0=d0.detach(),delta1=d1.detach())
                b.mlp_query(torch.cat((q0,q2),-1));features=b.decoder(q_pos=q2)
                rel=self.decode_head(self.reduce_map(torch.cat((features,q2),-1))).reshape(x.shape[0],256,32,3)
                dense=(rel+q2[:,:,None]).reshape(x.shape[0],8192,3)
                return (q2,q2[:,:0],dense[:,:0],dense) if self.training else (q2,dense)
            def get_loss(self,ret,target,**kwargs):
                self.loss_calls+=1
                return ret[0].sum()*0,(ret[0].mean(1)-target.mean(1)).square().mean()+(ret[-1]-target).square().mean()
        old_prefix=e.gradient_prefixes;e.gradient_prefixes=lambda:['base_model.coarse_pred.','reduce_map.']
        g=torch.Generator().manual_seed(118);x=torch.randn(8,8192,3,generator=g);target=torch.randn(8,8192,3,generator=g)
        counts=e.counters();events=[];reference=None;records=[];model_calls=[]
        try:
            for phase in e.PHASES:
                with torch.random.fork_rng(devices=[]):torch.manual_seed(0);m=Fixture(phase[1])
                before=state(m);before_rng=parent.rng_state()
                record,baseline=e.phase_checks(Proxy(),np,m,helper,parent,x,target,phase,reference,counts,events.append,lambda *args:None)
                if baseline is not None:reference=baseline
                check('phase restored all persistent state '+phase[0],state(m)==before and parent.rng_state()==before_rng and all(p.grad is None for p in m.parameters()))
                records.append(record);model_calls.append((m.calls,m.loss_calls))
            check('actual phase engine totals5F4loss4B0step',counts['full_forward']==5 and counts['full_loss']==counts['full_backward']==4 and model_calls==[(1,0),(1,1),(1,1),(1,1),(1,1)])
            check('S reference has no loss gradients',records[0]['loss'] is None and records[0]['gradients'] is None)
            check('both RF evals equal same-session S reference',all(v['close'] for r in records[1:3] for v in r['initial_equivalence']))
            check('four head gradient records precede assertions',len([v for v in events if v.get('kind')=='HEAD_GRADIENTS_BEFORE_ASSERTIONS'])==4)
            with torch.random.fork_rng(devices=[]):torch.manual_seed(0);broken=Fixture('RF-Requery',True)
            initial=state(broken);failed_events=[];failed_counts=e.counters()
            reject('injected forward failure propagates',lambda:e.phase_checks(Proxy(),np,broken,helper,parent,x,target,e.PHASES[-1],reference,failed_counts,failed_events.append,lambda *args:None))
            check('injected failure restores state modes RNG gradients',state(broken)==initial and failed_counts['full_forward']==1 and failed_counts['full_backward']==0 and failed_events[-1]['kind']=='PHASE_RESTORATION' and all(v for k,v in failed_events[-1].items() if k not in ('kind','phase')))
        finally:e.gradient_prefixes=old_prefix
        # Exercise inherited exact read wrapper with the actual new files and raw initializer.
        class Deny:
            def allow(self,*args):return False
            def close(self):pass
        rf=R/'outputs/scq_rf_implementation_20261114_v1'
        bound=[rec(rf/n) for n in ('bcsp_scq_rf_residual_v1.py','bcsp_scq_rf_factory_v1.py','initialization_v1.bin')]
        guard=e.ExactSCQReads(Deny(),bound)
        try:
            check('RF exact source and initializer read wrappers',all(guard.allow(r['path']) for r in bound))
            for row in bound:reject('bound write rejected '+Path(row['path']).name,lambda:guard.allow(row['path'],True))
            check('unbound neighboring path not allowed',not guard.allow(str(rf/'UNBOUND_neighbor.py')))
        finally:guard.close()
        result=dict(status='RF_CUDA_ENTRY_ARTIFICIAL_CPU_PASS',count=len(checks),checks=checks,entry=rec(path),test=rec(Path(__file__)),engine_counts=counts,phases=records,
                    CUDA=False,server_operations=0,real_data=False,checkpoint_loads=0,optimizer_steps=0,
                    limitations=['Cheap CPU model and loss exercise actual phase engine with a CPU CUDA facade; no native Mamba/PointNet2 or real full cdist computation here.',
                                 'Production35 shared-gradient groups unchanged from exact inherited engine; this CPU facade checks two synthetic groups only. Original full8192 loss and full surrogate graph already covered by RF implementation59 checks.',
                                 'Exact RF read wrapper exercised, not a new system-wide audit framework or fresh server readiness proof.'])
        with (D/'result_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
        print(json.dumps(dict(status=result['status'],count=len(checks))))
    except BaseException as exc:
        with (D/'failure_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()),f,indent=2)
        raise


if __name__=='__main__':main()
