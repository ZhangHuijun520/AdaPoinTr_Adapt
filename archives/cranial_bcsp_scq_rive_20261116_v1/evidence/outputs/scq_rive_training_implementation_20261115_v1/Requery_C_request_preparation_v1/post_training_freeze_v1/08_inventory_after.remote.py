import pathlib,hashlib,json,os,socket,stat,subprocess
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
root=P("/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_training_20261115_v1");run="SCQ_RIVE_Requery_foldC_seed0_train_20261115_v1";out=P("/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba")/run
assert subprocess.run(["tmux","has-session","-t","="+run],capture_output=True).returncode==1
assert not P("/proc/"+(out/"worker.pid").read_text().strip()).exists()
assert (out/"exit_code.txt").read_text().strip()=="0"
rows={};dirs={};total=0
for label,r in [("output",out),("install",root)]:
 assert r.is_dir() and not any(x.is_symlink() for x in (r,*r.parents))
 dirs[label]=[]
 for p in sorted(r.rglob("*")):
  assert not p.is_symlink(),str(p)
  if p.is_dir():dirs[label].append(p.relative_to(r).as_posix());continue
  s=p.stat();assert stat.S_ISREG(s.st_mode) and s.st_uid==1000 and s.st_size<=600000000
  total+=s.st_size;assert total<=800000000 and len(rows)<64
  h=hashlib.sha256()
  with p.open("rb") as f:
   for b in iter(lambda:f.read(1048576),b""):h.update(b)
  z=p.stat();keys=("st_ino","st_dev","st_size","st_mtime_ns","st_ctime_ns","st_mode","st_uid")
  assert all(getattr(s,k)==getattr(z,k) for k in keys),str(p)
  rows[label+"/"+p.relative_to(r).as_posix()]=dict(bytes=s.st_size,sha256=h.hexdigest(),fingerprint=[getattr(z,k) for k in keys])
print(json.dumps(dict(status="STABLE_COMPLETED_RUN_INVENTORY",files=rows,directories=dirs,total_bytes=total,tmux_absent=True,worker_absent=True,exit_code=0)))
