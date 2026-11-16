import os,json,hashlib,pathlib,tarfile,io,subprocess,socket
P=pathlib.Path
phase="START"
def event(k,**v):
 global phase
 phase=k;print(json.dumps(dict(phase=k,**v)),flush=True)
def clean(p):assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
event("B_START")
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
 event("B_IDENTITY_UPLOAD_PASS",hostname=I["hostname"],uid=os.getuid(),gpu=gpu,targets=11,archive_sha256=ah)
except BaseException as e:
 event("FAILED_STOP_NO_RETRY",failed_phase=phase,error=repr(e),stderr=str(getattr(e,"stderr",""))[:2048])
 raise
