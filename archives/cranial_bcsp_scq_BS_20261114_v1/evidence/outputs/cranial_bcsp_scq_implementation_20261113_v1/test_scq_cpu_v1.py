"""One retained artificial CPU batch; exact mother forwards/head/loss, surrogate grouper/SSMs."""
from pathlib import Path
import ast,json,hashlib,sys,types,time,traceback,math,gc
from functools import partial
import torch
from torch import nn
O=Path(__file__).resolve().parent;R=O.parents[1];OUT=O/'cpu_batch_v1'
P=R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'
L=R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1'
SNAP=R/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot'
sys.path[:0]=[str(O),str(L),str(P)]
import bcsp_scq_factory_v1 as factory
from bcsp_scq_residual_v1 import SCQResidual,load_initialization

def emit(name,j):
 with (OUT/name).open('x',encoding='utf-8') as f:json.dump(j,f,indent=2,allow_nan=False)
def fingerprint(model):return {n:factory.parent.parent.tensor_sha(t) for n,t in model.state_dict().items()}
def main():
 OUT.mkdir();start=time.monotonic();checks=[];torch.set_num_threads(2)
 def check(n,v=True):
  assert bool(v),n
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError,TypeError):checks.append(n);return
  raise AssertionError('unexpected accept '+n)
 try:
  init=json.loads((O/'initialization_manifest_v1.json').read_bytes());frozen=load_initialization(init)
  # Use exact inherited KNN, including no_grad/topk and batched advanced indexing.
  adapter={};tree=ast.parse((SNAP/'tools/bcsp_adapter.py').read_text(encoding='utf-8'))
  nodes=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('_shape_check','torch_knn')]
  exec(compile(ast.Module(nodes,[]),str(SNAP/'tools/bcsp_adapter.py'),'exec'),adapter)
  knn=adapter['torch_knn'];g=torch.Generator().manual_seed(118)
  S=torch.randn(1,256,3,generator=g);F=torch.randn(1,256,384,generator=g);z=torch.randn(1,1024,generator=g);Q=torch.randn(1,256,3,generator=g)
  rng=torch.random.get_rng_state().clone();hs=SCQResidual('S',knn,init);hf=SCQResidual('F',knn,init)
  check('private initialization preserves CPU RNG',torch.equal(rng,torch.random.get_rng_state()))
  check('F S exact same parameter buffer bytes',fingerprint(hs)==fingerprint(hf))
  check('exact693507 trainable parameters and buffer not parameter',sum(p.numel() for p in hs.parameters())==693507 and 'Pfix' in dict(hs.named_buffers()) and 'Pfix' not in dict(hs.named_parameters()))
  check('projection orthogonal frozen bytes',torch.equal(hs.Pfix,frozen['Pfix']) and torch.allclose(hs.Pfix@hs.Pfix.T,torch.eye(7),atol=1e-6))
  head,info=hs.describe(S,F,z,Q);idx=info['indices']
  reference=torch.cdist(Q.double(),S.double()).topk(8,largest=False).indices
  check('full key Q to S KNN independent float64 reference',torch.equal(idx.sort(-1).values,reference.sort(-1).values))
  selected=torch.stack([F[0,idx[0,i]] for i in range(256)])[None]
  mean=selected.mean(-1,keepdim=True);var=((selected-mean)**2).mean(-1,keepdim=True)
  normalized=(selected-mean)/torch.sqrt(var+1e-5)
  check('LN before mean max exact independent scalar formula',torch.allclose(info['fa'],normalized.mean(2),atol=2e-6) and torch.allclose(info['fm'],normalized.max(2).values,atol=2e-6))
  d=S[0,idx[0]][None]-Q[:,:,None];dm=d.mean(2)
  geom=torch.cat((dm,torch.sqrt(((d-dm[:,:,None])**2).mean(2)+1e-6),torch.sqrt((d*d).sum(-1)).mean(2,keepdim=True)),-1)
  check('sevenD direction spread distance independent formula',torch.allclose(info['geometry'],geom,atol=2e-6) and head.shape==(1,256,1802))
  fhi,fi=hf.describe(S,F,z,Q)
  check('F active sevenD projection distinct from S',torch.allclose(fi['channel'],torch.nn.functional.layer_norm(fi['fa'],(384,),eps=1e-5)@hf.Pfix.T) and not torch.equal(fi['channel'],info['channel']))
  check('zero last layer exact Q identity',torch.equal(hs(S,F,z,Q)[0],Q) and torch.equal(hf(S,F,z,Q)[0],Q))
  perm=torch.randperm(256,generator=g);phead,_=hs.describe(S[:,perm],F[:,perm],z,Q)
  check('S F synchronous permutation unique-distance consistency',torch.allclose(head,phead,atol=3e-6,rtol=2e-6))
  tied=S.clone();tied[:,1]=tied[:,0];_,ti=hs.describe(tied,F,z,Q)
  check('ties inherit actual topk contract',torch.equal(ti['indices'],knn(8,tied,Q)))
  thin=torch.stack((torch.linspace(-1,1,128),torch.zeros(128),torch.zeros(128)),1);thin=torch.cat((thin,thin+torch.tensor([0,0,.004])),0)[None]
  _,ti=hs.describe(thin,F,z,thin)
  check('thin double surface neighbor indices remain valid',torch.isfinite(ti['geometry']).all() and ti['indices'].max()<256)
  far=Q+100;_,farinfo=hs.describe(S,F,z,far)
  check('far query remains far no hidden radius filtering',farinfo['geometry'][...,-1].min()>100)
  s8=S.expand(8,-1,-1).clone();f8=F.expand(8,-1,-1).clone();z8=z.expand(8,-1).clone();q8=Q.expand(8,-1,-1).clone()
  s8[1:]+=20;q8[1:]+=20;f8[1:]*=2
  hi8,_=hs.describe(s8,f8,z8,q8)
  check('B8 batch isolation in residual path',torch.allclose(hi8[:1],head,atol=1e-6))
  check('center-preserving compact query exposed not silently fixed',torch.equal(hs(S,F,z,(Q-Q.mean(1,keepdim=True))*.1+Q.mean(1,keepdim=True))[0],(Q-Q.mean(1,keepdim=True))*.1+Q.mean(1,keepdim=True)))
  reject('wrong dtype rejected',lambda:hs(S.double(),F,z,Q))
  reject('wrong point shape rejected',lambda:hs(S[:,:255],F,z,Q))
  reject('GT kwargs not accepted by model condition',lambda:hs(S,F,z,Q,gt=Q))
  bad=F.clone();bad[0,0,0]=float('nan');reject('nonfinite rejected',lambda:hs(S,bad,z,Q))
  reject('bad frozen initialization hash rejected',lambda:load_initialization({**init,'sha256':'0'*64}))
  qr=Q.clone().requires_grad_();fr=F.clone().requires_grad_();sr=S.clone().requires_grad_();zr=z.clone().requires_grad_()
  yy,_=hs(sr,fr,zr,qr);yy.square().mean().backward()
  check('initial W2 has gradient while W1 zero is expected',hs.W2.weight.grad.abs().sum()>0 and hs.W1.weight.grad.abs().sum()==0)
  hs.zero_grad(set_to_none=True)
  with torch.no_grad():hs.W2.weight.copy_(torch.sin(torch.arange(1152).reshape(3,384))*.002)
  qr=Q.clone().requires_grad_();fr=F.clone().requires_grad_();sr=S.clone().requires_grad_();zr=z.clone().requires_grad_()
  yy,_=hs(sr,fr,zr,qr);yy.square().mean().backward()
  check('nonzero W2 all continuous inputs gradient',all(x.grad is not None and torch.isfinite(x.grad).all() and x.grad.abs().sum()>0 for x in (qr,fr,sr,zr)))
  check('nonzero W2 W1 gradient finite',torch.isfinite(hs.W1.weight.grad).all() and hs.W1.weight.grad.abs().sum()>0)
  check('discrete indices not falsely differentiable',not info['indices'].requires_grad)

  # Exact computational classes, full mother forward and loss; constructors below are artificial.
  env=dict(torch=torch,nn=nn,partial=partial,trunc_normal_=nn.init.trunc_normal_,knn_point=knn,chamfer=None)
  env['index_points']=lambda pts,ix:pts[torch.arange(pts.shape[0]).reshape(-1,*([1]*(ix.ndim-1))),ix]
  def extract(path,classes=(),functions=()):
   t=ast.parse(path.read_text(encoding='utf-8'));nodes=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name in classes or isinstance(n,ast.FunctionDef) and n.name in functions]
   assert len(nodes)==len(classes)+len(functions)
   for n in nodes:
    if isinstance(n,ast.ClassDef):n.decorator_list=[]
   exec(compile(ast.Module(nodes,[]),str(path),'exec'),env)
  extract(SNAP/'models/Transformer_utils.py',['Mlp','Attention','CrossAttention','DynamicGraphAttention','LayerScale'])
  extract(SNAP/'models/AdaPoinTr.py',['CrossAttnBlockApi','TransformerDecoder','PointTransformerDecoder','SimpleRebuildFCLayer','PCTransformer','AdaPoinTr'])
  extract(SNAP/'extensions/chamfer_dist/__init__.py',['ChamferDistanceL1','ChamferDistanceL1Directional'],['_torch_chamfer_forward'])
  extract(R/'outputs/cranial_bcsp_fullmamba_20261110/implementation_v1/test_f0_cpu_v1.py',['ArtificialCausalMixer','EncoderFixture'])
  # Prior fixture EncoderFixture resolves the exact extracted computational classes here.
  env['env']=env
  class Grouper(nn.Module):
   def forward(self,xyz,n):return xyz[:,:256],xyz[:,:256]
  class Encoder(nn.Module):
   def __init__(self):
    super().__init__();self.blocks=nn.Module();self.blocks.blocks=nn.ModuleList([env['EncoderFixture'](i) for i in range(6)])
   def forward(self,x,pos):
    for b in self.blocks.blocks:x=b(x,pos)
    return x
  class IdentityAdapter(nn.Module):
   def forward(self,x,pos):return x
  fps_calls=[]
  env['misc']=types.SimpleNamespace(fps=lambda xyz,n:(fps_calls.append(n) or xyz[:,:n]))
  def legacy():
   m=env['AdaPoinTr'].__new__(env['AdaPoinTr']);nn.Module.__init__(m)
   b=env['PCTransformer'].__new__(env['PCTransformer']);nn.Module.__init__(b);m.base_model=b
   b.full_instrumentation_enabled=False;b._last_full_instrumentation=None;b.scqr_contract=types.SimpleNamespace(enabled=False,contact_supervision_enabled=False)
   b.query_selection='learned_only';b.num_query=256;b.center_num=[512,256];b.rim_query_enabled=False;b.use_denoise=False;b.scqr_local_geometry=None;b.scqr_query_conditioner=None
   b.grouper=Grouper();b.pos_embed=nn.Linear(3,384);b.input_proj=nn.Linear(3,384);b.encoder=Encoder();b.encoder_adapter=IdentityAdapter()
   b.increase_dim=nn.Sequential(nn.Linear(384,1024),nn.GELU(),nn.Linear(1024,1024));b.mem_link=nn.Identity()
   b.coarse_pred=nn.Sequential(nn.Linear(1024,1024),nn.GELU(),nn.Linear(1024,768))
   b.mlp_query=nn.Sequential(nn.Linear(1027,1024),nn.GELU(),nn.Linear(1024,1024),nn.GELU(),nn.Linear(1024,384))
   b.decoder=env['PointTransformerDecoder'](embed_dim=384,depth=8,num_heads=6,mlp_ratio=2,k=8,self_attn_block_style_list=['attn-graph']+['attn']*7,cross_attn_block_style_list=['attn-graph']+['attn']*7)
   m.full_instrumentation_enabled=False;m._last_full_instrumentation=None;m.decoder_type='fc';m.factor=32;m.num_query=256;m.denoise_weight=0.;m.fine_coverage_weight=1.;m.fine_local_weight=0.
   for name in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']:setattr(m,name,False)
   m.scqr_contract=b.scqr_contract
   m.increase_dim=nn.Sequential(nn.Conv1d(384,1024,1),nn.BatchNorm1d(1024),nn.LeakyReLU(.2),nn.Conv1d(1024,1024,1))
   m.reduce_map=nn.Linear(1411,384);m.decode_head=env['SimpleRebuildFCLayer'](768,32)
   m.loss_func=env['ChamferDistanceL1']();m.fine_loss_func=env['ChamferDistanceL1Directional']()
   return m
  rng=torch.random.get_rng_state().clone();mix=env['ArtificialCausalMixer']
  baseline,be=factory.build_artificial_fixture(legacy,mix,'B',init)
  model,se=factory.build_artificial_fixture(legacy,mix,'S',init)
  fm,fe=factory.build_artificial_fixture(legacy,mix,'F',init)
  check('complete artificial factory preserves caller RNG',torch.equal(rng,torch.random.get_rng_state()))
  bs=fingerprint(baseline);ss=fingerprint(model);fs=fingerprint(fm)
  check('all common state exactly B F S including BN',all(ss[n]==fs[n]==h for n,h in bs.items()))
  check('F S full state exact same init',ss==fs)
  check('actual parameter difference693507',sum(p.numel() for p in model.parameters())-sum(p.numel() for p in baseline.parameters())==693507)
  check('no registered attention survives',factory.parent.no_attention_inventory(model)['forbidden_registered_modules']==[])
  inp=torch.randn(1,8192,3,generator=g)*.5
  baseline.eval();model.eval();fm.eval();before=fingerprint(model);rng=torch.random.get_rng_state().clone()
  qcalls=[];h=model.base_model.mlp_query.register_forward_pre_hook(lambda m,a:qcalls.append(a[0].detach().clone()))
  with torch.inference_mode():rb=baseline(inp);rs=model(inp);rf=fm(inp)
  h.remove()
  check('initial actual full forward B F S exact8192 outputs',all(torch.equal(a,b) and torch.equal(a,c) for a,b,c in zip(rb,rs,rf)) and rs[1].shape==(1,8192,3))
  check('query mlp once only correct1027 input',len(qcalls)==1 and qcalls[0].shape==(1,256,1027))
  check('inherited unused FPS128 call preserved across3 arms',fps_calls==[128,128,128])
  check('eval CPU RNG and all persistent state unchanged',torch.equal(rng,torch.random.get_rng_state()) and fingerprint(model)==before)
  # Use a known, fixed nonzero head; no optimizer step or fitting.
  with torch.no_grad():model.base_model.scq.W2.weight.copy_(torch.sin(torch.arange(1152).reshape(3,384))*.002);model.base_model.scq.W2.bias.copy_(torch.tensor([.18,-.10,.07]))
  tracked={};b=model.base_model;dec=b.decoder;old_knn=dec.knn
  def track_knn(k,source,query):
   tracked.setdefault('knn',[]).append((source.detach().clone(),query.detach().clone()));return old_knn(k,source,query)
  dec.knn=track_knn
  hooks=[b.mlp_query.register_forward_pre_hook(lambda m,a:tracked.update(mlp=a[0].detach().clone())),dec.register_forward_pre_hook(lambda m,a,kw:tracked.update(dec_q=kw['q_pos'].detach().clone()),with_kwargs=True),dec.coordinate_pe.register_forward_pre_hook(lambda m,a:tracked.setdefault('pe',[]).append(a[0].detach().clone())),dec.blocks[0].register_forward_pre_hook(lambda m,a:tracked.update(cross=a[10].detach().clone(),order=a[6].detach().clone())),model.reduce_map.register_forward_pre_hook(lambda m,a:tracked.update(rebuild=a[0].detach().clone())),model.decode_head.register_forward_hook(lambda m,a,v:tracked.update(relative=v.detach().clone()))]
  model.full_instrumentation_enabled=False
  with torch.inference_mode():rn=model(inp)
  for h in hooks:h.remove()
  dec.knn=old_knn;diag=b._scq_last_info
  check('actual known residual Qused raw plus delta',torch.equal(rn[0],diag['Q0']+diag['delta']) and not torch.equal(rn[0],rs[0]))
  check('actual query feature decoder PE all consume Qused',torch.equal(tracked['mlp'][...,-3:],rn[0]) and torch.equal(tracked['dec_q'],rn[0]) and torch.equal(tracked['pe'][0],rn[0]))
  check('actual self cross KNN recomputed Qused',len(tracked['knn'])==2 and all(torch.equal(query,rn[0]) for _,query in tracked['knn']) and torch.equal(tracked['cross'],old_knn(8,tracked['knn'][1][0],rn[0])))
  order,_=sys.modules['bcsp_mamba_encoder_v1'].lexicographic_order(rn[0])
  check('actual sorting recomputed Qused',torch.equal(tracked['order'],order))
  check('actual rebuild feature and dense center consume Qused',torch.equal(tracked['rebuild'][...,-3:],rn[0]) and torch.equal(rn[1],(tracked['relative']+rn[0][:,:,None]).reshape(1,8192,3)))
  check('known residual changes dense not merely diagnostics',not torch.equal(rn[1],rs[1]))
  check('SCQ diagnostic tensors detached',all(not t.requires_grad for t in diag.values()))
  # Parent policy not reimplemented: exact shared partition plus explicit new groups.
  new_ids={id(p) for p in b.scq.parameters()};common=[p for p in model.parameters() if id(p) not in new_ids]
  groups=factory.optimizer_groups(model,[dict(params=common,weight_decay=0.)])
  check('new optimizer groups precise weights bias decay',groups[-2]['weight_decay']==5e-4 and groups[-1]['weight_decay']==0 and sum(len(x['params']) for x in groups)==len(list(model.parameters())))
  reject('duplicate parent optimizer partition rejected',lambda:factory.optimizer_groups(model,[dict(params=common+common)]))
  reject('double install rejected',lambda:factory.install(model,'S',init))
  # Original training return and original get_loss route, original full cdist implementation.
  del baseline,fm,bs,ss,fs;gc.collect();model.train()
  before=fingerprint(b.scq);bn_before={n:t.clone() for n,t in model.named_buffers()}
  ret=model(inp);check('actual no-denoise train tuple preserved',len(ret)==4 and ret[0].shape==(1,256,3) and ret[1].shape==(1,0,3) and ret[3].shape==(1,8192,3))
  target=torch.randn(1,8192,3,generator=g)*.5+torch.tensor([.8,.2,-.3])
  call_shapes=[];hh=[model.loss_func.register_forward_pre_hook(lambda m,a:call_shapes.append(('coarse',tuple(a[0].shape)))),model.fine_loss_func.register_forward_pre_hook(lambda m,a:call_shapes.append(('dense',tuple(a[0].shape))))]
  ld,loss=model.get_loss(ret,target);[h.remove() for h in hh]
  check('actual coarse dense loss called once and denoise zero',call_shapes==[('coarse',(1,256,3)),('dense',(1,8192,3))] and ld.item()==0 and torch.isfinite(loss))
  ret[0].retain_grad();loss.backward()
  check('original full loss reaches Qused and residual W1 W2',ret[0].grad is not None and torch.isfinite(ret[0].grad).all() and all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in b.scq.parameters()))
  check('backward no optimizer step new parameter bytes unchanged',before==fingerprint(b.scq))
  with torch.no_grad():
   for n,t in model.named_buffers():t.copy_(bn_before[n])
  check('train BN temporary buffers restored',all(torch.equal(t,bn_before[n]) for n,t in model.named_buffers()))
  # Static differential proof complements real consumer hooks, including eval instrumentation sites.
  tree=ast.parse((O/'bcsp_scq_factory_v1.py').read_text(encoding='utf-8'));adapt=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_scq_base_forward')
  mother=ast.parse((SNAP/'models/AdaPoinTr.py').read_text(encoding='utf-8'));cl=next(x for x in mother.body if isinstance(x,ast.ClassDef) and x.name=='PCTransformer');original=next(x for x in cl.body if isinstance(x,ast.FunctionDef) and x.name=='forward')
  adapt.name='forward';adapt.body=[n for n in adapt.body if not isinstance(n,ast.Assign) or 'self.scq(' not in ast.unparse(n)]
  check('isolated base forward only one AST insertion',ast.dump(adapt,include_attributes=False)==ast.dump(original,include_attributes=False))
  emit('result_v1.json',dict(status='SCQ_ARTIFICIAL_CPU_CONTRACT_PASS',checks=checks,count=len(checks),seconds=time.monotonic()-start,torch=torch.__version__,initialization_sha256=init['sha256'],new_parameters=se['scq']['new_parameters'],measured_artificial_model_parameters=se['scq']['total_parameters'],original_full_cdist_loss=float(loss.detach()),real_data=False,real_checkpoint=False,CUDA=False,optimizer_steps=0,limitations=['Actual mother forward, LQI decoder, FC head and get_loss methods used; constructors/grouper are artificial and Mamba uses causal surrogate mixers.','CPU full8192 loss/backward does not certify CUDA batch8, native provider/Mamba, GPU memory or scientific benefit.','No optimizer instantiated or stepped; parent grouping supplied as synthetic partition solely to test new parameter allocation.']))
  print(json.dumps(dict(status='PASS',count=len(checks),seconds=time.monotonic()-start)))
 except BaseException as e:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',completed_checks=checks,error=repr(e),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
