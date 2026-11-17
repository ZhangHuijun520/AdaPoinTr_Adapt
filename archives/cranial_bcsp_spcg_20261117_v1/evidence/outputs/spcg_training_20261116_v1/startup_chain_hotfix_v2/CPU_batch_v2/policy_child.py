
from pathlib import Path
import json,sys,os,types,hashlib,traceback,textwrap,linecache
import torch
c=json.loads(Path(sys.argv[1]).read_text());R=c['records']
def load(n,r):
 import importlib.util
 s=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m);return m
e=load('actual_train_entry_v2',R['entry']);parent=load('actual_native',R['native']);helper=load('actual_helper',R['helper'])
if sys.platform=='win32':
 class BinaryReadOS:
  def __getattr__(self,n):return getattr(os,n)
  def open(self,path,flags,*a,**kw):
   assert not flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)
   return os.open(path,flags|os.O_BINARY,*a,**kw)
 parent.os=BinaryReadOS()
g=parent.ExactSourceReads(dict(encoder=R['entry'],factory=R['bridge'],f0_decoder=R['head'],f0_factory=R['observe']))
for r in [*R.values(),c['self_source']]:
 p=parent.exact(r)
 if p not in g.records:g.records[p]=r;g.fds[p]=parent.os.open(p,parent.os.O_RDONLY|getattr(parent.os,'O_NOFOLLOW',0));g.verify(p)
tools=types.ModuleType('tools');tools.__path__=[];sys.modules['tools']=tools
# Dependencies are real frozen source, not fake observation/runtime objects.
e.source('bcsp_training_contract_v1',R['contract']);e.source('tools.bcsp_adapter',R['adapter'])
class UTC:
 def allow(self,*a):return False
out=Path(c['owned']);policy=parent.make_policy(helper,[],out,[],[],[],UTC(),g);sys.addaudithook(policy.audit)
q=dict(implementation={k:R[k] for k in ['bridge','head','observe','training_runtime']})
try:
 bridge,observe,runtime=e.load_training_chain(q)
 assert sys.modules['bcsp_spcg_head_v1'].__file__==R['head']['path'] and observe.need is sys.modules['bcsp_spcg_head_v1'].need
 assert runtime.BCSPDataset.__module__=='spcg_frozen_training_runtime' and callable(runtime.train_lifecycle)
 Q=torch.randn(1,256,3,requires_grad=True);Q.square().mean().backward();assert observe.Q_gradient_record(Q)['L2']>0 and 'rms_radius' in observe.geometry(Q)
 def reject(fn):
  try:fn()
  except (RuntimeError,ValueError):return True
  return False
 assert reject(lambda:Path(R['head']['path']).open('wb'))
 assert reject(lambda:Path(c['neighbor']).read_bytes())
 assert reject(lambda:e.exact(dict(R['head'],sha256='0'*64)))
 e.emit(out/'chain_checks.json',dict(real_chain=True,observation_tensors=True,source_write_denied=True,neighbor_read_denied=True,bad_hash_denied=True,load_order=['bridge','head','observe','training_runtime']))
 try:raise RuntimeError('ARTIFICIAL_TRAINING_START_FAILURE')
 except RuntimeError as ex:e.fail_with_traceback(out,ex)
finally:
 e.emit(out/'cleanup_record.json',dict(before_close=True,guard_descriptors_open=bool(g.fds)))
 g.close()
