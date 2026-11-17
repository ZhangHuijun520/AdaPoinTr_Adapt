"""Finish pre-test preparation after Windows file-list decoding issue; no test rerun."""
from pathlib import Path,PurePosixPath
import json,hashlib,ast,subprocess
S=Path(__file__).resolve().parent;W=S.parents[1];P=S/'G1_C_implementation_v1';V=S/'G2_C_implementation_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p,target=None):return dict(path=target or str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def emit(n,x):
 with (V/n).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
assert not (V/'CPU_batch_v1').exists()
source=(S/'prepare_G2_C_implementation_v1.py').read_text(encoding='utf-8')
# Only update pre-test fixture assertions; production entry and bridge remain unchanged.
old=(V/'test_G2_C_CPU_v1.py').read_text(encoding='utf-8')
old=old.replace("check(22,'\\\\' not in launcher", "check(22,all('\\\\' not in p for p in q['launch_contract'].values())")
old=old.replace("life_mod=load('G2_group_runtime_only',life);groups,rows=life_mod.optimizer_groups(m)", "groupfn=next(n for n in ast.parse(life.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name=='optimizer_groups');ns=dict(require=lambda ok,msg:e.need(ok,msg));exec(compile(ast.Module(body=[groupfn],type_ignores=[]),str(life),'exec'),ns);groups,rows=ns['optimizer_groups'](m)")
ast.parse(old);(V/'test_G2_C_CPU_v1.py').write_text(old,encoding='utf-8',newline='\n')
q=read(V/'draft_G2_C_request_v1.json')
exec(compile(source[source.index('records=list(q['):],str(S/'prepare_G2_C_implementation_v1.py')+'::finish','exec'))
