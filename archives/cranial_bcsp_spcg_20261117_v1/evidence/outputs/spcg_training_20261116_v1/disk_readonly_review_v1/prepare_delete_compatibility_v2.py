from pathlib import Path
import ast
V=Path(__file__).resolve().parent
s=(V/'delete_authorized_58_parts_v1.py').read_text(encoding='utf-8')
assert s.count('p.is_relative_to(r)')==1
s=s.replace('p.is_relative_to(r)','r in p.parents').replace("O=V/'authorized_delete58_v1'","O=V/'authorized_delete58_v2'")
ast.parse(s)
assert Path('/a/b/c').is_relative_to(Path('/a/b'))==(Path('/a/b') in Path('/a/b/c').parents)
assert Path('/a/b2/c').is_relative_to(Path('/a/b'))==(Path('/a/b') in Path('/a/b2/c').parents)
with (V/'delete_authorized_58_parts_v2.py').open('x',encoding='utf-8') as f:f.write(s)
print('STATIC_PATH_COMPATIBILITY_PASS')
