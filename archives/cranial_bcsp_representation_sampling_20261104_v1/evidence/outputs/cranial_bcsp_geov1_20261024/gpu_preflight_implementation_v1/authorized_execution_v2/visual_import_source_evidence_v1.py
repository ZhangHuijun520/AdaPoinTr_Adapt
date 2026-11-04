import ast,hashlib,json,os,socket
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-o9mz8z-0' and os.getuid()==1000
base=Path('/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/matplotlib')
rows=[];total=0;selected={}
for name in ['pyplot.py','image.py','backend_bases.py','text.py','font_manager.py']:
 p=base/name;assert p.is_file() and not p.is_symlink()
 total+=p.stat().st_size;assert total<=2*1024**2
 raw=p.read_bytes();s=raw.decode('utf-8');tree=ast.parse(s)
 rows.append({'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
 snippets=[]
 for n in ast.walk(tree):
  if name=='font_manager.py' and isinstance(n,ast.FunctionDef) and n.name in {'_get_fontconfig_fonts','findSystemFonts','_load_fontmanager'}:
   snippets.append({'line':n.lineno,'source':ast.get_source_segment(s,n)})
  if isinstance(n,(ast.Import,ast.ImportFrom)) and any(x in ast.unparse(n) for x in ('matplotlib.image','backend_bases','font_manager','matplotlib.text','text,')):
   snippets.append({'line':n.lineno,'source':ast.get_source_segment(s,n)})
 if name=='font_manager.py':
  lines=s.splitlines()
  for i,line in enumerate(lines):
   if 'fontManager = _load_fontmanager()' in line or '*findSystemFonts(fontext=fontext)' in line:
    snippets.append({'line':i+1,'source':'\n'.join(lines[max(0,i-4):i+4])})
 selected[name]=snippets
out=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/artificial_gpu_zero_update_v2')
p=out/'monitor_events.jsonl';assert p.stat().st_size<1024**2
ev=[json.loads(x) for x in p.read_text().splitlines()]
starts=[e for e in ev if e['event']=='smi_start'];ends=[e for e in ev if e['event']=='smi_result']
assert len(starts)==len(ends) and {e['query_id'] for e in starts}=={e['query_id'] for e in ends}
assert all(e['status']=='OK' and e['returncode']==0 and e['query_attempts']==1 for e in ends)
print(json.dumps({'source_files':rows,'bytes_read':total,'import_source':selected,'monitor':{'paired_queries':len(ends),'all_success':True,'max_seconds':max(e['elapsed_seconds'] for e in ends),'min_seconds':min(e['elapsed_seconds'] for e in ends),'over_3_seconds':[(e['query_id'],e['phase_at_start'],e['elapsed_seconds']) for e in ends if e['elapsed_seconds']>3],'phases':[e for e in ev if e['event']=='phase']},'executed_imports_or_fc_list':False,'remote_writes':0}))
