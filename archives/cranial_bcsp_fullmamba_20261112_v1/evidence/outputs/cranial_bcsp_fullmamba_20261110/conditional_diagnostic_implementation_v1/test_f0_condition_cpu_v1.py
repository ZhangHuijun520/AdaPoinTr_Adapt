"""One targeted artificial CPU batch. No Native arrays, weights, server or CUDA."""
import ast,copy,hashlib,importlib.util,json,sys,types,traceback
from pathlib import Path
from functools import partial
import numpy as np
import torch
from torch import nn

S=Path(__file__).resolve().parent;R=S.parents[2];O=S/'artificial_cpu_batch_v1'
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def record(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 O.mkdir();checks=[];torch.set_num_threads(2)
 def check(n,v=True):
  if not v:raise AssertionError(n)
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (RuntimeError,ValueError,KeyError,AssertionError):checks.append(n);return
  raise AssertionError('unexpected accept '+n)
 def emit(name,data):
  path=O/name
  with path.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,allow_nan=False)
  return record(path)
 try:
  p=module('condition_native_helper_cpu',S.parent/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py')
  impl={k:record(path) for k,path in {
   'encoder':R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_mamba_encoder_v1.py',
   'factory':R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_model_factory_v1.py',
   'f0_decoder':S.parent/'implementation_v1/bcsp_f0_decoder_v1.py',
   'f0_factory':S.parent/'implementation_v1/bcsp_f0_factory_v1.py'}.items()}
  factory=p.load_f0_builder(impl);a=module('condition_adapter_cpu',S/'bcsp_f0_condition_adapter_v1.py');e=module('condition_entry_cpu',S/'bcsp_f0_condition_diagnostic_v1.py')
  env=dict(torch=torch,nn=nn,partial=partial,factory=factory)
  def knn_point(k,xyz,query):return torch.cdist(query,xyz).topk(k,largest=False).indices
  def index_points(points,idx):return points[torch.arange(points.shape[0]).view(-1,1,1),idx]
  env.update(knn_point=knn_point,index_points=index_points,trunc_normal_=nn.init.trunc_normal_)
  SNAP=R/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot/models'
  for file,names in [('Transformer_utils.py',{'Mlp','Attention','CrossAttention','DynamicGraphAttention','LayerScale'}),('AdaPoinTr.py',{'CrossAttnBlockApi','TransformerDecoder','PointTransformerDecoder','SimpleRebuildFCLayer'})]:
   tree=ast.parse((SNAP/file).read_text(encoding='utf-8'));nodes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in names];assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'),env)
  env['env']=env;tree=ast.parse((S.parent/'implementation_v1/test_f0_cpu_v1.py').read_text(encoding='utf-8'))
  exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in {'ArtificialCausalMixer','EncoderFixture','ArtificialModel'}],type_ignores=[]),'prior_fixture','exec'),env)
  torch.manual_seed(81);model,ev=factory.build_artificial_fixture(env['ArtificialModel'],env['ArtificialCausalMixer'])
  model.decoder_type='fc';model.factor=32
  model.increase_dim=nn.Sequential(nn.Conv1d(384,1024,1),nn.BatchNorm1d(1024),nn.LeakyReLU(.2),nn.Conv1d(1024,1024,1))
  model.reduce_map=nn.Linear(1411,384);model.decode_head=env['SimpleRebuildFCLayer'](768,32);model.eval()
  r=dict(F=torch.randn(1,256,384),S=torch.randn(1,256,3),z=torch.randn(1,1024),Q=torch.randn(1,256,3),X=torch.randn(1,256,384))
  d={k:torch.randn_like(v) for k,v in r.items()};state=factory.parent.state_fingerprints(model) if hasattr(factory.parent,'state_fingerprints') else {n:v.clone() for n,v in model.state_dict().items()}
  state={n:v.clone() for n,v in model.state_dict().items()};rng=torch.get_rng_state().clone()
  hooks_before={id(m):(len(m._forward_pre_hooks),len(m._forward_hooks)) for m in model.modules()}
  with torch.inference_mode():
   q,native=model.base_model.decoder(r['X'],r['F'],r['Q'],r['S'],return_instrumentation=True)
   native_dense=a.dense_head(model,q,r['Q'])
   # Independently reproduce the exact mother head calculation.
   g=model.increase_dim(q.transpose(1,2)).transpose(1,2).max(1)[0]
   rf=model.reduce_map(torch.cat([g[:,None,:].expand(-1,256,-1),q,r['Q']],-1))
   expected=(model.decode_head(rf)+r['Q'][:,:,None,:]).reshape(1,8192,3)
   check('01 exact mother head including nested pooling',torch.equal(native_dense,expected))
   native_arrays={'layer_'+str(i)+'__'+k:l[k] for i,l in enumerate(native) for k in a.TRACE_KEYS}
   neutral,layers,proof=a.intervene(model,r,r,'prefix_donor')
   check('02 identical donor is Native on artificial full decoder/head',torch.equal(neutral,native_dense) and all(torch.equal(layers[i][k],native[i][k]) for i in range(8) for k in a.TRACE_KEYS))
   results={}
   for condition in a.CONDITIONS:
    dense,layers,proof=a.intervene(model,r,d,condition);results[condition]=(dense,layers,proof)
    check('03 '+condition+' exact1 decoder1 head24SSM',proof['counts']==dict(decoder=1,head=1,self_ssm=16,cond_ssm=8,local_cross=1,forbidden=0,donor_knn=int(condition=='local_graph_donor')))
    rows,response=a.compare(layers,native_arrays,dense,native_dense,r,100.)
    check('04 '+condition+' 64 layer/group responses',len(rows)==64 and response['world_mm']['RMSE']>=0)
   check('05 local donor first prefix unchanged',torch.equal(results['local_graph_donor'][1][0]['prefix_suffix'],native[0]['prefix_suffix']))
   check('06 prefix donor affects conditional path',not torch.equal(results['prefix_donor'][1][0]['prefix_suffix'],native[0]['prefix_suffix']))
   check('07 null retains PE/LN site and recipient graph',all(x['raw_feature_zero'] and x['local_source']=='recipient' for x in results['prefix_feature_null'][2]['isolation']))
   check('08 hooks removed after success',hooks_before=={id(m):(len(m._forward_pre_hooks),len(m._forward_hooks)) for m in model.modules()})
   unchanged={k:v.clone() for k,v in r.items()};changed=dict(r,z=r['z']+99)
   pz,_,_=a.intervene(model,changed,d,'prefix_donor')
   check('09 cached z never substituted into rebuild pooling',torch.equal(pz,results['prefix_donor'][0]))
   check('10 recipient tensors unchanged',all(torch.equal(r[k],v) for k,v in unchanged.items()))
   reject('11 unknown condition denied',lambda:a.intervene(model,r,d,'Native'))
   bad=dict(r,Q=r['Q'][:,:255]);reject('12 malformed cached Q denied',lambda:a.intervene(model,bad,d,'prefix_donor'))
   old=model.base_model.decoder.knn
   seen=[]
   def knn(k,s,q):seen.append((s is d['S'],q is r['Q']));return old(k,s,q)
   model.base_model.decoder.knn=knn
   try:a.intervene(model,r,d,'local_graph_donor')
   finally:model.base_model.decoder.knn=old
   check('13 donor KNN recomputed with donor S recipient Q',seen[0]==(True,True))
   def fail(*args):raise RuntimeError('ARTIFICIAL_COND_FAILURE')
   handle=model.base_model.decoder.blocks[3].cond_ssm.register_forward_pre_hook(fail)
   fail_hooks={id(m):(len(m._forward_pre_hooks),len(m._forward_hooks)) for m in model.modules()}
   try:reject('14 injected failure propagates no retry',lambda:a.intervene(model,r,d,'prefix_donor'))
   finally:handle.remove()
   check('15 hooks removed on failure',hooks_before=={id(m):(len(m._forward_pre_hooks),len(m._forward_hooks)) for m in model.modules()})
   check('16 zero response is valid diagnostic',a.response(native_dense,native_dense)['allclose'])
   wrong=dict(native_arrays,layer_0__after_self=native_arrays['layer_0__after_self']+1)
   reject('17 saved Native isolation mismatch stops',lambda:a.compare(native,wrong,native_dense,native_dense,r,100))
  check('18 all parameters and BN buffers unchanged',all(torch.equal(v,model.state_dict()[n]) for n,v in state.items()))
  check('19 CPU RNG unchanged by suffix interventions',torch.equal(rng,torch.get_rng_state()))
  reject('20 training mode denied',lambda:a.intervene(model,r,d,'prefix_donor'))
  index=json.loads((S/'context_index_candidate_v1.json').read_bytes());e.validate_index(index);check('21 actual frozen ten-pair metadata')
  for name,mutate in [('22 donor reselection denied',lambda x:x['pairs'][0].update(donor='train__007__bilateral')),('23 wrong weights denied',lambda x:x['runs'][0]['checkpoint'].update(sha256='0'*64))]:
   bad=copy.deepcopy(index);mutate(bad);reject(name,lambda:e.validate_index(bad))
  qbase=dict(schema='f0-30-decoder-only-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',conditions=list(e.CONDITIONS),decoder_calls=30,head_calls=30,native_ssm_calls=720,limits=e.LIMITS,null_site='RAW_F_BEFORE_NORM_V_KEEP_PE_AND_LN_BETA',fixed_recipient=['z','Q','X'],query_groups=[[0,86],[86,171],[171,256]],comparison=dict(atol=1e-6,rtol=1e-5,relative_denominator_floor=1e-12,response_is_not_performance=True,current_noise_floor_measured=False),context_index=record(S/'context_index_candidate_v1.json'),entry=record(S/'bcsp_f0_condition_diagnostic_v1.py'),adapter=record(S/'bcsp_f0_condition_adapter_v1.py'))
  qbase.update({k:0 for k in ('encoder_calls','coarse_calls','Native_replay','loss_calls','backward','optimizer_steps','BNCal','training','GT_access')})
  qbase['P3']=emit('artificial_P3.json',dict(status='F0_CONDITION_LOCAL_P3_PASS',entry_sha256=qbase['entry']['sha256'],adapter_sha256=qbase['adapter']['sha256']))
  serial=0
  def triplet(change=None,yes=True,wrong=False):
   nonlocal serial
   serial+=1;q=copy.deepcopy(qbase)
   if change:change(q)
   qr=emit('q%d.json'%serial,q);ar=emit('a%d.json'%serial,dict(schema='bcsp-development-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_ONLY'))
   rr=emit('r%d.json'%serial,dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if wrong else ar['sha256']));return qr,ar,rr
  e.authorize(*triplet());check('24 full authorize actual frozen index path')
  reject('25 explicit authorization required',lambda:e.authorize(*triplet(yes=False)))
  reject('26 runtime one way binding enforced',lambda:e.authorize(*triplet(wrong=True)))
  reject('27 extra suffix denied',lambda:e.authorize(*triplet(lambda q:q.update(decoder_calls=31))))
  reject('28 encoder replay denied',lambda:e.authorize(*triplet(lambda q:q.update(encoder_calls=1))))
  reject('29 changed null site denied',lambda:e.authorize(*triplet(lambda q:q.update(null_site='NORMALIZED_F_ZERO'))))
  reject('30 real GT access denied',lambda:e.authorize(*triplet(lambda q:q.update(GT_access=1))))
  emit('result.json',dict(status='ARTIFICIAL_CPU_CONTRACT_PASS',count=len(checks),checks=checks,torch=torch.__version__,CUDA_used=False,real_arrays_read=False,production_sources=[record(S/'bcsp_f0_condition_adapter_v1.py'),record(S/'bcsp_f0_condition_diagnostic_v1.py')],limitation='Actual frozen F0 decoder and mother FC head, artificial causal mixer/contexts; not CUDA certification or scientific results.'))
  print(json.dumps(dict(status='PASS',count=len(checks))))
 except BaseException as exc:
  emit('failure.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
