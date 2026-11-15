"""Single stdlib CPU regression batch for the two changed identity validators."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,shlex,traceback
S=Path(__file__).resolve().parent;O=S/'CPU_contract_v2'
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 O.mkdir();checks=[];sp=importlib.util.spec_from_file_location('scq_rebind_cpu',S/'bcsp_scq_fourmodel_native_predict_v2.py');e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
 def check(n,v=True):assert v,n;checks.append(n)
 def reject(n,fn):
  try:fn()
  except (RuntimeError,ValueError,AssertionError,KeyError):check(n);return
  raise AssertionError('unexpected accept '+n)
 def emit(n,v):p=O/n;e.emit(p,v);return rec(p)
 try:
  ctx=read(S/'context_v2.json');q=ctx['candidate'];mirror=ctx['mirror'];index=read(S/'SCQ_BS_CD_input_index_v2.json')
  root=S.parents[3];C=root/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1'
  folds=read(C/'candidate_payload/fold_binding.json');manifest=[json.loads(x) for x in (C/'candidate_payload/manifest_8192.jsonl').read_text().splitlines()]
  check('01 new index four420 and correct existing paths',len(e.validate_index(index,folds)[1])==420)
  e.validate_source(index,None,manifest);check('02 unchanged hashes cases normalization provenance')
  old=read(S.parent/'SCQ_BS_CD_input_index_v1.json')
  check('03 all210 physical paths corrected only',all(a['input']['path']!=b['input']['path'] and {k:v for k,v in a.items() if k!='input'}=={k:v for k,v in b.items() if k!='input'} and a['input']['sha256']==b['input']['sha256'] and a['input']['bytes']==b['input']['bytes'] for a,b in zip(old['inputs'],index['inputs'])))
  bad=copy.deepcopy(index);bad['inputs'][0]['input']['path']=old['inputs'][0]['input']['path'];reject('04 former bad root rejected',lambda:e.validate_index(bad,folds))
  bad=copy.deepcopy(index);bad['inputs'][0]['fold']='D';reject('05 fold not changed with physical path',lambda:e.validate_index(bad,folds))
  serial=0
  def triplet(change=None,auth=True,wrongruntime=False):
   nonlocal serial
   serial+=1;v=copy.deepcopy(q)
   if change:change(v)
   qr=emit('q'+str(serial)+'.json',v);ar=emit('a'+str(serial)+'.json',dict(schema='bcsp-development-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=auth,user_authorization_text='ARTIFICIAL_CPU_ONLY'))
   rr=emit('r'+str(serial)+'.json',dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if wrongruntime else ar['sha256']));return qr,ar,rr
  e.authorize(*triplet());check('06 complete new identity authorize path')
  reject('07 old prediction identity denied',lambda:e.authorize(*triplet(lambda v:v.update(identity=copy.deepcopy(v['training_identity'])))))
  reject('08 fabricated training identity denied',lambda:e.authorize(*triplet(lambda v:v['training_identity'].update(hostname=e.CURRENT_IDENTITY['hostname']))))
  reject('09 old GPU environment denied',lambda:e.authorize(*triplet(lambda v:v['environment'].update(CUDA_VISIBLE_DEVICES=v['training_identity']['gpu_uuid']))))
  reject('10 missing authorization denied',lambda:e.authorize(*triplet(auth=False)))
  reject('11 wrong runtime digest denied',lambda:e.authorize(*triplet(wrongruntime=True)))
  reject('12 extra forward denied',lambda:e.authorize(*triplet(lambda v:v.update(forward_budget=421))))
  reject('13 resource threshold change denied',lambda:e.authorize(*triplet(lambda v:v['limits'].update(device_MiB=24564))))
  exact=e.exact
  e.exact=lambda r:exact(dict(r,path=mirror.get(r['path'],r['path'])))
  evidence=copy.deepcopy(q);evidence['dependencies']=[]
  evidence['P3']=emit('P3_artificial_fixture.json',dict(status='LOCAL_SCQ_NATIVE_PREDICTION_P3_PASS',entry_sha256=q['entry']['sha256'],checks={'artificial_only':True}))
  try:
   e.validate_evidence(evidence,index);check('14 actual four historical audits plus new identity proof pass')
   wrong=copy.deepcopy(evidence);wrong['training_identity']=copy.deepcopy(e.CURRENT_IDENTITY);reject('15 historical audit never relabeled',lambda:e.validate_evidence(wrong,index))
   wrong=copy.deepcopy(evidence);wrong['resource_rebind']['sha256']='0'*64;reject('16 changed rebind hash rejected',lambda:e.validate_evidence(wrong,index))
   wrong=copy.deepcopy(evidence);wrong['training_audits']['S_D']=wrong['training_audits']['B_D'];reject('17 swapped training audit rejected',lambda:e.validate_evidence(wrong,index))
  finally:e.exact=exact
  def nodes(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  a,b=nodes(S.parent/'bcsp_scq_fourmodel_native_predict_v1.py'),nodes(S/'bcsp_scq_fourmodel_native_predict_v2.py')
  check('18 only authorize evidence functions changed',{k for k in b if a[k]!=b[k]}=={'authorize','validate_evidence'})
  check('19 source models numeric resource lifecycle unchanged',all(a[k]==b[k] for k in ['execute_pair','make_source_guard','load_scq_builder','build_scq_model','load_checkpoint','scq_arrays','make_policy','Budget','predict_once','main']))
  rendered=e.render_launcher(q,'a'*64,'b'*64,'c'*64);cmd=next(v for v in rendered.splitlines() if v.startswith('/usr/bin/timeout'));argv=shlex.split(cmd)
  check('20 new POSIX entry request launcher paths',q['entry']['path'] in argv and q['launch_contract']['request_path'] in argv and '\\' not in cmd and rendered.index('mkdir -p --')<rendered.index(' >'))
  check('21 source initializer pins unchanged',all(q['implementation'][k]['sha256']==v for k,v in e.PINS.items()) and q['initialization']==e.INITIALIZATION)
  oldcpu=read(S.parent/'artificial_cpu_batch_v1/result_v1.json');check('22 inherited42 CPU verification retained',oldcpu['status']=='SCQ_NATIVE_CPU_CONTRACT_PASS' and oldcpu['checks_passed']==42)
  e.emit(O/'result_v2.json',dict(status='SCQ_REBIND_CPU_CONTRACT_PASS',checks=checks,checks_passed=len(checks),entry=rec(S/'bcsp_scq_fourmodel_native_predict_v2.py'),test=rec(Path(__file__)),inherited_CPU_result=rec(S.parent/'artificial_cpu_batch_v1/result_v1.json'),changed_function_count=2,real_arrays=0,checkpoint_loads=0,model_forwards=0,GPU_calls=0,server_calls=0,limitations=['New22 checks cover only identity/path validators and AST preservation; original42 tests not rerun.','No environment binary verification in local validator fixture; declared remote binaries verified in preceding bounded readonly audit.','No GPU or scientific equivalence claim after device/driver migration.']))
  print(json.dumps(dict(status='SCQ_REBIND_CPU_CONTRACT_PASS',checks=len(checks))))
 except BaseException as exc:
  e.emit(O/'failure_v2.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
