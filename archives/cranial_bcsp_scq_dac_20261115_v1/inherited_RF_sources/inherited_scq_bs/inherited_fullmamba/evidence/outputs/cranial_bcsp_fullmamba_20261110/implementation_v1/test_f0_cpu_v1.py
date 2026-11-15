"""One bounded artificial CPU batch. No native Mamba, CUDA, real data or weights."""
import ast
import hashlib
import json
import sys
import traceback
from functools import partial
from pathlib import Path
import torch
from torch import nn

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PARENT=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'
SNAP=ROOT/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/models'
sys.path[:0]=[str(HERE),str(PARENT)]
import bcsp_f0_factory_v1 as factory
from bcsp_f0_decoder_v1 import F0Decoder
import bcsp_f0_runtime_adapter_v1 as runtime

OUT=HERE/'artificial_cpu_batch_v1'
assert not OUT.exists()
OUT.mkdir()
torch.set_num_threads(2)
torch.random.default_generator.manual_seed(170)
checks=[]


def check(name, condition):
    assert bool(condition), name
    checks.append(name)


def reject(name, fn):
    try:fn()
    except (ValueError,RuntimeError):checks.append(name);return
    raise AssertionError('accepted invalid input: '+name)


def knn_point(k, xyz, query):
    return torch.cdist(query,xyz).topk(k,largest=False).indices


def index_points(points, idx):
    batch=torch.arange(points.shape[0]).view(-1,1,1)
    return points[batch,idx]


env=dict(torch=torch,nn=nn,partial=partial,knn_point=knn_point,index_points=index_points,
         trunc_normal_=nn.init.trunc_normal_)
def extract(path,names):
    tree=ast.parse(path.read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in names]
    assert {n.name for n in nodes}==set(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),env)

extract(SNAP/'Transformer_utils.py',['Mlp','Attention','CrossAttention','DynamicGraphAttention','LayerScale'])
extract(SNAP/'AdaPoinTr.py',['CrossAttnBlockApi','TransformerDecoder','PointTransformerDecoder'])


class ArtificialCausalMixer(nn.Module):
    def __init__(self):
        super().__init__()
        self.gain=nn.Parameter(torch.rand(384)*.02+.1)
        self.gain._no_weight_decay=True
        self.lengths=[]
    def forward(self,x):
        self.lengths.append(x.shape[1])
        return x*self.gain+torch.cumsum(x,1)*.001


class EncoderFixture(nn.Module):
    def __init__(self,i):
        super().__init__();self.combine_style='concat';self.block_length=2 if i==0 else 1
        self.norm1=nn.LayerNorm(384,eps=1e-6);self.norm2=nn.LayerNorm(384,eps=1e-6)
        self.attn=env['Attention'](384,num_heads=6)
        self.local_attn=env['DynamicGraphAttention'](384,k=8) if i==0 else None
        if i==0:self.merge_map=nn.Linear(768,384)
        self.mlp=env['Mlp'](384,hidden_features=768)
        for n in ['drop_path1','drop_path2','ls1','ls2']:setattr(self,n,nn.Identity())


class ArtificialModel(nn.Module):
    def __init__(self):
        super().__init__();b=nn.Module();self.base_model=b
        b.encoder=nn.Module();b.encoder.blocks=nn.Module();b.encoder.blocks.blocks=nn.ModuleList([EncoderFixture(i) for i in range(6)])
        b.mem_link=nn.Identity();b.scqr_local_geometry=None;b.scqr_query_conditioner=None;b.rim_query_enabled=False
        b.decoder=env['PointTransformerDecoder'](embed_dim=384,depth=8,num_heads=6,mlp_ratio=2,k=8,
            self_attn_block_style_list=['attn-graph']+['attn']*7,cross_attn_block_style_list=['attn-graph']+['attn']*7)
        self.project=nn.Linear(3,384);self.to_global=nn.Linear(384,1024);self.coarse=nn.Linear(1024,768)
        self.query=nn.Linear(1027,384);self.offset=nn.Linear(384,96)
        self.seen_input=None;self.loss_target=None
    def forward(self,x):
        self.seen_input=x
        s=x[:,:256];mem=self.project(s)
        z=self.to_global(mem.max(1).values);q=self.coarse(z).reshape(-1,256,3)
        query=self.query(torch.cat([z[:,None].expand(-1,256,-1),q],-1))
        y=self.base_model.decoder(query,mem,q,s)
        delta=self.offset(y).reshape(-1,256,32,3)
        p=(q[:,:,None]+delta).reshape(-1,8192,3)
        return q,p,delta
    def get_loss(self,ret,target,epoch,partial=None):
        # Artificial cheap scalar only; actual 8k Chamfer is NOT certified by this fixture.
        self.loss_target=target
        return ret[1].new_zeros(()),(ret[1]-target).square().mean()+ret[0].square().mean()


