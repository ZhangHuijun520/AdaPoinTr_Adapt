import os,json,hashlib,pathlib,tarfile,io,socket
P=pathlib.Path
phase="START";written=[];created=False;attempted=None
def event(k,**v):
 global phase
 phase=k;print(json.dumps(dict(phase=k,**v)),flush=True)
def clean(p):assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
event("C_START_AFTER_LOCAL_AB_GATE")
try:
 p=P("/home/jovyan/bcsp_rive_Static_C_pending_20261115_v1.tar.gz");clean(p)
 assert p.is_file() and p.stat().st_size==41020
 b=p.read_bytes();ah=hashlib.sha256(b).hexdigest();assert ah=="97fcdbe8fe31e410127301581dd7280588b71da0361059937e84015881396445"
 with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:
  m=json.loads(t.extractfile("installation_mapping_v1.json").read());assert len(m["files"])==11
  data={r["member"]:t.extractfile(r["member"]).read() for r in m["files"]}
 I=m["identity"];assert socket.gethostname()==I["hostname"]=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==I["uid"]==1000
 project=P(I["project"]);clean(project);assert str(project)=="/home/jovyan/adapointr_work/PoinTr" and project.is_dir()
 os.chdir(project);assert P.cwd()==project
 root=P(m["install_root"]);clean(root);assert root.parent==project/"third_party" and root.parent.is_dir() and not os.path.lexists(root)
 for r in m["files"]:
  x=P(r["target"]);clean(x);assert x.parent==root and not os.path.lexists(x) and r["overwrite"] is False
  v=data[r["member"]];assert len(v)==r["bytes"] and hashlib.sha256(v).hexdigest()==r["sha256"]
 for x in m["must_remain_absent_during_installation"]:assert not os.path.lexists(x),x
 event("C_TARGETS_PARENTS_PASS",targets=11)
 assert not os.path.lexists(root)
 root.mkdir(mode=0o700);created=True
 for r in m["files"]:
  x=P(r["target"]);attempted=str(x)
  with x.open("xb") as f:f.write(data[r["member"]]);f.flush();os.fsync(f.fileno())
  written.append(str(x));event("EXCLUSIVE_FILE_WRITTEN",path=str(x))
 assert {x.name for x in root.iterdir()}=={P(r["target"]).name for r in m["files"]}
 rows=[]
 for r in m["files"]:
  x=P(r["target"]);clean(x);assert x.stat().st_size==r["bytes"] and digest(x)==r["sha256"]
  rows.append(dict(path=str(x),bytes=r["bytes"],sha256=r["sha256"]))
 for x in m["must_remain_absent_during_installation"]:assert not os.path.lexists(x),x
 event("INSTALLATION_READBACK_PASS",files=rows,root=str(root),tests=0,forward=0,training=0,controls_created=False)
except BaseException as e:
 event("FAILED_STOP_NO_RETRY",failed_phase=phase,error=repr(e),stderr=str(getattr(e,"stderr",""))[:2048],root_created=created,written=written,attempted_target=attempted)
 raise
