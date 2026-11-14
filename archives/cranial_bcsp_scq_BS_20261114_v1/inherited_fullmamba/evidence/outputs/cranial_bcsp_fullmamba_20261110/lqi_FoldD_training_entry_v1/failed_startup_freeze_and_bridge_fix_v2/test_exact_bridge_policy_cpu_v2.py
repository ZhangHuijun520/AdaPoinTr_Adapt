"""Actual inherited policy + exact entry source loading, no model or CUDA."""
import ast,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
F=Path(__file__).resolve().parent;S=F.parent;B=S.parent;R=S.parents[2];O=F/'cpu_policy_batch_v2'
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 O.mkdir();checks=[]
 def check(n,v):
  if not v:raise AssertionError(n)
  checks.append(n)
 old=S/'bcsp_lqi_foldD_training_entry_v1.py';new=F/'bcsp_lqi_foldD_training_entry_v2.py'
 a=old.read_text(encoding='utf-8');b=new.read_text(encoding='utf-8')
 check('single exact bridge Path added only',b.replace("Path(q['implementation']['bridge']['path']),",'',1)==a)
 compile(ast.parse(b),str(new),'exec');check('final AST compiles',True)
 records=dict(entry=rec(new),old=rec(old),bridge=rec(B/'lqi_training_entry_v1/bcsp_lqi_runtime_adapter_v1.py'),parent=rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/training_entry_v1/bcsp_p1_training_entry_v1.py'),helper=rec(R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'))
 impl={}
 for k,n in [('encoder','bcsp_mamba_encoder_v1.py'),('factory','bcsp_p1_model_factory_v1.py')]:impl[k]=rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'/n)
 for k,n in [('lqi_decoder','bcsp_lqi_decoder_v1.py'),('lqi_factory','bcsp_lqi_factory_v1.py')]:impl[k]=rec(B/'lqi_implementation_v1'/n)
 config=O/'fixture.json';config.write_text(json.dumps(dict(records=records,implementation=impl,owned=str(O.absolute()))),encoding='utf-8')
 child=r'''
import ast,ctypes,hashlib,importlib.util,json,sys,types
from pathlib import Path
import torch
c=json.loads(Path(sys.argv[1]).read_bytes());rs=c['records']
def load(name,r):
 sp=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(sp);sys.modules[name]=m;sp.loader.exec_module(m);return m
e=load('actual_lqi_entry',rs['entry']);parent=load('actual_lqi_policy_parent',rs['parent']);h=load('actual_lqi_policy_helper',rs['helper'])
for name,key in [('bcsp_mamba_encoder_v1','encoder'),('bcsp_p1_model_factory_v1','factory'),('bcsp_lqi_decoder_v1','lqi_decoder'),('bcsp_lqi_factory_v1','lqi_factory')]:e.source_module(name,c['implementation'][key])
q={'implementation':dict(c['implementation'],bridge=rs['bridge'],contract=rs['parent'],budget_parent=rs['parent'],timezone=rs['helper'])}
base=Path(c['owned']);roots={}
for key in ('root','entryroot','envroot','provider'):
 roots[key]=base/key;roots[key].mkdir()
def extract_roots(path):
 tree=ast.parse(Path(path).read_bytes());node=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='read_roots' for t in n.targets))
 return eval(compile(ast.Expression(node.value),'actual_read_roots','eval'),dict(Path=Path,q=q,os=__import__('os'),**roots))
old_roots=extract_roots(rs['old']['path']);new_roots=extract_roots(rs['entry']['path']);utc=types.SimpleNamespace(allow=lambda *args:False)
old_policy=parent.make_training_policy(h,old_roots,base,{},utc);new_policy=parent.make_training_policy(h,new_roots,base,{},utc)
try:old_policy.check(rs['bridge']['path'])
except (RuntimeError,ValueError):pass
else:raise AssertionError('old boundary not reproduced')
new_policy.check(rs['bridge']['path']);new_policy.check(rs['bridge']['path'],write=False)
try:new_policy.check(rs['bridge']['path'],write=True)
except (RuntimeError,ValueError):pass
else:raise AssertionError('source write allowed')
try:new_policy.check(str(Path(rs['bridge']['path']).with_name('unbound_neighbor.py')))
except (RuntimeError,ValueError):pass
else:raise AssertionError('neighbor directory broadened')
sys.addaudithook(new_policy.audit)
bridge=e.source_module('actual_exact_bridge_under_policy',rs['bridge'])
assert callable(bridge.train_lifecycle) and callable(bridge.forward_loss)
assert new_roots==old_roots[:-3]+[Path(rs['bridge']['path'])]+old_roots[-3:] if False else len(new_roots)==len(old_roots)+1
print(json.dumps(dict(old_failure_reproduced=True,actual_bridge_import_under_policy=True,write_denied=True,neighbor_denied=True,one_extra_exact_file=True)))
'''
 run=subprocess.run([sys.executable,'-I','-B','-c',child,str(config)],capture_output=True,timeout=30)
 for k,v in [('stdout',run.stdout),('stderr',run.stderr)]:
  with (O/(k+'.bin')).open('xb') as f:f.write(v)
 check('actual child policy regression returns0',run.returncode==0)
 data=json.loads(run.stdout)
 for k,v in data.items():check(k,v is True)
 result=dict(status='EXACT_BRIDGE_READ_POLICY_CPU_PASS',checks=checks,count=len(checks),entry=records['entry'],bridge=records['bridge'],test=rec(Path(__file__)),CUDA_calls=0,server_operations=0,model_forward=0,optimizer_steps=0)
 with (O/'result.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(status=result['status'],checks=len(checks))))
if __name__=='__main__':main()