def test():
    rng=torch.random.get_rng_state().clone()
    model,evidence=factory.build_artificial_fixture(ArtificialModel,ArtificialCausalMixer)
    check('factory preserves caller CPU RNG',torch.equal(rng,torch.random.get_rng_state()))
    check('fixture visibly labeled',evidence['artificial_fixture'])
    check('all common initial tensors preserved',evidence['common_initialization_preserved'])
    check('six old encoder branches replaced',evidence['parent']['replaced_global_branches']==6)
    decoder=model.base_model.decoder
    check('eight isolated decoder layers',len(decoder.blocks)==8)
    check('sixteen new mixers',sum(isinstance(v,ArtificialCausalMixer) for v in decoder.modules())==16)
    check('shared PE has1152 parameters',sum(p.numel() for p in decoder.coordinate_pe.parameters())==1152)
    check('local graph only at first decoder block',all((b.local_self_attn is not None)==(i==0) and (b.local_cross_attn is not None)==(i==0) for i,b in enumerate(decoder.blocks)))
    check('old attention unregistered',not any(type(v).__name__ in ['Attention','CrossAttention'] for v in model.modules()))
    check('first merges keep768to384',decoder.blocks[0].self_attn_merge_map.in_features==768 and decoder.blocks[0].cross_attn_merge_map.out_features==384)
    again,_=factory.build_artificial_fixture(ArtificialModel,ArtificialCausalMixer)
    check('deterministic fixture factory',all(torch.equal(v,again.state_dict()[k]) for k,v in model.state_dict().items()))
    del again
    q=torch.randn(1,256,384);v=torch.randn_like(q);qp=torch.randn(1,256,3);vp=torch.randn_like(qp)
    decoder.eval()
    with torch.no_grad():
        y,trace=decoder(q,v,qp,vp,return_instrumentation=True)
        y2=decoder(q,v,qp,vp)
    check('actual eight-block forward finite',y.shape==q.shape and torch.isfinite(y).all())
    check('same input repeated output',torch.equal(y,y2))
    check('eight structured eval traces',len(trace)==8 and all('prefix_suffix' in r for r in trace))
    check('query scan lengths256',all(b.self_ssm.lengths==[256]*4 for b in decoder.blocks))
    check('condition scan whole512',all(b.cond_ssm.lengths==[512]*2 for b in decoder.blocks))
    permutation=torch.randperm(256);inverse=torch.argsort(permutation)
    with torch.no_grad():
        yp=decoder(q[:,permutation],v,qp[:,permutation],vp)[:,inverse]
        ym=decoder(q,v[:,permutation],qp,vp[:,permutation])
    check('query sort/restore and graph slots',torch.allclose(y,yp,atol=2e-6,rtol=2e-6))
    check('paired memory order invariant without ties',torch.allclose(y,ym,atol=2e-6,rtol=2e-6))
    from bcsp_mamba_encoder_v1 import lexicographic_order
    ties=torch.zeros(2,256,3);order,inv=lexicographic_order(ties)
    check('stable complete ties preserve input index',torch.equal(order,torch.arange(256).expand(2,-1)) and torch.equal(order,inv))
    with torch.no_grad():
        batch=decoder(q.expand(2,-1,-1).clone(),v.expand(2,-1,-1).clone(),qp.expand(2,-1,-1).clone(),vp.expand(2,-1,-1).clone())
    check('batch2 independent samples',torch.allclose(batch[0],y[0],atol=2e-6,rtol=2e-6) and torch.equal(batch[0],batch[1]))
    with torch.no_grad():
        batch8=decoder(q.expand(8,-1,-1),v.expand(8,-1,-1),qp.expand(8,-1,-1),vp.expand(8,-1,-1))
    check('CPU batch8 interface only',batch8.shape==(8,256,384) and torch.isfinite(batch8).all())
    reject('denoise refused',lambda:decoder(q,v,qp,vp,denoise_length=0))
    reject('FP64 refused',lambda:decoder(q.double(),v,qp,vp))
    reject('wrong memory length refused',lambda:decoder(q,v[:,:128],qp,vp[:,:128]))
    bad=qp.clone();bad[0,0,0]=float('nan')
    reject('nonfinite position refused',lambda:decoder(q,v,bad,vp))
    reject('cross batch refused',lambda:decoder(q,v.expand(2,-1,-1),qp,vp))
    decoder.train();reject('full trace refused during training',lambda:decoder(q,v,qp,vp,return_instrumentation=True))
    decoder.eval();memory=v.clone().requires_grad_();out=decoder(q,memory,qp,vp);out.square().mean().backward()
    check('memory gradient connected',memory.grad is not None and torch.isfinite(memory.grad).all() and memory.grad.norm()>0)
    check('new PE gradient connected',decoder.coordinate_pe.weight.grad is not None and decoder.coordinate_pe.weight.grad.norm()>0)
    check('each self mixer gradient finite nonzero',all(b.self_ssm.gain.grad is not None and torch.isfinite(b.self_ssm.gain.grad).all() and b.self_ssm.gain.grad.norm()>0 for b in decoder.blocks))
    check('each condition mixer gradient finite nonzero',all(b.cond_ssm.gain.grad is not None and torch.isfinite(b.cond_ssm.gain.grad).all() and b.cond_ssm.gain.grad.norm()>0 for b in decoder.blocks))
    # Isolate a layer with no graph; early-prefix perturbation avoids the boundary.
    b=decoder.blocks[1];pq,iq=lexicographic_order(qp);pm,_=lexicographic_order(vp);pe=decoder.coordinate_pe
    with torch.no_grad():
        first=b(q,v,qp,vp,pe(qp),pe(vp),pq,iq,pm,None,None,True)[1]['prefix_suffix']
        changed=v.clone();changed[:,pm[0,:64],0]+=1
        second=b(q,changed,qp,vp,pe(qp),pe(vp),pq,iq,pm,None,None,True)[1]['prefix_suffix']
    check('isolated prefix responds to early memory in fixture',(first-second).norm()>1e-5)
    check('synthetic mixer not native certification',type(b.cond_ssm).__name__=='ArtificialCausalMixer')
    # Use actual inherited optimizer grouping function, without importing data/provider modules.
    source=PARENT/'bcsp_p1_training_runtime_v1.py'
    tree=ast.parse(source.read_text(encoding='utf-8'));fns=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups']
    scope=dict(torch=torch,require=lambda v,s:factory.require(v,s));exec(compile(ast.Module(body=fns,type_ignores=[]),str(source),'exec'),scope)
    groups,records=scope['optimizer_groups'](model)
    check('all trainable parameters exactly once',sum(len(g['params']) for g in groups)==len(list(model.parameters())))
    check('SSM fixture flags no-decay inherited',all(r['weight_decay']==0 for r in records if r['name'].endswith('.gain')))
    check('PE matrix regular decay',next(r['weight_decay'] for r in records if r['name'].endswith('coordinate_pe.weight'))==.0005)
    reject('artificial model blocked from production training',lambda:runtime.train_lifecycle(None,'',model,admission={}))
    # Full interface-only artificial8k forward; no actual Chamfer/GPU evidence claimed.
    model.eval();x=torch.randn(1,8192,3);gt=torch.randn_like(x)
    ret,loss=runtime.forward_loss(model,x,gt,0)
    check('8k caller output',ret[0].shape==(1,256,3) and ret[1].shape==(1,8192,3))
    check('32 points anchored to correct coarse slot',torch.allclose(ret[1].reshape(1,256,32,3),ret[0][:,:,None]+ret[2]))
    check('GT only passed to loss',model.seen_input is x and model.loss_target is gt)
    check('caller loss autograd connected',loss.requires_grad and torch.isfinite(loss))
    stats=runtime.lightweight_geometry(ret[0],ret[1]);check('lightweight training stats detached',not stats['coarse']['centroid'].requires_grad)
    reject('caller non8k rejected',lambda:runtime.forward_loss(model,x[:,:32],gt[:,:32],0))
    # Structural order verified with actual trace: FFN reads after_cross, not after_self.
    with torch.no_grad():
        r=trace[1];expected=r['after_cross']+decoder.blocks[1].mlp(decoder.blocks[1].norm2(r['after_cross']))
    check('FFN uses second residual',torch.equal(expected,r['output']))
    return dict(status='ARTIFICIAL_CPU_CONTRACT_BATCH_PASS',checks=checks,check_count=len(checks),torch_version=torch.__version__,native_Mamba_executed=False,CUDA_calls=0,real_data_access=False,real_8k_Chamfer_tested=False,optimizer_steps=0,model_fixture_full8k_forward=1,production_training_started=False)


if __name__=='__main__':
    try:
        result=test()
    except BaseException as error:
        (OUT/'failure_v1.json').write_text(json.dumps(dict(status='FAIL_STOP',checks_passed=checks,error=repr(error),traceback=traceback.format_exc()),indent=2),encoding='utf-8')
        raise
    (OUT/'result_v1.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result),flush=True)
