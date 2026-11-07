"""One bounded artificial CPU validation batch, no real model/checkpoint/NPZ or server."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2'
import ast,copy,hashlib,importlib.util,json,random,sys,types
from pathlib import Path
import numpy as np
import torch

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];F=HERE/'artificial_cpu_batch_v1'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def main():
 F.mkdir(exist_ok=False);checks=[];torch.set_num_threads(2)
 p=load('artificial_H1_twofold_prediction_entry',HERE/'bcsp_p2_h1_twofold_predict_v1.py')
 def check(n,v):
  if not bool(v):raise AssertionError(n)
  checks.append(n)
 def rejects(n,fn):
  try:fn()
  except (RuntimeError,ValueError,KeyError,AssertionError):checks.append(n)
  else:raise AssertionError(n)
 def rec(path):return dict(path=str(path.absolute()),bytes=path.stat().st_size,sha256=p.sha(path))
 def emit(n,v):
  path=F/n;p.emit(path,v);return rec(path)
 def digest(v):return hashlib.sha256(v.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
 try:
  index=json.loads((HERE/'H1_C_D_input_index_v1.json').read_bytes())
  folds=json.loads((ROOT/'outputs/cranial_bcsp_geov1_20261024/consolidated_binding_v1/fold_binding.json').read_bytes())
  source=json.loads((ROOT/'outputs/cranial_bcsp_geov1_20261024/development_eval_v1/development_input_index_v1.json').read_bytes())
  manifest=[json.loads(s) for s in (ROOT/'outputs/cranial_bcsp_geov1_20261024/real_data_qc_v1/manifest_8192.jsonl').read_text().splitlines()]
  check('P01 twofold index complete105each',len(p.validate_index(index,folds)[1])==210)
  p.validate_source(index,source,manifest);check('P02 both folds provenance target frame exact',True)
  mutations=[('P03 missing case',lambda x:x['inputs'].pop()),('P04 wrong fold assignment',lambda x:x['inputs'][105].update(fold='C')),('P05 training source injection',lambda x:x['inputs'][0].update(source_id=x['runs'][0]['train_sources'][0])),('P06 wrong cross-storage path',lambda x:x['inputs'][0]['input'].update(path=x['inputs'][0]['input']['path'].replace('foldd','foldc'))),('P07 checkpoint hash drift',lambda x:x['runs'][1]['checkpoint'].update(sha256='0'*64)),('P08 H1 weight drift',lambda x:x['runs'][0]['H1'].update(weight=.2)),('P09 wrong model variant',lambda x:x['runs'][1].update(variant='T0')),('P10 case duplicate',lambda x:x['inputs'].__setitem__(1,x['inputs'][0]))]
  for name,change in mutations:
   x=copy.deepcopy(index);change(x);rejects(name,lambda:p.validate_index(x,folds))
  x=copy.deepcopy(index);x['inputs'][105]['normalization']['scale']*=1.1
  rejects('P11 D provenance frame drift',lambda:p.validate_source(x,source,manifest))
  static=json.loads((ROOT/'outputs/cranial_bcsp_mamba_p2_20261106/H1_implementation_v1/first_FoldC_request_v1/transport_payload/static_H1_training_config_v1.json').read_bytes())
  baseline=copy.deepcopy(static['model']);baseline.pop('coarse_geometry_guard')
  p.validate_static_h1(static,baseline);check('P12 H1-only baseline YAML delta',True)
  bad=copy.deepcopy(static);bad['model']['denoise_weight']=.1
  rejects('P13 unrelated model config rejected',lambda:p.validate_static_h1(bad,baseline))
  proto=json.loads((HERE/'H1_C_D_prediction_protocol_v1.json').read_bytes())
  counter=0
  def chain(auth=True,reverse=False,budget=210):
   nonlocal counter
   counter+=1;qr=emit('q'+str(counter)+'.json',dict(schema='bcsp-p2-H1-twofold-development-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',forward_budget=budget,batch_size=1,backward=0,optimizer_steps=0,BNCal=0,loss_calls=0,input_index=rec(HERE/'H1_C_D_input_index_v1.json'),protocol=rec(HERE/'H1_C_D_prediction_protocol_v1.json')))
   ar=emit('a'+str(counter)+'.json',dict(schema='bcsp-development-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=auth,user_authorization_text='ARTIFICIAL ONLY'))
   rr=emit('r'+str(counter)+'.json',dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if reverse else ar['sha256']))
   return qr,ar,rr
  p.authorize(*chain());check('P14 full authorize one-way contract',True)
  rejects('P15 execution authorization required',lambda:p.authorize(*chain(auth=False)))
  rejects('P16 runtime binding drift rejected',lambda:p.authorize(*chain(reverse=True)))
  rejects('P17 extra forwards rejected',lambda:p.authorize(*chain(budget=211)))
  # Real frozen audit files contain metadata only, no checkpoint deserialization.
  H=ROOT/'outputs/cranial_bcsp_mamba_p2_20261106/H1_implementation_v1'
  evidence=dict(training_audits={'C':rec(H/'post_training_freeze_audit_v1/audit_report_v1.json'),'D':rec(H/'FoldD_request_v1/post_training_freeze_audit_v1/audit_report_v1.json')},implementation={},dependencies=[],numeric_policy=emit('policy_fixture.json',{'ARTIFICIAL_ONLY':True}),protocol=rec(HERE/'H1_C_D_prediction_protocol_v1.json'),entry=rec(HERE/'bcsp_p2_h1_twofold_predict_v1.py'),P3=emit('p3_fixture.json',dict(status='LOCAL_H1_TWOFOLD_PREDICTION_P3_PASS',entry_sha256=p.sha(HERE/'bcsp_p2_h1_twofold_predict_v1.py'))))
  p.validate_evidence(evidence,index);check('P18 real twofold frozen training audit contract',True)
  wrong=copy.deepcopy(evidence);wrong['training_audits']['D']=wrong['training_audits']['C']
  rejects('P19 wrong fold audit rejected',lambda:p.validate_evidence(wrong,index))

  class Tiny(torch.nn.Module):
   def __init__(self,mode=None):
    super().__init__();self.bn=torch.nn.BatchNorm1d(3);self.calls=0;self.mode=mode
    self.num_query=256;self.num_points=8192;self.factor=32;self.decoder_type='fc'
    self.denoise_weight=0;self.fine_coverage_weight=1;self.fine_local_weight=0
    self.base_model=types.SimpleNamespace(center_num=[512,256],encoder_type='graph',query_selection='learned_only',use_denoise=False,encoder_adapter=types.SimpleNamespace(enabled=False))
    self.scqr_contract=types.SimpleNamespace(enabled=False)
    self.local_rim_guard_enabled=self.moment_trust_enabled=self.dense_contact_enabled=self.rim_query_enabled=False
    self.coarse_geometry_guard_enabled=True;self.coarse_geometry_guard_mode='centroid_radius'
    self.coarse_geometry_guard_weight=.1;self.coarse_geometry_guard_beta=.1;self.coarse_geometry_guard_cvar_fraction=.1;self.coarse_geometry_guard_eps=1e-6
   def forward(self,x):
    self.calls+=1
    assert torch.is_inference_mode_enabled() and not torch.is_grad_enabled()
    if self.mode=='fail':raise RuntimeError('artificial failure')
    if self.mode=='rng':torch.rand(1)
    if self.mode=='state':self.bn.running_mean.add_(1)
    y=self.bn(x.transpose(1,2)).transpose(1,2)
    if self.mode=='nonfinite':y=y*float('nan')
    return y[:,:256].contiguous(),y[:,:1].expand(1,8192,3).contiguous()
  class Helper:
   tensor_sha=staticmethod(digest)
   @staticmethod
   def state_sha(m):return {k:digest(v) for k,v in m.state_dict().items()}
   @staticmethod
   def assert_numeric(t):pass
  class Budget:
   def __init__(self):self.events=[]
   def sample(self,label,count):self.events.append((label,count))
  model=Tiny();p.validate_model_h1(model);check('P20 H1 actual attribute contract accepted',True)
  model.dense_contact_enabled=True;rejects('P21 other objectives rejected',lambda:p.validate_model_h1(model))
  model.dense_contact_enabled=False
  x=np.arange(8192*3,dtype=np.float32).reshape(8192,3)/8192
  ip=F/'artificial_only.npz'
  with ip.open('xb') as f:np.savez(f,partial=x,implant=np.array([object()],dtype=object))
  check('P22 reads only partial never GT object payload',np.array_equal(p.load_partial(np,dict(input=rec(ip),n_input=8192)),x))
  cp=F/'artificial_final.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=Tiny().state_dict()),cp)
  p.load_checkpoint(torch,Tiny(),rec(cp));check('P23 actual weights_only strict synthetic final checkpoint load',True)
  broken=F/'artificial_wrong_epoch.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=98,updates=3900,base_model=Tiny().state_dict()),broken)
  rejects('P24 nonfinal checkpoint rejected',lambda:p.load_checkpoint(torch,Tiny(),rec(broken)))
  runs=copy.deepcopy(index['runs']);rows=copy.deepcopy(index['inputs'])
  for run in runs:run['checkpoint']=rec(cp)
  for row in rows:row['input']=rec(ip)
  built=[]
  def builder(run,mode=None):
   m=Tiny(mode);built.append(m)
   return m,dict(variant='M0',replaced_global_branches=6,common_state_unchanged=True,artificial_fixture=False)
  out=F/'successful210';out.mkdir();(out/'predictions').mkdir();budget=Budget()
  preds,extra,models=p.execute_pair(torch,np,Helper,runs,rows,out,budget,builder,proto['coarse_tensor_cases_by_fold'],device='cpu')
  check('P25 full artificial twofold105each210 exact no warmup',len(preds)==210 and [m.calls for m in built]==[105,105])
  events=[json.loads(s) for s in (out/'inference_manifest.jsonl').read_text().splitlines()]
  check('P26 correct C/D manifest fold and label',all(r['fold']=='C' for r in events[:105]) and all(r['fold']=='D' for r in events[105:]) and [r['forward_index'] for r in events]==list(range(1,211)))
  check('P27 state BN and all RNG unchanged105each',all(r['state_before']==r['state_after'] and r['RNG_before']==r['RNG_after'] and r['backward']==r['optimizer']==r['BNCal']==0 for r in models))
  coarse_counts={'C':0,'D':0}
  for path in preds:
   with np.load(path,allow_pickle=False) as z:
    if 'coarse' in z:coarse_counts[path.name[0]]+=1
  check('P28 exact per-fold coarse representatives7and5',coarse_counts=={'C':7,'D':5})
  check('P29 all210 same-forward geometry summaries',len((out/'geometry_summary.jsonl').read_text().splitlines())==210)
  for name,mode in [('P30 first failure stops no second model','fail'),('P31 nonfinite output stops','nonfinite'),('P32 RNG mutation detected','rng'),('P33 persistent BN mutation detected','state')]:
   failout=F/('failure_'+mode);failout.mkdir();(failout/'predictions').mkdir();built.clear()
   rejects(name,lambda:p.execute_pair(torch,np,Helper,runs,rows,failout,Budget(),lambda r:builder(r,mode),proto['coarse_tensor_cases_by_fold'],device='cpu'))
   assert len(built)==1 and (failout/'failure.json').is_file()
  archive=p.pack(out,preds+extra)
  check('P34 archive exact predictions and metadata count',len(archive['members'])==213 and archive['bytes']>0)
  # Prove safety-critical reused functions remain AST-identical rather than rewriting fixtures.
  parent=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/paired_development_evaluator_v2/bcsp_p1_paired_predict_v2.py'
  def funcs(path):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  a=funcs(parent);b=funcs(HERE/'bcsp_p2_h1_twofold_predict_v1.py')
  unchanged=['load_partial','load_checkpoint','predict_once','ExactSourceReads','source_module','load_p1_factory','make_policy','Budget','pack','rng_state','geometry_summary']
  check('P35 inherited payload/source/backend-adjacent guards AST unchanged',all(a[k]==b[k] for k in unchanged))
  realH=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'
  im={k:rec(realH/n) for k,n in [('encoder','bcsp_mamba_encoder_v1.py'),('factory','bcsp_p1_model_factory_v1.py')]}
  guard=p.ExactSourceReads(im)
  try:
   check('P36 exact encoder factory read pin verified',all(guard.allow(r['path']) for r in im.values()))
   rejects('P37 bound source write refused',lambda:guard.allow(im['encoder']['path'],True))
   fake=copy.deepcopy(im);fake['encoder']['sha256']='0'*64
   rejects('P38 source hash drift refused',lambda:p.ExactSourceReads(fake))
  finally:guard.close()
  result=dict(status='ARTIFICIAL_CPU_CONTRACT_PASS',checks_passed=len(checks),checks=checks,python=sys.version,torch=torch.__version__,numpy=np.__version__,synthetic_successful_forwards=210,additional_artificial_failure_scenarios=True,real_model_or_checkpoint_loaded=False,real_point_payloads_read=0,CUDA_used=False,server_operations=0,limitations=['Tiny synthetic models and artificial NPZ/checkpoints only; no native Mamba/PointNet2/CUDA construction','Frozen real metadata read only; guard correctness partly inherited via exact AST comparison'])
  emit('result_v1.json',result)
  print(json.dumps(dict(status=result['status'],checks_passed=len(checks),real_forwards=0,synthetic_successful_forwards=210)))
 except BaseException as e:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(e),checks_passed=len(checks),checks=checks));raise
if __name__=='__main__':main()
