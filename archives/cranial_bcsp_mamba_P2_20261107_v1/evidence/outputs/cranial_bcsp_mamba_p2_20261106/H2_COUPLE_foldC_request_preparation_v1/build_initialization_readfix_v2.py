"""One-expression policy root fix, plus isolated actual audit-hook regression."""
import ast,hashlib,json
from pathlib import Path
A=Path(__file__).resolve().parent;S=A.parent/'H2_COUPLE_foldC_initialization_readfix_v2';S.mkdir()
audit=A/'failed_attempt_freeze_audit_v1/audit_report_v1.json';assert json.loads(audit.read_bytes())['status']=='FORMAL_COUPLE_V1_FAILED_STARTUP_FREEZE_AUDIT_PASS'
old=A/'bcsp_h2_couple_foldC_training_entry_v1.py';source=old.read_text(encoding='utf-8')
needle="read_roots=[root,impl,Path(q['implementation']['h2_range']['path']).parent,"
replacement="read_roots=[root,impl,Path(q['aux_pairing']['initialization']['path']),Path(q['implementation']['h2_range']['path']).parent,"
assert source.count(needle)==1;source=source.replace(needle,replacement);ast.parse(source)
with (S/'bcsp_h2_couple_foldC_training_entry_v2.py').open('x',encoding='utf-8',newline='\n') as f:f.write(source)
test=(A/'test_couple_entry_cpu_v1.py').read_text(encoding='utf-8').replace('bcsp_h2_couple_foldC_training_entry_v1.py','bcsp_h2_couple_foldC_training_entry_v2.py').replace("O=S/'artificial_cpu_batch_v2'","O=S/'artificial_cpu_batch_v1'")
test=test.replace('import ast,copy,hashlib,importlib.util,json,sys,types','import ast,copy,hashlib,importlib.util,json,subprocess,sys,types')
anchor="  emit('result_v1.json',dict(status='H2_COUPLE_ENTRY_CPU_CONTRACT_PASS'"
extra='''  # Exercise the actual source read_roots expression and installed FilePolicy.audit in a child.
  helperfile=G/'gpu_preflight_plotting_lazy_v3/bcsp_artificial_gpu_preflight_v3.py'
  check('33 exact original helper source',bind(helperfile)['sha256']=='7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291')
  fixture=O/'policy_fixture';fixture.mkdir();owned=fixture/'owned';owned.mkdir();external=fixture/'outside';external.mkdir()
  ref=external/'initialization.json';ref.write_text(json.dumps({'fixture':'EXACT_READ_ONLY'}));sibling=external/'other.json';sibling.write_text('{}');secret=external/'.env';secret.write_text('ARTIFICIAL_ONLY');ckpt=external/'old.pth';ckpt.write_bytes(b'ARTIFICIAL_ONLY');npz=external/'other.npz';npz.write_bytes(b'ARTIFICIAL_ONLY')
  roots={}
  for key in ['root','impl','factory_root','envroot','provider','contract']:
   path=fixture/key;path.mkdir();roots[key]=str(path.absolute())
  child_q=dict(implementation={'h2_range':{'path':str(Path(roots['impl'])/'range.py')},'contract':{'path':str(Path(roots['contract'])/'contract.py')}},aux_pairing={'initialization':bind(ref)})
  config=emit('policy_fixture_definition.json',dict(entry=bind(S/'bcsp_h2_couple_foldC_training_entry_v2.py'),helper=bind(helperfile),q=child_q,roots=roots,owned=str(owned.absolute()),sibling=str(sibling.absolute()),secret=str(secret.absolute()),ckpt=str(ckpt.absolute()),npz=str(npz.absolute())))
  child_code=r"""
import ast,hashlib,importlib.util,json,os,sys,types
from pathlib import Path
cfg=json.loads(Path(sys.argv[1]).read_bytes())
def load(name,r):
 b=Path(r['path']).read_bytes();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']
 spec=importlib.util.spec_from_file_location(name,r['path']);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
entry=load('policy_target_entry',cfg['entry']);helper=load('original_policy_helper',cfg['helper']);q=cfg['q'];ns=dict(Path=Path,os=os,q=q,**{k:Path(v) for k,v in cfg['roots'].items()})
tree=ast.parse(Path(cfg['entry']['path']).read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');assignment=next(n for n in ast.walk(main) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='read_roots' for t in n.targets))
roots=eval(compile(ast.Expression(assignment.value),'<actual-main-read-roots>','eval'),ns)
ref=Path(q['aux_pairing']['initialization']['path']);assert ref in roots and ref.parent not in roots
utc=types.SimpleNamespace(allow=lambda *args:False);old=entry.make_training_policy(helper,[r for r in roots if r!=ref],cfg['owned'],{},utc)
try:old.check(ref)
except RuntimeError:old_rejected=True
else:raise AssertionError('old policy unexpectedly allowed exact reference')
policy=entry.make_training_policy(helper,roots,cfg['owned'],{},utc);sys.addaudithook(policy.audit)
checks={'actual_old_policy_reproduces_boundary':old_rejected,'exact_file_not_parent_in_real_roots':True,'actual_json_bound_under_installed_audit_hook':entry.json_bound(q['aux_pairing']['initialization'])=={'fixture':'EXACT_READ_ONLY'}}
def reject(name,fn):
 try:fn()
 except (ValueError,RuntimeError):checks[name]=True
 else:raise AssertionError(name)
reject('write_to_reference_denied',lambda:ref.open('w'))
for k in ['sibling','secret','ckpt','npz']:reject(k+'_read_denied',lambda k=k:Path(cfg[k]).read_bytes())
bad=dict(q['aux_pairing']['initialization'],sha256='0'*64);reject('wrong_reference_hash_denied',lambda:entry.json_bound(bad))
bad=dict(q['aux_pairing']['initialization'],bytes=1);reject('wrong_reference_size_denied',lambda:entry.json_bound(bad))
owned=Path(cfg['owned'])/'allowed.log';owned.write_text('ARTIFICIAL_ONLY');checks['owned_log_write_still_allowed']=owned.read_text()=='ARTIFICIAL_ONLY'
checks['reference_unchanged']=hashlib.sha256(ref.read_bytes()).hexdigest()==q['aux_pairing']['initialization']['sha256']
assert all(checks.values());print(json.dumps(checks))
"""
  cp=subprocess.run([sys.executable,'-I','-B','-c',child_code,config['path']],capture_output=True,timeout=25)
  for name,data in [('stdout',cp.stdout),('stderr',cp.stderr)]:
   with (O/('actual_policy_child_'+name+'.bin')).open('xb') as f:f.write(data)
  check('34 actual policy child passes',cp.returncode==0)
  policy_checks=json.loads(cp.stdout);check('35 old boundary reproduced new exact read succeeds',policy_checks['actual_old_policy_reproduces_boundary'] and policy_checks['actual_json_bound_under_installed_audit_hook'])
  check('36 file-only allowlist not parent directory',policy_checks['exact_file_not_parent_in_real_roots'] and policy_checks['sibling_read_denied'])
  check('37 reference write denied unchanged',policy_checks['write_to_reference_denied'] and policy_checks['reference_unchanged'])
  check('38 secrets and nonallowlisted payloads denied',all(policy_checks[k+'_read_denied'] for k in ['secret','ckpt','npz']))
  check('39 reference hash and size still enforced',policy_checks['wrong_reference_hash_denied'] and policy_checks['wrong_reference_size_denied'])
  check('40 original owned log write preserved',policy_checks['owned_log_write_still_allowed'])
'''
assert test.count(anchor)==1;test=test.replace(anchor,extra+anchor);ast.parse(test)
with (S/'test_couple_readfix_cpu_v2.py').open('x',encoding='utf-8',newline='\n') as f:f.write(test)
assert source.replace(replacement,needle)==old.read_text(encoding='utf-8')
files=[S/'bcsp_h2_couple_foldC_training_entry_v2.py',S/'test_couple_readfix_cpu_v2.py']
with (S/'static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='STATIC_S0_S1_PASS',one_expression_production_delta=True,exact_file_allowlist_not_parent=True,old_entry_sha256=hashlib.sha256(old.read_bytes()).hexdigest(),failure_freeze_audit_sha256=hashlib.sha256(audit.read_bytes()).hexdigest(),files=[dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],server_writes=0),f,indent=2)
print('STATIC_S0_S1_PASS_ONE_EXACT_FILE_ROOT_ONLY')
