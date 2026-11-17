"""Isolated BCSP lifecycle; no automatic execution, no legacy runner mutation."""
import hashlib
import json
import random
from pathlib import Path
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from tools.bcsp_adapter import Contract, UpdateGuard, load_case

STAGE='BCSP_INPUT_DENSITY_V1'

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

class BCSPDataset(Dataset):
    def __init__(self, root, records, sources, n_input):
        if n_input not in (8192,16384):raise ValueError('input count')
        if len(records)!=315 or len(sources)!=63:raise ValueError('source/case counts')
        ids=[r['case_id'] for r in records]
        if len(set(ids))!=315:raise ValueError('duplicate case')
        counts={s:0 for s in sources}
        for r in records:
            if r['source_id'] not in counts:raise ValueError('source outside train fold')
            counts[r['source_id']]+=1
        if set(counts.values())!={5}:raise ValueError('five cases per source required')
        self.root=root;self.records=tuple(records);self.sources=frozenset(sources);self.n_input=n_input
    def __len__(self):return len(self.records)
    def __getitem__(self,i):
        x,y=load_case(self.root,self.records[i],self.sources,self.n_input,training=True)
        return torch.from_numpy(x),torch.from_numpy(y)

def make_loader(dataset,epoch):
    if len(dataset)!=315 or not 0<=epoch<100:raise ValueError('loader contract')
    g=torch.Generator(device='cpu').manual_seed(epoch)
    return DataLoader(dataset,batch_size=8,shuffle=True,drop_last=True,num_workers=0,generator=g)

def make_optimizer(model):
    decay=[];no_decay=[]
    for name,p in model.named_parameters():
        if p.requires_grad:(no_decay if p.ndim==1 or name.endswith('.bias') else decay).append(p)
    return torch.optim.AdamW([{'params':no_decay,'weight_decay':0.},
                             {'params':decay,'weight_decay':.0005}],lr=.0001)

def set_bn_momentum(model,epoch):
    value=max(.9*.5**(epoch/21),.01)
    for module in model.modules():
        if isinstance(module,torch.nn.modules.batchnorm._BatchNorm):module.momentum=value
    return value

def train_lifecycle(model,loader_factory,out,device='cpu',knn_enable=None):
    """Same lifecycle used by gated production entry and artificial CPU validation."""
    out=Path(out);out.mkdir(exist_ok=False)
    model.to(device)
    guard=UpdateGuard(Contract());optimizer=make_optimizer(model)
    scheduler=torch.optim.lr_scheduler.LambdaLR(optimizer,lambda e:max(.9**(e/21),.02))
    counts={'forward':0,'backward':0,'clip':0,'step':0,'lr_scheduler':0,'bn_scheduler':0}
    final=out/'ckpt-last.pth'
    try:
        if knn_enable is not None:knn_enable()
        for epoch in range(100):
            loader=loader_factory(epoch)
            guard.begin_epoch(epoch,len(loader));model.train()
            set_bn_momentum(model,epoch);counts['bn_scheduler']+=1
            for partial,target in loader:
                guard.before_step(len(partial))
                if len(target)!=8:raise ValueError('target batch')
                partial=partial.to(device);target=target.to(device)
                optimizer.zero_grad(set_to_none=True)
                ret=model(partial);counts['forward']+=1
                sparse,dense=model.get_loss(ret,target,epoch,partial=partial)
                loss=sparse+dense
                if not torch.isfinite(loss).all().item():raise ValueError('nonfinite loss')
                loss.backward();counts['backward']+=1
                torch.nn.utils.clip_grad_norm_(model.parameters(),10,error_if_nonfinite=True);counts['clip']+=1
                optimizer.step();counts['step']+=1;guard.after_step()
            guard.end_epoch();scheduler.step();counts['lr_scheduler']+=1
        state=guard.finish()
        with final.open('xb') as f:
            torch.save({'base_model':model.state_dict(),'optimizer':optimizer.state_dict(),
                        'scheduler':scheduler.state_dict(),'epoch':99,'stage':STAGE,'updates':3900},f)
        receipt={**state,'counts':counts,'checkpoint_sha256':sha(final),
                 'bncal_executed':False,'evaluation_executed':False,'resume':False}
        with (out/'completion.json').open('x',encoding='utf8') as f:json.dump(receipt,f,indent=2)
        return receipt
    except BaseException as exc:
        guard.abort()
        with (out/'failure.json').open('x',encoding='utf8') as f:
            json.dump({'status':'FAILED_STOP','error':str(exc),'counts':counts,'committed_steps':guard.steps},f,indent=2)
        raise

def run_bcsp(args,config):
    """Future request-gated isolated entry. No request is created by this module."""
    execution=config.get('bcsp_execution',{})
    if execution.get('stage')!=STAGE:raise ValueError('wrong stage')
    request_path=execution.get('request');authorization_path=execution.get('authorization')
    if not request_path or not authorization_path:raise PermissionError('separate execution authorization required')
    if sha(request_path)!=execution.get('request_sha256'):raise PermissionError('request drift')
    request=json.loads(Path(request_path).read_text(encoding='utf8'))
    auth=json.loads(Path(authorization_path).read_text(encoding='utf8'))
    if not auth.get('execution_authorized') or auth.get('request_sha256')!=sha(request_path):raise PermissionError('authorization mismatch')
    if request.get('stage')!=STAGE or request.get('optimizer_updates')!=3900:raise ValueError('new task contract')
    if request.get('config_sha256')!=sha(args.config):raise ValueError('config mismatch')
    for key in ('manifest','fold_binding','data_qc'):
        if sha(request[key])!=request[key+'_sha256']:raise ValueError(key+' drift')
    qc=json.loads(Path(request['data_qc']).read_text(encoding='utf8'))
    if qc.get('status')!='PASS' or qc.get('manifest_sha256')!=request['manifest_sha256']:raise ValueError('data QC absent')
    fold=json.loads(Path(request['fold_binding']).read_text(encoding='utf8'))['folds'][request['fold']]
    records=[json.loads(s) for s in Path(request['manifest']).read_text(encoding='utf8').splitlines() if s.strip()]
    records_by_id={r['case_id']:r for r in records}
    if len(records_by_id)!=len(records):raise ValueError('manifest duplicates')
    selected=[records_by_id[i] for i in fold['train_case_ids']]
    dataset=BCSPDataset(request['data_root'],selected,fold['train_sources'],request['n_input'])
    # Exact code/environment/GPU binding remains a separate execution-readiness gate.
    if execution.get('resource_preflight_passed') is not True:raise PermissionError('separate GPU readiness required')
    random.seed(0);np.random.seed(0);torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    torch.backends.cudnn.deterministic=True;torch.backends.cudnn.benchmark=False
    from models import Transformer_utils
    from models import build_model_from_cfg
    model=build_model_from_cfg(config.model)
    return train_lifecycle(model,lambda e:make_loader(dataset,e),request['output'],
                           device='cuda:0',knn_enable=Transformer_utils.enable_bcsp_knn)
