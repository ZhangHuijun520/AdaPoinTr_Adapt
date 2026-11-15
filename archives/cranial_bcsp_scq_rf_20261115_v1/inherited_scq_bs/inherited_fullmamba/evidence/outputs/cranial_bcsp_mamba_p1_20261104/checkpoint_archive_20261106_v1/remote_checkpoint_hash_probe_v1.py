RECORDS=[{'run': 'T0_C', 'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/T0_foldC_seed0_train_20261105_v1/ckpt-last.pth', 'bytes': 380368111, 'sha256': '8671656b5a2b0843ed426868d9d06976a2ead816808f9f7c54ddadb83515ab07'}, {'run': 'M0_C', 'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/M0_foldC_seed0_train_20261106_v1/ckpt-last.pth', 'bytes': 407224375, 'sha256': 'bc6a489bcd4df5123a3bb6616105d7ec4628fc365e71313398ee516bcf72ef9a'}, {'run': 'T0_D', 'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/T0_foldD_seed0_train_20261106_v1/ckpt-last.pth', 'bytes': 380368111, 'sha256': 'ed901f18be2efb84f9b7b159cec2b71a3602e2e960087ac53d510881be9eba7c'}, {'run': 'M0_D', 'path': '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_mamba_p1/M0_foldD_seed0_train_20261106_v1/ckpt-last.pth', 'bytes': 407224375, 'sha256': '9e6f5c3034b051474e0ca78de725ba1579c2ddd25b2acf9848a1f8bf21c79263'}]
import pathlib,hashlib,json,socket,os,time
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
start=time.monotonic();out=[]
for r in RECORDS:
 p=pathlib.Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));st=p.stat();assert st.st_size==r['bytes'];h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 assert h.hexdigest()==r['sha256'] and p.stat().st_size==st.st_size and p.stat().st_mtime_ns==st.st_mtime_ns
 out.append(r)
print(json.dumps(dict(status='FOUR_FROZEN_P1_CHECKPOINTS_REHASHED_PASS',files=out,seconds=time.monotonic()-start,checkpoint_deserialized=False,server_writes=0)),flush=True)
