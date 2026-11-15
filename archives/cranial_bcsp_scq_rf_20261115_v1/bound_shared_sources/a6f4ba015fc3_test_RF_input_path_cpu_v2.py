"""One offline path-only CPU contract batch; no torch/model/real array loading."""
from pathlib import Path,PurePosixPath
import ast,copy,hashlib,importlib.util,json,shlex,traceback
V=Path(__file__).resolve().parent;S=V.parent;O=V/'CPU_contract_v2'
def read(p):return json.loads(p.read_bytes())
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 O.mkdir();checks=[];entry=V/'bcsp_scq_rf_sixmodel_native_predict_v2.py'
 sp=importlib.util.spec_from_file_location('RF_path_cpu_v2',entry);e=importlib.util.module_from_spec(sp);sp.loader.exec_module(e)
 def check(n,v=True):assert v,n;checks.append(n)
 def reject(n,fn):
  try:fn()
  except (RuntimeError,ValueError,AssertionError,KeyError):check(n);return
  raise AssertionError('unexpected acceptance '+n)
 def emit(n,v):p=O/n;e.emit(p,v);return rec(p)
 try:
  c=read(V/'context_v2.json');q=c['candidate'];index=read(V/'RF_sixmodel_input_index_v2.json');oldq=read(S/'pending_request_v1/payload/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json');oldindex=read(S/'RF_sixmodel_input_index_v1.json')
  R=S.parents[2];C=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload';folds=read(C/'fold_binding.json');manifest=[json.loads(x) for x in (C/'manifest_8192.jsonl').read_text(encoding='utf-8').splitlines()]
  check('01 six630 index corrected roots',len(e.validate_index(index,folds)[1])==630)
  e.validate_source(index,None,manifest);check('02 source fold normalization unchanged')
  check('03 only630 occurrence paths changed',all(a['input']['path']!=b['input']['path'] and {k:v for k,v in a.items() if k!='input'}=={k:v for k,v in b.items() if k!='input'} and a['input']['bytes']==b['input']['bytes'] and a['input']['sha256']==b['input']['sha256'] for a,b in zip(oldindex['inputs'],index['inputs'])))
  check('04 all six model pins immutable',all({k:v for k,v in a.items() if k!='training_audit'}=={k:v for k,v in b.items() if k!='training_audit'} and a['training_audit']['sha256']==b['training_audit']['sha256'] and a['training_audit']['bytes']==b['training_audit']['bytes'] for a,b in zip(oldindex['runs'],index['runs'])))
  for name,change in [('05 former root rejected',lambda b:b['inputs'][0]['input'].update(path=oldindex['inputs'][0]['input']['path'])),('06 wrong fold rejected',lambda b:b['inputs'][0].update(fold='D')),('07 wrong source rejected',lambda b:b['inputs'][0].update(source_id='train:999')),('08 extra case rejected',lambda b:b['inputs'].append(copy.deepcopy(b['inputs'][0]))),('09 path traversal rejected',lambda b:b['inputs'][0]['input'].update(path=e.DATA_ROOTS['C']+'/../'+PurePosixPath(b['inputs'][0]['input']['path']).name))]:
   bad=copy.deepcopy(index);change(bad);reject(name,lambda:e.validate_index(bad,folds))
  bad=copy.deepcopy(index);bad['inputs'][0]['input']['sha256']='0'*64;reject('10 changed payload hash rejected',lambda:e.validate_source(bad,None,manifest))
  keys=['identity','environment','limits','implementation','initialization','rf_initialization','dependencies','model_root','static_config','preflight_scope','prior_native_admission','comparison_qualification','entry_contract','forward_budget','batch_size','BNCal','loss_calls','backward','optimizer_steps','warmup','TTA']
  check('11 all scientific numeric resource model contracts preserved',all(q[k]==oldq[k] for k in keys))
  serial=0
  def triplet(change=None,yes=True,wrong=False):
   nonlocal serial
   serial+=1;v=copy.deepcopy(q)
   if change:change(v)
   qr=emit('fixture_request_'+str(serial)+'.json',v);ar=emit('fixture_authorization_'+str(serial)+'.json',dict(schema='bcsp-development-authorization-v1',request_sha256=qr['sha256'],explicit_user_authorization=yes,user_authorization_text='ARTIFICIAL_CPU_ONLY_NOT_EXECUTION_AUTHORIZATION'))
   rr=emit('fixture_runtime_'+str(serial)+'.json',dict(schema='bcsp-development-runtime-v1',request_sha256=qr['sha256'],authorization_sha256='0'*64 if wrong else ar['sha256']));return qr,ar,rr
  e.authorize(*triplet());check('12 complete authorize path v2 binding')
  reject('13 old index pin rejected',lambda:e.authorize(*triplet(lambda b:b.update(input_index=oldq['input_index']))))
  reject('14 missing authorization rejected',lambda:e.authorize(*triplet(yes=False)))
  reject('15 wrong runtime digest rejected',lambda:e.authorize(*triplet(wrong=True)))
  reject('16 extra forward rejected',lambda:e.authorize(*triplet(lambda b:b.update(forward_budget=631))))
  reject('17 changed resource budget rejected',lambda:e.authorize(*triplet(lambda b:b['limits'].update(device_MiB=24564))))
  oldexact=e.exact;mirror=c['mirror'];e.exact=lambda r:oldexact(dict(r,path=mirror.get(r['path'],r['path'])))
  try:
   v=copy.deepcopy(q);v['dependencies']=[];v['P3']=emit('fixture_P3.json',dict(status='LOCAL_RF_NATIVE_PREDICTION_P3_PASS',entry_sha256=q['entry']['sha256'],checks={'fixture_only':True}))
   e.validate_evidence(v,index);check('18 actual six frozen audits evidence validator')
   bad=copy.deepcopy(v);bad['training_audits']['Static_D']=bad['training_audits']['Sref_D'];reject('19 swapped audit rejected',lambda:e.validate_evidence(bad,index))
  finally:e.exact=oldexact
  def functions(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  check('20 every production function class AST unchanged',functions(entry)==functions(S/'bcsp_scq_rf_sixmodel_native_predict_v1.py'))
  render=e.render_launcher(q,'a'*64,'b'*64,'c'*64);cmd=next(x for x in render.splitlines() if x.startswith('/usr/bin/timeout'));argv=shlex.split(cmd)
  check('21 fresh POSIX paths and parent before redirection',q['entry']['path'] in argv and q['launch_contract']['request_path'] in argv and '\\' not in cmd and render.index('mkdir -p --')<render.index(' >') and q['output']!=oldq['output'] and q['launch_attempt']!=oldq['launch_attempt'])
  original=read(S/'artificial_cpu_batch_v1/result_v1.json');p3=read(S/'implementation_P3_v1.json')
  check('22 inherited51 CPU P3 evidence intact',original['checks_passed']==51 and original['status']=='RF_NATIVE_CPU_CONTRACT_PASS' and all(p3['checks'].values()) and rec(Path(original['entry']['path']))==original['entry'] and rec(Path(original['test']['path']))==original['test'])
  resolution=read(V/'input_path_resolution_v2.json');obs=Path(resolution['observation']['path']);check('23 exact210 read-only path proof bound',rec(obs)==resolution['observation'] and resolution['unique_cases']==210 and resolution['roots']==e.DATA_ROOTS)
  check('24 no implicit v1 retry',q['supersedes']['request_sha256']==rec(S/'pending_request_v1/payload/SCQ_RF_sixmodel_native_prediction_execution_request_v1.json')['sha256'] and 'NOT_REUSABLE' in q['supersedes']['status'] and q['execution_authorized'] is False)
  e.emit(O/'result_v2.json',dict(status='RF_INPUT_PATH_CPU_CONTRACT_PASS',checks=checks,checks_passed=len(checks),entry=rec(entry),test=rec(Path(__file__)),inherited_CPU_result=rec(S/'artificial_cpu_batch_v1/result_v1.json'),inherited_P3=rec(S/'implementation_P3_v1.json'),new_model_forwards=0,real_checkpoint_loads=0,real_payload_array_reads=0,server_calls=0,GPU_calls=0,limitations=['24 new checks cover path binding and full authorization/evidence metadata only.','Original51 checks and630 artificial lifecycle are inherited through exact AST preservation, not rerun.','Fresh server asset,210 input and6 checkpoint hashes remain mandatory after separate execution authorization.']))
  print(json.dumps(dict(status='RF_INPUT_PATH_CPU_CONTRACT_PASS',checks=len(checks))))
 except BaseException as exc:
  e.emit(O/'failure_v2.json',dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()));raise
if __name__=='__main__':main()
