"""Only adapt the artificial Windows child; immutable production sources untouched."""
from pathlib import Path
import ast,json,hashlib
V=Path(__file__).resolve().parent
p=V/'test_output_policy_cpu_v3.py';text=p.read_text(encoding='utf-8')
text=text.replace("O=V/'CPU_batch_v3'","O=V/'CPU_batch_v4'")
needle="p=load('actual_parent_policy',q['parent_helper']);h=load('actual_helper',q['helper']);e=load('actual_entry_v3',q['entry']);g=e.traceback_source_guard(p,q)"
replacement="""p=load('actual_parent_policy',q['parent_helper']);h=load('actual_helper',q['helper']);e=load('actual_entry_v3',q['entry'])
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
g=e.traceback_source_guard(p,q)"""
assert text.count(needle)==1;text=text.replace(needle,replacement)
text=text.replace("traceback_sources=4)))","traceback_sources=4,compatibility=compatibility)))")
# Direct negative-binding check also uses a local proxy in this testing process.
# Avoid this: perform it in the already-compatible child instead, preserving parent test process.
needle="g.close();print(json.dumps"
replacement="""g.close()
bad=dict(q,parent_helper=dict(q['parent_helper'],sha256='0'*64))
assert reject(lambda:e.traceback_source_guard(p,bad))
print(json.dumps"""
assert text.count(needle)==1;text=text.replace(needle,replacement)
start=text.index("  parentmod=load('parent_direct',parent)")
end=text.index("  def funcs(p):",start)
text=text[:start]+"  check(9,result['traceback_sources']==4 and result['compatibility']['applied']==(sys.platform=='win32'))\n  check(10,result['negative_hash_binding_rejected'])\n"+text[end:]
text=text.replace("compatibility=compatibility)))","compatibility=compatibility,negative_hash_binding_rejected=True)))")
text=text.replace("SPCG_OUTPUT_POLICY_CPU_PASS","SPCG_OUTPUT_POLICY_WINDOWS_BINARY_CPU_PASS")
text=text.replace("'scope':", "'scope':")
out=V/'test_output_policy_cpu_v4.py';assert not out.exists();ast.parse(text);out.write_text(text,encoding='utf-8')
sources=[V/'bcsp_spcg_cuda_entry_v3.py',V.parents[0]/'bcsp_spcg_head_v1.py',V.parents[0]/'bcsp_spcg_factory_v1.py',V.parents[0]/'bcsp_spcg_runtime_v1.py']
scope=dict(status='FROZEN_BEFORE_SINGLE_WINDOWS_COMPAT_CPU_BATCH',output='CPU_batch_v4',attempts=1,production_sources=[dict(path=str(x),sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in sources],test_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),changes='Windows artificial child only readonly os.open O_BINARY proxy; direct guard assertions moved to same compatible child',server_calls=0,models=0,production_changes=0)
(V/'Windows_CPU_scope_v4.json').write_text(json.dumps(scope,indent=2),encoding='utf-8');print('V4_TEST_PREPARED')
