"""Resume remaining authorized read-only log audit; reuse prior hash/readback evidence."""
from pathlib import Path
import ast
V=Path(__file__).resolve().parent;p=V/'post_training_freeze_G0_C_v3.py';s=p.read_text(encoding='utf-8');tree=ast.parse(s);lines=s.splitlines(keepends=True)
replacements=[]
for n in tree.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('inventory','binding'):
  name=n.targets[0].id;file='01_inventory_checkpoint_result.json' if name=='inventory' else '02_binding_initialization_result.json';replacements.append((n.lineno-1,n.end_lineno,name+"=json.loads((O/'"+file+"').read_text(encoding='utf-8'))\n"))
for start,end,value in sorted(replacements,reverse=True):lines[start:end]=[value]
s=''.join(lines).replace("O.mkdir()","assert O.is_dir()",1).replace('code=PREFIX+body;','code=(PREFIX.split(\'def record(p):\')[0] if label.startswith(\'03\') else PREFIX)+body;',1)
compile(s,str(p)+'::remaining','exec');exec(compile(s,str(p)+'::remaining','exec'),dict(__file__=str(p),__name__='__main__'))
