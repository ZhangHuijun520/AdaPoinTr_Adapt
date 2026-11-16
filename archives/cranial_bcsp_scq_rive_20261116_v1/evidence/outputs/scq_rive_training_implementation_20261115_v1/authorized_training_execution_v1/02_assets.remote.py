import pathlib,json,hashlib,tarfile,io,os,socket
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
p=P("/home/jovyan/bcsp_rive_Static_C_pending_20261115_v1.tar.gz");b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=="97fcdbe8fe31e410127301581dd7280588b71da0361059937e84015881396445"
with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:b=t.extractfile("installation_mapping_v1.json").read()
assert hashlib.sha256(b).hexdigest()=="a8f1015ea0b17b3a7de82e0bd4ad271950b41040d5dbaf3b12903e186f93887c"
m=json.loads(b);rs=m["reused_readonly_records"]+[dict(path=x["target"],bytes=x["bytes"],sha256=x["sha256"]) for x in m["files"]]
assert len(rs)==69 and sum(r["bytes"] for r in rs)<=1073741824
for r in rs:
 p=P(r["path"]);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r["bytes"],str(p)
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 assert h.hexdigest()==r["sha256"],str(p)
print(json.dumps(dict(status="ALL69_BOUND_ASSETS_PASS",reused=58,installed=11,bytes=sum(r["bytes"] for r in rs))))
