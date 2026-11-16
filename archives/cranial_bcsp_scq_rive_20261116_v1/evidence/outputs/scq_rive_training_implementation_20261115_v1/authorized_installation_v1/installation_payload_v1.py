import os,sys,json,hashlib,pathlib,tarfile,io,subprocess
P=pathlib.Path
phase="START";written=[];created=False;attempted=None
def event(k,**v):
 global phase
 phase=k;print(json.dumps(dict(phase=k,**v)),flush=True)
def clean(p):
 assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
try:
 p=P("/home/jovyan/bcsp_rive_Static_C_pending_20261115_v1.tar.gz");clean(p)
 assert p.is_file() and p.stat().st_size==41020
 b=p.read_bytes();ah=hashlib.sha256(b).hexdigest();assert ah=="97fcdbe8fe31e410127301581dd7280588b71da0361059937e84015881396445"
 with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:
  ms=t.getmembers();assert len(ms)==len({m.name for m in ms})==12 and sum(m.size for m in ms)<=262144
  data={}
  for m in ms:
   n=pathlib.PurePosixPath(m.name);assert m.isfile() and not n.is_absolute() and ".." not in n.parts
   data[m.name]=t.extractfile(m).read();assert len(data[m.name])==m.size
 contents="".join(hashlib.sha256(v).hexdigest()+"  "+n+"\n" for n,v in sorted(data.items()))
 for suffix,expected in [(".bytes","41020\n"),(".sha256",ah+"  "+p.name+"\n"),(".contents.sha256",contents)]:
  x=P(str(p)+suffix);clean(x);assert x.is_file() and x.stat().st_size==len(expected.encode()) and x.read_bytes()==expected.encode(),str(x)
 m=json.loads(data["installation_mapping_v1.json"]);assert len(m["files"])==11 and len(m["reused_readonly_records"])==58
 I=m["identity"];assert __import__("socket").gethostname()==I["hostname"]=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==I["uid"]==1000
 project=P(I["project"]);clean(project);assert str(project)=="/home/jovyan/adapointr_work/PoinTr" and project.is_dir()
 os.chdir(project);assert P.cwd()==project
 args=["/usr/bin/nvidia-smi","--id="+I["gpu_uuid"],"--query-gpu=uuid,name,driver_version,memory.total","--format=csv,noheader,nounits"]
 smi=subprocess.run(args,capture_output=True,text=True,timeout=10,check=True)
 gpu=[s.strip() for s in smi.stdout.strip().split(",")];assert gpu==[I["gpu_uuid"],I["gpu_name"],I["driver_version"],str(I["nvidia_smi_memory_total_MiB"])]
 q=json.loads(data[next(r["member"] for r in m["files"] if r["role"]=="request")]);assert q["identity"]==I and q["environment"]["CUDA_VISIBLE_DEVICES"]==I["gpu_uuid"] and q["execution_authorized"] is False
 event("IDENTITY_UPLOAD_PASS",hostname=I["hostname"],gpu=gpu)
 root=P(m["install_root"]);clean(root);assert root.parent==project/"third_party" and root.parent.is_dir() and not os.path.lexists(root)
 for r in m["files"]:
  x=P(r["target"]);clean(x);assert x.parent==root and not os.path.lexists(x) and r["overwrite"] is False
  v=data[r["member"]];assert len(v)==r["bytes"] and hashlib.sha256(v).hexdigest()==r["sha256"]
 for x in m["must_remain_absent_during_installation"]:assert not os.path.lexists(x),x
 event("TARGETS_PARENTS_PASS",targets=11)
 assert sum(r["bytes"] for r in m["reused_readonly_records"])<=1073741824
 for r in m["reused_readonly_records"]:
  x=P(r["path"]);clean(x);assert x.is_file() and x.stat().st_size==r["bytes"] and digest(x)==r["sha256"],str(x)
 event("REUSED_HASHES_PASS",files=58)
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
