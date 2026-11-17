"""Single frozen 32-item artificial CPU batch; failure stops, no automatic repair/rerun."""
import ast,copy,hashlib,importlib.util,inspect,json,random,sys,time,traceback,types
from pathlib import Path
import numpy as np
import torch
from torch import nn
S=Path(__file__).resolve().parent;W=S.parents[1];O=S/'artificial_cpu_batch_v1'
MOTHER=W/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot/models/AdaPoinTr.py'
def load(n,p):
    spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    O.mkdir(exist_ok=False);start=time.monotonic();checks=[];scope=json.loads((S/'CPU_batch_scope_v1.json').read_text(encoding='utf-8'));torch.set_num_threads(2)
    def check(n,v=True):
        if not v:raise AssertionError(scope['tests'][n-1])
        need_name=scope['tests'][n-1];assert len(checks)==n-1;checks.append(need_name)
    def reject(fn):
        try:fn()
        except (ValueError,RuntimeError,TypeError,AssertionError):return True
        return False
    def emit(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    candidates=[S/n for n in ['bcsp_spcg_head_v1.py','bcsp_spcg_factory_v1.py','bcsp_spcg_runtime_v1.py','bcsp_spcg_cuda_entry_v1.py','test_spcg_cpu_v1.py']]
    before={p.name:sha(p) for p in candidates}
    try:
        h=load('bcsp_spcg_head_v1',S/'bcsp_spcg_head_v1.py');f=load('bcsp_spcg_factory_v1',S/'bcsp_spcg_factory_v1.py');r=load('bcsp_spcg_runtime_v1',S/'bcsp_spcg_runtime_v1.py');e=load('bcsp_spcg_cuda_entry_v1',S/'bcsp_spcg_cuda_entry_v1.py')
        U=torch.quasirandom.SobolEngine(3,scramble=False).draw_base2(8).float();rng=torch.get_rng_state().clone();g1=h.SPCGHead('G1',U);g2=h.SPCGHead('G2',U)
        ub=U.numpy().tobytes();hb=h.head_bytes(g1);(O/'probe_U_fp32_v1.bin').write_bytes(ub);(O/'head_initialization_fp32_v1.bin').write_bytes(hb)
        torch.manual_seed(918);D=torch.randn(2,8192,3);pos=torch.randn(2,256,3);F=torch.randn(2,256,384);z=torch.randn(2,1024)
        A=g1.probes(D);check(1,torch.equal(U[0],torch.zeros(3)) and torch.equal(U[1],torch.ones(3)*.5) and torch.allclose(A,D.amin(1)[:,None]+(D.amax(1)-D.amin(1))[:,None]*U))
        x1,d1=g1.describe(D,pos,F,z);q1=g1(D,pos,F,z);check(2,x1.shape==(2,256,1416) and q1.shape==(2,256,3) and sum(p.numel() for p in g1.parameters())==1845763)
        centered=pos-pos.mean(1)[:,None];check(3,torch.allclose(d1['mu']+A,pos.mean(1)[:,None].expand_as(A),atol=5e-7) and torch.equal(d1['tau'][:,0],d1['tau'][:,-1]) and torch.allclose(d1['tau'][:,0,0],(centered.square().sum(-1).mean(1)+1e-6).sqrt()))
        x2,d2=g2.describe(D,pos,F,z);norm=torch.nn.functional.layer_norm(F,(384,),eps=1e-5)
        b,i=1,17;idx=sorted(range(256),key=lambda j:(float(((pos[b,j]-A[b,i])**2).sum()),j))[:8];sel=pos[b,idx]-A[b,i];mu=sel.mean(0)
        ref=torch.cat((z[b],norm[b,idx].mean(0),A[b,i],mu,torch.linalg.vector_norm(sel,dim=-1).mean()[None],(torch.mean(torch.sum((sel-mu)**2,-1))+1e-6).sqrt()[None]))
        check(4,torch.equal(d2['index'][b,i],torch.tensor(idx)) and torch.allclose(x2[b,i],ref,atol=2e-6,rtol=1e-5))
        check(5,float(d2['rho'][b,i])>float(torch.linalg.vector_norm(sel,dim=-1).min()))
        check(6,torch.equal(g2.probes(D.flip(1)),A))
        perm=torch.randperm(256);check(7,torch.allclose(g2(D,pos[:,perm],F[:,perm],z),g2(D,pos,F,z),atol=2e-6,rtol=1e-5))
        tied=torch.zeros_like(pos);_,td=g2.describe(D,tied,F,z);check(8,torch.equal(td['index'],torch.arange(8).view(1,1,8).expand(2,256,8)))
        check(9,torch.allclose(g2(D[:1],pos[:1],F[:1],z[:1]),g2(D,pos,F,z)[:1],atol=2e-6,rtol=1e-5))
        bad=D.clone();bad[0,0,0]=float('nan');check(10,reject(lambda:g2(bad,pos,F,z)) and reject(lambda:g2(torch.zeros_like(D),pos,F,z)))
        check(11,reject(lambda:g2(D.half(),pos,F,z)) and reject(lambda:g2(D,pos[:,:255],F,z)))
        fl=F.clone().requires_grad_();zl=z.clone().requires_grad_();q=g2(D,pos,fl,zl);q.square().mean().backward()
        check(12,all(t.grad is not None and bool(torch.isfinite(t.grad).all()) and float(t.grad.abs().sum())>0 for t in [fl,zl]) and all(p.grad is not None and bool(torch.isfinite(p.grad).all()) for p in g2.parameters()))
        sl=pos.clone().requires_grad_();g2.zero_grad();g2(D,sl,F,z).square().mean().backward();check(13,sl.grad is not None and bool(torch.isfinite(sl.grad).all()) and float(sl.grad.abs().sum())>0)
        check(14,not pos.requires_grad and bool(torch.isfinite(g2(D,pos,F,z)).all()))
        rs=torch.get_rng_state().clone();h.SPCGHead('G1',U);check(15,torch.equal(rs,torch.get_rng_state()))
        fresh=h.SPCGHead('G2',h.from_bytes(ub,(256,3)),hb);check(16,h.head_bytes(fresh)==hb==h.head_bytes(g1) and torch.equal(fresh.U,U))
        # Extract actual mother forward, FC head and loss routing, with artificial CPU encoder/decoder/loss.
        env=dict(torch=torch,nn=nn,misc=types.SimpleNamespace(fps=lambda x,n:x[:,:n]))
        tr=W/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot/models/Transformer_utils.py'
        tree=ast.parse(tr.read_text(encoding='utf-8'));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Mlp'],type_ignores=[]),str(tr),'exec'),env)
        tree=ast.parse(MOTHER.read_text(encoding='utf-8'))
        pc=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PCTransformer');ad=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AdaPoinTr')
        def method(cls,name):
            n=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name==name);d=dict(env);exec(compile(ast.Module(body=[n],type_ignores=[]),str(MOTHER),'exec'),d);return d[name]
        node=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SimpleRebuildFCLayer');exec(compile(ast.Module(body=[node],type_ignores=[]),str(MOTHER),'exec'),env)
        class Decoder(nn.Module):
            def __init__(self):super().__init__();self.proj=nn.Linear(384,384);self.pos=nn.Linear(3,384);self.last=None
            def forward(self,q,v,q_pos,v_pos,**kwargs):self.last=q_pos;return self.proj(q+v.mean(1)[:,None])+self.pos(q_pos)
        class Base(nn.Module):
            forward=method(pc,'forward')
            def __init__(self):
                super().__init__();self.encoder=nn.Sequential(nn.Linear(3,384),nn.GELU());self.bn=nn.BatchNorm1d(384);self.increase_dim=nn.Linear(384,1024);self.coarse_pred=nn.Sequential(nn.Linear(1024,1024),nn.GELU(),nn.Linear(1024,768));self.mlp_query=nn.Sequential(nn.Linear(1027,384),nn.GELU());self.mem_link=nn.Identity();self.decoder=Decoder();self.query_selection='learned_only';self.num_query=256;self.use_denoise=False;self.rim_query_enabled=False;self.full_instrumentation_enabled=False;self.scqr_contract=types.SimpleNamespace(enabled=False);self.scqr_local_geometry=None;self.scqr_query_conditioner=None
            def encode_rim_proxy_tokens(self,D):
                S=D[:,:256].detach();x=self.bn(self.encoder(S).transpose(1,2)).transpose(1,2);return S,torch.cat((x,torch.zeros_like(x)),-1),x,x
        class SurrogateCD(nn.Module):
            def forward(self,a,b):return (a.mean(1)-b.mean(1)).square().mean()+.1*a.square().mean()
        class Model(nn.Module):
            forward=method(ad,'forward');get_loss=method(ad,'get_loss');get_fine_loss_components=method(ad,'get_fine_loss_components')
            def __init__(self):
                super().__init__();self.base_model=Base();self.increase_dim=nn.Conv1d(384,16,1);self.reduce_map=nn.Linear(403,384);self.decode_head=env['SimpleRebuildFCLayer'](768,32,hidden_dim=32);self.full_instrumentation_enabled=False;self.decoder_type='fc';self.factor=32;self.num_query=256;self.denoise_weight=0;self.fine_local_weight=0;self.coarse_geometry_guard_enabled=False;self.local_rim_guard_enabled=False;self.moment_trust_enabled=False;self.dense_contact_enabled=False;self.rim_query_enabled=False;self.scqr_contract=types.SimpleNamespace(contact_supervision_enabled=False);self.loss_func=SurrogateCD();self.fine_loss_func=SurrogateCD();self.f0_evidence=dict(artificial_fixture=True)
        def build(arm):
            with torch.random.fork_rng(devices=[]):torch.manual_seed(11);m=Model()
            return f.install(m,arm,U,hb,MOTHER,sha(MOTHER))
        m,ev=build('G2');check(17,ev['patch']['replaced_assignments']==1 and m.base_model.forward.__func__.__code__.co_filename.endswith('::SPCG_one_expression'))
        m.eval();m.base_model.spcg_head.capture=True;ret=m(D[:1]);check(18,torch.equal(ret[0],m.base_model.decoder.last) and torch.equal(ret[0],m.base_model.spcg_head.last_q))
        m.train();ret=m(D[:1]);check(19,len(ret)==4 and torch.equal(ret[0],m.base_model.decoder.last) and ret[-1].shape==(1,8192,3))
        base,_=build('G0');check(20,hasattr(base.base_model,'coarse_pred') and not hasattr(base.base_model,'spcg_head') and not hasattr(m.base_model,'coarse_pred'))
        target=torch.randn(1,8192,3);a,c=m.get_loss(ret,target,0,partial=D[:1]);expected=m.loss_func(ret[0],target)+m.fine_loss_func(ret[-1],target);check(21,float(a)==0 and torch.equal(c,expected) and type(m.decode_head).__name__=='SimpleRebuildFCLayer')
        ret[0].retain_grad();c.backward();qr=r.Q_gradient_record(ret[0]);geo=r.geometry(ret[0]);check(22,qr['origin']=='TOTAL_LOSS_NOT_ISOLATED_COARSE' and qr['L2']>0 and geo['rms_radius'][0]>0)
        accessed=[]
        class Archive:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def __getitem__(self,k):accessed.append(k);assert k=='partial';return np.ones((8192,3),dtype=np.float32)
        blob=O/'artificial_partial_only.npz';blob.write_bytes(b'ARTIFICIAL_CONTAINER_SENTINEL')
        np_proxy=types.SimpleNamespace(load=lambda *args,**kw:Archive(),float32=np.float32,isfinite=np.isfinite)
        r.read_partial(np_proxy,dict(path=str(blob),bytes=blob.stat().st_size,sha256=sha(blob)))
        check(23,list(inspect.signature(h.SPCGHead.forward).parameters)==['self','D','S','F','z'] and accessed==['partial'] and reject(lambda:g2(D,pos,F,z,GT=target)))
        marked=m.base_model.encoder[0].weight;marked._no_weight_decay=True;groups=r.optimizer_groups(m);check(24,any(p is marked for p in groups[1]['params']) and all(p is not marked for p in groups[0]['params']))
        estimate=r.output_estimate(m);planned=39912132*12+2*1024**2+160*1024**2;check(25,estimate['total_bytes']<1024**3 and planned<1024**3 and len({('G'+str(a),f) for a in range(3) for f in ['C','D']})==6)
        q=dict(schema='bcsp-spcg-cuda-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,science=e.SCIENCE,limits=e.LIMITS,fixture=e.FIXTURE,real_inputs=[dict(source_id=str(i)) for i in range(5)],project='/home/jovyan/adapointr_work/PoinTr',output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_v1',identity=dict(python_realpath='/opt/conda/envs/adapointr-mamba/bin/python3.10'),entry=dict(path='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1/bcsp_spcg_cuda_entry_v1.py'),environment=dict(CUBLAS_WORKSPACE_CONFIG=':4096:8'),launch_contract=dict(request_path='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1/request.json',authorization_path='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1/control/a.json',runtime_path='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1/control/r.json'))
        ab,rb=e.materialization(q,'a'*64,'ARTIFICIAL_CPU_ONLY');aa=json.loads(ab);rr=json.loads(rb);check(26,e.authorize(q,'a'*64,aa,hashlib.sha256(ab).hexdigest(),rr) is q and reject(lambda:e.authorize(q,'a'*64,dict(aa,runtime_sha256='c'*64),'b'*64,rr)) and reject(lambda:e.authorize(q,'a'*64,dict(aa,explicit_user_authorization=False),'b'*64,rr)))
        budget=r.CallBudget()
        for _ in range(11):budget.claim('full_forward')
        check(27,reject(lambda:budget.claim('full_forward')) and reject(lambda:budget.claim('optimizer_steps')) and reject(lambda:budget.finish()))
        launcher=e.render_launcher(q,'a'*64,'b'*64,'c'*64);check(28,launcher.index('mkdir -p')<launcher.index(' >') and 'mkdir '+q['output']+'\n' in launcher and '\\' not in launcher.replace('\\n','') and max(len(x.encode()) for x in launcher.splitlines())<=2048 and 'exit "$rc"' in launcher)
        xd,yg=e.fixture(np);events=[];memory=[];reads=[]
        result=e.run_checks(torch,np,r,build,torch.from_numpy(xd),torch.from_numpy(yg),[dict(case_id=str(i)) for i in range(5)],lambda row:(reads.append(row['case_id']) or xd[0]),events.append,lambda *a:None,lambda *a:memory.append(a[0]),device='cpu',cuda=False)
        check(29,result['counts']==r.SCIENCE and len([v for v in events if v.get('kind')=='RESTORED'])==3 and all(v['state'] and v['RNG'] and v['modes'] for v in events if v.get('kind')=='RESTORED'))
        check(30,reads==list(map(str,range(5))) and memory==list(range(5)) and len([v for v in events if v.get('kind')=='REAL_D_ONLY'])==5 and result['counts']['full_backward']==3)
        failures=[]
        def failbuild(arm):
            m,ev=build(arm)
            def fail(*a,**kw):raise RuntimeError('ARTIFICIAL_FIRST_FORWARD_FAIL')
            m.forward=fail;return m,ev
        check(31,reject(lambda:e.run_checks(torch,np,r,failbuild,torch.from_numpy(xd),torch.from_numpy(yg),[],lambda _:None,failures.append,lambda *a:None,lambda *a:None,device='cpu',cuda=False)) and len([v for v in failures if v.get('operation')=='full_forward'])==1 and failures[-1]['kind']=='RESTORED')
        helper=W/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py';module=load('spcg_cpu_numeric_helper',helper);module.configure_numeric(torch)
        s0=json.loads((W/'outputs/spcg_S0_readonly_20261116_v1/S0_local_metadata_and_boundary_review_v1.json').read_text(encoding='utf-8'))
        check(32,all(sha(x['local'])==x['sha256'] for x in s0['local_source_matches']) and all(sha(p)==before[p.name] for p in candidates) and torch.are_deterministic_algorithms_enabled() and not torch.backends.cuda.matmul.allow_tf32)
        emit('result.json',dict(status='SPCG_ARTIFICIAL_CPU_PASS',count=len(checks),checks=checks,seconds=time.monotonic()-start,torch=torch.__version__,numpy=np.__version__,source_sha256=before,scope_sha256=sha(S/'CPU_batch_scope_v1.json'),probe_sha256=sha(O/'probe_U_fp32_v1.bin'),head_sha256=sha(O/'head_initialization_fp32_v1.bin'),admission_fixture=result,entry_events=events,output_estimate_fixture=estimate,production_output_estimate_bytes=planned,native_Mamba=False,CUDA=False,real_payload_reads=0,trained_checkpoint_loads=0,optimizer_steps=0,limitations=['Artificial encoder/decoder and cheap scalar CD substitute; actual mother forward/outer FC/loss routing extracted unchanged.','Actual Mamba/provider/production full cdist loss, CUDA gradients and memory NOT validated.','U and H are CPU torch2.5.1 frozen FP32 bytes, loaded as authoritative bytes on target torch2.4.1; no runtime regeneration equality.']))
        print(json.dumps(dict(status='SPCG_ARTIFICIAL_CPU_PASS',count=len(checks),seconds=time.monotonic()-start)))
    except BaseException as ex:emit('failure.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc(),source_sha256=before));raise
if __name__=='__main__':main()
