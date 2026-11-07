"""Artificial-only D authorization, dispatch and real audit-hook contracts. No optimizer."""
import ast,copy,hashlib,importlib.util,json,subprocess,sys,types
from pathlib import Path
import torch
S=Path(__file__).resolve().parent;R=S.parents[2];G=R/'outputs/cranial_bcsp_geov1_20261024';O=S/'artificial_cpu_batch_v1'
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);return m
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 O.mkdir();checks=[];torch.set_num_threads(2)
 def check(n,v):
  if not v:raise AssertionError(n)
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError):checks.append(n)
  else:raise AssertionError(n)
 def emit(n,v):
  p=O/n
  with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
  return bind(p)
 try:
  ep=S/'bcsp_h2_foldD_training_entry_v1.py';e=load('foldD_entry_test',ep);cp=G/'resource_rebind_implementation_v1/monitor_diagnostic_v3/research_priority_monitor_v4/new_container_training_v1/bcsp_training_contract_01dt08_v3.py';c=load('bcsp_training_contract_v1',cp)
  t=load('D_actual_parent_artificial_ops',S.parent/'H2_implementation_v1/test_h2_cpu_v2.py');adapter=t.a
  def builder():
   m=t.Model();m.base_model.center_num=[512,256];m.base_model.encoder_type='graph';return m
  def state(m,parameter_only=False):
   items=m.named_parameters() if parameter_only else m.state_dict().items();return hashlib.sha256(b''.join(n.encode()+v.detach().contiguous().numpy().tobytes() for n,v in items)).hexdigest()
  auxmodel=adapter.build_h2(t.Factory(),builder,'AUX')[0];couplemodel=adapter.build_h2(t.Factory(),builder,'COUPLE')[0]
  check('01 AUX COUPLE identical full zero initialization',state(auxmodel)==state(couplemodel) and state(auxmodel,True)==state(couplemodel,True))
  for mode,m in [('AUX',auxmodel),('COUPLE',couplemodel)]:e.validate_model_h2(m,mode)
  check('02 both model mode guards pass zero head',True)
  reject('03 OFF rejected',lambda:e.mode_config('OFF'))
  auxmodel.h2_range_head.bias.data.fill_(.1);reject('04 nonzero training head rejected',lambda:e.validate_model_h2(auxmodel,'AUX'))
  static=json.loads((G/'first_run_freeze_foldC_8192_v1/static_training_config_v1.json').read_bytes());configs={mode:dict(static,H2=e.mode_config(mode)) for mode in ['AUX','COUPLE']}
  for mode in configs:e.validate_static_h2(configs[mode],static,c,mode)
  check('05 both static modes preserve original contract',True)
  for n,mutate in [('06 H1 rejected',lambda x:x['model'].update(coarse_geometry_guard={'enabled':True})),('07 updates drift rejected',lambda x:x['counts'].update(updates=3901)),('08 resources drift rejected',lambda x:x['resources'].update(RSS_bytes=99999999999)),('09 wrong mode static rejected',lambda x:x['H2'].update(mode='COUPLE'))]:
   bad=copy.deepcopy(configs['AUX']);mutate(bad);reject(n,lambda:e.validate_static_h2(bad,static,c,'AUX'))
  sources=['fixture:'+str(i).zfill(3) for i in range(84)];ids=[s.replace(':','__')+'__defect'+str(j) for s in sources for j in range(5)];manifests={}
  for count in (8192,16384):
   p=O/('manifest_'+str(count)+'.jsonl')
   with p.open('x') as f:
    for i,cid in enumerate(ids):f.write(json.dumps(dict(case_id=cid,source_id=sources[i//5],target_array_sha256='0'*64,normalization={'center':[0,0,0],'scale':1},raw={'origin':'ARTIFICIAL_ONLY'},schema='BCSP-normalized-v1',normalization_source='defective_bbox',n_input=count,n_target=8192,point_path='points/'+cid+'_'+str(count)+'.npz',sha256='1'*64))+'\n')
   manifests[str(count)]=bind(p)
  fid=ids[105:];fold=dict(train_case_ids=fid,train_sources=sources[21:],dev_sources=sources[:21],train_allowlist_sha256=hashlib.sha256(('\n'.join(fid)+'\n').encode()).hexdigest())
  fr=emit('fold.json',dict(folds={'D':fold},confirmation_count_excluded=20));vr=emit('QC.json',dict(status=c.QC_STATUS,verified_sources=84,verified_cases=420,verified_point_files=840,interpretation={'anatomical_semantics':'UNRESOLVED ARTIFICIAL_ONLY'},important_file_hashes={'manifest_'+k+'.jsonl':v['sha256'] for k,v in manifests.items()}));qualified,selected,_=c.bind_metadata(vr,manifests,fr,'D',8192)
  plan=dict(schema='bcsp-shared-order-v1',case_ids=fid,epochs=[dict(epoch=i,batches=[fid[j:j+8] for j in range(0,312,8)],dropped=fid[312:]) for i in range(100)])
  H=S.parent/'H2_implementation_v1';impl=dict(entry=bind(ep),contract=bind(cp),runtime=bind(H/'bcsp_h2_training_runtime_v1.py'))
  base=dict(schema='ARTIFICIAL_M0_D_BASELINE',status='AWAITING_EXPLICIT_USER_AUTHORIZATION',stage='P1',variant='M0',fold='D',n_input=8192,n_output=8192,static_config=emit('baseline_static.json',static),QC=dict(qualified_receipt=emit('qualified.json',qualified),verification=vr,manifests=manifests,fold_binding=fr),order_plan=emit('order.json',plan),implementation=impl,identity=e.CURRENT_IDENTITY,environment={'CUDA_VISIBLE_DEVICES':e.CURRENT_IDENTITY['gpu_uuid']},run_id='ARTIFICIAL_D',output='ARTIFICIAL_ONLY',launch_attempt='ARTIFICIAL_ONLY',launch_contract={},provenance={},not_authorized=[],data_root='ARTIFICIAL_FOLD_D_ONLY',numeric_policy={'sha256':'0'*64},cuda_audit='unused')
  # cuda_audit is an H2 extra, not part of the M0 baseline.
  base.pop('cuda_audit');br=emit('baseline.json',base);ba=emit('baseline_audit.json',dict(status='FORMAL_P1_M0_POST_TRAINING_AND_PAIR_FREEZE_AUDIT_PASS',request_sha256=br['sha256'],checks_passed=1,checks={'ARTIFICIAL_ONLY':True}))
  ca=emit('cuda_fixture.json',{'status':'FORMAL_POST_H2_CUDA_FREEZE_AUDIT_PASS'});p3=emit('P3_fixture.json',dict(status='LOCAL_H2_FOLDD_TRAINING_ENTRY_P3_PASS',entry_sha256=impl['entry']['sha256'],H2_source_hashes=e.H2_HASHES));ready=emit('ready_fixture.json',dict(status='FOLDD_H2_NECESSARY_READONLY_READINESS_PASS',identity=e.CURRENT_IDENTITY,training_cases=315,sources=63))
  q=copy.deepcopy(base);q.update(schema='bcsp-p2-H2-foldD-training-request-v1',stage='CRANIAL_BCSP_MAMBA_P2_H2',baseline_request=br,baseline_audit=ba,cuda_audit=ca,p3=p3,readiness=ready,h2_config=e.mode_config('AUX'),static_config=emit('AUX_static.json',configs['AUX']),aux_pairing=None)
  q['implementation'].update(h2_range=bind(H/'bcsp_h2_range_v1.py'),h2_adapter=bind(H/'bcsp_h2_model_adapter_v1.py'))
  auxqr=emit('AUX_request.json',q);ai=emit('AUX_initial.json',dict(parameter_sha256=state(couplemodel,True),persistent_state_sha256=state(couplemodel),order_sha256=c.canonical_sha(plan),seed=0));aa=emit('AUX_audit.json',dict(status='FORMAL_H2_AUX_FOLDD_POST_TRAINING_FREEZE_AUDIT_PASS',request_sha256=auxqr['sha256'],checks_passed=1,checks={'ARTIFICIAL_ONLY':True},initialization={'record':json.loads(Path(ai['path']).read_bytes())}))
  qc=copy.deepcopy(q);qc.update(h2_config=e.mode_config('COUPLE'),static_config=emit('COUPLE_static.json',configs['COUPLE']),aux_pairing=dict(request=auxqr,audit=aa,initialization=ai))
  pins=copy.deepcopy(e.FROZEN_BASELINES);cuda_pin=e.CUDA_AUDIT_SHA;e.FROZEN_BASELINES={'D':dict(request_sha256=br['sha256'],audit_sha256=ba['sha256'])};e.CUDA_AUDIT_SHA=ca['sha256'];serial=0
  def triplet(request,yes=True,bad_runtime=False):
   nonlocal serial
   serial+=1;qr=emit('request_'+str(serial)+'.json',request);ar=emit('auth_'+str(serial)+'.json',dict(schema='bcsp-p2-H2-training-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_TEST_ONLY'));rr=emit('runtime_'+str(serial)+'.json',dict(schema='bcsp-p2-H2-training-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if bad_runtime else ar['sha256']));return qr,ar,rr
  try:
   check('10 full authorize AUX D with315 exact metadata rows',len(e.authorize(*triplet(q))[3])==315)
   check('11 full authorize COUPLE D only with frozen AUX D evidence',len(e.authorize(*triplet(qc))[3])==315)
   reject('12 explicit authorization required',lambda:e.authorize(*triplet(q,False)));reject('13 one-way runtime required',lambda:e.authorize(*triplet(q,bad_runtime=True)))
   for n,mutate in [('14 C fold rejected',lambda x:x.update(fold='C')),('15 invalid mode rejected',lambda x:x['h2_config'].update(mode='OFF')),('16 identity drift rejected',lambda x:x['identity'].update(gpu_uuid='OTHER')),('17 D order hash drift rejected',lambda x:x['order_plan'].update(sha256='0'*64)),('18 shared runtime drift rejected',lambda x:x['implementation']['runtime'].update(sha256='0'*64)),('19 AUX prior pairing rejected',lambda x:x.update(aux_pairing=qc['aux_pairing']))]:
    bad=copy.deepcopy(q);mutate(bad);reject(n,lambda:e.authorize(*triplet(bad)))
   bad=copy.deepcopy(qc);bad['aux_pairing']=None;reject('20 COUPLE missing AUX D audit rejected',lambda:e.authorize(*triplet(bad)))
   bad=copy.deepcopy(qc);bad['aux_pairing']['audit']['sha256']='0'*64;reject('21 wrong AUX D audit hash rejected',lambda:e.authorize(*triplet(bad)))
  finally:e.FROZEN_BASELINES=pins;e.CUDA_AUDIT_SHA=cuda_pin
  check('22 production pins restored',e.FROZEN_BASELINES['D']['request_sha256']=='55793bca2fa9472d45b3cca0b9598154cdb12a84a3eb89633daa52b85a039d5f')
  class Factory:
   def build_model(self,b,v,seed=0):
    m,ev=t.Factory().build_model(b,v,seed);ev['artificial_fixture']=False;return m,ev
  captured={}
  class Runtime:
   def BCSPDataset(self,*args):captured['dataset']=args;return 'ARTIFICIAL_ONLY'
   def make_loader(self,*args):return args
   def train_lifecycle(self,m,loader,records,p,output,**kw):captured.update(model=m,records=records,plan=p,kw=kw,loader=loader(0));return 'NO_TRAINING'
  helper=types.SimpleNamespace(state_sha=state,assert_numeric=lambda x:None);expected={'variant':'M0','common_state_unchanged':True,'artificial_fixture':False}
  for mode,request in [('AUX',q),('COUPLE',qc)]:
   budget=types.SimpleNamespace();ret=e.dispatch_training(request,configs[mode],selected,fold,plan,factory=Factory(),h2_adapter=adapter,model_builder=builder,runtime=Runtime(),helper=helper,budget=budget,torch=torch,knn_enable=lambda:None,expected_factory=expected,device='cpu')
   check('23 '+mode+' actual dispatch same D data/order/zero state',ret=='NO_TRAINING' and captured['plan'] is plan and captured['records'] is selected and captured['model'].h2_metadata()==e.mode_config(mode) and captured['dataset']==('ARTIFICIAL_FOLD_D_ONLY',selected,fold['train_sources'],8192) and state(captured['model'])==state(couplemodel))
   m=captured['model'];m.h2_range_head.bias.data.fill_(.2);x,g=t.inputs();out=m(x);ctx=m._h2_controller.context
   check('24 '+mode+' correct actual coordinate dispatch',torch.equal(ctx['raw'],ctx['used']) if mode=='AUX' else not torch.equal(ctx['raw'],ctx['used']))
   for value in [m.base_model.mlp_query.last[:,:,-3:],m.base_model.decoder.last_pos,m.reduce_map.last[:,:,-3:],out[0]]:torch.testing.assert_close(value,ctx['used'],rtol=0,atol=0)
   torch.testing.assert_close(out[3].reshape(1,256,32,3),ctx['used'].unsqueeze(2)+m.decode_head.last,rtol=0,atol=0)
   m.get_loss(out,g);check('25 '+mode+' five consumers and one loss',m.h2_runtime_record()['H2_mode']==mode)
  badhelper=types.SimpleNamespace(state_sha=lambda *args:'0'*64,assert_numeric=lambda x:None)
  reject('26 COUPLE different initial fingerprints rejected',lambda:e.dispatch_training(qc,configs['COUPLE'],selected,fold,plan,factory=Factory(),h2_adapter=adapter,model_builder=builder,runtime=Runtime(),helper=badhelper,budget=types.SimpleNamespace(),torch=torch,knn_enable=lambda:None,expected_factory=expected,device='cpu'))
  check('27 AUX no extra read root',e.pair_read_roots(q)==[]);check('28 COUPLE exact file root not directory',e.pair_read_roots(qc)==[Path(ai['path'])])
  old=ast.parse((S.parent/'H2_COUPLE_foldC_initialization_readfix_v2/bcsp_h2_couple_foldC_training_entry_v2.py').read_text());new=ast.parse(ep.read_text());nodes=lambda tree,n:next(v for v in tree.body if isinstance(v,(ast.FunctionDef,ast.ClassDef)) and v.name==n)
  check('29 original payload/resource/file-policy AST unchanged',all(ast.dump(nodes(old,n),include_attributes=False)==ast.dump(nodes(new,n),include_attributes=False) for n in ['payload_paths','make_training_policy','TrainingBudget','P1Budget']))
  hp=G/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py';assert bind(hp)['sha256']=='7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'
  owned=O/'owned';owned.mkdir();neighbor=Path(ai['path']).with_name('neighbor.json');neighbor.write_text('{}')
  fixture=emit('policy_fixture.json',dict(entry=bind(ep),helper=bind(hp),AUX=q,COUPLE=qc,owned=str(owned.absolute()),neighbor=str(neighbor.absolute())))
  child=r"""
import ast,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
cfg=json.loads(Path(sys.argv[1]).read_bytes())
def load(n,r):
 assert hashlib.sha256(Path(r['path']).read_bytes()).hexdigest()==r['sha256'];s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
e=load('D_policy_entry',cfg['entry']);h=load('D_original_policy',cfg['helper']);utc=types.SimpleNamespace(allow=lambda *x:False);roots=e.pair_read_roots(cfg['COUPLE']);ref=Path(cfg['COUPLE']['aux_pairing']['initialization']['path']);assert roots==[ref] and e.pair_read_roots(cfg['AUX'])==[]
tree=ast.parse(Path(cfg['entry']['path']).read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');rootassignment=next(n for n in ast.walk(main) if isinstance(n,ast.Assign) and any(isinstance(v,ast.Name) and v.id=='read_roots' for v in n.targets));assert any(isinstance(v,ast.Starred) and isinstance(v.value,ast.Call) and v.value.func.id=='pair_read_roots' for v in rootassignment.value.elts)
old=e.make_training_policy(h,[],cfg['owned'],{},utc)
try:old.check(ref)
except RuntimeError:pass
else:raise AssertionError('missing-root regression not reproduced')
p=e.make_training_policy(h,roots,cfg['owned'],{},utc);sys.addaudithook(p.audit);assert e.json_bound(cfg['COUPLE']['aux_pairing']['initialization'])['seed']==0
def reject(fn):
 try:fn()
 except (ValueError,RuntimeError):return True
 raise AssertionError('policy unexpectedly allowed operation')
assert reject(lambda:ref.open('w')) and reject(lambda:Path(cfg['neighbor']).read_bytes()) and reject(lambda:e.json_bound(dict(cfg['COUPLE']['aux_pairing']['initialization'],sha256='0'*64)))
for name in ['.env','other.npz','old.pth']:assert reject(lambda name=name:p.check(ref.with_name(name)))
print(json.dumps(dict(actual_hook_exact_JSON_read=True,reference_write_denied=True,neighbor_and_secret_payload_denied=True,hash_still_checked=True,AUX_no_extra_root=True,actual_main_uses_pair_read_roots=True)))
"""
  proc=subprocess.run([sys.executable,'-I','-B','-c',child,fixture['path']],capture_output=True,timeout=25)
  for key,b in [('stdout',proc.stdout),('stderr',proc.stderr)]:
   with (O/('policy_child_'+key+'.bin')).open('xb') as f:f.write(b)
  check('30 installed audit-hook actual reference read and deny regression',proc.returncode==0 and all(json.loads(proc.stdout).values()))
  emit('result_v1.json',dict(status='H2_FOLDD_ENTRY_CPU_CONTRACT_PASS',checks_passed=len(checks),checks=checks,python=sys.version,torch=torch.__version__,native_Mamba_loaded=False,real_payloads_read=0,production_forward=0,production_backward=0,optimizer_steps=0,fixture_notes='Native factory facade and audit evidence are explicitly artificial. Production M0 D/CUDA pins restored; no production bypass flag.',source_bindings=[bind(ep),bind(cp),bind(hp)]+[bind(H/n) for n in ['bcsp_h2_range_v1.py','bcsp_h2_model_adapter_v1.py','bcsp_h2_training_runtime_v1.py']]))
  print(json.dumps(dict(status='H2_FOLDD_ENTRY_CPU_CONTRACT_PASS',checks=len(checks))))
 except BaseException as exc:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),checks=checks));raise
if __name__=='__main__':main()
