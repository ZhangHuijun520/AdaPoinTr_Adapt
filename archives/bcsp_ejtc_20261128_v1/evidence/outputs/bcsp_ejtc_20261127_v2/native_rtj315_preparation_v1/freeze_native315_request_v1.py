"""Local P3 differential checks and pending request freeze; no execution approval."""
from pathlib import Path
import ast,difflib,hashlib,importlib.util,json
d=Path(__file__).resolve().parent
h=lambda b:hashlib.sha256(b).hexdigest()
def rec(p):return dict(local_path=str(p),bytes=p.stat().st_size,sha256=h(p.read_bytes()))
def write(p,value):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
worker=d/'ejtc_native_rtj315_v1.py';launcher=d/'launch_ejtc_native315_v1.py'
q=json.loads((d/'Native315_execution_request_CPU_fixture_v1.json').read_bytes())
cpu=d/'cpu_validation_v2/Native315_CPU_validation_receipt_v1.json';startup=d/'cpu_startup_validation_v1/startup_receipt_v1.json'
c=json.loads(cpu.read_bytes());s=json.loads(startup.read_bytes())
assert c['passed']==28 and c['CUDA_initialized'] is False and s['status']=='ACTUAL_WORKER_MAIN_CPU_STARTUP_PASS'
assert c['worker_sha256']==s['worker_sha256']==h(worker.read_bytes()) and c['launcher_sha256']==h(launcher.read_bytes())
for p in (worker,launcher,d/'verify_native315_cpu_v2.py',d/'verify_native315_startup_cpu_v1.py'):compile(p.read_bytes(),str(p),'exec')
tree=ast.parse(worker.read_bytes());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
assert not any(isinstance(n.func,ast.Attribute) and n.func.attr in ('backward','step','get_loss','train') for n in calls)
run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
assert sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='observe' for n in ast.walk(run))==1
text=worker.read_text();assert 'temporary_order' not in text and 'loss_candidate' not in text
old=d.parent/'d1_j_d_preparation_v1/launch_ejtc_j_d_v1.py'
before=ast.parse(old.read_bytes());after=ast.parse(launcher.read_bytes())
def function(t,name):return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
for name in ('need','exact','gpu','observe'):assert ast.dump(function(before,name))==ast.dump(function(after,name))
# Compare the unchanged launcher body after its Native-specific authorization checks.
bm=function(before,'main');am=function(after,'main')
assert ast.dump(ast.Module(body=bm.body[:14],type_ignores=[]))==ast.dump(ast.Module(body=am.body[:14],type_ignores=[]))
assert ast.dump(ast.Module(body=bm.body[16:],type_ignores=[]))==ast.dump(ast.Module(body=am.body[16:],type_ignores=[]))
diff=''.join(difflib.unified_diff(old.read_text().splitlines(True),launcher.read_text().splitlines(True),fromfile=old.name,tofile=launcher.name))
(d/'launcher_P3_diff_v1.txt').write_text(diff,encoding='utf-8')
p3=dict(status='EJTC_NATIVE315_P3_LIMITED_REVIEW_PASS',review_type='Local bounded source and contract review, not an independent external review',
 checks=['All four implementation/test files compile','28 CPU checks pass with unchanged production entry','Actual worker.main startup path passes with explicit CPU fixtures','No train/loss/backward/step call in Native worker','One observed full forward per fixed case, 315 claims; overrun rejected','Frozen Native observer checks S+delta, consumed coarse and FC parent-major output','No RBSS permutation intervention','Only partial array is accessed; unreadable artificial GT is never accessed','Three checkpoint arm identities and strict state loading checked','Parameters/buffers and RNG unchanged per arm; mutation detection checked','Archive has 315 predictions plus five evidence members','Launcher resource monitor, GPU query, termination logic and trailing startup body unchanged from J launcher'],
 worker=rec(worker),launcher=rec(launcher),CPU=rec(cpu),startup_CPU=rec(startup),launcher_diff=rec(d/'launcher_P3_diff_v1.txt'),
 prior_failed_batch=dict(path=str(d/'cpu_validation_v1/failed_checks.json'),cause='Artificial coarse head returned delta/used in reverse order; fixture-only v2 correction'),
 CUDA_executed=False,server_operations=0,limitations=c['limitations']+s['limitations'])
p3path=d/'Native315_P3_review_v1.json';write(p3path,p3)
q['readiness_status']='LOCAL_CPU_P3_PASS_PENDING_FRESH_SERVER_RECHECK_INSTALL_AND_EXPLICIT_EXECUTION_AUTHORIZATION'
q['validation_evidence']=dict(CPU=rec(cpu),startup_CPU=rec(startup),P3=rec(p3path),CPU_does_not_certify_CUDA=True,GPU_preflight_not_repeated=True)
assert q['files']['worker']['sha256']==h(worker.read_bytes()) and q['launch']['launcher']['sha256']==h(launcher.read_bytes())
final=d/'EJTC_RTJ_D_native315_execution_request_h7vvrr_v1.json';write(final,q)
raw=final.read_bytes();digest=h(raw)
spec=importlib.util.spec_from_file_location('worker',worker);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
spec=importlib.util.spec_from_file_location('materializer',q['authorization_materializer']['local_path']);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
a,r=m.materialize(raw,'Final-byte CPU authorization-chain fixture only; not live approval',execution_authorized=True)
w.authorize(json.loads(raw),digest,json.loads(a),h(a),json.loads(r))
with Path(str(final)+'.sha256').open('x',encoding='ascii') as f:f.write(digest+'  '+final.name+'\n')
write(d/'Native315_final_request_freeze_receipt_v1.json',dict(status='FINAL_PENDING_REQUEST_FROZEN',request=rec(final),P3=rec(p3path),counts=q['counts'],
 final_serialized_authorize_path_CPU_PASS=True,live_authorization_materialized=False,execution_authorized=False,
 next_boundary='Fresh read-only server readiness and minimal transport preparation; installation and execution separately authorized'))
print(json.dumps(dict(status='FINAL_PENDING_REQUEST_FROZEN',sha256=digest,bytes=len(raw))))
