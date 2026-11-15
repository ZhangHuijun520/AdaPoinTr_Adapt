from pathlib import Path;import hashlib
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/SCQ_B_FoldD_training_execution_request_v1.json', 'bytes': 15615, 'sha256': '4f1db753d12693eb909d5d795997b542ca7a2082b73b6737521a1154f1777ed4'}]:
 p=Path(r['path']);assert not p.is_symlink() and p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
print('INSTALLED_HASHES_PASS')