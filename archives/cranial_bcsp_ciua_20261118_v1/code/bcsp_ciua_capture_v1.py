"""CIUA read-only prefix observation; imports never load torch, numpy or payloads."""
import hashlib
import random

HEAD_SHA = '687c123ae7d0769c9ee89e2067367ff7fc2762f66bf47a814bf077ac68c59d3b'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def array(np, value, shape, dtype=None):
    a = np.asarray(value)
    need(a.shape == shape and np.isfinite(a).all(), 'finite array shape '+str(shape))
    if dtype is not None:
        need(a.dtype == dtype, 'array dtype')
    return a


def geometry18(np, D):
    p = array(np, D, (8192, 3)).astype(np.float64)
    c = p-p.mean(0)
    return np.r_[p.mean(0), (c.T@c/len(p))[np.triu_indices(3)],
                 np.quantile(p, [.1,.5,.9], axis=0, method='linear').T.ravel()]


def compact(np, D, F, f, z, Q):
    """Same offline FP64 arithmetic for cached and fresh FP32 captures."""
    D = array(np,D,(8192,3),np.float32)
    F = array(np,F,(256,384),np.float32).astype(np.float64)
    f = array(np,f,(256,384),np.float32).astype(np.float64)
    z = array(np,z,(1024,),np.float32)
    Q = array(np,Q,(256,3),np.float32)
    centered = F-F.mean(1,keepdims=True)
    ln = centered/np.sqrt((centered*centered).mean(1,keepdims=True)+1e-5)
    out = dict(z=z.copy(),mF=ln.mean(0).astype(np.float32),
               mf=f.mean(0).astype(np.float32),Q=Q.copy(),D18=geometry18(np,D))
    need(all(np.isfinite(x).all() for x in out.values()), 'finite compact summary')
    return out


def state(torch, np, model):
    h = hashlib.sha256()
    for k,v in sorted(model.state_dict().items()):
        h.update(k.encode());h.update(str(v.dtype).encode());h.update(str(tuple(v.shape)).encode())
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    cuda = torch.cuda.is_initialized()
    return dict(parameters_buffers=h.hexdigest(),modes=[(n,m.training) for n,m in model.named_modules()],
                torch_CPU=torch.get_rng_state().numpy().tobytes().hex(),
                torch_CUDA=[x.cpu().numpy().tobytes().hex() for x in torch.cuda.get_rng_state_all()] if cuda else [],
                python=repr(random.getstate()),numpy=repr(np.random.get_state()))


class _PrefixComplete(BaseException):
    def __init__(self, owner):
        self.owner = owner


class Prefix:
    def __init__(self, torch, head, source_bytes):
        need(hashlib.sha256(source_bytes).hexdigest()==HEAD_SHA,'exact frozen SPCGHead bytes')
        need(head.arm=='G2' and head.net[0].in_features==1416, 'actual G2 H consumer')
        self.t,self.h=torch,head
        self.hooks=[];self.saved=None;self.raw=None;self.x=None
        self.calls=dict(input=0,x=0,Q=0)

    def __enter__(self):
        h=self.h
        self.saved=(h.capture,h.last,h.last_q)
        h.capture=False
        try:
            self.hooks.append(h.register_forward_pre_hook(self.inputs))
            self.hooks.append(h.net[0].register_forward_pre_hook(self.head_input))
            self.hooks.append(h.register_forward_hook(self.output))
            return self
        except BaseException:
            self.__exit__();raise

    def inputs(self, module, args):
        self.calls['input']+=1
        need(len(args)==4 and self.calls['input']==1,'one actual D/S/F/z call')
        self.raw=tuple(v.detach().clone() for v in args)

    def head_input(self, module, args):
        self.calls['x']+=1
        need(len(args)==1 and self.calls['x']==1,'one actual x consumer')
        self.x=args[0].detach().clone()

    def output(self, module, args, Q):
        t=self.t;self.calls['Q']+=1
        need(self.calls==dict(input=1,x=1,Q=1),'one prefix call')
        D,S,F,z=self.raw
        expected=[(D,(1,8192,3)),(S,(1,256,3)),(F,(1,256,384)),(z,(1,1024)),(self.x,(1,256,1416)),(Q,(1,256,3))]
        need(all(tuple(v.shape)==shape and v.dtype==t.float32 and bool(t.isfinite(v).all()) for v,shape in expected),'actual finite FP32 prefix tensors')
        need(t.equal(self.x[...,:1024],z[:,None].expand(-1,256,-1)),'actual z input block')
        self.result=dict(F=F[0].cpu().contiguous().numpy().copy(),
                         f=self.x[0,:,1024:1408].cpu().contiguous().numpy().copy(),
                         z=z[0].cpu().contiguous().numpy().copy(),Q=Q[0].detach().cpu().contiguous().numpy().copy())
        raise _PrefixComplete(self)

    def __exit__(self,*exc):
        for hook in self.hooks:
            hook.remove()
        self.hooks=[]
        if self.saved is not None:
            self.h.capture,self.h.last,self.h.last_q=self.saved


