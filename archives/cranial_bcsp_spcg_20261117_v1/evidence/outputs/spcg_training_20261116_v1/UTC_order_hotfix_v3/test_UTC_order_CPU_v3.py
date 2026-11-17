"""Single artificial CPU policy-order regression; no server/model/CUDA."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys,traceback
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'CPU_contract_batch_v3'
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def main():
 O.mkdir();checks=[];scope=json.loads((V/'CPU_scope_v3.json').read_text());entry=V/'bcsp_spcg_training_entry_v3.py';oldpath=S/'startup_chain_hotfix_v2/bcsp_spcg_training_entry_v2.py'
 def check(n,v):assert v,scope['checks'][n-1];assert len(checks)==n-1;checks.append(scope['checks'][n-1])
 def reject(fn):
  try:fn()
  except (ValueError,RuntimeError):return True
  return False
 try:
  text=entry.read_text(encoding='utf-8');old=oldpath.read_text(encoding='utf-8');addition='                if utc.allow(filename,write):return\n';check(1,text.replace(addition,'',1)==old)
  e=load('utc_v3_cpu',entry);e2=load('utc_v2_cpu',oldpath);check(2,e.COUNTS==e2.COUNTS and e.RESOURCES==e2.RESOURCES)
  # Extract the actual nested Policy class; inherited training policy remains real.
  parent=load('actual_budget_for_order',W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/inherited_training_budget_v1.py');helper=load('actual_helper_for_order',W/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py')
  calls=[]
  class UTC:
   fail=False
   def allow(self,p,write=False):
    calls.append('UTC')
    if str(p) not in ['/usr/share/zoneinfo/UTC','/usr/share/zoneinfo/Etc/UTC']:return False
    if write:raise RuntimeError('UTC readonly')
    if self.fail:raise RuntimeError('UTC exact metadata/hash drift')
    return True
  utc=UTC();owned=O/'owned';owned.mkdir();base=parent.make_training_policy(helper,[],owned,{},utc)
  source=O/'bound.py';source.write_bytes(b'BOUND=1\n')
  class Guard:
   def allow(self,p,write=False):
    calls.append('SOURCE')
    if str(p)=='/usr/share/zoneinfo/UTC' or str(p)=='/unrelated_link':raise RuntimeError('symlink rejected')
    if Path(p)==source.absolute():
     if write:raise RuntimeError('source readonly')
     return True
    return False
  guard=Guard();tree=ast.parse(text);mainnode=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');node=next(n for n in ast.walk(mainnode) if isinstance(n,ast.ClassDef) and n.name=='Policy');env=dict(base=base,guard=guard,utc=utc);exec(compile(ast.Module(body=[node],type_ignores=[]),str(entry)+'::actualPolicy','exec'),env);policy=env['Policy']([],owned)
  calls.clear();policy.check('/usr/share/zoneinfo/UTC');check(3,calls==['UTC'])
  calls.clear();check(4,reject(lambda:policy.check('/usr/share/zoneinfo/UTC',True)) and calls==['UTC'])
  utc.fail=True;calls.clear();check(5,reject(lambda:policy.check('/usr/share/zoneinfo/UTC')) and calls==['UTC']);utc.fail=False
  calls.clear();check(6,reject(lambda:policy.check('/unrelated_link')) and calls==['UTC','SOURCE'])
  policy.check(source.absolute());check(7,reject(lambda:policy.check(source.absolute(),True)))
  check(8,reject(lambda:policy.check(owned/'not_allowed.npz',True)))
  calls.clear();policy.check(5);check(9,calls==[])
  calls.clear();base.check('/usr/share/zoneinfo/UTC');check(10,calls==['UTC'])
  def fns(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef)}
  a=fns(oldpath);b=fns(entry);check(11,{n for n in a if a[n]!=b[n]}=={'main'} and a['fail_with_traceback']==b['fail_with_traceback'] and a['load_training_chain']==b['load_training_chain'])
  utcpath=W/'outputs/cranial_bcsp_mamba_p1_20261104/gpu_admission_v3/exact_utc_resource_v1.py';check(12,rec(utcpath)['sha256']=='038267da9f78be5ea9d03164e674d388228768bf0c42959097fcadfd807f830e' and rec(entry)['sha256']==scope['entry_sha256'])
  (O/'result.json').write_text(json.dumps(dict(status='SPCG_G0C_UTC_ORDER_CPU_PASS',count=len(checks),checks=checks,entry=rec(entry),test=rec(Path(__file__)),scope=rec(V/'CPU_scope_v3.json'),inherited_budget=rec(W/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/inherited_training_budget_v1.py'),UTC_source=rec(utcpath),server_calls=0,GPU=0,model_calls=0,limitations=['Actual nested Policy extracted and real inherited base policy used; UTC/source guard behavior is artificial to test dispatch ordering without Windows symlinks.','RealLinuxUTC binding validated by preceding read-only audit; no newLinux/GPU execution.','Previous12 actual-load-chain and16 lifecycleCPU evidence inherited, not rerun.']),indent=2),encoding='utf-8');print('PASS12_UTC_ORDER_NO_GPU')
 except BaseException as ex:(O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
if __name__=='__main__':main()
