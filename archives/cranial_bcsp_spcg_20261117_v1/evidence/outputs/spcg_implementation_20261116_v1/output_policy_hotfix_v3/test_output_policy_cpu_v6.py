"""Single bounded CPU policy regression, using real inherited audit hook in child."""
from pathlib import Path
import ast,hashlib,importlib.util,json,subprocess,sys,traceback
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'CPU_batch_v6'
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 O.mkdir();checks=[];scope=json.loads((V/'CPU_scope_v3.json').read_text());e=load('spcg_v3',V/'bcsp_spcg_cuda_entry_v3.py');q=json.loads((S/'binding_hotfix_v2/pending_transport_v2/payload/SPCG_CUDA_execution_request_v2.json').read_text(encoding='utf-8'))
 def check(n,v):assert v,scope['tests'][n-1];assert len(checks)==n-1;checks.append(scope['tests'][n-1])
 try:
  owned=O/'owned';owned.mkdir();inputs=O/'inputs';inputs.mkdir();inp=inputs/'partial.npz';inp.write_bytes(b'ARTIFICIAL_ONLY');neighbor=O/'neighbor.py';neighbor.write_text('NOT_ALLOWED=1\n')
  parent=W/'outputs/cranial_bcsp_fullmamba_20261110/Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py';helper=W/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'
  # Exact UTC implementation bytes are found from the frozen mirror, not environment paths.
  context=json.loads((W/'outputs/scq_rive_training_implementation_20261115_v1/implementation_context_v1.json').read_text(encoding='utf-8'));utc=Path(context['mirror'][q['timezone_implementation']['path']])
  fixture=dict(parent_helper=rec(parent),helper=rec(helper),timezone_implementation=rec(utc),entry=rec(V/'bcsp_spcg_cuda_entry_v3.py'))
  paths=e.exact_output_paths(owned);check(1,len(set(paths))==5 and all(p.parent==owned.absolute() for p in paths))
  config=dict(q=fixture,owned=str(owned.absolute()),input=str(inp.absolute()),neighbor=str(neighbor.absolute()))
  cp=O/'child_config.json';cp.write_text(json.dumps(config),encoding='utf-8')
  child=r'''
from pathlib import Path
import json,sys,importlib.util,traceback,linecache
c=json.loads(Path(sys.argv[1]).read_text());q=c['q']
def load(n,r):
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('actual_parent_policy',q['parent_helper']);h=load('actual_helper',q['helper']);e=load('actual_entry_v3',q['entry'])
# Artificial child only: preserve exact raw bytes for Windows read-only descriptors.
import os,types
compatibility=dict(applied=False,scope='artificial_child_parent_module_os_open_readonly_only')
if sys.platform=='win32':
 class BinaryReadOS:
  def __getattr__(self,name):return getattr(os,name)
  def open(self,path,flags,*args,**kwargs):
   assert flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)==0
   return os.open(path,flags|os.O_BINARY,*args,**kwargs)
 p.os=BinaryReadOS();compatibility['applied']=True
g=e.traceback_source_guard(p,q)
# Test-only exact self-source record, frozen by parent after writing child bytes.
self_record=c['self_source'];self_path=p.exact(self_record)
assert self_path==Path(__file__).absolute()
self_fd=p.os.open(self_path,p.os.O_RDONLY|getattr(p.os,'O_NOFOLLOW',0))
g.records[self_path]=self_record;g.fds[self_path]=self_fd;g.verify(self_path)
out=Path(c['owned']);paths=e.exact_output_paths(out)
class UTC:
 def allow(self,*a):return False
policy=p.make_policy(h,[],out,[c['input']],[],paths,UTC(),g);sys.addaudithook(policy.audit)
def reject(fn):
 try:fn()
 except (ValueError,RuntimeError):return True
 return False
try:
 for x in paths:
  with x.open('xb') as f:f.write(b'ARTIFICIAL_OUTPUT_NOT_REAL_NPZ')
 assert reject(lambda:(out/'real_D_05.npz').open('wb'))
 assert reject(lambda:Path(c['input']).open('wb'))
 assert Path(q['parent_helper']['path']).read_bytes()
 assert reject(lambda:Path(q['parent_helper']['path']).open('wb'))
 assert reject(lambda:Path(c['neighbor']).read_bytes())
 assert reject(lambda:Path(__file__).open('wb'))
 assert Path(__file__).read_bytes()
 for record in q.values():
  linecache.cache.pop(record['path'],None)
  assert linecache.getline(record['path'],1)
  try:exec(compile("raise RuntimeError('ARTIFICIAL_TRACEBACK')",record['path'],'exec'))
  except RuntimeError as ex:assert 'ARTIFICIAL_TRACEBACK' in ''.join(traceback.format_exception(type(ex),ex,ex.__traceback__))
 bad=dict(q,parent_helper=dict(q['parent_helper'],sha256='0'*64))
 assert reject(lambda:e.traceback_source_guard(p,bad))
 print(json.dumps(dict(outputs=5,neighbor_denied=True,input_write_denied=True,source_read=True,source_write_denied=True,neighbor_source_denied=True,traceback_sources=4,compatibility=compatibility,negative_hash_binding_rejected=True,self_source_readonly_verified=True)))
finally:
 g.close()
'''
  ch=O/'policy_child.py';ch.write_text(child,encoding='utf-8');config['self_source']=rec(ch);cp.write_text(json.dumps(config),encoding='utf-8');r=subprocess.run([sys.executable,'-I','-S','-B',str(ch),str(cp)],capture_output=True,timeout=30);(O/'child_stdout.bin').write_bytes(r.stdout);(O/'child_stderr.bin').write_bytes(r.stderr);assert r.returncode==0,r.stderr.decode(errors='replace');result=json.loads(r.stdout)
  for n,key in [(2,'outputs'),(3,'neighbor_denied'),(4,'input_write_denied'),(5,'source_read'),(6,'source_write_denied'),(7,'neighbor_source_denied'),(8,'traceback_sources')]:check(n,bool(result[key]))
  check(9,result['self_source_readonly_verified'] and result['traceback_sources']==4 and result['compatibility']['applied']==(sys.platform=='win32'))
  check(10,result['negative_hash_binding_rejected'])
  def funcs(p):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_text(encoding='utf-8')).body if isinstance(x,ast.FunctionDef)}
  a=funcs(S/'binding_hotfix_v2/bcsp_spcg_cuda_entry_v2.py');b=funcs(V/'bcsp_spcg_cuda_entry_v3.py')
  check(11,{n for n in a if a[n]!=b[n]}=={'main'} and set(b)-set(a)=={'exact_output_paths','traceback_source_guard'})
  prev=load('spcg_prev',S/'binding_hotfix_v2/bcsp_spcg_cuda_entry_v2.py');check(12,e.SCIENCE==prev.SCIENCE and e.LIMITS==prev.LIMITS and e.FIXTURE==prev.FIXTURE)
  (O/'result.json').write_text(json.dumps(dict(status='SPCG_OUTPUT_POLICY_LIFECYCLE_CPU_PASS',count=len(checks),checks=checks,entry=rec(V/'bcsp_spcg_cuda_entry_v3.py'),test=rec(Path(__file__)),scope=rec(V/'CPU_scope_v3.json'),actual_policy_sources=[rec(parent),rec(helper)],child=result,server_calls=0,SMI=0,models=0,CUDA=0),indent=2),encoding='utf-8');print('PASS12_ACTUAL_POLICY_NO_GPU')
 except BaseException as ex:(O/'failure.json').write_text(json.dumps(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(ex),traceback=traceback.format_exc()),indent=2),encoding='utf-8');raise
if __name__=='__main__':main()
