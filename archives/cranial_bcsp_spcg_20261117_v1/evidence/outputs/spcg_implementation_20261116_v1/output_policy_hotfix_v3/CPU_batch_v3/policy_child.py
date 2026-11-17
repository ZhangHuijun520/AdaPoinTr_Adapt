
from pathlib import Path
import json,sys,importlib.util,traceback,linecache
c=json.loads(Path(sys.argv[1]).read_text());q=c['q']
def load(n,r):
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('actual_parent_policy',q['parent_helper']);h=load('actual_helper',q['helper']);e=load('actual_entry_v3',q['entry']);g=e.traceback_source_guard(p,q)
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
for record in q.values():
 linecache.cache.pop(record['path'],None)
 assert linecache.getline(record['path'],1)
 try:exec(compile("raise RuntimeError('ARTIFICIAL_TRACEBACK')",record['path'],'exec'))
 except RuntimeError as ex:assert 'ARTIFICIAL_TRACEBACK' in ''.join(traceback.format_exception(type(ex),ex,ex.__traceback__))
g.close();print(json.dumps(dict(outputs=5,neighbor_denied=True,input_write_denied=True,source_read=True,source_write_denied=True,neighbor_source_denied=True,traceback_sources=4)))
