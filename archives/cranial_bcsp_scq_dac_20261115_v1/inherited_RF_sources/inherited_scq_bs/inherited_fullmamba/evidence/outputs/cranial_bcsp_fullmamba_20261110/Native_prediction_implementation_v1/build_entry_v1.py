"""Local source derivation only. Does not import models or execute predictions."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent
R=S.parents[2]
old=R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_fourmodel_prediction_implementation_v1/bcsp_h2_fourmodel_native_predict_v1.py'
text=old.read_text(encoding='utf-8')
tree=ast.parse(text)
names=['require','clean','sha','exact','bound','emit','load_partial','predict_once','ExactSourceReads','source_module','make_policy','Budget','pack','append_event','geometry_summary','rng_state']
parts=[]
for name in names:
 n=next(n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
 code=ast.get_source_segment(text,n)
 if name=='ExactSourceReads':code=code.replace("('factory','encoder','h2_range','h2_adapter')","('encoder','factory','f0_decoder','f0_factory')").replace('Only two pinned source files','Four exact pinned source files')
 parts.append(code)
extra=(S/'entry_additions_source_v1.txt').read_text(encoding='utf-8')
entry=S/'bcsp_f0_twofold_native_predict_v1.py'
with entry.open('x',encoding='utf-8',newline='\n') as f:
 f.write('"""F0 C/D: exactly210 Native forwards. Inert import; separate exact-hash authorization."""\n')
 f.write('import argparse,gc,hashlib,importlib.util,json,os,random,shlex,shutil,socket,subprocess,sys,tarfile,time\nfrom pathlib import Path,PurePosixPath\nfrom collections import Counter\n\n')
 f.write('\n\n'.join(parts)+'\n\n'+extra)
ast.parse(entry.read_text(encoding='utf-8'))
print(entry)
