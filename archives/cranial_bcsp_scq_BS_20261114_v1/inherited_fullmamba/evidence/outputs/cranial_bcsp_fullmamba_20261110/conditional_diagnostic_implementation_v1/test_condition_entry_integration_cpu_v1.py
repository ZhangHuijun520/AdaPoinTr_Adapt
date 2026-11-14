"""Single lightweight artificial entry-loop integration; does not replay tensor tests."""
import copy,hashlib,importlib.util,json,subprocess,sys,types
from pathlib import Path
import numpy as np
import torch
from torch import nn
S=Path(__file__).resolve().parent;O=S/'artificial_entry_integration_v1'
def module(n,p):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def main():
 O.mkdir();torch.set_num_threads(2);checks=[]
 def check(n,yes=True):
  if not yes:raise AssertionError(n)
  checks.append(n)
 e=module('entry_integration_cpu',S/'bcsp_f0_condition_diagnostic_v1.py');p=module('native_helpers_integration_cpu',S.parent/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py')
 class Model(nn.Module):
  def __init__(self):
   super().__init__();self.weight=nn.Parameter(torch.tensor(0.1));self.num_query=256;self.num_points=8192;self.factor=32;self.decoder_type='fc';self.denoise_weight=0;self.fine_coverage_weight=1;self.fine_local_weight=0;self.scqr_contract=types.SimpleNamespace(enabled=False)
   self.base_model=nn.Module();b=self.base_model;b.center_num=[512,256];b.encoder_type='graph';b.query_selection='learned_only';b.use_denoise=False;b.encoder_adapter=types.SimpleNamespace(enabled=False);b.decoder=nn.Module();b.decoder.blocks=nn.ModuleList([nn.Identity() for _ in range(8)])
   for k in ('coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled'):setattr(self,k,False)
  def forward(self,*args):raise AssertionError('whole model forbidden')
 model=Model();ck=O/'artificial3900.pth';torch.save(dict(stage='BCSP_INPUT_DENSITY_V1',epoch=99,updates=3900,base_model=model.state_dict()),ck)
 index=copy.deepcopy(json.loads((S/'context_index_candidate_v1.json').read_bytes()))
 f=np.zeros((1,256,384),dtype=np.float32);q=np.zeros((1,256,3),dtype=np.float32)
 cache=O/'context.npz';np.savez_compressed(cache,F=f,S=q,Q=q,X=f,z=np.zeros((1,1024),np.float32))
 trace=O/'trace.npz';np.savez_compressed(trace,**{'layer_'+str(i)+'__'+k:f for i in range(8) for k in ('input','after_self','prefix_suffix','after_cross','output')})
 prediction=O/'prediction.npz';np.savez_compressed(prediction,prediction=np.zeros((8192,3),np.float32),coarse=q[0])
 for row in index['pairs']:
  for k,path in [('recipient_context',cache),('donor_context',cache),('Native_trace',trace),('Native_prediction',prediction)]:row[k]=rec(path)
 for run in index['runs']:run['checkpoint']=rec(ck)
 evidence=dict(version='F0-P-v2-implementation-v1',artificial_fixture=True,new_mamba_mixers=16,shared_coordinate_pe_parameters=1152,common_initialization_preserved=True,parent=dict(variant='M0',replaced_global_branches=6,common_state_unchanged=True),inventory=dict(forbidden_registered_modules=[]))
 def fingerprint(m):return hashlib.sha256(b''.join(v.detach().numpy().tobytes() for v in m.state_dict().values())).hexdigest()
 helper=types.SimpleNamespace(state_sha=fingerprint,tensor_sha=lambda t:hashlib.sha256(t.numpy().tobytes()).hexdigest(),assert_numeric=lambda t:None)
 calls=[]
 def intervene(m,r,d,c):
  calls.append(c);return torch.zeros(1,8192,3),[dict(layer_index=i,**{k:torch.zeros(1,256,384) for k in ('input','after_self','prefix_suffix','after_cross','output')}) for i in range(8)],dict(artificial_entry_surrogate=True)
 adapter=types.SimpleNamespace(TRACE_KEYS=('input','after_self','prefix_suffix','after_cross','output'),intervene=intervene,compare=lambda *args:([dict(artificial=True)]*64,dict(artificial=True)))
 out=O/'owned';out.mkdir()
 for name in ('predictions','traces'):(out/name).mkdir()
 samples=[];budget=types.SimpleNamespace(sample=lambda label,n:samples.append((label,n)))
 files,states=e.execute(torch,np,helper,p,adapter,index,out,budget,lambda run:(Model(),evidence),device='cpu',artificial=True)
 check('01 actual entry loop exact30 suffix calls',calls==list(e.CONDITIONS)*10 and len(files)==63)
 check('02 exact30 predictions30 traces',len(list((out/'predictions').glob('*.npz')))==len(list((out/'traces').glob('*.npz')))==30)
 responses=[json.loads(l) for l in (out/'responses.jsonl').read_text().splitlines()]
 check('03 exactly30 responses1920 stage/group rows',len(responses)==30 and sum(len(r['layers']) for r in responses)==1920)
 check('04 two eval state/RNG invariants',len(states)==2 and all(r['state_before']==r['state_after'] and r['RNG_before']==r['RNG_after'] for r in states))
 check('05 exact30 claimed/complete records',len((out/'calls.jsonl').read_text().splitlines())==60 and len(samples)==60)
 check('06 injected first call failure stops without retry')
 failed=O/'failure_owned';failed.mkdir()
 for name in ('predictions','traces'):(failed/name).mkdir()
 failures=[]
 def fail(*args):failures.append(1);raise RuntimeError('ARTIFICIAL_FIRST_SUFFIX_FAIL')
 try:e.execute(torch,np,helper,p,types.SimpleNamespace(TRACE_KEYS=adapter.TRACE_KEYS,intervene=fail),index,failed,budget,lambda run:(Model(),evidence),device='cpu',artificial=True)
 except RuntimeError as exc:assert str(exc)=='ARTIFICIAL_FIRST_SUFFIX_FAIL'
 else:raise AssertionError('failure swallowed')
 assert len(failures)==1 and len((failed/'calls.jsonl').read_text().splitlines())==1
 # Compile/load the fifth exact source under the production finite file policy.
 child=r'''
import ctypes,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
import torch
c=json.loads(Path(sys.argv[1]).read_bytes())
def load(n,r):
 sp=importlib.util.spec_from_file_location(n,r['path']);m=importlib.util.module_from_spec(sp);sys.modules[n]=m;sp.loader.exec_module(m);return m
p=load('entry_policy_native',c['native']);h=load('entry_policy_source_helper',c['helper']);guard=p.ExactSourceReads(c['implementation'])
r=c['adapter'];path=p.exact(r);fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0));guard.records[path]=r;guard.fds[path]=fd;guard.verify(path)
policy=p.make_policy(h,[],Path(c['owned']),[],[],[],types.SimpleNamespace(allow=lambda *args:False),guard);sys.addaudithook(policy.audit)
p.load_f0_builder(c['implementation']);adapter=p.source_module('entry_policy_adapter',r);assert len(adapter.CONDITIONS)==3
try:Path(r['path']).open('w')
except (RuntimeError,ValueError):pass
else:raise AssertionError('source write accepted')
try:Path(c['neighbor']).read_bytes()
except (RuntimeError,ValueError):pass
else:raise AssertionError('neighbor accepted')
guard.close();print('{"fifth_source_load":true,"write_denied":true,"neighbor_denied":true}')
'''
 R=S.parents[2];impl={}
 for k,n in [('encoder','bcsp_mamba_encoder_v1.py'),('factory','bcsp_p1_model_factory_v1.py')]:impl[k]=rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'/n)
 for k,n in [('f0_decoder','bcsp_f0_decoder_v1.py'),('f0_factory','bcsp_f0_factory_v1.py')]:impl[k]=rec(S.parent/'implementation_v1'/n)
 neighbor=O/'neighbor.py';neighbor.write_bytes(b'VALUE=0\n');owned=O/'policy_owned';owned.mkdir()
 config=O/'policy_fixture.json';config.write_text(json.dumps(dict(native=rec(S.parent/'Native_prediction_implementation_v1/bcsp_f0_twofold_native_predict_v1.py'),helper=rec(R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'),implementation=impl,adapter=rec(S/'bcsp_f0_condition_adapter_v1.py'),owned=str(owned),neighbor=str(neighbor))),encoding='utf-8')
 run=subprocess.run([sys.executable,'-I','-B','-c',child,str(config)],capture_output=True,timeout=30)
 for k,data in [('stdout',run.stdout),('stderr',run.stderr)]:(O/('policy_'+k+'.bin')).write_bytes(data)
 check('07 actual fifth-source load and exact policy',run.returncode==0 and all(json.loads(run.stdout).values()))
 result=dict(status='ARTIFICIAL_ENTRY_INTEGRATION_PASS',count=len(checks),checks=checks,real_data=False,CUDA=False,production_sources=[rec(S/'bcsp_f0_condition_adapter_v1.py'),rec(S/'bcsp_f0_condition_diagnostic_v1.py')],limitation='Entry loop uses lightweight artificial suffix surrogate. Actual F0 tensor semantics are separately covered by the frozen34-check batch.')
 (O/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(dict(status=result['status'],count=len(checks))))
if __name__=='__main__':main()
