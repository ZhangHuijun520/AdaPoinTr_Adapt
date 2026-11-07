"""One local artificial batch. No real arrays, checkpoint, native Mamba or CUDA."""
import ast,copy,hashlib,importlib.util,json,subprocess,sys,types
from pathlib import Path
import torch
S=Path(__file__).resolve().parent;R=S.parents[2];G=R/'outputs/cranial_bcsp_geov1_20261024'
O=S/'artificial_cpu_batch_v1'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 O.mkdir();checks=[];torch.set_num_threads(2)
 def emit(n,v):
  p=O/n
  with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
  return bind(p)
 def check(n,v):
  if not v:raise AssertionError(n)
  checks.append(n)
 def rejects(n,fn):
  try:fn()
  except (ValueError,RuntimeError):checks.append(n)
  else:raise AssertionError(n)
 try:
  e=load('h2_couple_entry_test',S/'bcsp_h2_couple_foldC_training_entry_v2.py')
  cpath=G/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1/bcsp_training_contract_01dt08_v3.py'
  c=load('bcsp_training_contract_v1',cpath)
  static=json.loads((G/'first_run_freeze_foldC_8192_v1/static_training_config_v1.json').read_bytes());candidate=dict(static,H2=e.H2)
  check('01 exact static H2-only delta',e.validate_static_h2(candidate,static,c)==candidate)
  for n,fn in [('02 H1 forbidden',lambda x:x['model'].update(coarse_geometry_guard={'enabled':True})),('03 count unchanged',lambda x:x['counts'].update(updates=3901)),('04 AUX not this run',lambda x:x['H2'].update(mode='AUX')),('05 resources unchanged',lambda x:x['resources'].update(device_MiB=24000))]:
   bad=copy.deepcopy(candidate);fn(bad);rejects(n,lambda:e.validate_static_h2(bad,static,c))
  # Real metadata validator, exclusively artificial rows. Production pins restored below.
  sources=['fixture:'+str(i).zfill(3) for i in range(84)];ids=[s.replace(':','__')+'__defect'+str(j) for s in sources for j in range(5)];manifests={}
  for count in (8192,16384):
   p=O/('manifest_'+str(count)+'.jsonl')
   with p.open('x') as f:
    for i,cid in enumerate(ids):f.write(json.dumps(dict(case_id=cid,source_id=sources[i//5],target_array_sha256='0'*64,normalization={'center':[0,0,0],'scale':1},raw={'origin':'ARTIFICIAL_ONLY'},schema='BCSP-normalized-v1',normalization_source='defective_bbox',n_input=count,n_target=8192,point_path='points/'+cid+'_'+str(count)+'.npz',sha256='1'*64))+'\n')
   manifests[str(count)]=bind(p)
  fid=ids[:315];fold=dict(train_case_ids=fid,train_sources=sources[:63],dev_sources=sources[63:],train_allowlist_sha256=hashlib.sha256(('\n'.join(fid)+'\n').encode()).hexdigest())
  fr=emit('fold.json',dict(folds={'C':fold},confirmation_count_excluded=20))
  vr=emit('qc.json',dict(status=c.QC_STATUS,verified_sources=84,verified_cases=420,verified_point_files=840,interpretation={'anatomical_semantics':'UNRESOLVED artificial fixture'},important_file_hashes={'manifest_'+k+'.jsonl':v['sha256'] for k,v in manifests.items()}))
  qualified,selected,_=c.bind_metadata(vr,manifests,fr,'C',8192)
  plan=dict(schema='bcsp-shared-order-v1',case_ids=fid,epochs=[dict(epoch=i,batches=[fid[j:j+8] for j in range(0,312,8)],dropped=fid[312:]) for i in range(100)])
  impl=dict(entry=bind(S/'bcsp_h2_couple_foldC_training_entry_v2.py'),contract=bind(cpath),runtime=bind(S.parent/'H2_implementation_v1/bcsp_h2_training_runtime_v1.py'))
  base=dict(schema='ARTIFICIAL_BASELINE_ONLY',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='P1',variant='M0',fold='C',n_input=8192,n_output=8192,static_config=emit('baseline_static.json',static),QC=dict(qualified_receipt=emit('qualified.json',qualified),verification=vr,manifests=manifests,fold_binding=fr),order_plan=emit('order.json',plan),implementation=impl,identity=e.CURRENT_IDENTITY,environment={'CUDA_VISIBLE_DEVICES':e.CURRENT_IDENTITY['gpu_uuid']},run_id='ARTIFICIAL_BASELINE',output=str(O/'baseline'),launch_attempt=str(O/'old_claim'),launch_contract={},provenance={},not_authorized=[])
  br=emit('baseline.json',base);ba=emit('baseline_audit.json',dict(status='FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS',request_sha256=br['sha256'],checks_passed=1,checks={'ARTIFICIAL_ONLY':True}))
  ca=emit('cuda_audit_fixture.json',{'status':'FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS'})
  p3=emit('p3_fixture.json',dict(status='LOCAL_H2_COUPLE_TRAINING_ENTRY_P3_PASS',entry_sha256=impl['entry']['sha256'],H2_source_hashes=e.H2_HASHES))
  ready=emit('readiness_fixture.json',dict(status='BOUNDED_H2_AUX_C_READINESS_PASS',identity=e.CURRENT_IDENTITY,training_payloads=315))
  q=copy.deepcopy(base);q.update(schema='bcsp-p2-H2-COUPLE-training-request-v1',stage='CRANIAL_BCSP_MAMBA_P2_H2',baseline_request=br,baseline_audit=ba,cuda_audit=ca,p3=p3,readiness=ready,h2_config=e.H2,static_config=emit('candidate_static.json',candidate))
  q['implementation'].update(h2_range=bind(S.parent/'H2_implementation_v1/bcsp_h2_range_v1.py'),h2_adapter=bind(S.parent/'H2_implementation_v1/bcsp_h2_model_adapter_v1.py'))
  auxinitial=emit('aux_initial_fixture.json',dict(parameter_sha256='1'*64,persistent_state_sha256='2'*64,order_sha256=c.canonical_sha(plan),seed=0))
  auxq=copy.deepcopy(q);auxq['h2_config']=dict(e.H2,mode='AUX');auxq['static_config']=emit('aux_static_fixture.json',dict(static,H2=dict(e.H2,mode='AUX')))
  auxq['implementation']['entry']=bind(S.parent/'H2_AUX_foldC_training_preparation_v1/bcsp_h2_aux_foldC_training_entry_v1.py')
  auxqr=emit('aux_request_fixture.json',auxq)
  auxar=emit('aux_audit_fixture.json',dict(status='FORMAL_H2_AUX_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS',request_sha256=auxqr['sha256'],checks_passed=1,checks={'ARTIFICIAL_ONLY':True},initialization={'record':json.loads(Path(auxinitial['path']).read_bytes())}))
  q['aux_pairing']=dict(request=auxqr,audit=auxar,initialization=auxinitial)
  oldpairpins=e.AUX_PAIR_PINS;e.AUX_PAIR_PINS={k:r['sha256'] for k,r in q['aux_pairing'].items()}
  oldpins=e.FROZEN_BASELINES;oldcuda=e.CUDA_AUDIT_SHA
  e.FROZEN_BASELINES={'C':dict(request_sha256=br['sha256'],audit_sha256=ba['sha256'])};e.CUDA_AUDIT_SHA=ca['sha256'];serial=0
  def triple(v,authorized=True,bad_runtime=False):
   nonlocal serial
   serial+=1;qr=emit('q'+str(serial)+'.json',v);ar=emit('a'+str(serial)+'.json',dict(schema='bcsp-p2-H2-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=authorized,user_authorization_text='ARTIFICIAL TEST ONLY'))
   rr=emit('r'+str(serial)+'.json',dict(schema='bcsp-p2-H2-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if bad_runtime else ar['sha256']));return qr,ar,rr
  try:
   out=e.authorize(*triple(q));check('06 full actual authorize 315 rows 100 traversals',len(out[3])==315 and len(out[5]['epochs'])==100)
   bad=copy.deepcopy(q);bad['aux_pairing']['audit']['sha256']='0'*64
   rejects('25 AUX audit binding cannot drift',lambda:e.authorize(*triple(bad)))
   rejects('07 explicit authorization required',lambda:e.authorize(*triple(q,False)))
   rejects('08 one-way runtime binding',lambda:e.authorize(*triple(q,bad_runtime=True)))
   for n,fn in [('09 device drift rejected',lambda x:x['identity'].update(gpu_uuid='OTHER')),('10 fold D rejected',lambda x:x.update(fold='D')),('11 order drift rejected',lambda x:x['order_plan'].update(sha256='0'*64)),('12 source drift rejected',lambda x:x['implementation']['runtime'].update(sha256='0'*64)),('13 unknown field rejected',lambda x:x.update(extra=True))]:
    bad=copy.deepcopy(q);fn(bad);rejects(n,lambda:e.authorize(*triple(bad)))
  finally:e.FROZEN_BASELINES=oldpins;e.CUDA_AUDIT_SHA=oldcuda;e.AUX_PAIR_PINS=oldpairpins
  check('14 production pins restored',e.CUDA_AUDIT_SHA=='545a5996309fbc865beb145f4a1df4aef5e2077e4374d52a6fc930dd9080313c' and e.FROZEN_BASELINES['C']['request_sha256']=='48dedc867ce2a9c46bc1a6fdc7db3506b6f2405dbdf914de49cf561e2fe12b54')
  t=load('h2_previous_artificial_fixture',S.parent/'H2_implementation_v1/test_h2_cpu_v2.py');a=t.a
  def builder():
   m=t.Model();m.base_model.center_num=[512,256];m.base_model.encoder_type='graph';return m
  model=a.build_h2(t.Factory(),builder,'COUPLE')[0];e.validate_model_h2(model)
  check('15 actual adapter zero head accepted',sum(p.numel() for p in model.h2_range_head.parameters())==1025)
  model.h2_range_head.bias.data.fill_(.1);rejects('16 synthetic CUDA bias rejected',lambda:e.validate_model_h2(model))
  model.h2_range_head.bias.data.zero_();model.coarse_geometry_guard_enabled=True;rejects('17 H1 cannot leak',lambda:e.validate_model_h2(model))
  # Mock the native boundary explicitly; actual dispatch and adapter, no real Mamba/provider.
  class Factory:
   def build_model(self,b,variant,seed=0):
    m,ev=t.Factory().build_model(b,variant,seed);ev['artificial_fixture']=False;return m,ev
  expected={'variant':'M0','common_state_unchanged':True,'artificial_fixture':False};captured={}
  class Runtime:
   def BCSPDataset(self,*args):captured['dataset']=args;return 'ARTIFICIAL_DATASET'
   def make_loader(self,*args):return ('ARTIFICIAL_LOADER',args)
   def train_lifecycle(self,m,loader,records,p,output,**kw):captured.update(model=m,plan=p,records=records,options=kw,loader=loader(0));return 'NOT_TRAINED'
  helper=types.SimpleNamespace(assert_numeric=lambda x:None,state_sha=lambda x,parameter_only=False:('1' if parameter_only else '2')*64);budget=types.SimpleNamespace()
  dq=dict(variant='M0',fold='C',data_root='ARTIFICIAL_ONLY',stage='TEST_ONLY',numeric_policy={'sha256':'0'*64},cuda_audit={'sha256':oldcuda},aux_pairing={'initialization':auxinitial},output='ARTIFICIAL_ONLY')
  result=e.dispatch_training(dq,candidate,selected,fold,plan,factory=Factory(),h2_adapter=a,model_builder=builder,runtime=Runtime(),helper=helper,budget=budget,torch=torch,knn_enable=lambda:None,expected_factory=expected,device='cpu')
  check('18 actual dispatch scratch COUPLE zero head',result=='NOT_TRAINED' and captured['model'].h2_metadata()==e.H2 and captured['model'].h2_range_head.bias.item()==0)
  check('19 exact original plan dataset forwarded',captured['plan'] is plan and captured['dataset']==('ARTIFICIAL_ONLY',selected,fold['train_sources'],8192))
  check('20 CPU dispatch no optimizer or real arrays',captured['options']['device']=='cpu' and captured['records'] is selected)
  raw=(S/'bcsp_h2_couple_foldC_training_entry_v2.py').read_text();pt=ast.parse((S.parent/'H1_implementation_v1/bcsp_p2_h1_training_entry_v1.py').read_text());ct=ast.parse(raw)
  node=lambda tree,name:next(x for x in tree.body if isinstance(x,(ast.FunctionDef,ast.ClassDef)) and x.name==name)
  for n in ['TrainingBudget','P1Budget','payload_paths','make_training_policy']:
   assert ast.dump(node(pt,n),include_attributes=False)==ast.dump(node(ct,n),include_attributes=False)
  check('21 resource and payload guards AST unchanged',True)
  check('22 training imports bind own exact H2 modules',"load_bound('bcsp_h2_range_v1'" in raw and "load_bound('bcsp_h2_model_adapter_v1'" in raw and "str(impl),str(Path(q['implementation']['h2_range']['path']).parent),str(factory_root)" in raw)
  check('23 no checkpoint initialization or eval',not any(k in raw for k in ['torch.load(','load_state_dict(','model.eval()']))
  check('24 PID telemetry consistent with accepted policy',"and not helper.smi('pid',True)" not in raw and "int(gpu[4])<=256" in raw and e.RESOURCES==static['resources'])
  check('26 AUX production pairing pins restored',e.AUX_PAIR_PINS==oldpairpins and e.AUX_PAIR_PINS['audit']=='580a0b195c5730e56f260e357e135966e2ab954b9cef7582ff7298b35d33ee1c')
  badhelper=types.SimpleNamespace(assert_numeric=lambda x:None,state_sha=lambda x,parameter_only=False:'0'*64)
  rejects('27 different full initialization rejected',lambda:e.dispatch_training(dq,candidate,selected,fold,plan,factory=Factory(),h2_adapter=a,model_builder=builder,runtime=Runtime(),helper=badhelper,budget=budget,torch=torch,knn_enable=lambda:None,expected_factory=expected,device='cpu'))
  aux,auxev=a.build_h2(t.Factory(),builder,'AUX');couple,coupleev=a.build_h2(t.Factory(),builder,'COUPLE')
  check('28 same full initial AUX COUPLE state',set(aux.state_dict())==set(couple.state_dict()) and all(torch.equal(v,couple.state_dict()[n]) for n,v in aux.state_dict().items()))
  m=captured['model'];m.h2_range_head.bias.data.fill_(.2);x,g=t.inputs();ret=m(x);context=m._h2_controller.context
  check('29 actual COUPLE path changes raw coarse',not torch.equal(context['raw'],context['used']) and context['scale'].item()>1)
  for value in [m.base_model.mlp_query.last[:,:,-3:],m.base_model.decoder.last_pos,m.reduce_map.last[:,:,-3:],ret[0]]:torch.testing.assert_close(value,context['used'],rtol=0,atol=0)
  torch.testing.assert_close(ret[3].reshape(1,256,32,3),context['used'].unsqueeze(2)+m.decode_head.last,rtol=0,atol=0)
  check('30 all five original coordinate consumers use coupled coarse',True)
  sparse,dense=m.get_loss(ret,g);event=m.h2_runtime_record()
  check('31 original actual loss adds auxiliary exactly once',event['H2_mode']=='COUPLE' and abs(float(dense)-event['loss_original_reconstruction']-event['H2_aux_weighted'])<1e-6)
  check('32 reused H2 module parent available to read policy',"read_roots=[root,impl,Path(q['implementation']['h2_range']['path']).parent" in raw)
  # Exercise the actual source read_roots expression and installed FilePolicy.audit in a child.
  helperfile=G/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'
  check('33 exact original helper source',bind(helperfile)['sha256']=='7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291')
  fixture=O/'policy_fixture';fixture.mkdir();owned=fixture/'owned';owned.mkdir();external=fixture/'outside';external.mkdir()
  ref=external/'initialization.json';ref.write_text(json.dumps({'fixture':'EXACT_READ_ONLY'}));sibling=external/'other.json';sibling.write_text('{}');secret=external/'.env';secret.write_text('ARTIFICIAL_ONLY');ckpt=external/'old.pth';ckpt.write_bytes(b'ARTIFICIAL_ONLY');npz=external/'other.npz';npz.write_bytes(b'ARTIFICIAL_ONLY')
  roots={}
  for key in ['root','impl','factory_root','envroot','provider','contract']:
   path=fixture/key;path.mkdir();roots[key]=str(path.absolute())
  child_q=dict(implementation={'h2_range':{'path':str(Path(roots['impl'])/'range.py')},'contract':{'path':str(Path(roots['contract'])/'contract.py')}},aux_pairing={'initialization':bind(ref)})
  config=emit('policy_fixture_definition.json',dict(entry=bind(S/'bcsp_h2_couple_foldC_training_entry_v2.py'),helper=bind(helperfile),q=child_q,roots=roots,owned=str(owned.absolute()),sibling=str(sibling.absolute()),secret=str(secret.absolute()),ckpt=str(ckpt.absolute()),npz=str(npz.absolute())))
  child_code=r"""
import ast,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
cfg=json.loads(Path(sys.argv[1]).read_bytes())
def load(name,r):
 b=Path(r['path']).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
 spec=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
entry=load('policy_target_entry',cfg['entry']);helper=load('original_policy_helper',cfg['helper']);q=cfg['q'];ns=dict(Path=Path,os=os,q=q,**{k:Path(v) for k,v in cfg['roots'].items()})
tree=ast.parse(Path(cfg['entry']['path']).read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');assignment=next(n for n in ast.walk(main) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='read_roots' for t in n.targets))
roots=eval(compile(ast.Expression(assignment.value),'<actual-main-read-roots>','eval'),ns)
ref=Path(q['aux_pairing']['initialization']['path']);assert ref in roots and ref.parent not in roots
utc=types.SimpleNamespace(allow=lambda *args:False);old=entry.make_training_policy(helper,[r for r in roots if r!=ref],cfg['owned'],{},utc)
try:old.check(ref)
except RuntimeError:old_rejected=True
else:raise AssertionError('old policy unexpectedly allowed exact reference')
policy=entry.make_training_policy(helper,roots,cfg['owned'],{},utc);sys.addaudithook(policy.audit)
checks={'actual_old_policy_reproduces_boundary':old_rejected,'exact_file_not_parent_in_real_roots':True,'actual_json_bound_under_installed_audit_hook':entry.json_bound(q['aux_pairing']['initialization'])=={'fixture':'EXACT_READ_ONLY'}}
def reject(name,fn):
 try:fn()
 except (ValueError,RuntimeError):checks[name]=True
 else:raise AssertionError(name)
reject('write_to_reference_denied',lambda:ref.open('w'))
for k in ['sibling','secret','ckpt','npz']:reject(k+'_read_denied',lambda k=k:Path(cfg[k]).read_bytes())
bad=dict(q['aux_pairing']['initialization'],sha256='0'*64);reject('wrong_reference_hash_denied',lambda:entry.json_bound(bad))
bad=dict(q['aux_pairing']['initialization'],bytes=1);reject('wrong_reference_size_denied',lambda:entry.json_bound(bad))
owned=Path(cfg['owned'])/'allowed.log';owned.write_text('ARTIFICIAL_ONLY');checks['owned_log_write_still_allowed']=owned.read_text()=='ARTIFICIAL_ONLY'
checks['reference_unchanged']=hashlib.sha256(ref.read_bytes()).hexdigest()==q['aux_pairing']['initialization']['sha256']
assert all(checks.values());print(json.dumps(checks))
"""
  cp=subprocess.run([sys.executable,'-I','-B','-c',child_code,config['path']],capture_output=True,timeout=25)
  for name,data in [('stdout',cp.stdout),('stderr',cp.stderr)]:
   with (O/('actual_policy_child_'+name+'.bin')).open('xb') as f:f.write(data)
  check('34 actual policy child passes',cp.returncode==0)
  policy_checks=json.loads(cp.stdout);check('35 old boundary reproduced new exact read succeeds',policy_checks['actual_old_policy_reproduces_boundary'] and policy_checks['actual_json_bound_under_installed_audit_hook'])
  check('36 file-only allowlist not parent directory',policy_checks['exact_file_not_parent_in_real_roots'] and policy_checks['sibling_read_denied'])
  check('37 reference write denied unchanged',policy_checks['write_to_reference_denied'] and policy_checks['reference_unchanged'])
  check('38 secrets and nonallowlisted payloads denied',all(policy_checks[k+'_read_denied'] for k in ['secret','ckpt','npz']))
  check('39 reference hash and size still enforced',policy_checks['wrong_reference_hash_denied'] and policy_checks['wrong_reference_size_denied'])
  check('40 original owned log write preserved',policy_checks['owned_log_write_still_allowed'])
  emit('result_v1.json',dict(status='H2_COUPLE_ENTRY_CPU_CONTRACT_PASS',checks_passed=len(checks),checks=checks,python=sys.version,torch=torch.__version__,production_forward=0,production_backward=0,optimizer_steps=0,real_payloads_read=0,native_Mamba_loaded=False,fixture_notes='Only tests patch baseline/CUDA audit pins and native artificial flag; restored production pins and hashes verified. No production bypass flag.',source_bindings=[bind(S/'bcsp_h2_couple_foldC_training_entry_v2.py'),bind(cpath)]+[bind(S.parent/'H2_implementation_v1'/n) for n in ['bcsp_h2_range_v1.py','bcsp_h2_model_adapter_v1.py','bcsp_h2_training_runtime_v1.py']]))
  print(json.dumps(dict(status='H2_COUPLE_ENTRY_CPU_CONTRACT_PASS',checks=len(checks))))
 except BaseException as exc:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks));raise
if __name__=='__main__':main()
