
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
g.close()
bad=dict(q,parent_helper=dict(q['parent_helper'],sha256='0'*64))
assert reject(lambda:e.traceback_source_guard(p,bad))
print(json.dumps(dict(outputs=5,neighbor_denied=True,input_write_denied=True,source_read=True,source_write_denied=True,neighbor_source_denied=True,traceback_sources=4,compatibility=compatibility,negative_hash_binding_rejected=True,self_source_readonly_verified=True)))
