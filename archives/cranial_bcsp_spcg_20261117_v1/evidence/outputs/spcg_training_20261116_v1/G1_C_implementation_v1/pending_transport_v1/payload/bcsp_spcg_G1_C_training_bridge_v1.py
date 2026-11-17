"""Keep the frozen training lifecycle; add same-forward observations only."""
import hashlib,json,os
from pathlib import Path

LOG_STEPS=(1,39,390,1950,3900)
def need(v,s):
    if not v:raise ValueError(s)
def dispatch(q,model,runtime,selected,fold,plan,helper,budget,observe,*,device='cuda:0',artificial_cpu=False,knn_enable=lambda:None):
    need((device=='cpu') is artificial_cpu,'CPU only explicit fixture')
    need(bool(model.f0_evidence['artificial_fixture']) is artificial_cpu,'production/fixture identity')
    need(hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest()==q['implementation']['training_runtime']['sha256'],'frozen lifecycle')
    need(q['arm']=='G1' and q['fold']=='C','first run only')
    if not artificial_cpu:
        h=hashlib.sha256()
        for n,t in model.state_dict().items():h.update(n.encode());h.update(t.detach().cpu().contiguous().numpy().tobytes())
        need(h.hexdigest()==q['expected_initial_state_sha256'],'CUDA admitted initial state (same fingerprint algorithm)')
    dataset=runtime.BCSPDataset(q['data_root'],selected,fold['train_sources'],8192)
    tracker=dict(step=0,pending=None,losses={},Q=None)
    def forward(module,args,ret):
        need(module.training and len(args)==1 and tracker['pending'] is None,'one D-only forward')
        Q,P=ret[0],ret[-1]
        need(Q.shape[1:]==(256,3) and P.shape[1:]==(8192,3),'8k output')
        import torch
        with torch.no_grad():
            tracker['pending']={n:dict(centroid=t.detach().mean(1).cpu().tolist(),radius=(t.detach()-t.detach().mean(1)[:,None]).square().sum(-1).mean(1).sqrt().cpu().tolist()) for n,t in [('coarse',Q),('dense',P)]}
        if tracker['step']+1 in LOG_STEPS:Q.retain_grad();tracker['Q']=Q;tracker['pending']['diversity']=observe.geometry(Q)
    def loss(name):
        def hook(m,args,value):need(name not in tracker['losses'],'one loss '+name);tracker['losses'][name]=float(value.detach())
        return hook
    old_after=budget.after_step;old_final=budget.before_final
    def after(step):
        need(step==tracker['step']+1 and tracker['pending'] is not None and set(tracker['losses'])=={'coarse_CD','dense_CD'},'step observations')
        row=dict(step=step,epoch=(step-1)//39,batch=(step-1)%39,case_ids=plan['epochs'][(step-1)//39]['batches'][(step-1)%39],frame='D_only_normalized',geometry=tracker['pending'],loss_components=tracker['losses'])
        if step in LOG_STEPS:row['total_loss_Q_gradient']=observe.Q_gradient_record(tracker['Q'])
        with (Path(q['output'])/'SPCG_geometry.jsonl').open('x' if step==1 else 'a',encoding='utf-8') as f:f.write(json.dumps(row,allow_nan=False)+'\n');f.flush()
        tracker.update(step=step,pending=None,losses={},Q=None);old_after(step)
    def final():need(tracker['step']==3900 and tracker['pending'] is None,'3900 observations');old_final()
    hooks=[model.register_forward_hook(forward),model.loss_func.register_forward_hook(loss('coarse_CD')),model.fine_loss_func.register_forward_hook(loss('dense_CD'))]
    budget.after_step=after;budget.before_final=final
    try:
        return runtime.train_lifecycle(model,lambda epoch:runtime.make_loader(dataset,plan,epoch),selected,plan,q['output'],device=device,numeric_check=helper.assert_numeric,resources=budget,knn_enable=knn_enable,state_fingerprint=helper.state_sha)
    finally:
        for h in hooks:h.remove()
        budget.after_step=old_after;budget.before_final=old_final
