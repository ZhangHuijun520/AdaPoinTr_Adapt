import os,socket,json,hashlib,base64,stat,time,io,tarfile,subprocess,shutil
from pathlib import Path
M=json.loads(base64.b64decode('ewogICJzY2hlbWEiOiAiYmNzcC1mb2xkQy0xNjM4NC1hdXRob3JpemF0aW9uLWhvdGZpeC1pbnN0YWxsYXRpb24tdjIiLAogICJzdGF0dXMiOiAiUFJFUEFSRURfTk9UX0RFUExPWUVEIiwKICAiZXhwZWN0ZWRfaWRlbnRpdHkiOiB7CiAgICAiaG9zdG5hbWUiOiAic2h1LWNvbW1vbi0yNTcyMTQ1Mi1ub3RlYm9vay0wMWR0MDgtMCIsCiAgICAidWlkIjogMTAwMCwKICAgICJwcm9qZWN0IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIiLAogICAgImdwdV91dWlkIjogIkdQVS1lNzYzZDM4OS1iNGMyLTRkYzgtOTU3MS1kNzM0M2VjMzI4YjEiLAogICAgImdwdV9uYW1lIjogIk5WSURJQSBHZUZvcmNlIFJUWCA0MDkwIEQiLAogICAgImRyaXZlcl92ZXJzaW9uIjogIjU3MC4xOTAiLAogICAgIm52aWRpYV9zbWlfbWVtb3J5X3RvdGFsX01pQiI6IDI0NTY0LAogICAgInB5dGhvbl9yZWFscGF0aCI6ICIvb3B0L2NvbmRhL2VudnMvYWRhcG9pbnRyLW1hbWJhL2Jpbi9weXRob24zLjEwIiwKICAgICJweXRob25fdmVyc2lvbiI6ICIzLjEwLjIwIiwKICAgICJ0b3JjaF92ZXJzaW9uIjogIjIuNC4xK2N1MTE4IiwKICAgICJudW1weV92ZXJzaW9uIjogIjIuMi42IiwKICAgICJ0aW1tX3ZlcnNpb24iOiAiMS4wLjI3IiwKICAgICJtZW1vcnlfcXVlcnlfc2VtYW50aWNzIjogIlNNSSBwaHlzaWNhbCBVVUlEL3JvdW5kZWQgbWVtb3J5IHNlcGFyYXRlIGZyb20gdG9yY2ggbG9naWNhbCBjdWRhOjAvcHJvcGVydGllcy4gRG8gbm90IGRlbWFuZCBieXRlIGVxdWFsaXR5IGJldHdlZW4gdGhlIHR3byBpbnRlcmZhY2VzOyByZXF1aXJlIG9uZSB2aXNpYmxlIGxvZ2ljYWwgZGV2aWNlIG1hcHBlZCB2aWEgdGhlIGZpeGVkIFVVSUQgYW5kIHJlY29yZCB0b3JjaCBjYXBhY2l0eS4iCiAgfSwKICAiZmlsZXMiOiBbCiAgICB7CiAgICAgICJhcmNoaXZlX21lbWJlciI6ICJiY3NwX3RyYWluaW5nX2VudHJ5X2ZvbGRDXzE2Mzg0X3Y2LnB5IiwKICAgICAgInRhcmdldCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfZ2VvdjFfdHJhaW5pbmdfZm9sZGNfODE5Ml9zZWVkMF92MS9iY3NwX3RyYWluaW5nX2VudHJ5X2ZvbGRDXzE2Mzg0X3Y2LnB5IiwKICAgICAgImJ5dGVzIjogMTYwNjQsCiAgICAgICJzaGEyNTYiOiAiZjliYjkyOTE4NTFlYzczNWYwNjU0OWJlNmYxZjVlZWI5NzM0ZjI5YjI3MmRmZTk5ZmEzYmQzM2M0NTQxMTk0MSIsCiAgICAgICJsb2NhbF9maWxlIjogIkU6XFxDb2RleFxcMjAyNi0wNi0wNlxcbWFtYmEtY2NmLWMtMS1oaWdoLXJlc29sdXRpb25cXG91dHB1dHNcXGNyYW5pYWxfYmNzcF9nZW92MV8yMDI2MTAyNFxcZm9sZENfMTYzODRfdHJhaW5pbmdfdjFcXGF1dGhvcml6ZV9nYXRlX2hvdGZpeF92MlxcYmNzcF90cmFpbmluZ19lbnRyeV9mb2xkQ18xNjM4NF92Ni5weSIKICAgIH0sCiAgICB7CiAgICAgICJhcmNoaXZlX21lbWJlciI6ICJiY3NwX3RyYWluaW5nX2NvbnRyYWN0X2ZvbGRDXzE2Mzg0X3Y0LnB5IiwKICAgICAgInRhcmdldCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfZ2VvdjFfdHJhaW5pbmdfZm9sZGNfODE5Ml9zZWVkMF92MS9iY3NwX3RyYWluaW5nX2NvbnRyYWN0X2ZvbGRDXzE2Mzg0X3Y0LnB5IiwKICAgICAgImJ5dGVzIjogMTY1MjksCiAgICAgICJzaGEyNTYiOiAiMDg0MDM5YjllMTc5MDdlYTU0M2M2YjMxZjI0MDI3OTlhNGQyMjc1MTIzMmRkZGVkYTQxOWQ2ZmRlYjk3YjJmMyIsCiAgICAgICJsb2NhbF9maWxlIjogIkU6XFxDb2RleFxcMjAyNi0wNi0wNlxcbWFtYmEtY2NmLWMtMS1oaWdoLXJlc29sdXRpb25cXG91dHB1dHNcXGNyYW5pYWxfYmNzcF9nZW92MV8yMDI2MTAyNFxcZm9sZENfMTYzODRfdHJhaW5pbmdfdjFcXGF1dGhvcml6ZV9nYXRlX2hvdGZpeF92MlxcYmNzcF90cmFpbmluZ19jb250cmFjdF9mb2xkQ18xNjM4NF92NC5weSIKICAgIH0KICBdLAogICJuZXdfZGlyZWN0b3JpZXMiOiBbXSwKICAiY29kZV9yb290IjogIi9ob21lL2pvdnlhbi9hZGFwb2ludHJfd29yay9Qb2luVHIvdGhpcmRfcGFydHkvYmNzcF9nZW92MV90cmFpbmluZ19mb2xkY184MTkyX3NlZWQwX3YxIiwKICAicmV1c2VfaW5zdGFsbGVkX2RhdGEiOiB0cnVlLAogICJkYXRhX3Jvb3QiOiAiL2hvbWUvam92eWFuL2FkYXBvaW50cl93b3JrL1BvaW5Uci9kYXRhL2Jjc3BfZ2VvdjFfZm9sZGNfMTYzODRfc2VlZDBfdjEiLAogICJyZXVzZWRfZGF0YV9pbnN0YWxsYXRpb24iOiB7CiAgICAicGF0aCI6ICJFOlxcQ29kZXhcXDIwMjYtMDYtMDZcXG1hbWJhLWNjZi1jLTEtaGlnaC1yZXNvbHV0aW9uXFxvdXRwdXRzXFxjcmFuaWFsX2Jjc3BfZ2VvdjFfMjAyNjEwMjRcXGZvbGRDXzE2Mzg0X3RyYWluaW5nX3YxXFxhdXRob3JpemVkX2V4ZWN1dGlvbl92MlxcaW5zdGFsbF9zZXJ2ZXJfZXZlbnRzX3YxLmpzb24iLAogICAgImJ5dGVzIjogMTIwOCwKICAgICJzaGEyNTYiOiAiMjEzNzFhNzA5Nzc4OTEyMTgxZjUwNWE4YzkzMGRiNDFjMjliZWRmNmIyMDM5YzI0M2I0NDhiYzMwZWM1ZDNlNCIKICB9LAogICJyZXVzZWQzMTVfZGF0YV9tYXBwaW5nIjogewogICAgInBhdGgiOiAiRTpcXENvZGV4XFwyMDI2LTA2LTA2XFxtYW1iYS1jY2YtYy0xLWhpZ2gtcmVzb2x1dGlvblxcb3V0cHV0c1xcY3JhbmlhbF9iY3NwX2dlb3YxXzIwMjYxMDI0XFxmb2xkQ18xNjM4NF90cmFpbmluZ192MVxcbWluaW1hbF9pbnN0YWxsYXRpb25fbWFwcGluZ192MS5qc29uIiwKICAgICJieXRlcyI6IDE1ODYxOSwKICAgICJzaGEyNTYiOiAiNTQxNWYxNWExMTU0YWRiODJlNjJhYTZkNzFlN2MyNDdjYmFkMjYwZjVkNWMzYWVjYzFmYjdkODIxNWE4N2EwYiIKICB9LAogICJxdWFsaWZpZWRfUUMiOiB7CiAgICAicGF0aCI6ICIvaG9tZS9qb3Z5YW4vYWRhcG9pbnRyX3dvcmsvUG9pblRyL3RoaXJkX3BhcnR5L2Jjc3BfZ2VvdjFfdHJhaW5pbmdfZm9sZGNfODE5Ml9zZWVkMF92MS9ldmlkZW5jZS9xdWFsaWZpZWRfZGF0YV9xY19mb2xkQ18xNjM4NF92MS5qc29uIiwKICAgICJieXRlcyI6IDE2NjAsCiAgICAic2hhMjU2IjogImY2ZjYyNTQwYTgxMTQxNmQ4MjMyMTEwMGU0NTM2NzZmMDMxZDBlOWNhYmIxOTc5OGZjYmMyNGQ4YjIyMjA0MWIiCiAgfSwKICAicnVsZXMiOiBbCiAgICAiUmVjaGVjayBpZGVudGl0eSx1cGxvYWQgaGFzaCx0d28gZXhhY3QgdGFyZ2V0cyBhYnNlbnQgYW5kIHNhZmUgZXhpc3RpbmcgcGFyZW50IiwKICAgICJFeGNsdXNpdmUgbm8tZm9sbG93IGNyZWF0aW9uO25vIG92ZXJ3cml0ZTtyZWFkIGJhY2sgYm90aCBoYXNoZXMiLAogICAgIkRvIG5vdCByZWluc3RhbGwzMTUgcG9pbnQgZmlsZXMgb3JRQztyZXZlcmlmeSBleGlzdGluZzMxNSBwYXlsb2FkL1FDIGhhc2hlcyBiZWZvcmUgbGF1bmNoIiwKICAgICJPbGQgY29udHJvbC9vdXRwdXQvcmVxdWVzdCByZW1haW4gY29uc3VtZWQgYW5kIHVuY2hhbmdlZCIsCiAgICAiQW55IGV4ZWN1dGlvbiBmYWlsdXJlIHN0b3BzO25vIGF1dG9tYXRpYyByZXRyeS9yZXN1bWUvYmFja2VuZCBvciBiYXRjaCBjaGFuZ2VzIgogIF0KfQo='))
PINS=[{'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/bcsp_training_runtime_v5.py', 'bytes': 10171, 'sha256': '55ad69b0e87f3fc4ecac68a5ebcc4cdd560c4825ff01363ba9868de5875f0847'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/bcsp_artificial_gpu_preflight_v3.py', 'bytes': 32728, 'sha256': '7e645e4638624bb172567e39291da81edb6b762f0d5628844998d52e5f643291'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/static_training_config_v1.json', 'bytes': 2024, 'sha256': '86dbbb7b216a932209abd446bdd28408ad5327433834336f2584b087c1b35647'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/shared_order_foldC_seed0_v1.json', 'bytes': 1248506, 'sha256': '6ab424177d5227bd34585a710eedca578acdd2eeb226bec10cdfc86ee89cec9d'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/post_preflight_freeze_audit_report_v1.json', 'bytes': 31109, 'sha256': 'af3c3053be96a443d203c486ccede4d2bf2f0799ae753294ee946618726cf000'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_isolated_preflight_v3/evidence/frozen_scope_v3.json', 'bytes': 23220, 'sha256': 'c6edb9bfcf833d2abf98eb18749d03b49a490579d79475e4823750df6a8311e6'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/research_priority_01dt08_v1/resource_rebind_01dt08_v1.json', 'bytes': 3594, 'sha256': '7730f66a165bd10d9086f01fad10edbde61062ee42cb2f8431c12f51dfb7f59a'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/qualified_data_qc_foldC_16384_v1.json', 'bytes': 1660, 'sha256': 'f6f62540a811416d82321100e453676f031d0e9cabb19798fcbc24d8b222041b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/real_data_qc_verification_v1.json', 'bytes': 5769, 'sha256': '54fcd0018f9a51f04b8408b3842b6d5c4243777979a0e0add31541e04fa3c55b'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/fold_binding.json', 'bytes': 35012, 'sha256': 'cbd96c29002b959e6a05e0ccbf6d57e7a6134e4394f2013472c3944b1a641f90'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/manifest_8192.jsonl', 'bytes': 427975, 'sha256': 'f94dbe21cb9e406db49a51f6578496db3228d783f15c07b28e3d8ae234a33758'}, {'path': '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_geov1_training_foldc_8192_seed0_v1/evidence/manifest_16384.jsonl', 'bytes': 428815, 'sha256': '1cd06c7d3b33191d02b5464e72fd83ba4b38c839c0bb4da865bed374076734b5'}]
ARCHIVE='/home/jovyan/bcsp_foldC_16384_authorize_hotfix_v2.tar.gz'
ARCHIVE_SIZE=11107
ARCHIVE_SHA='977e2ff0c25af03b57d87ec208318befd12b6243a2c9f3ae359c483b722aff1f'
SCOPE_SHA='7221de1a48d700f3e2b90e3904689c9e63239832203356785e8cd0f2278de2fd'
START=time.monotonic();created=[];phase='IDENTITY';reads=0;DIRS=[]
PROJECT=Path(M['expected_identity']['project']);CODE=Path(M['code_root'])
def need(ok,why):
 if not ok:raise RuntimeError(why)

def budget():need(time.monotonic()-START<100,'installation wall budget')

def parents(p,missing=False):
 for a in reversed(p.parents):
  if missing and not os.path.lexists(a):need(a in DIRS,'unlisted missing parent '+str(a));continue
  need(stat.S_ISDIR(a.lstat().st_mode),'linked/non-directory parent '+str(a))

def absent(p,missing=False):parents(p,missing);need(not os.path.lexists(p),'target already exists '+str(p))

def exact(r):
 global reads
 budget();p=Path(r['path']);parents(p);s=p.lstat()
 need(stat.S_ISREG(s.st_mode) and s.st_size==r['bytes'] and s.st_size<=100663296,'type/size '+str(p))
 b=p.read_bytes();reads+=len(b);need(reads<=536870912,'installation read budget')
 need((s.st_ino,s.st_size,s.st_mtime_ns)==(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns),'changed '+str(p))
 need(hashlib.sha256(b).hexdigest()==r['sha256'],'hash '+str(p));return b

def dirfd(p):
 fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
 try:
  for part in p.parts[1:]:
   nxt=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=nxt
  return fd
 except BaseException:os.close(fd);raise

def event(d):print(json.dumps(d),flush=True)

def cmd(args):return subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10,check=True).stdout.decode().strip()

try:
 identity=M['expected_identity'];need(socket.gethostname()==identity['hostname'] and os.getuid()==identity['uid'],'hostname/uid')
 parents(PROJECT);need(stat.S_ISDIR(PROJECT.lstat().st_mode),'project');os.chdir(PROJECT)
 v=[x.strip() for x in cmd(['/usr/bin/nvidia-smi','--query-gpu=uuid,name,driver_version,memory.total,memory.used','--format=csv,noheader,nounits']).split(',')]
 need(v[:4]==[identity['gpu_uuid'],identity['gpu_name'],identity['driver_version'],str(identity['nvidia_smi_memory_total_MiB'])] and int(v[4])<=256,'GPU identity/idle')
 need(not cmd(['/usr/bin/nvidia-smi','--query-compute-apps=pid','--format=csv,noheader,nounits']),'GPU occupied')
 phase='UPLOAD_AND_EXISTING_ASSETS'
 archive=exact(dict(path=ARCHIVE,bytes=ARCHIVE_SIZE,sha256=ARCHIVE_SHA))
 rows=M['files'];need(len(rows)==len({x['target'] for x in rows})==2 and not M['new_directories'],'exact two files,no directories')
 expected={r['archive_member']:r for r in rows};content={}
 with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tf:
  ms=tf.getmembers();need(len(ms)==len({x.name for x in ms})==2 and {x.name for x in ms}==set(expected),'exact members')
  for x in ms:
   need(x.isfile() and '/' not in x.name and chr(92) not in x.name and x.size<=65536,'member type/path/size')
   r=expected[x.name];p=Path(r['target']);need(p==CODE/x.name,'exact target')
   b=tf.extractfile(x).read();need(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'member hash');content[p]=b
 for r in PINS:exact(r)
 phase='ALL_TARGETS_ABSENT'
 for p in content:absent(p)
 need(shutil.disk_usage(PROJECT).free>=4294967296+sum(map(len,content.values())),'disk reserve')
 event(dict(status='TWO_FILE_PREWRITE_PASS',scope_sha256=SCOPE_SHA,targets=2,server_writes=0))
 phase='EXCLUSIVE_INSTALLATION'
 for p,b in content.items():
  absent(p);fd=dirfd(p.parent)
  try:
   child=os.open(p.name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644,dir_fd=fd);created.append(str(p))
   with os.fdopen(child,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
  finally:os.close(fd)
 for r in rows:exact(dict(path=r['target'],bytes=r['bytes'],sha256=r['sha256']))
 event(dict(status='TWO_FILE_INSTALLATION_HASH_PASS',scope_sha256=SCOPE_SHA,created=created,reinstalled_data_files=0,training_started=False,seconds=time.monotonic()-START))
except BaseException as exc:
 event(dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),created=created,training_started=False));raise
