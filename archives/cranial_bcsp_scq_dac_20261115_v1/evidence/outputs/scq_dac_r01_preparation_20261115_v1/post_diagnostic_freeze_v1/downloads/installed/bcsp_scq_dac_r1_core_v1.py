"""Frozen-weight R1 only. Inert import; no training, data loading, GT or optimizer."""
import hashlib
from collections import Counter

DEFECTS=('bilateral','frontoorbital','parietotemporal','random_1','random_2')
FIXED=(('C','012','parietotemporal'),('C','025','parietotemporal'),
       ('C','053','frontoorbital'),('D','069','random_2'),('D','087','frontoorbital'),
       ('C','025','random_2'),('D','008','frontoorbital'))
COUNTS=dict(native=20,decoder_only=40,decoder=60,h1_new=20,h1_old=20,first_head=20)

def require(ok,message):
    if not ok:raise RuntimeError(message)

def select_cases(index):
    candidates=[r for r in index['inputs'] if r['run'] in ('Requery_C','Requery_D')]
    require(len(candidates)==210 and len({(r['fold'],r['case_id']) for r in candidates})==210,'210 unique Requery inputs')
    fixed={(f,'train__'+s+'__'+t) for f,s,t in FIXED}
    require(fixed<={(r['fold'],r['case_id']) for r in candidates},'all seven fixed cases present')
    selected=[]
    for fold in 'CD':
        for defect in DEFECTS:
            cell=[r for r in candidates if r['fold']==fold and r['defect_type']==defect]
            require(len(cell)==21 and len({r['source_id'] for r in cell})==21,'21 development sources per cell')
            chosen=[r for r in cell if (fold,r['case_id']) in fixed]
            remaining=[r for r in cell if (fold,r['case_id']) not in fixed]
            def key(r):return hashlib.sha256(('SCQ_DAC_R1_v2|'+fold+'|'+r['source_id']+'|'+defect).encode()).hexdigest()
            chosen+=sorted(remaining,key=lambda r:(key(r),r['case_id']))[:2-len(chosen)]
            for r in sorted(chosen,key=lambda r:r['case_id']):
                row={k:r[k] for k in ('run','fold','case_id','source_id','defect_type','input','normalization','normalization_source','n_input','n_output')}
                row['selection']='PREDECLARED_STRESS_CASE' if (fold,r['case_id']) in fixed else 'SCORE_BLIND_HASH_COMPLETION'
                row['selection_hash']=key(r);selected.append(row)
    require(len(selected)==20 and Counter((r['fold'],r['defect_type']) for r in selected)==Counter({(f,t):2 for f in 'CD' for t in DEFECTS}),'exact balanced20')
    return selected

class Calls:
    def __init__(self,journal=lambda *a:None):self.counts={k:0 for k in COUNTS};self.journal=journal
    def claim(self,key,case):
        require(key in COUNTS and self.counts[key]<COUNTS[key],'exhausted '+key)
        self.counts[key]+=1;self.journal(key,case,dict(self.counts))

def combine(torch,u,v):
    require(u.shape==v.shape and u.shape[-1]==3 and u.dtype==v.dtype==torch.float32,'proposal shape/dtype')
    require(bool(torch.isfinite(u).all()) and bool(torch.isfinite(v).all()),'finite proposals')
    nu=u.norm(dim=-1,keepdim=True);nv=v.norm(dim=-1,keepdim=True)
    valid=(nu>1e-6)&(nv>1e-6)
    safe=((u/nu.clamp_min(1e-6))*(v/nv.clamp_min(1e-6))).sum(-1,keepdim=True).clamp(-1,1)
    c=torch.where(valid,safe,torch.zeros_like(safe))
    a=(0.5+0.5*c.clamp_min(0)).detach()
    return (u+v)*0.5,a*v+(1-a)*u,dict(nu=nu,nv=nv,valid=valid,c=c,a=a)

def old_descriptor(torch,M,F,z,Q1,N0):
    require(M.shape==Q1.shape==(1,256,3) and F.shape==(1,256,384) and z.shape==(1,1024),'actual Memory shapes')
    require(N0.shape==(1,256,8) and N0.dtype==torch.int64 and bool(((N0>=0)&(N0<256)).all()),'N0 identity')
    batch=torch.arange(1,device=M.device)[:,None,None]
    nf=torch.nn.functional.layer_norm(F,(384,),eps=1e-5)[batch,N0]
    d=M[batch,N0]-Q1[:,:,None,:];mu=d.mean(2)
    sigma=((d-mu[:,:,None,:]).square().mean(2)+1e-6).sqrt()
    rho=d.norm(dim=-1).mean(2,keepdim=True)
    h=torch.cat((z[:,None,:].expand(-1,256,-1),nf.mean(2),nf.max(2).values,Q1,mu,sigma,rho),-1)
    require(h.shape==(1,256,1802) and bool(torch.isfinite(h).all()),'old context at current Q1')
    return h

