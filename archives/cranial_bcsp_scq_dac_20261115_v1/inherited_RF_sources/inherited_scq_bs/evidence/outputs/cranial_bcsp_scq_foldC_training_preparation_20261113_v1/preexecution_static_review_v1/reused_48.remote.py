from pathlib import Path;import hashlib,socket;assert socket.gethostname()=='shu-common-25721452-notebook-t6ibfm-0'
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/bcsp_scq_cuda_admission_v3.py', 'bytes': 23393, 'sha256': 'fe7fc491cdeed22ba939b1a0c45b08905f8ebdb67d5f09b41b6f1975d2630ad6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_cuda_20261113_v1/initialization_v1.bin', 'bytes': 2784780, 'sha256': 'e7858ee3ae4c0bf6d68e447727c36514f5bbab42b95e1935f1686620ec089416'}]:
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],str(p)
print('EXACT_BINDINGS_PASS')