from pathlib import Path
import os,socket,hashlib,json,time,subprocess,shutil,ast
T=time.monotonic();used=0;seen={};last=None
P=Path('/home/jovyan/adapointr_work/PoinTr')
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
def clean(p):
 p=Path(p);assert p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)),str(p);return p
def exact(r):
 global used,last
 p=clean(r['path']);last=str(p)
 if str(p) in seen:
  assert (r['bytes'],r['sha256'])==(seen[str(p)]['bytes'],seen[str(p)]['sha256']);return p
 s=p.stat();assert p.is_file() and s.st_size==r['bytes'],str(p)
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):
   used+=len(b);assert used<=805306368 and time.monotonic()-T<55;h.update(b)
 assert h.hexdigest()==r['sha256'],str(p)
 assert (s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns)
 seen[str(p)]={'path':str(p),'bytes':r['bytes'],'sha256':r['sha256']};assert len(seen)<=96;return p
old=P/'third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v2/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json'
q=json.loads(exact(dict(path=str(old),bytes=18606,sha256='5dd2daae783133d1456054a362c359779a29033cc92fb1c5e775fa1cb45f39d9')).read_bytes())

new=clean(P/'third_party/bcsp_scq_dac_r1_20261115_v1');out=clean(P/'logs/cranial_bcsp_fullmamba/SCQ_DAC_R1_frozen20_20261115_v1')
targets=['weights/Requery_C_epoch99_step3900.pth', 'weights/Requery_D_epoch99_step3900.pth', 'replay/Requery_C__train__001__bilateral.npz', 'replay/Requery_C__train__012__parietotemporal.npz', 'replay/Requery_C__train__012__random_1.npz', 'replay/Requery_C__train__025__parietotemporal.npz', 'replay/Requery_C__train__025__random_2.npz', 'replay/Requery_C__train__042__random_1.npz', 'replay/Requery_C__train__053__frontoorbital.npz', 'replay/Requery_C__train__076__random_2.npz', 'replay/Requery_C__train__081__bilateral.npz', 'replay/Requery_C__train__094__frontoorbital.npz', 'replay/Requery_D__train__004__parietotemporal.npz', 'replay/Requery_D__train__005__bilateral.npz', 'replay/Requery_D__train__008__frontoorbital.npz', 'replay/Requery_D__train__037__bilateral.npz', 'replay/Requery_D__train__044__parietotemporal.npz', 'replay/Requery_D__train__052__random_1.npz', 'replay/Requery_D__train__062__random_2.npz', 'replay/Requery_D__train__069__random_2.npz', 'replay/Requery_D__train__079__random_1.npz', 'replay/Requery_D__train__087__frontoorbital.npz', 'bcsp_scq_dac_r1_entry_v1.py', 'bcsp_scq_dac_r1_core_v1.py', 'selected20_cases_v1.json', 'R01_protocol_v1.json', 'local_P3_v1.json', 'SCQ_DAC_R1_execution_request_v1.json']
assert not new.exists() and not out.exists()
for rel in targets:assert not clean(new/rel).exists()
print(json.dumps(dict(status='ALL28_TARGETS_AND_NEW_ROOT_ABSENT',absent_targets=[str(new/x) for x in targets],output_absent=True,server_writes=0)))
