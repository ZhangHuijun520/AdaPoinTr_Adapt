"""Read-only audit arithmetic matches actual FP32 addition; no training/loss changes."""
from pathlib import Path
import ast
V=Path(__file__).resolve().parent;p=V/'post_training_freeze_G0_C_v3.py';s=p.read_text(encoding='utf-8');tree=ast.parse(s);lines=s.splitlines(keepends=True);replacements=[]
for n in tree.body:
 if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('inventory','binding'):
  name=n.targets[0].id;file='01_inventory_checkpoint_result.json' if name=='inventory' else '02_binding_initialization_result.json';replacements.append((n.lineno-1,n.end_lineno,name+"=json.loads((O/'"+file+"').read_text(encoding='utf-8'))\n"))
for start,end,value in sorted(replacements,reverse=True):lines[start:end]=[value]
s=''.join(lines).replace('O.mkdir()','assert O.is_dir()',1).replace('code=PREFIX+body;','code=(PREFIX.split(\'def record(p):\')[0] if label.startswith(\'04\') else PREFIX)+body;',1).replace("'03_all3900_order_numeric'","'04_all3900_FP32_order_numeric'")
s=s.replace("close(m['loss'],sum(g['loss_components'].values()))","m['loss']==__import__('struct').unpack('f',__import__('struct').pack('f',sum(g['loss_components'].values())))[0]")
compile(s,str(p)+'::FP32_contract','exec');exec(compile(s,str(p)+'::FP32_contract','exec'),dict(__file__=str(p),__name__='__main__'))
