"""One synthetic CPU batch: actual H2 checkpoint load/forward loop/read policy; no real weights."""
import ast,copy,hashlib,importlib.util,json,random,subprocess,sys,types
from pathlib import Path
import numpy as np
import torch
S=Path(__file__).resolve().parent;R=S.parents[2];PRE=S.parent/'H2_fourmodel_prediction_preparation_v1';O=S/'artificial_cpu_batch_v2'
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def main():
 O.mkdir();checks=[];torch.set_num_threads(2);p=load('H2_predict_cpu_entry',S/'bcsp_h2_fourmodel_native_predict_v1.py')
 def check(n,v):
  if not v:raise AssertionError(n)
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (RuntimeError,ValueError,AssertionError,KeyError):checks.append(n)
  else:raise AssertionError(n)
 def rec(path):return dict(path=str(path.absolute()),bytes=path.stat().st_size,sha256=p.sha(path))
 def emit(n,v):
  f=O/n;p.emit(f,v);return rec(f)
 def fingerprint(m,parameter_only=False):
  items=m.named_parameters() if parameter_only else m.state_dict().items();return hashlib.sha256(b''.join(n.encode()+v.detach().cpu().contiguous().numpy().tobytes() for n,v in items)).hexdigest()
 try:
  index=json.loads((PRE/'H2_C_D_fourmodel_input_index_v1.json').read_bytes());proto=json.loads((PRE/'H2_fourmodel_native_prediction_protocol_v1.json').read_bytes());G=R/'outputs/cranial_bcsp_geov1_20261024'
  folds=json.loads((G/'consolidated_binding_v1/fold_binding.json').read_bytes());source=json.loads((G/'development_eval_v1/development_input_index_v1.json').read_bytes());manifest=[json.loads(x) for x in (G/'real_data_qc_v1/manifest_8192.jsonl').read_text().splitlines()]
  check('01 real frozen four model420 index',len(p.validate_index(index,folds)[1])==420)
  p.validate_source(index,source,manifest);check('02 exact original source frame across both arms',True)
  for name,fn in [('03 missing row',lambda x:x['inputs'].pop()),('04 mode mismatch',lambda x:x['runs'][1].update(mode='AUX')),('05 checkpoint drift',lambda x:x['runs'][2]['checkpoint'].update(sha256='0'*64)),('06 train source injected',lambda x:x['inputs'][0].update(source_id=x['runs'][0]['train_sources'][0])),('07 wrong fold',lambda x:x['inputs'][210].update(fold='C')),('08 duplicated input identity',lambda x:x['inputs'].__setitem__(1,x['inputs'][0]))]:
   bad=copy.deepcopy(index);fn(bad);reject(name,lambda:p.validate_index(bad,folds))
  bad=copy.deepcopy(index);bad['inputs'][105]['normalization']['scale']*=1.1;reject('09 altered frame provenance rejected',lambda:p.validate_source(bad,source,manifest))
  serial=0
  def triplet(yes=True,bad_runtime=False,budget=420):
   nonlocal serial
   serial+=1;qr=emit('q'+str(serial)+'.json',dict(schema='bcsp-p2-H2-fourmodel-native-prediction-v1',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',forward_budget=budget,batch_size=1,backward=0,optimizer_steps=0,BNCal=0,loss_calls=0,input_index=rec(PRE/'H2_C_D_fourmodel_input_index_v1.json'),protocol=rec(PRE/'H2_fourmodel_native_prediction_protocol_v1.json')));ar=emit('a'+str(serial)+'.json',dict(schema='bcsp-development-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_TEST_ONLY'));rr=emit('r'+str(serial)+'.json',dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if bad_runtime else ar['sha256']));return qr,ar,rr
  p.authorize(*triplet());check('10 full one-way authorization',True);reject('11 explicit authorization required',lambda:p.authorize(*triplet(False)));reject('12 runtime binding mismatch',lambda:p.authorize(*triplet(bad_runtime=True)));reject('13 extra forward forbidden',lambda:p.authorize(*triplet(budget=421)))
  evidence=dict(training_audits={k:v['formal_audit'] for k,v in index['training_audit_evidence'].items()},implementation={},dependencies=[],numeric_policy=emit('numeric_fixture.json',{}),protocol=rec(PRE/'H2_fourmodel_native_prediction_protocol_v1.json'),entry=rec(S/'bcsp_h2_fourmodel_native_predict_v1.py'),P3=emit('p3_fixture.json',dict(status='LOCAL_H2_FOURMODEL_PREDICTION_P3_PASS',entry_sha256=p.sha(S/'bcsp_h2_fourmodel_native_predict_v1.py'))))
  p.validate_evidence(evidence,index);check('14 all four actual frozen audits checked',True)
  bad=copy.deepcopy(evidence);bad['training_audits']['D_AUX']=bad['training_audits']['C_AUX'];reject('15 wrong training audit rejected',lambda:p.validate_evidence(bad,index))
  t=load('H2_existing_artificial_model',S.parent/'H2_implementation_v1/test_h2_cpu_v2.py');adapter=t.a
  def builder(mode):
   def make():
    m=t.Model();m.base_model.center_num=[512,256];m.base_model.encoder_type='graph';return m
   m,ev=adapter.build_h2(t.Factory(),make,mode);ev.update(replaced_global_branches=6,artificial_fixture=False);return m,ev
  saved={};models={}
  for mode in ['AUX','COUPLE']:
   m,_=builder(mode);m.h2_range_head.bias.data.fill_(.12);f=O/('synthetic_'+mode+'.pth');torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,H2=dict(p.H2_COMMON,mode=mode),base_model=m.state_dict()),f);saved[mode]=rec(f);models[mode]=m
  for mode in models:
   m,_=builder(mode);p.load_checkpoint(torch,m,dict(mode=mode,checkpoint=saved[mode]));p.validate_model_h2(m,mode);check('16 '+mode+' actual strict synthetic checkpoint load',fingerprint(m)==fingerprint(models[mode]))
  m,_=builder('AUX');reject('17 wrong checkpoint mode',lambda:p.load_checkpoint(torch,m,dict(mode='AUX',checkpoint=saved['COUPLE'])))
  raw=torch.load(saved['AUX']['path'],weights_only=True);bad=copy.deepcopy(raw);bad['H2']['maximum_scale']=2.;f=O/'wrong_constants.pth';torch.save(bad,f);reject('18 checkpoint constants drift',lambda:p.load_checkpoint(torch,builder('AUX')[0],dict(mode='AUX',checkpoint=rec(f))))
  bad=copy.deepcopy(raw);bad['base_model'].pop('h2_range_head.weight');f=O/'missing_head.pth';torch.save(bad,f);reject('19 strict missing head key',lambda:p.load_checkpoint(torch,builder('AUX')[0],dict(mode='AUX',checkpoint=rec(f))))
  bad=copy.deepcopy(raw);bad['base_model']['unexpected']=torch.zeros(1);f=O/'extra_key.pth';torch.save(bad,f);reject('20 strict extra key',lambda:p.load_checkpoint(torch,builder('AUX')[0],dict(mode='AUX',checkpoint=rec(f))))
  bad=copy.deepcopy(raw);bad['updates']=3899;f=O/'wrong_updates.pth';torch.save(bad,f);reject('21 final update metadata',lambda:p.load_checkpoint(torch,builder('AUX')[0],dict(mode='AUX',checkpoint=rec(f))))
  # Partial-only read: archive proxy raises on any attempt to access G/target.
  x,g=t.inputs();array=x[0].numpy();npz=O/'artificial_input.npz'
  with npz.open('xb') as f:np.savez_compressed(f,partial=array,GT=np.full((1,),np.nan,dtype=np.float32))
  accessed=[]
  class Archive:
   def __enter__(self):return self
   def __exit__(self,*args):pass
   def __getitem__(self,key):accessed.append(key);assert key=='partial';return array
  proxy=types.SimpleNamespace(load=lambda *args,**kw:Archive(),float32=np.float32,isfinite=np.isfinite)
  p.load_partial(proxy,dict(input=rec(npz),n_input=8192));check('22 partial only, no GT key',accessed==['partial'])
  helper=types.SimpleNamespace(assert_numeric=lambda t:None,state_sha=fingerprint,tensor_sha=lambda x:hashlib.sha256(x.cpu().numpy().tobytes()).hexdigest())
  synthetic_runs=[];synthetic_rows=[]
  for run in index['runs']:
   rr=copy.deepcopy(run);rr['checkpoint']=saved[rr['mode']];synthetic_runs.append(rr)
   for row in [r for r in index['inputs'] if r['run']==run['label']]:z=copy.deepcopy(row);z['input']=rec(npz);synthetic_rows.append(z)
  out=O/'synthetic420';out.mkdir();(out/'predictions').mkdir();resources=[]
  budget=types.SimpleNamespace(sample=lambda label,count:resources.append((label,count)))
  def build(run):return builder(run['mode'])
  pred,logs,states=p.execute_pair(torch,np,helper,synthetic_runs,synthetic_rows,out,budget,build,proto['coarse_tensor_cases_by_fold'],device='cpu')
  check('23 exact420 actual synthetic forwards and files',len(pred)==420 and len(set(pred))==420 and len(states)==4 and all(v['forwards']==105 for v in states))
  check('24 state BN and all CPU/Python/numpy RNG unchanged',all(v['state_before']==v['state_after'] and v['RNG_before']==v['RNG_after'] for v in states))
  journal=[json.loads(x) for x in (out/'forward_attempts.jsonl').read_text().splitlines()];check('25 exact pre-forward journal',len(journal)==420 and [r['forward_index'] for r in journal]==list(range(1,421)))
  events=[json.loads(x) for x in (out/'geometry_summary.jsonl').read_text().splitlines()];check('26 native H2 logs no intervention or GT loss',len(events)==420 and all(r['H2']['condition_override'] is None and r['H2']['GT_read'] is False and r['H2']['loss_calls']==0 for r in events))
  check('27 AUX identity and COUPLE scaling in actual native logs',all(r['H2']['scale']==[1.] and r['H2']['raw']==r['H2']['used'] for r in events if r['H2']['mode']=='AUX') and all(r['H2']['scale'][0]>1 for r in events if r['H2']['mode']=='COUPLE'))
  check('28 inherited before after resource sampling count',len(resources)==845 and resources[-1]==('all_complete',420))
  m,_=builder('COUPLE');m.eval();m.h2_intervention(0);reject('29 condition override forbidden',lambda:p.validate_model_h2(m,'COUPLE'))
  # Actual exact-source loader under a real audit hook, including range->adapter import.
  sf=O/'source_policy';sf.mkdir();owned=sf/'owned';owned.mkdir();code={'encoder':'VALUE=3\n','factory':'from bcsp_mamba_encoder_v1 import VALUE\n','h2_range':'VALUE=7\n','h2_adapter':'from bcsp_h2_range_v1 import VALUE\n'};names={'encoder':'bcsp_mamba_encoder_v1.py','factory':'factory.py','h2_range':'bcsp_h2_range_v1.py','h2_adapter':'adapter.py'};impl={}
  for k,c in code.items():f=sf/names[k];f.write_bytes(c.encode('utf-8'));impl[k]=rec(f)
  neighbor=sf/'neighbor.py';neighbor.write_text('VALUE=99\n');f=emit('source_policy_fixture.json',dict(implementation=impl,entry=rec(S/'bcsp_h2_fourmodel_native_predict_v1.py'),helper=rec(G/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'),owned=str(owned.absolute()),neighbor=str(neighbor.absolute())))
  child=r"""
import hashlib,importlib.util,json,sys,types
from pathlib import Path
c=json.loads(Path(sys.argv[1]).read_bytes())
def load(n,r):
 assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'];s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
p=load('source_policy_entry',c['entry']);h=load('source_policy_helper',c['helper']);guard=p.ExactSourceReads(c['implementation']);utc=types.SimpleNamespace(allow=lambda *x:False);policy=p.make_policy(h,[],c['owned'],[],[],[],utc,guard);sys.addaudithook(policy.audit)
factory,adapter=p.load_h2_builder(c['implementation']);assert factory.VALUE==3 and adapter.VALUE==7
def reject(fn):
 try:fn()
 except (RuntimeError,ValueError):return True
 raise AssertionError('unexpected source policy allow')
assert reject(lambda:Path(c['implementation']['h2_range']['path']).open('w')) and reject(lambda:Path(c['neighbor']).read_text())
print(json.dumps(dict(actual_four_source_load_under_hook=True,exact_source_write_denied=True,neighbor_source_denied=True)))
guard.close()
"""
  proc=subprocess.run([sys.executable,'-I','-B','-c',child,f['path']],capture_output=True,timeout=20)
  for k,b in [('stdout',proc.stdout),('stderr',proc.stderr)]:
   with (O/('source_policy_child_'+k+'.bin')).open('xb') as fp:fp.write(b)
  check('30 actual four source load under audit hook and adjacent denial',proc.returncode==0 and all(json.loads(proc.stdout).values()))
  parent=ast.parse((S.parent/'H1_prediction_implementation_v1/bcsp_p2_h1_twofold_predict_v1.py').read_text());current=ast.parse((S/'bcsp_h2_fourmodel_native_predict_v1.py').read_text());node=lambda t,n:next(x for x in t.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==n)
  unchanged=['load_partial','predict_once','source_module','make_policy','Budget','pack','rng_state','geometry_summary']
  check('31 core read numeric memory and RNG guards AST unchanged',all(ast.dump(node(parent,n),include_attributes=False)==ast.dump(node(current,n),include_attributes=False) for n in unchanged))
  # Failure remains stop-first, never continue into another model.
  failout=O/'forced_failure';failout.mkdir();(failout/'predictions').mkdir();calls=[]
  def broken(run):calls.append(run['label']);raise RuntimeError('ARTIFICIAL_STOP')
  reject('32 fail immediately no next model',lambda:p.execute_pair(torch,np,helper,synthetic_runs,synthetic_rows,failout,budget,broken,proto['coarse_tensor_cases_by_fold'],device='cpu'))
  check('33 first error persisted no successful forward',calls==['C_AUX'] and json.loads((failout/'failure.json').read_bytes())['forward_attempts']==0)
  emit('result_v1.json',dict(status='H2_FOURMODEL_PREDICTION_CPU_CONTRACT_PASS',checks_passed=len(checks),checks=checks,synthetic_forwards=420,synthetic_checkpoint_loads=4,optimizer_steps=0,backward=0,loss_calls=0,real_model_or_checkpoint_or_payload_loads=0,server_operations=0,CUDA_used=False,source_bindings=[rec(S/'bcsp_h2_fourmodel_native_predict_v1.py'),rec(S.parent/'H2_implementation_v1/bcsp_h2_range_v1.py'),rec(S.parent/'H2_implementation_v1/bcsp_h2_model_adapter_v1.py')],limitations='Actual parent forward AST with artificial local operators and native factory facade; synthetic state/checkpoint/NPZ only. CUDA RNG not exercised on CPU. Full420-loop verification is synthetic, not real Mamba/PointNet2/CUDA performance.'))
  print(json.dumps(dict(status='H2_FOURMODEL_PREDICTION_CPU_CONTRACT_PASS',checks=len(checks),synthetic_forwards=420)))
 except BaseException as exc:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks));raise
if __name__=='__main__':main()
