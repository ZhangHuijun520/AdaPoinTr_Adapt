"""One bounded artificial CPU batch: actual LQI/F0 code, surrogate causal mixers.
No real arrays/checkpoints, deployment, CUDA, original training loss or training run.
"""
import ast,hashlib,importlib.util,json,sys,time,traceback
from functools import partial
from pathlib import Path
import torch
from torch import nn

S=Path(__file__).resolve().parent;R=S.parents[2];B=S.parent;O=S/'artificial_cpu_batch_v1'
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def module(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def state(m):return {n:t.detach().clone() for n,t in m.state_dict().items()}
def equal(a,b):return set(a)==set(b) and all(torch.equal(a[k],b[k]) for k in a)
def main():
 O.mkdir();torch.set_num_threads(2);start=time.monotonic();checks=[];handles=[]
 def check(name,v=True):
  if not v:raise AssertionError(name)
  checks.append(name)
 def reject(name,fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError):checks.append(name);return
  raise AssertionError('unexpected accept '+name)
 def emit(name,data):
  with (O/name).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,allow_nan=False)
 try:
  spec=json.loads((B/'query_aligned_condition_spec_v1/formula_interface_freeze_v1.json').read_bytes())
  check('01 frozen formula document identity',hashlib.sha256(Path(spec['document']['path']).read_bytes()).hexdigest()==spec['document']['sha256'])
  p=module('lqi_cpu_native_loader',B/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py')
  impl={}
  for k,n in [('encoder','bcsp_mamba_encoder_v1.py'),('factory','bcsp_p1_model_factory_v1.py')]:impl[k]=rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'/n)
  for k,n in [('f0_decoder','bcsp_f0_decoder_v1.py'),('f0_factory','bcsp_f0_factory_v1.py')]:impl[k]=rec(B/'implementation_v1'/n)
  f0=p.load_f0_builder(impl);lqi_decoder=module('bcsp_lqi_decoder_v1',S/'bcsp_lqi_decoder_v1.py');lqi=module('bcsp_lqi_factory_v1',S/'bcsp_lqi_factory_v1.py')
  env=dict(torch=torch,nn=nn,partial=partial,factory=f0)
  def knn_point(k,xyz,query):return torch.cdist(query,xyz).topk(k,largest=False).indices
  def index_points(points,idx):return points[torch.arange(points.shape[0]).reshape(-1,*([1]*(idx.ndim-1))),idx]
  env.update(knn_point=knn_point,index_points=index_points,trunc_normal_=nn.init.trunc_normal_);env['env']=env
  snap=R/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/models'
  for filename,names in [('Transformer_utils.py',{'Mlp','Attention','CrossAttention','DynamicGraphAttention','LayerScale'}),('AdaPoinTr.py',{'CrossAttnBlockApi','TransformerDecoder','PointTransformerDecoder','SimpleRebuildFCLayer'})]:
   tree=ast.parse((snap/filename).read_text(encoding='utf-8'));nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),filename,'exec'),env)
  tree=ast.parse((B/'implementation_v1/test_f0_cpu_v1.py').read_text(encoding='utf-8'));nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in {'ArtificialCausalMixer','EncoderFixture','ArtificialModel'}];exec(compile(ast.Module(body=nodes,type_ignores=[]),'prior_fixture_classes_only','exec'),env)
  class HeadFixture(env['ArtificialModel']):
   def __init__(self):
    super().__init__();self.decoder_type='fc';self.factor=32
    self.increase_dim=nn.Sequential(nn.Conv1d(384,1024,1),nn.BatchNorm1d(1024),nn.LeakyReLU(.2),nn.Conv1d(1024,1024,1));self.reduce_map=nn.Linear(1411,384);self.decode_head=env['SimpleRebuildFCLayer'](768,32)
  mixer=env['ArtificialCausalMixer']
  baseline,bev=f0.build_artificial_fixture(HeadFixture,mixer);candidate,cev=lqi.build_artificial_fixture(HeadFixture,mixer)
  check('02 exact all-state same initialization no new keys or parameters',equal(state(baseline),state(candidate)) and sum(t.numel() for t in baseline.parameters())==sum(t.numel() for t in candidate.parameters()))
  check('03 distinct candidate metadata and historical trace semantics',cev['version']=='F0-LQI-implementation-v1' and cev['variant']=='F0-LQI-v1' and cev['trace_prefix_suffix_semantics']=='interleaved conditional query-position output' and cev['additional_learned_parameters']==0)
  check('04 eight isolated LQI blocks',isinstance(candidate.base_model.decoder,lqi_decoder.LQIDecoder) and all(isinstance(b,lqi_decoder.LQIBlock) for b in candidate.base_model.decoder.blocks))
  check('05 no attention introduced',lqi.no_attention_inventory(candidate)['forbidden_registered_modules']==[])
  old=lqi.parent.native_mixer;lqi.parent.native_mixer=mixer
  try:built,ev=lqi.build_model(HeadFixture,seed=0)
  finally:lqi.parent.native_mixer=old
  check('06 production build_model legacy_builder seed0 path',equal(state(built),state(candidate)) and ev['artificial_fixture'] is False)
  del built
  # Batched, permuted Q ensures original-order and query-order cannot be confused.
  torch.manual_seed(93);X=torch.randn(2,256,384);F=torch.randn_like(X);Spos=torch.randn(2,256,3);Q=torch.randn_like(Spos)
  F[1]*=3;Spos[1]+=10;Q[1]+=10
  baseline.eval();candidate.eval();dec=candidate.base_model.decoder;mem_before=F.clone();q_before=Q.clone();x_before=X.clone();s_before=Spos.clone()
  before=state(candidate);rng=torch.get_rng_state().clone();inputs={};outputs={};local={};calls={'self':0,'cond':0};knn_calls=[]
  def capture_in(i):
   def hook(m,args):inputs[i]=args[0].detach().clone();calls['cond']+=1
   return hook
  def capture_out(i):
   def hook(m,args,value):outputs[i]=value.detach().clone()
   return hook
  def self_count(*args):calls['self']+=1
  def local_hook(m,args,kwargs):local.update({k:v.detach().clone() for k,v in kwargs.items()})
  def track_knn(k,source,query):knn_calls.append((k,source is Spos,query is Q,source is Q));return knn_point(k,source,query)
  original_knn=dec.knn;dec.knn=track_knn
  for i,b in enumerate(dec.blocks):
   handles.extend([b.cond_ssm.register_forward_pre_hook(capture_in(i)),b.cond_ssm.register_forward_hook(capture_out(i)),b.self_ssm.register_forward_pre_hook(self_count)])
  handles.append(dec.blocks[0].local_cross_attn.register_forward_pre_hook(local_hook,with_kwargs=True))
  with torch.inference_mode():
   y,trace=dec(X,F,Q,Spos,return_instrumentation=True);yb,tb=baseline.base_model.decoder(X,F,Q,Spos,return_instrumentation=True)
  for h in handles:h.remove()
  handles.clear();dec.knn=original_knn
  check('07 exact24 SSM calls and512 conditional tokens',calls=={'self':16,'cond':8} and all(t.shape==(2,512,384) for t in inputs.values()))
  check('08 existing KNN twice only and direction shared all8 layers',knn_calls==[(8,False,True,True),(8,True,True,False)])
  order,inverse=sys.modules['bcsp_mamba_encoder_v1'].lexicographic_order(Q)
  idx=knn_point(8,Spos,Q);neighbor_records=[]
  with torch.inference_mode():
   for layer,block in enumerate(dec.blocks):
    memory=block.norm_v(F)+dec.coordinate_pe(Spos);query=block.norm_q(trace[layer]['after_self'])+dec.coordinate_pe(Q)
    # Independent explicit-batch, explicit-neighbor reference (no candidate gather helper).
    avg=torch.stack([torch.stack([memory[b,idx[b,i]].sum(dim=0)/8 for i in range(256)]) for b in range(2)])
    expected=torch.stack([torch.stack([t for i in order[b].tolist() for t in (avg[b,i],query[b,i])]) for b in range(2)])
    check('09 layer%d exact LN-before-mean PE then interleaving B2'%layer,torch.allclose(inputs[layer],expected,atol=1e-6,rtol=1e-6))
    restored=torch.stack([outputs[layer][b,1::2][inverse[b]] for b in range(2)])
    check('10 layer%d odd-position readout and inverse Q sort'%layer,torch.equal(restored,trace[layer]['prefix_suffix']))
    wrong=torch.stack([block.norm_v(F[b,idx[b]].mean(dim=1))+dec.coordinate_pe(Spos)[b,idx[b]].mean(dim=1) for b in range(2)])
    check('11 layer%d distinguish LN(mean F) rejected by reference'%layer,not torch.allclose(avg,wrong,atol=1e-4,rtol=1e-4))
    neighbor_records.append(dict(layer=layer,input_shape=list(inputs[layer].shape),readout_exact=True,formula_reference=True))
  check('12 first self branch preserved before intervention',torch.equal(trace[0]['after_self'],tb[0]['after_self']))
  with torch.inference_mode():
   check('13 local branch unchanged recipient F S Q index',torch.equal(local['q'],dec.blocks[0].norm_q(trace[0]['after_self'])) and torch.equal(local['v'],dec.blocks[0].norm_v(F)) and torch.equal(local['q_pos'],Q) and torch.equal(local['v_pos'],Spos) and torch.equal(local['idx'],idx))
  check('14 all tensors original FP32 shape finite',y.shape==(2,256,384) and y.dtype==torch.float32 and bool(torch.isfinite(y).all()) and len(trace)==8)
  check('15 all8 trace stage chaining',all(torch.equal(trace[i]['output'],trace[i+1]['input']) for i in range(7)))
  check('16 eval state and CPU RNG unchanged',equal(before,state(candidate)) and torch.equal(rng,torch.get_rng_state()))
  check('17 input memory coordinates X Q unchanged',torch.equal(F,mem_before) and torch.equal(Q,q_before) and torch.equal(Spos,s_before) and torch.equal(X,x_before))
  with torch.inference_mode():
   alone=dec(X[:1],F[:1],Q[:1],Spos[:1]);plain=dec(X,F,Q,Spos)
  check('18 batch isolation with distinct second sample',torch.allclose(y[:1],alone,atol=2e-6,rtol=1e-5))
  check('19 trace on off identical',torch.equal(y,plain))
  check('20 actual causal artificial mixer changes result versus F0',not torch.allclose(y,yb,atol=1e-5,rtol=1e-5))
  dec.train();reject('21 training full trace denied',lambda:dec(X,F,Q,Spos,return_instrumentation=True));dec.eval()
  reject('22 denoise forbidden',lambda:dec(X,F,Q,Spos,denoise_length=1))
  reject('23 FP16 forbidden',lambda:dec(X.half(),F,Q,Spos))
  reject('24 wrong256 shape forbidden',lambda:dec(X[:,:255],F,Q,Spos))
  bad=F.clone();bad[0,0,0]=float('nan');reject('25 nonfinite input forbidden',lambda:dec(X,bad,Q,Spos))
  # Check tied coordinate sorting uses inherited stable ordering, no new tie policy.
  tied=Q.clone();tied[:,1]=tied[:,0];perm,rev=sys.modules['bcsp_mamba_encoder_v1'].lexicographic_order(tied)
  check('26 stable exactQ ties and inverse mapping',all(perm[b].tolist().index(0)<perm[b].tolist().index(1) for b in range(2)) and torch.equal(perm.gather(1,rev),torch.arange(256).expand(2,-1)))
  # Gradient check: no optimizer; all values artificial. Direct original FC head path.
  gradX=X.clone().requires_grad_();gradF=F.clone().requires_grad_();gradQ=Q.clone().requires_grad_();gradS=Spos.clone().requires_grad_()
  decoder_state=state(dec);grad_out=dec(gradX,gradF,gradQ,gradS)
  g=candidate.increase_dim(grad_out.transpose(1,2)).transpose(1,2).max(dim=1)[0]
  features=candidate.reduce_map(torch.cat([g[:,None,:].expand(-1,256,-1),grad_out,gradQ],-1))
  relative=candidate.decode_head(features);dense=(relative+gradQ[:,:,None,:]).reshape(2,8192,3)
  objective=dense.square().mean();objective.backward()
  check('27 artificial original head8192 points finite',dense.shape==(2,8192,3) and bool(torch.isfinite(dense).all()) and bool(torch.isfinite(objective)))
  check('28 X F S Q gradients finite nonzero no detach',all(v.grad is not None and bool(torch.isfinite(v.grad).all()) and bool(v.grad.abs().sum()>0) for v in (gradX,gradF,gradS,gradQ)))
  check('29 all8 norm_v and conditional mixers receive gradients',all(b.norm_v.weight.grad is not None and bool(b.norm_v.weight.grad.abs().sum()>0) and b.cond_ssm.gain.grad is not None and bool(b.cond_ssm.gain.grad.abs().sum()>0) for b in dec.blocks))
  check('30 PE gradients finite nonzero',dec.coordinate_pe.weight.grad is not None and bool(torch.isfinite(dec.coordinate_pe.weight.grad).all()) and bool(dec.coordinate_pe.weight.grad.abs().sum()>0))
  check('31 zero optimizer steps decoder state unchanged after backward',equal(decoder_state,state(dec)))
  # State compatibility does not imply identical architecture behavior.
  candidate.load_state_dict(baseline.state_dict(),strict=True);baseline.load_state_dict(candidate.state_dict(),strict=True)
  check('32 strict state compatibility both directions',equal(state(candidate),state(baseline)))
  check('33 signatures preserved',list(__import__('inspect').signature(lqi_decoder.LQIBlock.forward).parameters)==spec['parent_block_forward_arguments'])
  check('34 original F0 source remains frozen',rec(B/'implementation_v1/bcsp_f0_decoder_v1.py')['sha256']==spec['parent_decoder']['sha256'])
  gradients={name:dict(L1=float(v.grad.abs().sum()),finite=bool(torch.isfinite(v.grad).all())) for name,v in [('X',gradX),('F',gradF),('Q',gradQ),('S',gradS)]}
  emit('result.json',dict(status='F0_LQI_ARTIFICIAL_CPU_CONTRACT_PASS',count=len(checks),checks=checks,seconds=time.monotonic()-start,torch=torch.__version__,batch_size=2,source_records=[rec(S/'bcsp_lqi_decoder_v1.py'),rec(S/'bcsp_lqi_factory_v1.py'),rec(Path(__file__))],gradient_summaries=gradients,layer_evidence=neighbor_records,real_data=False,real_checkpoint=False,CUDA=False,optimizer_steps=0,limitations=['Native Mamba replaced by an artificial causal mixer, not actual CUDA certification.','Backprop objective is an artificial dense squared norm, not production Chamfer loss or3900-step training.','Original decoder and head computational classes extracted from frozen source; no full actual-data model run.']))
  print(json.dumps(dict(status='PASS',count=len(checks),seconds=time.monotonic()-start)))
 except BaseException as exc:
  emit('failure.json',dict(status='FAILED_STOP_NO_RETRY',completed_checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise
 finally:
  for h in handles:h.remove()
if __name__=='__main__':main()
