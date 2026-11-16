import os,json,hashlib,pathlib,tarfile,io,subprocess,socket
P=pathlib.Path
phase="START";written=[];created=False;attempted=None
def event(k,**v):
 global phase
 phase=k;print(json.dumps(dict(phase=k,**v)),flush=True)
def clean(p):assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
event("A_START")
try:
 assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
 p=P("/home/jovyan/bcsp_rive_Static_C_pending_20261115_v1.tar.gz");clean(p)
 assert p.is_file() and p.stat().st_size==41020
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=="97fcdbe8fe31e410127301581dd7280588b71da0361059937e84015881396445"
 with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:m=json.loads(t.extractfile("installation_mapping_v1.json").read())
 assert len(m["reused_readonly_records"])==58
 assert sum(r["bytes"] for r in m["reused_readonly_records"])<=1073741824
 for r in m["reused_readonly_records"]:
  x=P(r["path"]);clean(x);assert x.is_file() and x.stat().st_size==r["bytes"] and digest(x)==r["sha256"],str(x)
 event("REUSED_HASHES_PASS",files=58)
 event("A_REUSED_PASS",count=58,archive_sha256=hashlib.sha256(b).hexdigest())
except BaseException as e:
 event("FAILED_STOP_NO_RETRY",failed_phase=phase,error=repr(e),stderr=str(getattr(e,"stderr",""))[:2048],root_created=created,written=written,attempted_target=attempted)
 raise
