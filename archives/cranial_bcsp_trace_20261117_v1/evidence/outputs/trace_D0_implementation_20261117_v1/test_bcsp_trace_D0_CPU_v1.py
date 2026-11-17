"""One retained artificial CPU batch. No WSL/server, CUDA, real NPZ or trained weights."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2'
os.environ['MKL_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
import ast,copy,hashlib,importlib.util,json,sys,types,textwrap,traceback,tarfile,subprocess
from pathlib import Path
import numpy as np
import torch
from torch import nn

V=Path(__file__).resolve().parent;R=V.parents[1];O=V/'CPU_batch_v1'
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def load(name,p):
    m=importlib.util.module_from_spec(importlib.util.spec_from_file_location(name,p));sys.modules[name]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def reject(fn):
    try:fn()
    except (ValueError,RuntimeError,AssertionError,KeyError):return True
    return False
def js(p,x):p.write_text(json.dumps(x,indent=2),encoding='utf-8')

def main():
    O.mkdir();checks=[]
    def check(name,ok):
        if not ok:raise AssertionError(name)
        checks.append(name)
    try:
        torch.set_num_threads(2)
        e=load('TRACE_entry_CPU',V/'bcsp_trace_D0_entry_v1.py');obs=load('TRACE_observer_CPU',V/'bcsp_trace_D0_observer_v1.py');analysis=load('TRACE_analysis_CPU',V/'bcsp_trace_D0_analysis_v1.py')
        inputs=read(V/'CPU_test_bindings_v1.json');q=read(V/'draft_D0_configuration_v1.json');aliases=inputs['local_aliases']
        originalexact=e.exact
        def mapped(r):
            if r['path'] in aliases:
                p=Path(aliases[r['path']]);need=rec(p);assert (need['bytes'],need['sha256'])==(r['bytes'],r['sha256']);return p
            return originalexact(r)
        e.exact=mapped
        n=load('TRACE_native_CPU',Path(aliases[q['implementation']['native_reuse']['path']]));oldnativeexact=n.exact;n.exact=mapped
        frozen={p:rec(Path(p)) for p in inputs['unchanged_production_sources']}
        check('imports inert: no CLI/remote/GPU action',not torch.cuda.is_initialized() and os.environ['CUDA_VISIBLE_DEVICES']=='')
        # Exercise the complete authorize path with explicitly artificial receipt files.
        q['status']='AWAITING_EXPLICIT_USER_AUTHORIZATION'
        p3=O/'ARTIFICIAL_P3.json';js(p3,dict(status='TRACE_D0_LOCAL_P3_PASS',checks={'artificial':True},entry_sha256=q['entry']['sha256'],observer_sha256=q['implementation']['observer']['sha256']));q['P3']=rec(p3)
        qp=O/'ARTIFICIAL_request.json';js(qp,q)
        ap=O/'ARTIFICIAL_authorization.json';js(ap,dict(schema='bcsp-trace-D0-authorization-v1',request_sha256=rec(qp)['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL CPU FIXTURE ONLY; NO REAL EXECUTION AUTHORITY'))
        rp=O/'ARTIFICIAL_runtime.json';js(rp,dict(schema='bcsp-trace-D0-runtime-v1',request_sha256=rec(qp)['sha256'],authorization_sha256=rec(ap)['sha256']))
        check('full authorize and one-way runtime positive',e.authorize(rec(qp),rec(ap),rec(rp))==q)
        for key in ['counts','identity','input_records','checkpoints']:
            bad=copy.deepcopy(q)
            if key=='counts':bad[key]['full_forward']=81
            elif key=='identity':bad[key]['gpu_uuid']='GPU-wrong'
            elif key=='input_records':bad[key][0]['input']['sha256']='0'*64
            else:bad[key]['G1_C']['sha256']='0'*64
            p=O/('bad_'+key+'.json');js(p,bad);assert reject(lambda:e.authorize(rec(p),rec(ap),rec(rp)))
        check('count identity input checkpoint drift rejected',True)
        bad=read(ap);bad['runtime_sha256']='0'*64;p=O/'bad_cycle.json';js(p,bad)
        bad_auth=read(ap);bad_auth['explicit_user_authorization']=False;denied=O/'unauthorized.json';js(denied,bad_auth)
        check('reverse runtime binding and unauthorized receipt rejected',reject(lambda:e.authorize(rec(qp),rec(p),rec(rp))) and reject(lambda:e.authorize(rec(qp),rec(denied),rec(rp))))
        # Actual frozen SPCG head/factory and extracted actual mother forward + FC.
        base=R/'outputs/spcg_implementation_20261116_v1';h=load('bcsp_spcg_head_v1',base/'bcsp_spcg_head_v1.py');f=load('bcsp_spcg_factory_v1',base/'bcsp_spcg_factory_v1.py')
        MOTHER=Path(aliases[q['mother_source']['path']]);source=(base/'test_spcg_cpu_v1.py').read_text(encoding='utf-8');fixture=source[source.index('        env=dict(torch=torch'):source.index('        def build(arm):')]
        env=dict(torch=torch,nn=nn,ast=ast,types=types,W=R,MOTHER=MOTHER);exec(compile(textwrap.dedent(fixture),'actual_mother_fixture_definitions','exec'),env)
        helper=load('TRACE_helper_CPU',Path(aliases[q['helper']['path']]));helper.configure_numeric(torch)
        factory=dict(head=h,spcg=f,lqi=types.SimpleNamespace(build_model=lambda legacy,seed:(legacy(),dict(artificial_fixture=True))))
        torch.manual_seed(17);D=torch.randn(1,8192,3);outputs={}
        for arm in ('G1','G2'):
            model,ev=n.build_spcg_model(factory,env['Model'],dict(arm=arm),q,artificial_cpu=True);n.validate_model(model,ev,True);model.eval()
            before=n.raw_state_fingerprint(model);rng=torch.get_rng_state().clone()
            with torch.inference_mode():baseline=model(D)
            head=model.base_model.spcg_head
            with obs.Observer(head,mapped(q['implementation']['head']),torch) as capture:
                with torch.inference_mode():result=model(D);arrays=capture.finish(D,*result)
                assert all(torch.equal(x,y) for x,y in zip(result,baseline))
            assert n.raw_state_fingerprint(model)==before and torch.equal(rng,torch.get_rng_state())
            assert 'describe' not in head.__dict__ and not hasattr(head,'_trace_scores') and not head.capture and not head.net[0]._forward_pre_hooks
            outputs[arm]=arrays
        check('actual mother FC and G1/G2 observer exact output/state/RNG identity',True)
        check('captured actual x f descriptors and FP32 KNN complete',analysis.geometry(outputs['G1'],'G1')['consumed_neighborhood']=='ALL256' and analysis.geometry(outputs['G2'],'G2')['consumed_neighborhood']=='NATIVE_FP32_K8')
        originalhead=base/'bcsp_spcg_head_v1.py';wrong=O/'wrong_head.py';wrong.write_bytes(originalhead.read_bytes()+b'\n')
        check('observer refuses changed frozen source',reject(lambda:obs.Observer(head,wrong,torch).__enter__()))
        try:
            with obs.Observer(head,originalhead,torch):raise RuntimeError('ARTIFICIAL_INTERRUPTION')
        except RuntimeError:pass
        check('exception removes hook wrapper and restores capture',not head.capture and 'describe' not in head.__dict__ and not hasattr(head,'_trace_scores') and not head.net[0]._forward_pre_hooks)
        with obs.Observer(head,originalhead,torch) as capture:
            assert reject(lambda:capture.finish(D,*baseline))
        check('missing actual consumers cannot produce evidence',True)
        # Synthetic near-tie: native FP32 index differs legitimately from FP64.
        U=torch.zeros(256,3);tiehead=h.SPCGHead('G2',U);tiehead.eval();S=torch.ones(1,256,3)*2;S[0,0]=torch.tensor([1.,1e-5,0]);S[0,1]=torch.tensor([1.,0.,0]);FF=torch.randn(1,256,384);zz=torch.randn(1,1024)
        DD=torch.zeros(1,8192,3);DD[0,-1]=1
        with obs.Observer(tiehead,originalhead,torch) as capture:
            with torch.inference_mode():QQ=tiehead(DD,S,FF,zz);a=capture.finish(DD,QQ,QQ.repeat_interleave(32,1))
        check('FP32 native tie respected despite FP64 different order',a['index'][0,0]==0 and np.argsort(((a['S'].astype(np.float64)-a['A'][0])**2).sum(-1),kind='stable')[0]==1 and analysis.geometry(a,'G2')['S_unique']==3)
        broken={k:v.copy() for k,v in outputs['G2'].items()};broken['index'][0,0]=(broken['index'][0,0]+1)%256
        check('wrong native index rejected without substituting FP64',reject(lambda:analysis.geometry(broken,'G2')))
        check('zero spacing retained as uninformative, no epsilon replacement',analysis.geometry(a,'G2')['R_case'] is None)
        normal=dict(center=[10.,20.,30.],scale=120.)
        old=dict(prediction=outputs['G2']['P'],coarse=outputs['G2']['Q']);new=copy.deepcopy(outputs['G2'])
        check('replay exact-byte positive',all(x['exact_bytes'] for x in analysis.replay_arrays(new,old,normal).values()))
        new['P']=new['P']+.1
        check('replay large displacement rejected',reject(lambda:analysis.replay_arrays(new,old,normal)))
        tied=[dict(R_case=1.,delta_E=float(i),defect_type='bilateral') for i in range(4)]
        trend=[dict(R_case=float(i),delta_E=float(i),defect_type='a' if i<4 else 'b') for i in range(8)]
        check('association handles constant data and retains type adjustment',analysis.association(tied)['status']=='UNINFORMATIVE' and analysis.association(trend)['budget_motivation'])
        missing=copy.deepcopy(trend);missing[0]['R_case']=None
        check('undefined and singleton strata do not drop cases',analysis.association(missing)['status']=='UNINFORMATIVE' and analysis.association([dict(R_case=1,delta_E=1,defect_type='a'),dict(R_case=2,delta_E=2,defect_type='b')])['status']=='UNINFORMATIVE')
        # Real frozen scoring helpers, but only a small artificial bone/reference.
        scorer=load('TRACE_frozen_scorer_CPU',Path(inputs['frozen_scoring_source']))
        g=np.zeros((5,5,5),bool);g[1:4,1:4,1:4]=True;d=np.zeros_like(g);d[0]=True
        ref=scorer.metric.surface_references(g,d,np.eye(3),np.zeros(3));gt=np.repeat(ref['a_centers'],2,axis=0)
        norm=dict(center=[0.,0.,0.],scale=1.)
        synthetic=np.tile(gt,(int(np.ceil(8192/len(gt))),1))[:8192].astype(np.float32)
        check('frozen E/J scoring and risk replay on artificial geometry',analysis.score_replay(scorer,dict(P=synthetic),dict(prediction=synthetic),ref,gt,norm)['score_match'])
        # Partial-only NPZ reader: fail if any GT key is requested.
        accessed=[]
        class FakeArchive:
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def __getitem__(self,key):accessed.append(key);assert key=='partial';return np.ones((8192,3),np.float32)
        sentinel=O/'partial_sentinel.npz';sentinel.write_bytes(b'ARTIFICIAL_CONTAINER')
        proxy=types.SimpleNamespace(load=lambda *a,**k:FakeArchive(),float32=np.float32,isfinite=np.isfinite)
        n.load_partial(proxy,dict(input=rec(sentinel),n_input=8192))
        check('actual input reader touches partial only',accessed==['partial'])
        # Complete 80-row loop, strict loading and archive, with tiny artificial heads.
        class Tiny(nn.Module):
            calls=0
            def __init__(self,arm,mode='ok'):
                super().__init__();self.base_model=nn.Module();self.base_model.bn=nn.BatchNorm1d(3);self.base_model.spcg_head=h.SPCGHead(arm,torch.linspace(0,1,768).reshape(256,3));self.base_model.spcg_head.net=nn.Sequential(nn.Linear(1416,3));self.mode=mode
            def forward(self,x):
                Tiny.calls+=1
                if self.mode=='fail':raise RuntimeError('ARTIFICIAL_FIRST_FORWARD_FAIL')
                S=self.base_model.bn(x[:,:256].transpose(1,2)).transpose(1,2);F=S.repeat(1,1,128);z=x.mean(1).repeat(1,342)[:,:1024]
                Q=self.base_model.spcg_head(x,S,F,z)
                if self.mode=='state':self.base_model.bn.running_mean.add_(1)
                if self.mode=='rng':torch.rand(1)
                return Q,Q.repeat_interleave(32,1)
        fq=copy.deepcopy(q);fq['implementation']['head']=rec(originalhead);cache={};folder=O/'artificial_inputs';folder.mkdir()
        for row in fq['input_records']:
            key=(row['fold'],row['case_id'])
            if key not in cache:
                v=np.linspace(-.8,.8,8192,dtype=np.float32);part=np.stack((v,np.sin(v*3),np.cos(v*3)),1);p=folder/(row['fold']+'__'+row['case_id']+'.npz')
                with p.open('xb') as ff:np.savez_compressed(ff,partial=part,implant=np.zeros_like(part))
                cache[key]=rec(p)
            row['input']=cache[key]
        for label in e.ORDER:
            model=Tiny(label.split('_')[0]);p=O/(label+'_artificial.pth');torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=model.state_dict()),p);fq['checkpoints'][label]=rec(p);n.FROZEN_MODELS[label]=dict(n.FROZEN_MODELS[label],checkpoint=rec(p))
        samples=[];budget=types.SimpleNamespace(sample=lambda phase,count:samples.append((phase,count)))
        def builder(run,mode='ok'):return Tiny(run['arm'],mode),dict(artificial_fixture=True,arm=run['arm'],change=dict(old_head_removed=True,head_parameters=1845763))
        output=O/'artificial80';output.mkdir();(output/'traces').mkdir()
        files,states=e.execute(torch,np,n,helper,obs,fq,output,builder,budget,device='cpu',artificial_cpu=True)
        check('complete80 four-model20/source loop',Tiny.calls==80 and len(files)==82 and len(states)==4 and all(r['forwards']==20 for r in states))
        check('all80 state RNG fingerprints unchanged',all(r['state_before']==r['state_after'] and r['RNG_before']==r['RNG_after'] for r in states))
        journal=[json.loads(l) for l in (output/'forward_attempts.jsonl').read_text().splitlines()]
        manifest=[json.loads(l) for l in (output/'trace_manifest.jsonl').read_text().splitlines()]
        check('sequential claims and exact manifest identities',list(range(1,81))==[r['forward_index'] for r in journal] and len(manifest)==80 and all(r['trace']['sha256']==rec(Path(r['trace']['path']))['sha256'] for r in manifest))
        with np.load(Path(manifest[0]['trace']['path']),allow_pickle=False) as z:check('G1 capture contains no fabricated k8 fields','index' not in z.files and 'native_d2' not in z.files and z['x'].shape==(256,1416))
        with np.load(Path(manifest[20]['trace']['path']),allow_pickle=False) as z:check('G2 capture has actual native matrix and index',z['native_d2'].shape==(256,256) and z['index'].shape==(256,8))
        packed=n.pack(output,files)
        with tarfile.open(packed['path']) as tar:members=tar.getmembers();assert len(members)==82 and len({m.name for m in members})==82 and all(m.isfile() for m in members)
        check('archive SHA bytes contents and exact80 NPZ',rec(Path(packed['path']))['sha256']==packed['sha256'] and len(Path(packed['path']+'.contents.sha256').read_text().splitlines())==82)
        for mode in ['fail','state','rng']:
            failed=O/('negative_'+mode);failed.mkdir();(failed/'traces').mkdir();before=Tiny.calls
            assert reject(lambda:e.execute(torch,np,n,helper,obs,fq,failed,lambda run:builder(run,mode),budget,device='cpu',artificial_cpu=True))
            failure=read(failed/'diagnostic_failure.json');assert failure['attempts']==(1 if mode=='fail' else 20) and Tiny.calls-before==failure['attempts']
        check('forward state RNG failures stop with durable exact counts',True)
        wrong=O/'wrong_step.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=98,updates=3899,base_model={}),wrong)
        check('strict checkpoint stage/update rejects invalid synthetic file',reject(lambda:n.load_checkpoint(torch,Tiny('G1'),dict(checkpoint=rec(wrong)))))
        # Exercise the actual exact-source and FilePolicy dispatch on local fixtures.
        original_os=n.os;attrs=dict(vars(os));attrs['O_RDONLY']=os.O_RDONLY|getattr(os,'O_BINARY',0);n.os=types.SimpleNamespace(**attrs)
        guard=n.make_source_guard(q)
        try:
            utc=types.SimpleNamespace(allow=lambda filename,write=False:str(filename)=='EXACT_UTC_ARTIFICIAL' and not write)
            policy=n.make_policy(helper,[O,Path(sys.prefix)],O,[str(sentinel)],[],[],utc,guard)
            policy.check('EXACT_UTC_ARTIFICIAL');assert guard.allow(mapped(q['implementation']['head']))
            assert reject(lambda:guard.allow(mapped(q['implementation']['head']),write=True))
            assert reject(lambda:policy.check(O/'not_allowed.npz'))
            assert reject(lambda:policy.check(O/'not_allowed.pth'))
            try:raise RuntimeError('ARTIFICIAL_TRACEBACK')
            except RuntimeError:details=traceback.format_exc();js(O/'guarded_exception_fixture.json',dict(traceback=details,guard_open=bool(guard.fds)))
        finally:guard.close();n.os=original_os
        check('actual UTC/source dispatch exact reads payload denial and active-guard traceback',read(O/'guarded_exception_fixture.json')['guard_open'])
        child=subprocess.run([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--reader-child'],capture_output=True,timeout=40)
        (O/'reader_child_stdout.bin').write_bytes(child.stdout);(O/'reader_child_stderr.bin').write_bytes(child.stderr)
        check('full frozen module loading under actual active audit policy',child.returncode==0 and read(O/'reader_child_result.json')['status']=='ACTIVE_POLICY_FULL_SOURCE_CHAIN_PASS')
        launcher=n.render_launcher(q,'a'*64,'b'*64,'c'*64)
        check('900s POSIX launcher mkdir before redirect and explicit exit',launcher.index('mkdir -p')<launcher.index(' >') and '900s' in launcher and 'exit "$rc"' in launcher and max(map(len,launcher.splitlines()))<=2048 and '\\' not in q['launch_contract']['launcher'])
        check('four production sources unchanged and no CUDA initialized',all(rec(Path(p))==b for p,b in frozen.items()) and not torch.cuda.is_initialized())
        result=dict(status='TRACE_D0_ARTIFICIAL_CPU_PASS',count=len(checks),checks=checks,torch=torch.__version__,numpy=np.__version__,GPU=False,server_operations=0,trained_checkpoint_loads=0,real_NPZ_arrays_read=0,optimizer_steps=0,synthetic_full_loop_forward=80,source_bindings={p.name:rec(p) for p in V.glob('*.py')},limitations=['Real frozen head/factory and mother forward/FC exercised with artificial encoder/decoder; no actual Mamba/CUDA rerun.','Full80 loop uses tiny artificial coordinate heads, generated partial arrays and artificial state_dict files.','CPU fixture authorization and P3 files are not production authorization.','Real replay scores and R/DeltaE associations have not been computed.'])
        js(O/'result.json',result);print(json.dumps(dict(status=result['status'],count=len(checks))))
    except BaseException as exc:
        js(O/'failure.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise

def reader_child():
    e=load('TRACE_child_entry',V/'bcsp_trace_D0_entry_v1.py');q=read(V/'draft_D0_configuration_v1.json');aliases=read(V/'CPU_test_bindings_v1.json')['local_aliases']
    original=e.exact
    def mapped(r):
        if r['path'] in aliases:
            p=Path(aliases[r['path']]);b=rec(p);assert (b['bytes'],b['sha256'])==(r['bytes'],r['sha256']);return p
        return original(r)
    e.exact=mapped;n=load('TRACE_child_native',Path(aliases[q['implementation']['native_reuse']['path']]));n.exact=mapped
    helper=load('TRACE_child_helper',Path(aliases[q['helper']['path']]))
    attrs=dict(vars(os));attrs['O_RDONLY']=os.O_RDONLY|getattr(os,'O_BINARY',0);n.os=types.SimpleNamespace(**attrs)
    guard=n.make_source_guard(q);utc=types.SimpleNamespace(allow=lambda p,write=False:str(p)=='EXACT_UTC_ARTIFICIAL' and not write)
    policy=n.make_policy(helper,[V,Path(sys.prefix),Path(sys.base_prefix)],O,[],[],[],utc,guard);sys.addaudithook(policy.audit)
    try:
        factory=n.load_spcg_builder(q['implementation']);observer=e.module('TRACE_child_observer',q['implementation']['observer'])
        assert all(k in factory for k in ['lqi','spcg','head'])
        try:observer.need(False,'ARTIFICIAL_FAIL_AFTER_FULL_LOAD')
        except ValueError:details=traceback.format_exc()
        assert 'ARTIFICIAL_FAIL_AFTER_FULL_LOAD' in details
        js(O/'reader_child_result.json',dict(status='ACTIVE_POLICY_FULL_SOURCE_CHAIN_PASS',guard_open_before_traceback_saved=bool(guard.fds),production_source_writes=0,GPU=False))
    finally:guard.close()

if __name__=='__main__':
    if sys.argv[1:]==['--reader-child']:reader_child()
    else:main()
