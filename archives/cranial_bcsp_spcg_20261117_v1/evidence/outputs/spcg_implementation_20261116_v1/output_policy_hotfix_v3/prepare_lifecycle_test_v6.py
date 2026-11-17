from pathlib import Path
import ast,json,hashlib
V=Path(__file__).resolve().parent
text=(V/'test_output_policy_cpu_v5.py').read_text(encoding='utf-8').replace("O=V/'CPU_batch_v5'","O=V/'CPU_batch_v6'")
needle="\ng.close()\nbad=dict(q,parent_helper=dict(q['parent_helper'],sha256='0'*64))"
assert text.count(needle)==1;text=text.replace(needle,"\nbad=dict(q,parent_helper=dict(q['parent_helper'],sha256='0'*64))")
start=text.index('for x in paths:\n');end=text.index("\n'''",start)
block=text[start:end];text=text[:start]+'try:\n'+''.join(' '+line+'\n' for line in block.splitlines())+'finally:\n g.close()'+text[end:]
text=text.replace('SPCG_OUTPUT_POLICY_SELF_BOUND_CPU_PASS','SPCG_OUTPUT_POLICY_LIFECYCLE_CPU_PASS')
p=V/'test_output_policy_cpu_v6.py';assert not p.exists();ast.parse(text);p.write_text(text,encoding='utf-8')
scope=json.loads((V/'Windows_CPU_scope_v5.json').read_text());scope.update(output='CPU_batch_v6',test_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),changes='Artificial child fixture only: bad-hash negative case executes before guard closure; close in finally after all policy assertions and result print',attempts=1)
(V/'Windows_CPU_scope_v6.json').write_text(json.dumps(scope,indent=2),encoding='utf-8');print('V6_STATIC_READY')