def capture(torch, np, model, D, head_bytes):
    need(not any(m.training for m in model.modules()),'eval mode required; no mode mutation')
    need(D.dtype==torch.float32 and tuple(D.shape)==(1,8192,3),'D-only input')
    before=state(torch,np,model)
    observer=Prefix(torch,model.base_model.spcg_head,head_bytes)
    try:
        with observer:
            try:
                with torch.inference_mode():
                    model(D)
            except _PrefixComplete as done:
                need(done.owner is observer,'foreign prefix stop')
            else:
                raise ValueError('head not reached; no valid prefix')
    finally:
        need(state(torch,np,model)==before,'model/buffer/mode/RNG mutation')
    return compact(np,D[0].detach().cpu().numpy(),**observer.result),before


def cached(np, D, archive, member, expected_sha):
    """Archive context supplied by caller; only frozen named member, no extraction."""
    import io
    m=archive.getmember(member)
    need(m.isfile() and not member.startswith('/') and '..' not in member.split('/'),'regular trace member')
    with archive.extractfile(m) as stream:
        blob=stream.read(2*1024**2+1)
    need(len(blob)<=2*1024**2 and hashlib.sha256(blob).hexdigest()==expected_sha,'exact bounded trace bytes')
    with np.load(io.BytesIO(blob),allow_pickle=False) as z:
        x=array(np,z['x'],(256,1416),np.float32)
        f=array(np,z['f'],(256,384),np.float32)
        zg=array(np,z['z'],(1024,),np.float32)
        need(np.array_equal(x[:,1024:1408],f) and np.array_equal(x[:,:1024],np.broadcast_to(zg,(256,1024))),'cached actual x blocks')
        return compact(np,D,z['F'],f,zg,z['Q'])


def shadow(torch,np,head,x,native_Q,scale,on_call=None):
    array(np,x,(256,1416),np.float32);array(np,native_Q,(256,3),np.float32)
    need(scale>0 and not any(m.training for m in head.modules()),'shadow positive scale / eval')
    before=state(torch,np,head);outputs={};responses={}
    try:
        with torch.inference_mode():
            for arm in ('N','M','R'):
                y=x.copy()
                if arm=='M':y[:,1024:1408]=x[:,1024:1408].astype(np.float64).mean(0).astype(np.float32)
                if arm=='R':y[:,1024:1408]=np.roll(x[:,1024:1408],-1,axis=0)
                need(np.array_equal(y[:,:1024],x[:,:1024]) and np.array_equal(y[:,1408:],x[:,1408:]),'shadow non-f blocks unchanged')
                if on_call is not None:on_call(arm,'CLAIMED_BEFORE_HEAD')
                value=head.net(torch.from_numpy(y)).detach().cpu().numpy()
                if on_call is not None:on_call(arm,'HEAD_RETURNED')
                outputs[arm]=array(np,value,(256,3),np.float32).copy()
                if arm=='N':
                    diff=float(np.abs(value.astype(np.float64)-native_Q).max()*scale)
                    need(np.allclose(value,native_Q,rtol=2e-5,atol=2e-6) and diff<=.01,'shadow N incomparable')
                displacement=np.linalg.norm((value-outputs['N']).astype(np.float64),axis=1)*scale
                responses[arm]=dict(mean_mm=float(displacement.mean()),median_mm=float(np.median(displacement)),p95_mm=float(np.quantile(displacement,.95,method='linear')),max_mm=float(displacement.max()),f_delta_mean=float(np.linalg.norm((y[:,1024:1408]-x[:,1024:1408]).astype(np.float64),axis=1).mean()))
    finally:
        need(state(torch,np,head)==before,'shadow state/RNG mutation')
    return outputs,responses
