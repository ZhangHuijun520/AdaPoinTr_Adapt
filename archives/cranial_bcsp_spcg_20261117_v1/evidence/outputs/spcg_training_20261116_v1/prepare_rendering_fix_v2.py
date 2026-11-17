"""Repair local command rendering, compile all rendered scripts; no remote mutation."""
from pathlib import Path
import ast,hashlib,json
S=Path(__file__).resolve().parent;O=S/'rendering_fix_v2';O.mkdir()
original=(S/'execute_authorized_G0_C_v1.py').read_text(encoding='utf-8');tree=ast.parse(original)
pre=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='PRE' for t in n.targets))
calls=[(ast.literal_eval(n.value.args[0]),ast.literal_eval(n.value.args[1])) for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='remote']
review=[];updated=[]
for label,body in calls:
 if label=='04_materialize_launch_once':
  assert body.count("+'\n'")==2;body=body.replace("+'\n'","+chr(10)")
 code=pre+body;compile(code,label,'exec');p=O/(label+'_rendered_static.py');p.write_text(code,encoding='utf-8');review.append(dict(label=label,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),static_compile=True));updated.append((label,body))
# New invocation will only recheck existing installation, then materialize/start once.
prefix=original[:original.index("remote('01_reused_assets'")].replace("authorized_execution_v1","authorized_start_attempt_v2")
chosen=[]
for label,body in updated:
 if label=='03_install_once':continue
 if label=='02_targets_resources':
  body=body.replace('assert not root.exists() and not root.is_symlink()','assert root.is_dir() and not root.is_symlink()')
  body=body.replace('for v in [root,Path(q[\'output\'])]:','for v in [Path(q[\'output\'])]:')
  body=body.replace("assert not Path(r['target']).exists();b=t.extractfile(r['member']).read();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']","exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']));b=t.extractfile(r['member']).read();assert len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256']")
  body+="\nassert not (root/'control').exists()\n"
 compile(pre+body,label,'exec');chosen.append('remote('+repr(label)+','+repr(body)+')\n')
target=S/'start_existing_installation_attempt_v2.py';assert not target.exists();target.write_text(prefix+''.join(chosen),encoding='utf-8');ast.parse(target.read_text(encoding='utf-8'))
receipt=dict(status='LOCAL_RENDERING_STATIC_COMPILE_PASS_AWAITING_SEPARATE_START_AUTHORIZATION',change='serialization newline uses chr(10); same request/source/launcher contract',rendered_scripts=review,new_start_driver=dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest()),server_writes=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,training_started=False)
(O/'static_review_v2.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8');print('ALL4_RENDERED_SCRIPTS_COMPILE_NEW_DRIVER_NO_INSTALL')
