"""Bounded FP64 CPU gradient differences. Torch is supplied, never imported here."""
import math

GROUPS=('SSM_mixer','other_encoder','grouper','coarse_head','decoder','other')
CHUNK=65536
HEADROOM=64*1024**2

def require(ok,text):
    if not ok:raise RuntimeError(text)

def group_for(name):
    if '.attn.mixer.' in name:return 'SSM_mixer'
    for prefix,group in (('base_model.encoder.','other_encoder'),('base_model.grouper.','grouper'),('base_model.coarse_pred.','coarse_head'),('base_model.decoder.','decoder')):
        if name.startswith(prefix):return group
    return 'other'

def empty():
    return dict(elements=0,numeric_different=0,zero_to_nonzero=0,nonzero_to_zero=0,sum_abs_diff=0.,sum_squared_diff=0.,sum_squared_a=0.,sum_squared_b=0.,dot=0.,max_abs_diff=0.,max_abs_a=0.,max_abs_b=0.,maximum_location=None,parameter_tensors=0,present_tensors=0,byte_different_tensors=0)

SUM_KEYS=('elements','numeric_different','zero_to_nonzero','nonzero_to_zero','sum_abs_diff','sum_squared_diff','sum_squared_a','sum_squared_b','dot','parameter_tensors','present_tensors','byte_different_tensors')
def merge(dst,src):
    old_count=dst['elements']
    for k in SUM_KEYS:dst[k]+=src[k]
    if src['elements'] and (not old_count or src['max_abs_diff']>dst['max_abs_diff']):
        dst['max_abs_diff']=src['max_abs_diff'];dst['maximum_location']=src['maximum_location']
    for k in ('max_abs_a','max_abs_b'):dst[k]=max(dst[k],src[k])

def finish(s):
    r=dict(s);n=s['elements'];na=math.sqrt(s['sum_squared_a']);nb=math.sqrt(s['sum_squared_b']);nd=math.sqrt(s['sum_squared_diff'])
    require(all(math.isfinite(v) for v in s.values() if isinstance(v,float)),'nonfinite FP64 aggregate')
    denom=max(na,nb)
    raw=s['dot']/(na*nb) if na and nb else None
    r.update(l2_a=na,l2_b=nb,l2_difference=nd,mean_abs_difference=s['sum_abs_diff']/n if n else None,rms_difference=nd/math.sqrt(n) if n else None,rms_a=na/math.sqrt(n) if n else None,rms_b=nb/math.sqrt(n) if n else None,relative_l2=nd/denom if denom else (0. if nd==0 else None),relative_l2_reason=None if denom else 'both_zero',cosine_raw=raw,cosine_display=None if raw is None else min(1.,max(-1.,raw)),cosine_reason='zero_norm' if raw is None else None,numeric_different_fraction=s['numeric_different']/n if n else None)
    return r

def presence(model):return {n:p.grad is not None for n,p in model.named_parameters()}

def capture(torch,model,expected_presence,prepare,poll):
    params=dict(model.named_parameters())
    require(presence(model)==expected_presence,'gradient presence differs from frozen baseline')
    sizes=[p.grad.numel()*p.grad.element_size() for p in params.values() if p.grad is not None]
    prepare(sum(sizes),HEADROOM+2*max(sizes,default=0))
    reference={}
    for n,p in params.items():
        poll()
        if p.grad is None:reference[n]=None;continue
        require(p.grad.dtype==torch.float32 and bool(torch.isfinite(p.grad).all()),'finite FP32 gradient '+n)
        reference[n]=p.grad.detach().cpu().contiguous().clone()
    poll()
    return reference

def quantify(torch,reference,model,expected_presence,tensor_sha,write_row,poll,chunk=CHUNK):
    require(isinstance(chunk,int) and 0<chunk<=CHUNK,'bounded gradient chunk')
    params=dict(model.named_parameters())
    require(set(reference)==set(params) and presence(model)==expected_presence,'gradient presence/name mismatch')
    total=empty();groups={g:empty() for g in GROUPS}
    for name,p in params.items():
        poll();a=reference[name];g=group_for(name);s=empty();s['parameter_tensors']=1
        row=dict(name=name,group=g,shape=list(p.shape),dtype=str(p.dtype),parameter_elements=p.numel(),presence_a=a is not None,presence_b=p.grad is not None,nonfinite_elements_a=0,nonfinite_elements_b=0)
        if a is None:
            require(p.grad is None,'new gradient '+name)
            row.update(sha256_a=None,sha256_b=None,bytes_equal=True,numerically_equal=True,absence='allowed_by_frozen_v3_presence',statistics=None)
        else:
            b=p.grad.detach();require(a.shape==b.shape and a.dtype==b.dtype==torch.float32,'gradient shape/dtype '+name)
            ha=tensor_sha(a);hb=tensor_sha(b);s['byte_different_tensors']=int(ha!=hb);s['present_tensors']=1
            af=a.reshape(-1);bf=b.reshape(-1)
            for start in range(0,a.numel(),chunk):
                poll();aa=af[start:start+chunk].to(dtype=torch.float64);bb=bf[start:start+chunk].cpu().to(dtype=torch.float64)
                require(bool(torch.isfinite(aa).all()) and bool(torch.isfinite(bb).all()),'nonfinite gradient '+name)
                d=bb-aa;ad=d.abs();i=int(ad.argmax());value=float(ad[i]);old=s['elements']
                s['elements']+=len(aa);s['numeric_different']+=int((aa!=bb).sum());s['zero_to_nonzero']+=int(((aa==0)&(bb!=0)).sum());s['nonzero_to_zero']+=int(((aa!=0)&(bb==0)).sum())
                s['sum_abs_diff']+=float(ad.sum());s['sum_squared_diff']+=float((d*d).sum());s['sum_squared_a']+=float((aa*aa).sum());s['sum_squared_b']+=float((bb*bb).sum());s['dot']+=float((aa*bb).sum())
                if not old or value>s['max_abs_diff']:
                    s['max_abs_diff']=value;s['maximum_location']=dict(parameter=name,flat_index=start+i,a=float(aa[i]),b=float(bb[i]))
                s['max_abs_a']=max(s['max_abs_a'],float(aa.abs().max()));s['max_abs_b']=max(s['max_abs_b'],float(bb.abs().max()))
            row.update(sha256_a=ha,sha256_b=hb,bytes_equal=ha==hb,numerically_equal=s['numeric_different']==0,statistics=finish(s))
        write_row(row);merge(total,s);merge(groups[g],s)
    poll()
    return dict(global_statistics=finish(total),groups={g:finish(s) for g,s in groups.items()},method='CPU_FP64_elementwise_sums_not_tensor_average',chunk_elements=chunk,raw_gradient_arrays_saved=False)
