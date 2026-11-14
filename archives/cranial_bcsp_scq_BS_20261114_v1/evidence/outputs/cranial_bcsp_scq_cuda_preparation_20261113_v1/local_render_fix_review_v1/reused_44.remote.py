from pathlib import Path;import hashlib,socket;assert socket.gethostname()=='shu-common-25721452-notebook-t6ibfm-0'
for r in [{'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/timm-1.0.27.dist-info/METADATA', 'bytes': 40196, 'sha256': 'b6ecaedbcaea5d0d5e431983c3df8e05113a51a2dad062e51dab0500ac6f2bb4'}, {'path': '/opt/conda/envs/adapointr-mamba/lib/python3.10/site-packages/numpy-2.2.6.dist-info/METADATA', 'bytes': 62026, 'sha256': '22d648f53848429464ca643b40d73b49a920d47876fc77c395d4dca4e834904a'}]:
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],str(p)
print('EXACT_BINDINGS_PASS')