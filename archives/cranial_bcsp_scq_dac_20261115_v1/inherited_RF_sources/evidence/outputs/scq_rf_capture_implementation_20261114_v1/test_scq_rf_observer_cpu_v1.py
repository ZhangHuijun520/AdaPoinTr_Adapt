"""One artificial CPU batch. Existing initializer is not a trained checkpoint."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2'
os.environ['MKL_NUM_THREADS']='2'
import copy,hashlib,importlib.util,json,random,sys,traceback,types
from pathlib import Path
import numpy as np
import torch
from torch import nn

S=Path(__file__).resolve().parent;O=S/'artificial_cpu_batch_v1'
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
def emit(path,value):
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2)
def tensor_sha(t):return hashlib.sha256(t.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
def state_sha(m):return hashlib.sha256(''.join(n+tensor_sha(t) for n,t in m.state_dict().items()).encode()).hexdigest()

def main():
    O.mkdir();torch.set_num_threads(2);checks=[]
    def check(label,value=True):
        assert value,label;assert label not in checks;checks.append(label)
    def reject(label,fn):
        try:fn()
        except (RuntimeError,ValueError,AssertionError,KeyError,TypeError):check(label);return
        raise AssertionError('unexpected acceptance '+label)
    try:
        ctx=json.loads((S/'context_v1.json').read_bytes());q=ctx['candidate']
        e=load('scq_rf_cpu_entry',S/'bcsp_scq_rf_memory_capture_v1.py')
        p=load('scq_rf_cpu_parent',Path(ctx['parent_entry_local']))
        residual=load('scq_rf_cpu_actual_residual',Path(ctx['residual_local']))
        initialization=rec(Path(ctx['initializer_local']))
        e.validate(q);check('01 exact fixed ten metadata contract')
        for label,change in [('02 extra forward rejected',lambda z:z['counts'].update(forward=11)),('03 wrong case rejected',lambda z:z['cases'][0].update(case_id='train__000__bilateral')),('04 wrong checkpoint rejected',lambda z:z['runs'][0]['checkpoint'].update(sha256='0'*64)),('05 GT condition rejected',lambda z:z.update(GT_access=True))]:
            bad=copy.deepcopy(q);change(bad);reject(label,lambda:e.validate(bad))
        def triplet(yes=True,bad_runtime=False):
            folder=O/('chain_'+str(len(checks)));folder.mkdir()
            emit(folder/'q.json',q);qr=rec(folder/'q.json')
            emit(folder/'a.json',dict(schema='scq-rf-memory-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_FIXTURE_ONLY_NOT_REAL_AUTHORIZATION'));ar=rec(folder/'a.json')
            emit(folder/'r.json',dict(schema='scq-rf-memory-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if bad_runtime else ar['sha256']))
            return qr,ar,rec(folder/'r.json')
        assert e.authorize(*triplet())==q;check('06 complete actual authorization function')
        reject('07 absent authorization rejected',lambda:e.authorize(*triplet(yes=False)))
        reject('08 broken one-way runtime rejected',lambda:e.authorize(*triplet(bad_runtime=True)))
        class Toy(nn.Module):
            def __init__(self,fail_at=None,twice=False):
                super().__init__();self.base_model=nn.Module();self.knn_calls=0;self.forwards=0;self.fail_at=fail_at;self.twice=twice
                def knn(k,M,Q):
                    self.knn_calls+=1
                    return torch.cdist(Q,M).topk(k,largest=False,sorted=True).indices
                self.base_model.decoder=types.SimpleNamespace(knn=knn)
                self.base_model.scq=residual.SCQResidual('S',knn,initialization)
                with torch.no_grad():self.base_model.scq.W2.weight.fill_(.002)
                self.base_model._scq_last_info=None;self.full_instrumentation_enabled=False
            def enable_full_instrumentation(self,value):self.full_instrumentation_enabled=value
            def forward(self,x):
                self.forwards+=1
                M=x[:,:256,:];channels=torch.arange(384,dtype=torch.float32,device=x.device)[None,None,:]/384
                F=torch.sin(M[:,:,0:1]+channels)+torch.cos(M[:,:,1:2]*(channels+1))
                z=x.mean(1).repeat(1,342)[:,:1024];Q=torch.linspace(-.5,.5,768,device=x.device).reshape(1,256,3)
                self.last_inputs=(M.detach().clone(),F.detach().clone(),z.detach().clone(),Q.detach().clone())
                if self.fail_at==self.forwards:raise RuntimeError('injected forward failure')
                Q1,info=self.base_model.scq(M,F,z,Q)
                if self.twice:self.base_model.scq(M,F,z,Q)
                self.base_model._scq_last_info=info
                dense=Q1[:,:,None,:].expand(-1,-1,32,-1).reshape(1,8192,3).contiguous()
                return Q1,dense
            def get_loss(self,*a,**k):raise AssertionError('loss must never be called')
        partial=np.zeros((8192,3),np.float32);angle=np.linspace(-1,1,256,dtype=np.float32)
        partial[:256]=np.stack((angle,np.sin(angle*3),np.cos(angle*3)),-1)
        x=torch.from_numpy(partial).unsqueeze(0);model=Toy().eval()
        before=state_sha(model);rng=torch.get_rng_state().clone()
        baseline=p.predict_once(torch,model,x)
        arrays,summary=e.observe_once(torch,np,p,model,x)
        check('09 observation output matches baseline exactly',np.array_equal(arrays['prediction'],baseline[1][0]) and np.array_equal(arrays['Q1'],baseline[0][0]))
        check('10 parameters and CPU RNG unchanged',state_sha(model)==before and torch.equal(rng,torch.get_rng_state()))
        check('11 hooks removed after success',not model.base_model.scq._forward_hooks and not model.base_model.scq._forward_pre_hooks)
        check('12 captured actual SCQ M F z Qraw inputs',all(np.array_equal(arrays[k],v.numpy()[0]) for k,v in zip(('M','F','z','Qraw'),model.last_inputs)))
        check('13 exact capture key shape and dtype',set(arrays)=={'M','F','z','Qraw','Q1','delta0','N0','N1','h_static','h_requery','prediction','coarse'} and arrays['M'].shape==(256,3) and arrays['F'].shape==(256,384) and arrays['h_static'].shape==(256,1802) and arrays['N0'].dtype==np.int64)
        check('14 exactly original plus one extra KNN',model.knn_calls==3)
        check('15 Qraw delta0 Q1 arithmetic',np.allclose(arrays['Qraw']+arrays['delta0'],arrays['Q1'],rtol=2e-6,atol=2e-7))
        M,F,z,Q0=model.last_inputs;Q1=torch.from_numpy(arrays['Q1'][None]);N0=torch.from_numpy(arrays['N0'][None]);N1=torch.from_numpy(arrays['N1'][None])
        h0,_=e.descriptor(torch,M,F,z,Q1,N0);h1,_=e.descriptor(torch,M,F,z,Q1,N1)
        check('16 Static geometry centered on Q1',np.array_equal(h0.numpy()[0],arrays['h_static']))
        same,_=e.descriptor(torch,M,F,z,Q1,N0.clone());check('17 same indices same descriptor',torch.equal(same,h0))
        changed,_=e.descriptor(torch,M,F,z,Q1,(N0+73)%256);check('18 changed neighbors can change descriptor',not torch.equal(changed,h0))
        check('19 new neighbor distance consistency',summary['new_neighbor_mean_distance']<=summary['old_neighbor_mean_distance']+1e-6)
        reject('20 wrong index dtype rejected',lambda:e.descriptor(torch,M,F,z,Q1,N0.float()))
        reject('21 out of range index rejected',lambda:e.descriptor(torch,M,F,z,Q1,torch.full_like(N0,256)))
        class PartialOnly:
            files=['partial','gt']
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def __getitem__(self,key):assert key=='partial','GT access';return partial
        point=O/'partial_probe.npz';point.write_bytes(b'ARTIFICIAL_PARTIAL_ONLY')
        np_proxy=types.SimpleNamespace(load=lambda *a,**k:PartialOnly(),float32=np.float32,isfinite=np.isfinite)
        assert np.array_equal(p.load_partial(np_proxy,dict(input=rec(point),n_input=8192)),partial);check('22 inherited reader indexes partial only')
        fail=Toy(fail_at=1).eval()
        reject('23 forward error propagated',lambda:e.observe_once(torch,np,p,fail,x))
        check('24 hooks removed on failure',not fail.base_model.scq._forward_hooks and not fail.base_model.scq._forward_pre_hooks)
        twice=Toy(twice=True).eval();reject('25 duplicate SCQ call stops',lambda:e.observe_once(torch,np,p,twice,x))
        assert not twice.base_model.scq._forward_hooks and not twice.base_model.scq._forward_pre_hooks
        refs=O/'references';refs.mkdir();inputs=O/'inputs';inputs.mkdir();fq=copy.deepcopy(q)
        for i,row in enumerate(fq['cases']):
            artificial=partial.copy();artificial[:256,2]+=i*.001
            f=inputs/(str(i)+'.npz');np.savez_compressed(f,partial=artificial,gt=np.array(['MUST_NOT_READ']))
            row['input']=rec(f);ref=refs/(str(i)+'.npz');m=Toy().eval();co,de=p.predict_once(torch,m,torch.from_numpy(artificial).unsqueeze(0));info=m.base_model._scq_last_info
            np.savez_compressed(ref,prediction=de[0],coarse=co[0],Qraw=info['Q0'].numpy()[0],delta=info['delta'].numpy()[0]);row['reference']=rec(ref)
        helper=types.SimpleNamespace(state_sha=state_sha,tensor_sha=tensor_sha)
        class Budget:
            def __init__(self):self.events=[]
            def sample(self,label,count):self.events.append((label,count))
        def folder(name):
            out=O/name;out.mkdir();(out/'memory').mkdir();return out
        def loader(t,m,run):assert run['variant']=='S'
        built=[]
        def builder(run):m=Toy();built.append(m);return m,dict(artificial=True)
        out=folder('ten_complete');budget=Budget();files,states=e.execute(torch,np,p,helper,fq,out,budget,builder,loader,'cpu',True)
        check('26 actual ten-case orchestration',sum(m.forwards for m in built)==10 and len(files)==13 and [v['forwards'] for v in states]==[7,3])
        check('27 both model state and RNG checks passed',len(states)==2 and all(v['state_before']==v['state_after'] and v['RNG_before']==v['RNG_after'] for v in states))
        events=[json.loads(v) for v in (out/'forward_attempts.jsonl').read_text().splitlines()]
        check('28 ten durable forward claims',len(events)==10 and [v['forward_index'] for v in events]==list(range(1,11)))
        badout=folder('injected_failure');failed=[]
        def badbuilder(run):m=Toy(fail_at=3);failed.append(m);return m,dict(artificial=True)
        reject('29 execution stops at injected third attempt',lambda:e.execute(torch,np,p,helper,fq,badout,Budget(),badbuilder,loader,'cpu',True))
        failure=json.loads((badout/'failure.json').read_bytes());assert failure['forward_attempts']==3 and failure['valid_returns']==2 and len(failed)==1 and failed[0].forwards==3
        check('30 no retry or next model after failure')
        reject('31 production CPU bypass rejected',lambda:e.execute(torch,np,p,helper,q,folder('denied_cpu'),Budget(),builder,loader,'cpu',False))
        launcher=e.render_launcher(q,'a'*64,'b'*64,'c'*64,p)
        check('32 short POSIX launcher directory before redirect',max(len(l.encode()) for l in launcher.splitlines())<=2048 and '\\' not in launcher and launcher.index('mkdir --')<launcher.index(' >') and '1800s' in launcher)
        assert len(checks)==32
        for record in ctx['parent_sources']:
            assert rec(Path(record['path']))==record
        result=dict(status='SCQ_RF_OBSERVER_ARTIFICIAL_CPU_CONTRACT_PASS',checks=checks,checks_passed=32,entry=rec(S/'bcsp_scq_rf_memory_capture_v1.py'),test=rec(Path(__file__)),runtime=dict(python=sys.version.split()[0],torch=torch.__version__,numpy=np.__version__),parent_sources=ctx['parent_sources'],synthetic_orchestration_forwards=10,synthetic_failed_attempts=3,actual_frozen_SCQ_residual_used=True,artificial_outer_model=True,real_checkpoint_loads=0,real_patient_arrays=0,GPU_calls=0,server_operations=0,production_mutations=0,limitations=['Outer encoder/decoder are deterministic fixtures, native CUDA provider/Mamba not executed.','Production isolated environment bootstrapping and all remote asset existence remain to be freshly verified.','Same native SCQ forward and exact observer hooks/descriptor/execute/authorize/render paths tested, no RF head implemented.'])
        emit(O/'result_v1.json',result);print(json.dumps(result),flush=True)
    except BaseException as exc:
        emit(O/'failure_v1.json',dict(status='CPU_CONTRACT_FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()))
        raise

if __name__=='__main__':main()
