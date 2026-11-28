"""Read-only bounded follow-up of the missing exact development input path."""
from pathlib import Path
source=Path(__file__).with_name('verify_native315_server_readonly_v1.py').read_text()
source=source.split("first=run(scan,")[0].replace("e=d/'server_readonly_h7vvrr_v1'","e=d/'server_path_investigation_v1'")
exec(compile(source,'<readonly-definitions>','exec'))
result=run('''root=Path('/home/jovyan/adapointr_work/PoinTr/data')
dirs=[p for p in root.iterdir() if p.is_dir() and not p.is_symlink() and p.name.startswith('bcsp_geov1')]
print(json.dumps([dict(root=str(p),points=(p/'points').is_dir(),case_exists=(p/'points/train__004__bilateral_8192.npz').is_file()) for p in sorted(dirs)]))
''','bounded_data_roots')
read='''def read(name):
 p=Path(name);a=p.lstat();assert p.resolve(strict=True)==p and stat.S_ISREG(a.st_mode) and a.st_size<=536870912
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 z=p.lstat();assert (a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns)
 return [name,a.st_size,h.hexdigest()]
'''
for arm,rec in q['checkpoints'].items():
 got=run(read+'print(json.dumps(read('+repr(rec['path'])+')))','checkpoint_'+arm)
 assert got==[rec['path'],rec['bytes'],rec['sha256']]
print(json.dumps(dict(status='BOUNDED_PATH_INVESTIGATION_COMPLETE',roots=result,checkpoints_hashed=3,remote_mutations=False)))
