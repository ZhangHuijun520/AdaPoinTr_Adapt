"""Local bounded differential review and actual terminal-call CPU contract check."""
from pathlib import Path
from types import SimpleNamespace,ModuleType
import ast,builtins,copy,hashlib,json,runpy,sys
d=Path(__file__).resolve().parent;base=d.parent;project=base.parents[1]
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
worker_path=d/'ejtc_train_j_d_v1.py';launcher_path=d/'launch_ejtc_j_d_v1.py'
env=runpy.run_path(str(worker_path),run_name='P3_readonly_review')
cpu=d/'cpu_validation_v1/J_D_CPU_validation_receipt_v1.json';c=json.loads(cpu.read_bytes())
assert c['status']=='J_D_TARGETED_CPU_VALIDATION_PASS' and c['passed']==33 and not c['CUDA_initialized']
assert c['worker_sha256']==h(worker_path) and c['launcher_sha256']==h(launcher_path)
runtime=project/'outputs/scq_prime_publication_20261122_v1/archives/cranial_bcsp_scq_prime_20261122_v1/code/bcsp_scq_prime_runtime_v1.py'
tree=ast.parse(runtime.read_bytes());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='train_lifecycle')
runtime_env={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(runtime),'exec'),runtime_env)
captured=[]
def capture_compile(value,*args,**kwargs):
 if isinstance(value,ast.Module):captured.append(copy.deepcopy(value))
 return builtins.compile(value,*args,**kwargs)
env['lifecycle'].__globals__['compile']=capture_compile
try:env['lifecycle'](SimpleNamespace(train_lifecycle=runtime_env['train_lifecycle']),h(runtime),lambda p:p,lambda *a:None)
finally:env['lifecycle'].__globals__.pop('compile')
assert len(captured)==1
changed=captured[0].body[0]
# Revert the exact allowed T adapter edits and require the entire lifecycle AST
# (optimizer, order, resources, schedule, counters, serialization) to equal the parent.
changed.body[1]=copy.deepcopy(node.body[1])
for v in ast.walk(changed):
 if not isinstance(v,ast.Assign):continue
 if isinstance(v.value,ast.Call) and isinstance(v.value.func,ast.Name) and v.value.func.id=='_components':
  replacement=ast.parse('sparse, dense = model.get_loss(ret, target, epoch, partial=partial)').body[0]
  v.targets,v.value=replacement.targets,replacement.value
 if any(isinstance(t,ast.Name) and t.id=='loss' for t in v.targets):
  assert ast.dump(v.value)==ast.dump(ast.parse('sparse + dense + _lambda * ejtc_auxiliary',mode='eval').body)
  v.value=ast.parse('sparse + dense',mode='eval').body
 if any(isinstance(t,ast.Name) and t.id=='event' for t in v.targets):
  keys=[x.value for x in v.value.keys]
  assert keys[-4:]==['ejtc_auxiliary','ejtc_applied_lambda','ejtc_weighted_auxiliary','ejtc_region_counts']
  v.value.keys=v.value.keys[:-4];v.value.values=v.value.values[:-4]
assert ast.dump(changed)==ast.dump(node)
# Actual main() terminal expressions, including the concrete importlib consumer.
wt=ast.parse(worker_path.read_bytes());main=next(n for n in wt.body if isinstance(n,ast.FunctionDef) and n.name=='main')
assert isinstance(main.body[-3],ast.Assign) and isinstance(main.body[-2],ast.FunctionDef) and main.body[-2].name=='paired_components' and isinstance(main.body[-1],ast.Expr)
trace=[]
q=json.loads((d/'J_D_execution_request_CPU_fixture_v1.json').read_bytes())
def resources(*args):trace.append('TrainingResources');return 'CPU_RESOURCE_SENTINEL'
def factory(runtime,digest,claim,components):
 trace.append('lifecycle_factory')
 assert digest=='FROZEN_RUNTIME_DIGEST'
 def call(*args,**kwargs):
  assert kwargs['run_identity']==dict(variant='J',fold='D',seed=2026112801)
  assert kwargs['knn_enable']=='CPU_KNN_SENTINEL' and kwargs['resources']=='CPU_RESOURCE_SENTINEL'
  trace.append('training_lifecycle_boundary')
 return call