def dense_head(torch,model,q,Q):
    require(model.decoder_type=='fc' and model.factor==32,'FC32 only')
    global_feature=model.increase_dim(q.transpose(1,2)).transpose(1,2).max(1)[0]
    h=torch.cat((global_feature[:,None,:].expand(-1,256,-1),q,Q),-1)
    offsets=model.decode_head(model.reduce_map(h))
    require(offsets.shape==(1,256,32,3),'native FC offsets')
    p=(offsets+Q[:,:,None,:]).reshape(1,8192,3)
    require(bool(torch.isfinite(p).all()),'finite dense')
    return p

def decode_only(torch,model,M,F,z,Q,calls,case):
    """Actual mlp_query -> LQI decoder -> exact mother FC. Never whole model/backbone."""
    b=model.base_model;handles=[];seen=dict(decoder=0,query=0,head=0)
    def forbidden(*a):raise RuntimeError('backbone/first/RF execution inside decoder-only')
    def counter(key):
        def hook(*a):seen[key]+=1
        return hook
    try:
        for obj in (model,b,b.encoder,b.coarse_pred,b.scq,b.rf):handles.append(obj.register_forward_pre_hook(forbidden))
        for obj,key in ((b.decoder,'decoder'),(b.mlp_query,'query'),(model.decode_head,'head')):handles.append(obj.register_forward_pre_hook(counter(key)))
        calls.claim('decoder_only',case);calls.claim('decoder',case)
        q=b.mlp_query(torch.cat((z[:,None,:].expand(-1,256,-1),Q),-1))
        q=b.decoder(q=q,v=F,q_pos=Q,v_pos=M)
        p=dense_head(torch,model,q,Q)
        require(seen==dict(decoder=1,query=1,head=1),'exact suffix consumers')
        return p
    finally:
        for handle in handles:handle.remove()

def diagnose_case(torch,model,x,calls,case):
    require(not torch.is_grad_enabled() and not any(m.training for m in model.modules()),'eval inference only')
    require(x.shape==(1,8192,3) and x.dtype==torch.float32 and bool(torch.isfinite(x).all()),'D8192 only')
    b=model.base_model;require(b.rf.variant=='RF-Requery','frozen Requery required')
    require(not b.use_denoise and b.query_selection=='learned_only' and b.scqr_query_conditioner is None,'fixed generation path')
    captures={};handles=[]
    def first_pre(module,args):
        calls.claim('first_head',case);require('Q0' not in captures,'one first head')
        captures['Q0']=args[3].detach().clone()
    def rf_pre(module,args):
        calls.claim('h1_new',case);require('Q1' not in captures,'one RF head')
        for k,t in zip(('M','F','z','Q1','N0'),args):captures[k]=t.detach().clone()
    def rf_post(module,args,result):
        Q2,info=result;captures.update(Q2_R=Q2.detach().clone(),v=info['delta1'].detach().clone(),N1=info['indices'].detach().clone())
    def decoder_pre(*a):calls.claim('decoder',case)
    try:
        handles+=[b.scq.register_forward_pre_hook(first_pre),b.rf.register_forward_pre_hook(rf_pre),b.rf.register_forward_hook(rf_post),b.decoder.register_forward_pre_hook(decoder_pre)]
        calls.claim('native',case);Q2,P=model(x)
    finally:
        for handle in handles:handle.remove()
    require(set(captures)=={'Q0','M','F','z','Q1','N0','Q2_R','v','N1'},'complete single-native capture')
    require(torch.equal(Q2,captures['Q2_R']) and Q2.shape==(1,256,3) and P.shape==(1,8192,3),'native coarse handoff')
    M,F,z,Q1,N0=(captures[k] for k in ('M','F','z','Q1','N0'))
    calls.claim('h1_old',case)
    u=b.rf.V2(torch.nn.functional.gelu(b.rf.V1(old_descriptor(torch,M,F,z,Q1,N0)),approximate='none'))
    da,dd,agreement=combine(torch,u,captures['v'])
    QA,QD=Q1+da,Q1+dd
    PA=decode_only(torch,model,M,F,z,QA,calls,case+':Average')
    PD=decode_only(torch,model,M,F,z,QD,calls,case+':DAC')
    result={**captures,'u':u,'delta0':Q1-captures['Q0'],'delta_A':da,'delta_D':dd,'Q2_A':QA,'Q2_D':QD,
            'P_R':P,'P_A':PA,'P_D':PD,**agreement}
    require(all(bool(torch.isfinite(t).all()) for t in result.values()),'finite full diagnostic')
    b._scq_last_info=None
    return {k:t.detach().cpu().numpy().copy() for k,t in result.items()}
