"""Pure CPU policy regression with actual UTC validator and artificial fd/metadata fixtures."""
from pathlib import Path
from types import SimpleNamespace
import ast,json,hashlib,importlib.util,sys,os,traceback
O=Path(__file__).resolve().parent;R=O.parents[2];B=O.parent;D=O/'cpu_UTC_batch_v2'
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 D.mkdir();checks=[]
 def check(n,v=True):
  assert bool(v),n
  checks.append(n)
 def reject(n,fn):
  try:fn()
  except (ValueError,RuntimeError,AssertionError):checks.append(n);return
  raise AssertionError('unexpected accept '+n)
 try:
  old=B/'bcsp_scq_training_entry_v1.py';new=O/'bcsp_scq_training_entry_v2.py'
  ta=ast.parse(old.read_text(encoding='utf-8'));tb=ast.parse(new.read_text(encoding='utf-8'))
  policy_a=next(n for n in ast.walk(ta) if isinstance(n,ast.ClassDef) and n.name=='Policy')
  policy_b=next(n for n in ast.walk(tb) if isinstance(n,ast.ClassDef) and n.name=='Policy')
  fix=next(n for n in policy_b.body[0].body if isinstance(n,ast.If) and ast.unparse(n.test)=='utc.allow(filename, write)')
  body=copy_node=ast.parse(new.read_text(encoding='utf-8'));clone=next(n for n in ast.walk(body) if isinstance(n,ast.ClassDef) and n.name=='Policy')
  clone.body[0].body=[n for n in clone.body[0].body if not isinstance(n,ast.If) or ast.unparse(n.test)!='utc.allow(filename, write)']
  check('whole production AST unchanged after removing one UTC check',ast.dump(ta,include_attributes=False)==ast.dump(body,include_attributes=False))
  utc_path=R/'outputs/cranial_bcsp_mamba_p1_20261104/gpu_admission_v3/exact_utc_resource_v1.py'
  utcmod=load('UTC_order_actual_reader',utc_path)
  helper=load('UTC_order_actual_helper',R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py')
  parent=load('UTC_order_actual_training_policy',R/'outputs/cranial_bcsp_mamba_p1_20261104/training_entry_v1/bcsp_p1_training_entry_v1.py')
  # Exact real spellings; only the artificial fd content/metadata are simulated.
  payload=b'ARTIFICIAL_UTC_FIXED_BYTES';state=dict(data=payload,link_text='Etc/UTC',inode=77)
  binding=dict(utcmod.UTC_RESOURCE,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
  def observed(b):return dict(link_is_symlink=True,link_text=state['link_text'],resolved_target=b['target'],target_is_regular=True,target_has_link_ancestor=False,link_has_link_ancestor=False,bytes=len(payload),device=12,inode=state['inode'])
  utcmod.inspect_binding=observed
  utcmod.os=SimpleNamespace(fsdecode=os.fsdecode,fstat=lambda fd:SimpleNamespace(st_dev=12,st_ino=77,st_size=len(payload)),lseek=lambda *a:0,read=lambda *a:state['data'],close=lambda *a:None)
  utc=utcmod.ExactUTCReader.__new__(utcmod.ExactUTCReader);utc.binding=binding;utc.fd=91;utc.read_checks=0
  calls=[];guarded=str((D/'BOUND_SOURCE.py').resolve())
  class Guard:
   def allow(self,name,write=False):
    calls.append((os.fsdecode(name),write))
    if os.fsdecode(name) in (binding['link'],binding['target']):raise RuntimeError('linked path reached general guard')
    if os.fsdecode(name)==guarded:
     if write:raise RuntimeError('bound source write denied')
     return True
    if os.fsdecode(name)=='UNAUTHORIZED_LINK':raise RuntimeError('other symlink refused')
    return False
  guard=Guard();train=(D/'ARTIFICIAL_TRAIN.npz').resolve();dev=(D/'ARTIFICIAL_DEV.npz').resolve()
  base=parent.make_training_policy(helper,[],D,{train:'ARTIFICIAL_HASH_NOT_READ'},utc)
  def build(node):
   env=dict(base_policy=base,guard=guard,utc=utc);exec(compile(ast.Module([node],[]),'actual_policy_class_only','exec'),env);return env['Policy']([],D)
  before=build(policy_a);after=build(policy_b)
  reject('old policy reproduces UTC order conflict',lambda:before.check(binding['link'],False))
  calls.clear();after.check(binding['link'],False)
  check('new UTC link bypasses generic guard only after exact verify',calls==[] and utc.read_checks==1)
  after.check(binding['target'],False)
  check('exact target spelling verified too',calls==[] and utc.read_checks==2)
  after.check(binding['link'].encode(),False)
  check('bytes spelling follows same exact resource validator',calls==[] and utc.read_checks==3)
  reject('UTC link writes still denied',lambda:after.check(binding['link'],True))
  reject('UTC target writes still denied',lambda:after.check(binding['target'],True))
  state['data']=b'X'+payload[1:];reject('bad UTC target hash still fails closed',lambda:after.check(binding['link'],False));state['data']=payload
  state['link_text']='OTHER';reject('UTC link metadata drift still denied',lambda:after.check(binding['link'],False));state['link_text']='Etc/UTC'
  state['inode']=78;reject('UTC replaced target fd identity still denied',lambda:after.check(binding['target'],False));state['inode']=77
  calls.clear();read_before=utc.read_checks;after.check(91,False)
  check('integer fd bypass unchanged',calls==[] and utc.read_checks==read_before)
  after.check(guarded,False);check('exact source guard still handles nonUTC reads',calls[-1]==(guarded,False))
  reject('exact source writes still refused',lambda:after.check(guarded,True))
  reject('nonUTC symlink not generally allowed',lambda:after.check('UNAUTHORIZED_LINK',False))
  after.check(train,False);check('fixed training NPZ read still allowed',True)
  reject('development NPZ still denied',lambda:after.check(dev,False))
  reject('training NPZ write still denied',lambda:after.check(train,True))
  after.check(D/'ckpt-last.pth',True);check('original final checkpoint write allowance unchanged',True)
  reject('other checkpoint still denied',lambda:after.check(D/'other.pth',False))
  # No unrelated production function or training/runtime source was changed.
  ctx=json.loads((B/'training_context_candidate_v1.json').read_bytes())
  for key in ['runtime','contract','budget_parent']:
   r=ctx['request_candidate']['implementation'][key];p=Path(ctx['mirror'][r['path']]);check('original '+key+' bytes unchanged',rec(p)['sha256']==r['sha256'])
  result=dict(status='UTC_ORDER_CPU_REGRESSION_PASS',count=len(checks),checks=checks,entry=rec(new),test=rec(Path(__file__)),exact_UTC_reader_source=rec(utc_path),production_change='One UTC allow-before-general-guard condition',fixtures='Actual UTC verify/allow and actual nested old/new policies; simulated fd bytes/metadata only; no real UTC symlink created or modified',CUDA_calls=0,model_forward=0,optimizer_steps=0,server_writes=0)
  with (D/'result_v2.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
  print(json.dumps(dict(status='PASS',checks=len(checks))))
 except BaseException as exc:
  with (D/'failure_v2.json').open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()),f,indent=2)
  raise
if __name__=='__main__':main()