mock=ModuleType('models.Transformer_utils');mock.enable_bcsp_knn='CPU_KNN_SENTINEL'
prior=sys.modules.get('models.Transformer_utils');sys.modules['models.Transformer_utils']=mock
terminal=dict(env,old=SimpleNamespace(TrainingResources=resources),out=Path('CPU_FIXTURE_ONLY'),
 torch='CPU_TORCH_SENTINEL',helper=SimpleNamespace(assert_numeric='CPU_NUMERIC',state_sha='CPU_HASH'),
 support=SimpleNamespace(resources=None),parent={},prefix=SimpleNamespace(emit=None),
 binding=q['binding'],runtime='CPU_RUNTIME',impl={'training_runtime':{'sha256':'FROZEN_RUNTIME_DIGEST'}},
 claim='CPU_CLAIM',model='CPU_MODEL',loader='CPU_LOADER',rows=[],order={},lifecycle=factory,ch=None,candidate=None)
try:exec(compile(ast.Module(body=main.body[-3:],type_ignores=[]),str(worker_path),'exec'),terminal)
finally:
 if prior is None:sys.modules.pop('models.Transformer_utils')
 else:sys.modules['models.Transformer_utils']=prior
assert trace==['TrainingResources','lifecycle_factory','training_lifecycle_boundary']
old_launcher=project/'outputs/bcsp_rbss_20261126_v2/foldd_accuracy_preparation_v1/launch_rbss_r_d_v1.py'
expected=old_launcher.read_text().replace('Single-attempt R_D launcher','Single-attempt J_D launcher').replace("q['arm']=='R'","q['arm']=='J'").replace("'R_D frozen request'","'J_D frozen request'")
expected=expected.replace("q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'","q['schema']=='bcsp-ejtc-foldD-j-training-v1' and q['lambda']==0.027474069997873135\n         and q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION'")
assert ast.dump(ast.parse(expected))==ast.dump(ast.parse(launcher_path.read_bytes()))
assert h(base/'ejtc_loss_cpu_candidate_v1.py')=='eaab0e866a120e52655adf5bbcaca8aedc37df87c05c8b52016ec9e1d4a579f2'
T_source=ast.parse((base/'d1_t_d_preparation_v1/ejtc_train_t_d_v1.py').read_bytes())
J_source=ast.parse(worker_path.read_bytes())
for name in ['need','sha','bound','load_common_state','seed_pair_rng']:
 original=next(n for n in T_source.body if isinstance(n,ast.FunctionDef) and n.name==name)
 new=next(n for n in J_source.body if isinstance(n,ast.FunctionDef) and n.name==name)
 assert ast.dump(new)==ast.dump(original)
assert h(base/'d1_t_d_preparation_v1/ejtc_train_t_d_v1.py')=='589b2e38d5d0cdca6b1cb8fc08e8e202bf7047bb733e4b725f8bcd421e8a318d'
assert h(base/'ejtc_train_r_d_v2.py')=='0d797a8c0d910d139f0b21186eb35f069f468157babf3fbd9dedf98773199043'
receipt=dict(status='J_D_P3_BOUNDED_DIFFERENTIAL_REVIEW_PASS',worker_sha256=h(worker_path),launcher_sha256=h(launcher_path),CPU_receipt_sha256=h(cpu),CPU_checks=33,actual_start_terminal_call_path=trace,normalized_lifecycle_equals_parent=True,launcher_diff_limited_to_J_identity_and_schema_lambda=True,loss_candidate_unchanged=True,R_worker_unchanged=True,guards_resources_3900_contract_unchanged=True,pairing_includes_strict_frozen_state_and_four_RNG_checks=True,label_batch_binding_checks_pass=True,real_315_label_files_verified=True,actual_8_case_GT_row_hashes_verified=True,T_worker_unchanged=True,unresolved_required_before_execution=['Fresh server identity/resource/dependency/target recheck','No-overwrite installation authorization','Separate final request SHA256 execution authorization'],limitations=c['limitations'],CUDA_repeated=False,remote_operations=0,review_type='Local source differential and recorded CPU evidence review, no independent external reviewer')
with (d/'J_D_P3_review_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
