from pathlib import Path
import socket, os, hashlib, json, subprocess, base64
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
root = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1')
out = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_Static_foldD_seed0_train_20261115_v1')
assert not any((p.is_symlink() for p in (root, *root.parents, out, *out.parents)))
assert hashlib.sha256((root / 'SCQ_RF_Static_D_training_execution_request_v1.json').read_bytes()).hexdigest() == 'b89d2b8d1fea63bcc4fb0478dce4d283a57b6b774beb7ccd7fe0403ceb71b6d6'
q = json.loads((root / 'SCQ_RF_Static_D_training_execution_request_v1.json').read_bytes())
assert (out/'exit_code.txt').read_text().strip()=='1' and not (out/'worker.pid').exists()
assert subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
assert subprocess.run(['pgrep','-f',q['implementation']['entry']['path']],capture_output=True,timeout=5).returncode==1
files={};dirs={};paths=[];total=0
for label,p in [('output',out),('installed',root)]:
 ds=['.']
 for f in sorted(p.rglob('*')):
  assert not f.is_symlink() and (f.is_file() or f.is_dir())
  if f.is_dir():ds.append(str(f.relative_to(p)));assert len(ds)<=8
  else:paths.append((label+'/'+str(f.relative_to(p)),f))
 dirs[label]=sorted(ds)
paths.append(('helper/preflight_helper.py',Path(q['implementation']['preflight_helper']['path'])))
assert len(paths)<=24
fp=lambda s:[s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
for name,p in paths:
 assert not any(x.is_symlink() for x in (p,*p.parents));before=p.stat();assert before.st_size<=2097152
 raw=p.read_bytes();total+=len(raw);assert total<=8388608;after=p.stat();assert fp(before)==fp(after)
 files[name]=dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),fingerprint=fp(after))
print(json.dumps(dict(status='BOUNDED_STABLE_FAILED_STARTUP_INVENTORY',hostname=socket.gethostname(),uid=os.getuid(),exit_code=1,tmux_absent=True,entry_process_absent=True,files=files,directories=dirs,total_bytes=total)))
