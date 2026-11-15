from pathlib import Path;import hashlib,socket;assert socket.gethostname()=='shu-common-25721452-notebook-t6ibfm-0'
for r in [{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/static_training_config_v1.json', 'bytes': 2024, 'sha256': '86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_foldC_training_20261113_v1/training_entry_P3_v1.json', 'bytes': 4703, 'sha256': '20f93edd985f66f0821cb41aa8c9adf1883b7de0f1191cf1c4225166e4b6dced'}]:
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'],str(p)
print('EXACT_BINDINGS_PASS')