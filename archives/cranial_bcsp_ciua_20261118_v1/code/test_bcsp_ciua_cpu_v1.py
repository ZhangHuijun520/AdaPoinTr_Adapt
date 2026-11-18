"""One retained artificial CPU batch. Never reads real point/weight array values."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2'
os.environ['MKL_NUM_THREADS']='2'
os.environ['OPENBLAS_NUM_THREADS']='2'
import ast
import builtins
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import traceback
import types
import numpy as np
import torch
from torch import nn

V=Path(__file__).resolve().parent;R=V.parents[1];O=V/'CPU_batch_v1'
A0=R/'outputs/ciua_A0_local_review_20261118_v1'


def rec(p):
    p=Path(p);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))


def js(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,allow_nan=False)


def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);sys.modules[name]=m
    exec(compile(Path(p).read_bytes(),str(p),'exec',dont_inherit=True),m.__dict__);return m


def reject(fn):
    try:fn()
    except (ValueError,RuntimeError,KeyError,FileExistsError):return True
    return False


def rows840():
    out=[]
    for fold in ('C','D'):
        dev=set(range(21)) if fold=='C' else set(range(21,42))
        for role in ('train','development'):
            for s in range(84):
                if (s in dev)!=(role=='development'):continue
                for typ in ('bilateral','frontoorbital','parietotemporal','random_1','random_2'):
                    out.append(dict(run='G2_'+fold,fold=fold,role=role,source_id='train:%03d'%s,case_id='train__%03d__%s'%(s,typ),normalization=dict(center=[0.,0.,0.],scale=100.)))
    return out


class Model(nn.Module):
    def __init__(self,head,F,z):
        super().__init__();self.base_model=nn.Module();self.base_model.spcg_head=head
        self.register_buffer('F',F);self.register_buffer('z',z);self.tail=0;self.fail=False
    def forward(self,D):
        if self.fail:raise RuntimeError('ARTIFICIAL_FORWARD_FAILURE')
        Q=self.base_model.spcg_head(D,D[:,:256],self.F.unsqueeze(0),self.z.unsqueeze(0))
        self.tail+=1
        raise RuntimeError('FPS_QUERY_DECODER_MUST_NOT_RUN')


class Budget:
    def __init__(self):self.records=[]
    def sample(self,phase,count):self.records.append((phase,count))


def reader_child():
    e=load('ciua_child_entry',V/'bcsp_ciua_entry_v1.py');assets=read(A0/'frozen_local_asset_bindings_v1.json')
    shared={v['role']:v['local'] for v in assets['shared']}
    native=load('ciua_child_native',shared['native_reuse']['path']);helper=load('ciua_child_helper',next(v['path'] for v in assets['files'] if Path(v['path']).name=='bcsp_artificial_gpu_preflight_v3.py') if any(Path(v['path']).name=='bcsp_artificial_gpu_preflight_v3.py' for v in assets['files']) else R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py')
    implementation={k:r for k,r in shared.items() if str(r['path']).endswith('.py')}
    implementation.update(capture=rec(V/'bcsp_ciua_capture_v1.py'),analysis=rec(V/'bcsp_ciua_analysis_v1.py'),ciua_entry=rec(V/'bcsp_ciua_entry_v1.py'),ciua_test=rec(Path(__file__)))
    q=dict(implementation=implementation,entry=rec(V/'bcsp_ciua_entry_v1.py'),helper=rec(Path(helper.__file__)),probe_asset=shared['probe'],head_initialization=shared['head_init'],mother_source=shared['mother'])
    attrs=dict(vars(os));attrs['O_RDONLY']=os.O_RDONLY|getattr(os,'O_BINARY',0);native.os=types.SimpleNamespace(**attrs)
    guard=native.make_source_guard(q);utc=types.SimpleNamespace(allow=lambda p,write=False:str(p)=='EXACT_UTC_FIXTURE' and not write)
    policy=native.make_policy(helper,[R,Path(sys.prefix),Path(sys.base_prefix)],O,[],[],[],utc,guard)
    sys.addaudithook(policy.audit)
    try:
        policy.check('EXACT_UTC_FIXTURE')
        assert reject(lambda:policy.check(O/'UNAUTHORIZED.pth'))
        assert reject(lambda:policy.check(O/'UNAUTHORIZED.npz'))
        factory=native.load_spcg_builder(dict(encoder=shared['encoder'],factory=shared['factory'],lqi_decoder=shared['lqi_decoder'],lqi_factory=shared['lqi_factory'],head=shared['head'],spcg_factory=shared['spcg_factory']))
        c=e.module('ciua_child_capture',rec(V/'bcsp_ciua_capture_v1.py'));a=e.module('ciua_child_analysis',rec(V/'bcsp_ciua_analysis_v1.py'))
        try:c.need(False,'EXPECTED_CIUA_TRACEBACK_UNDER_ACTIVE_GUARD')
        except ValueError:detail=traceback.format_exc()
        assert 'EXPECTED_CIUA_TRACEBACK_UNDER_ACTIVE_GUARD' in detail and guard.fds
        js(O/'reader_child_result.json',dict(status='ACTIVE_POLICY_LOAD_AND_TRACEBACK_PASS',factory=list(factory),guard_open_before_traceback=True,real_payload_reads=0,CUDA=False))
    finally:guard.close()


def main():
    O.mkdir();start=time.monotonic();checks=[]
    def check(name,condition=True):
        if not condition:raise AssertionError(name)
        checks.append(dict(index=len(checks)+1,name=name,status='PASS'))
        print(json.dumps(checks[-1]),flush=True)
    try:
        torch.set_num_threads(2)
        old=builtins.__import__
        def no_numeric_import(name,*args,**kwargs):
            if name.split('.')[0] in ('numpy','torch'):raise AssertionError('non-inert import '+name)
            return old(name,*args,**kwargs)
        builtins.__import__=no_numeric_import
        try:
            c=load('ciua_capture_test',V/'bcsp_ciua_capture_v1.py');a=load('ciua_analysis_test',V/'bcsp_ciua_analysis_v1.py');e=load('ciua_entry_test',V/'bcsp_ciua_entry_v1.py')
        finally:builtins.__import__=old
        check('01 imports inert and no model/runtime/payload import')
        rows=rows840();a.validate_rows(rows);check('02 full840 roles and source counts')
        bad=copy.deepcopy(rows);bad[0]['source_id']='train:999'
        dup=copy.deepcopy(rows);dup[0]=dup[1].copy()
        leak=copy.deepcopy(rows);leak[0]['role']='development'
        check('03 identity duplicate and leakage rejected',all(reject(lambda x=x:a.validate_rows(x)) for x in (bad,dup,leak)))

        assets=read(A0/'frozen_local_asset_bindings_v1.json');hr=next(x['local'] for x in assets['shared'] if x['role']=='head');hb=Path(hr['path']).read_bytes()
        need_hash=hashlib.sha256(hb).hexdigest()==c.HEAD_SHA;assert need_hash
        hm=e.module('ciua_actual_frozen_head',hr)
        rng=np.random.default_rng(20261118);D=rng.normal(size=(8192,3)).astype('float32');F=rng.normal(size=(256,384)).astype('float32');z=rng.normal(size=1024).astype('float32');U=rng.uniform(size=(256,3)).astype('float32')
        head=hm.SPCGHead('G2',torch.from_numpy(U));model=Model(head,torch.from_numpy(F),torch.from_numpy(z)).eval()
        with torch.inference_mode():
            x,detail=head.describe(torch.from_numpy(D)[None],torch.from_numpy(D[:256])[None],torch.from_numpy(F)[None],torch.from_numpy(z)[None]);Q=head.net(x)[0].numpy().copy()
        check('04 actual frozen G2 source and real1416 input blocks',np.array_equal(x[0,:,:1024].numpy(),np.broadcast_to(z,(256,1024))))
        compact,state=c.capture(torch,np,model,torch.from_numpy(D)[None],hb)
        check('05 exact native Q and no FPS/query/decoder tail',model.tail==0 and np.array_equal(compact['Q'],Q))
        model.fail=True
        assert reject(lambda:c.capture(torch,np,model,torch.from_numpy(D)[None],hb));model.fail=False
        check('06 failure cleanup state RNG and hooks',not head._forward_hooks and not head._forward_pre_hooks and not head.net[0]._forward_pre_hooks and c.state(torch,np,model)==state)

        accessed=[]
        class NPZ:
            def __enter__(self):return self
            def __exit__(self,*x):pass
            def __getitem__(self,k):accessed.append(k);assert k=='partial';return D
        fake=types.SimpleNamespace(load=lambda *x,**y:NPZ(),float32=np.float32,isfinite=np.isfinite)
        original=e.exact;e.exact=lambda x:'ARTIFICIAL_ONLY'
        try:assert np.array_equal(e.read_D(fake,{'input':{}}),D)
        finally:e.exact=original
        check('07 prefix reader requests partial only',accessed==['partial'])
        check('08 shape dtype and frozen-source drift rejected',reject(lambda:c.compact(np,D,F[:20],F,z,Q)) and reject(lambda:c.Prefix(torch,head,hb+b' ')))
        F64=F.astype('float64');center=F64-F64.mean(1,keepdims=True);ln=center/np.sqrt((center**2).mean(1,keepdims=True)+1e-5)
        with torch.inference_mode():ref=torch.nn.functional.layer_norm(torch.from_numpy(F64),(384,),eps=1e-5).numpy()
        check('09 offline LN FP64 formula and stored FP32 summary',np.allclose(ln,ref,rtol=1e-12,atol=1e-12) and np.array_equal(compact['mF'],ln.mean(0).astype('float32')))
        blob=io.BytesIO()
        with torch.inference_mode():f=x[0,:,1024:1408].numpy().copy()
        np.savez_compressed(blob,F=F,f=f,z=z,Q=Q,x=x[0].numpy())
        cache_blob=blob.getvalue();cache_sha=hashlib.sha256(cache_blob).hexdigest();archive=O/'artificial_traces.tar.gz'
        reuse_rows=[r for fold in ('C','D') for r in rows if r['fold']==fold and r['role']=='development']
        chosen=[r for fold in ('C','D') for r in reuse_rows if r['fold']==fold][:0]
        chosen=[]
        for fold in ('C','D'):chosen.extend([r for r in reuse_rows if r['fold']==fold][:20])
        reuse=[]
        with tarfile.open(archive,'w:gz') as tf:
            for r in chosen:
                member='traces/'+r['run']+'__'+r['case_id']+'.npz';m=tarfile.TarInfo(member);m.size=len(cache_blob);tf.addfile(m,io.BytesIO(cache_blob));reuse.append(dict(run=r['run'],case_id=r['case_id'],member=member,trace=dict(sha256=cache_sha)))
        with tarfile.open(archive,'r:gz') as tf:cached=c.cached(np,D,tf,reuse[0]['member'],cache_sha)
        check('10 cached and fresh summaries exact same arithmetic',all(np.array_equal(compact[k],cached[k]) for k in compact))
        idx=detail['index'][0].numpy();freq=np.bincount(idx.ravel(),minlength=256)/(256*8)
        with torch.inference_mode():ln32=torch.nn.functional.layer_norm(torch.from_numpy(F),(384,),eps=1e-5).numpy()
        check('11 local mean is hit-frequency weighted F',np.allclose(f.astype('float64').mean(0),freq@ln32.astype('float64'),atol=2e-8))
        geom=c.geometry18(np,D);cov=np.cov(D.astype('float64'),rowvar=False,bias=True)
        target=a.targets(np,D,D);err=a.errors(np,target[None]+np.r_[.01,0,0,np.zeros(9)][None],target[None],np.array([100.]))
        check('12 D18 P2 layout and world centroid units',np.allclose(geom[3:9],cov[np.triu_indices(3)]) and abs(err[0,0]-1)<1e-12)
        pi=a.octants(np,np.array([[0,0,0],[1,-1,-1]],dtype=float),np.zeros(3));proj=a.simplex(np,np.array([[-1,-2,3,4,0,0,0,0.]]))
        check('13 moment octant boundary and simplex contracts',pi[7]==.5 and pi[1]==.5 and np.all(proj>=0) and abs(proj.sum()-1)<1e-12 and reject(lambda:a.moments(np,np.zeros((256,3)))))

        X=rng.normal(size=(20,7));Y=rng.normal(size=(20,12));src=['s'+str(i//5) for i in range(20)];fit=a.fit(np,X,Y,src)
        A=(X-fit['x_mean'])/fit['x_scale']/np.sqrt(20);B=(Y-fit['y_mean'])/fit['y_scale']/np.sqrt(20)
        dual=A.T@np.linalg.solve(A@A.T+np.eye(20),B)
        check('14 mean lambda1 primal dual and stationarity',np.allclose(fit['coefficient'],dual,atol=1e-12) and fit['stationarity']<1e-12)
        sep=np.c_[a.predict(np,a.fit(np,X,Y[:,:4],src),X),a.predict(np,a.fit(np,X,Y[:,4:],src),X)]
        check('15 combined12 equals separate4 and8',np.allclose(a.predict(np,fit,X),sep,atol=1e-12))
        XX=np.c_[X,np.ones(20)];YY=Y.copy();YY[:,3]=4
        ff=a.fit(np,XX,YY,src);pr=a.predict(np,ff,np.c_[X,np.ones(20)*100])
        check('16 constant columns train-only scaling and capacity records',np.all(pr[:,3]==4) and ff['constant_x'][-1] and 0<=ff['effective_df']<=7)
        train=[r for r in rows if r['fold']=='C' and r['role']=='train'];perm,info=a.permutation(np,train,'C')
        check('17 one source permutation preserves defect type blocks',len(set(perm.tolist()))==315 and all(train[i]['case_id'].split('__',2)[2]==train[j]['case_id'].split('__',2)[2] for i,j in enumerate(perm)) and info==a.permutation(np,train,'C')[1])
        bt=a.bootstrap(np,'C');cmp=a.compare(np,np.ones((21,3)),np.zeros((21,3)),bt)
        check('18 source21 bootstrap fixed2000 and shared indices',bt.shape==(2000,21) and bt.min()>=0 and bt.max()<21 and cmp['CI95']==[[1.,1.,1.],[1.,1.,1.]])
        base=np.tile([10.,.1,.5],(21,1));win=base-np.array([3.,0.,.1]);folds={k:dict(octant_informative=True,source_errors=dict(D18=base,Q=base,z=base,zF=win,zf=win)) for k in ('C','D')}
        gates=a.decide(np,folds);boundary=a.pass_gate(np,base-np.array([2.,0.,.03]),base,2.)
        check('19 z failure does not hide F and inclusive gates',not gates['z']['I_PASS'] and gates['zF']['I_PASS'] and gates['zF']['aggregation_increment'] and boundary)
        calls=[];head.eval();vals,responses=c.shadow(torch,np,head,x[0].numpy(),Q,100.,lambda arm,status:calls.append((arm,status)))
        check('20 NMR exact N, six journal events and state unchanged',np.array_equal(vals['N'],Q) and len(calls)==6 and responses['N']['max_mm']==0 and all(np.isfinite(v).all() for v in vals.values()))

        # Real authorization parser on control-only fixtures; no real arrays are read.
        original_rows=read(A0/'CIUA_model_case_manifest_840_v1.json')['records']
        control_rows=[]
        for r in original_rows:
            rr=copy.deepcopy(r);rr['input']=dict(path='NOT_OPENED',bytes=0,sha256=r['input_sha256']);control_rows.append(rr)
        scope=rec(A0/'implementation_scope_v1.json');protocol=read(A0/'implementation_scope_v1.json')['plan']
        qr=dict(schema='ciua-execution-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',execution_authorized=False,mode='analysis',counts=e.COUNTS['analysis'],protocol=protocol,implementation_scope=scope,implementation=dict(capture=rec(V/'bcsp_ciua_capture_v1.py'),analysis=rec(V/'bcsp_ciua_analysis_v1.py')),entry=rec(V/'bcsp_ciua_entry_v1.py'),limits=dict(wall_seconds=7200,RSS_bytes=8*1024**3,output_bytes=1024**3),attempts=1,automatic_retry=False,resume=False,all_manifest=rec(A0/'CIUA_model_case_manifest_840_v1.json'),reuse_manifest=rec(A0/'TRACE_G2_reuse_map_40_v1.json'),rows=control_rows)
        qp=O/'artificial_request.json';js(qp,qr);qb=rec(qp)
        ap=O/'artificial_authorization.json';js(ap,dict(schema='ciua-authorization-v1',request_sha256=qb['sha256'],explicit_user_authorization=True,user_authorization_text='ARTIFICIAL CPU CONTROL ONLY'))
        rp=O/'artificial_runtime.json';js(rp,dict(schema='ciua-runtime-v1',request_sha256=qb['sha256'],authorization_sha256=rec(ap)['sha256']))
        assert e.authorize(qb,rec(ap),rec(rp))['mode']=='analysis'
        bad=read(ap);bad['runtime_sha256']='reverse';bp=O/'bad_reverse.json';js(bp,bad)
        check('21 actual authorize one-way positive and reverse rejected',reject(lambda:e.authorize(qb,rec(bp),rec(rp))))

        child=subprocess.run([sys.executable,'-I','-B',str(Path(__file__)),'--reader-child'],capture_output=True,timeout=60)
        (O/'reader_child_stdout.bin').write_bytes(child.stdout);(O/'reader_child_stderr.bin').write_bytes(child.stderr)
        check('22 actual inherited guarded source loading and traceback',child.returncode==0 and read(O/'reader_child_result.json')['status']=='ACTIVE_POLICY_LOAD_AND_TRACEBACK_PASS')
        qpbad=O/'bad_request.json';bad=copy.deepcopy(qr);bad['counts']['solves']=15;js(qpbad,bad)
        rc=e.main(['--request',str(qpbad),'--request-sha256',rec(qpbad)['sha256'],'--authorization',str(ap),'--authorization-sha256',rec(ap)['sha256'],'--runtime',str(rp),'--runtime-sha256',rec(rp)['sha256']])
        # Four-file archive verification on an isolated artificial output.
        packdir=O/'pack_fixture';packdir.mkdir();e.save(packdir/'failure.json',dict(status='ARTIFICIAL_FAIL_STOP'));pack=e.pack(packdir)
        with tarfile.open(pack['path'],'r:gz') as tf:packed=tf.extractfile('failure.json').read()
        check('23 nonzero failure and immutable archived evidence',rc==1 and hashlib.sha256(packed).hexdigest()==pack['members'][0]['sha256'])

        point=O/'artificial_point.npz'
        with point.open('xb') as file:np.savez_compressed(file,partial=D,implant=D+np.array([.1,.2,.3],dtype=np.float32))
        point_rec=rec(point);summary=O/'artificial_summary.npz'
        with summary.open('xb') as file:np.savez_compressed(file,**compact)
        feature_rec=rec(summary);reusekeys={(r['run'],r['case_id']) for r in reuse};fresh=[]
        for r in rows:
            r['input']=point_rec.copy()
            if (r['run'],r['case_id']) in reusekeys:
                rr=next(v for v in reuse if (v['run'],v['case_id'])==(r['run'],r['case_id']));rr['input_sha256']=point_rec['sha256']
            else:fresh.append(dict(**r,feature=feature_rec))
        allp=O/'artificial_all_manifest.json';freshp=O/'artificial_fresh_manifest.json';reusep=O/'artificial_reuse_manifest.json'
        js(allp,dict(records=[dict(**{k:v for k,v in r.items() if k!='input'},input_sha256=r['input']['sha256']) for r in rows]));js(freshp,dict(records=fresh));js(reusep,dict(records=reuse))
        aq=dict(rows=rows,all_manifest=rec(allp),fresh_feature_index=rec(freshp),reuse_manifest=rec(reusep),trace_archive=rec(archive))
        out=O/'complete_artificial_analysis';out.mkdir();b=Budget();done=e.run_analysis(np,aq,out,c,a,b)
        full=read(out/'analysis_full.json')
        check('24 complete840 artificial reader16 fits two folds no model',done['records']==840 and done['solves']==16 and set(full['folds'])=={'C','D'} and len(b.records)==841 and all(len(f['rows'])==105 and len(f['source_order'])==21 for f in full['folds'].values()))
        assert len(checks)==24
        js(O/'result.json',dict(status='CIUA_ARTIFICIAL_CPU24_PASS',checks=checks,seconds=time.monotonic()-start,torch=torch.__version__,numpy=np.__version__,real_checkpoint_loads=0,real_point_array_reads=0,real_model_forward=0,real_ridge_fits=0,server_operations=0,CUDA_initialized=torch.cuda.is_initialized(),artificial_full_reader_rows=840,artificial_fixed_fits=16))
        print('CIUA_ARTIFICIAL_CPU24_PASS',flush=True)
    except BaseException as exc:
        js(O/'failure.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc(),seconds=time.monotonic()-start))
        print(traceback.format_exc(),file=sys.stderr,flush=True);return 1
    return 0


if __name__=='__main__':
    if sys.argv[1:]==['--reader-child']:reader_child()
    else:sys.exit(main())
