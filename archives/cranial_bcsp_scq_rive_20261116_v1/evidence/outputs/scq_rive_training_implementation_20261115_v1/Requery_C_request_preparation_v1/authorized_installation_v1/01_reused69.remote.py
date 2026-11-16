import pathlib,json,hashlib,tarfile,io,os,socket
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
p=P("/home/jovyan/bcsp_rive_Requery_C_pending_20261115_v1.tar.gz");assert not any(x.is_symlink() for x in (p,*p.parents))
b=p.read_bytes();assert len(b)==11331 and hashlib.sha256(b).hexdigest()=="a9ade27d44d8ab13ae121bee131051b6e43b363b2f0080df2ed35901a070c7d4"
with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:mb=t.extractfile("installation_mapping_v1.json").read()
assert hashlib.sha256(mb).hexdigest()=="edf429cb4e7169907e3b93399353822bda4b0bb3c7d96f90d36fb7961a2c9d54"
m=json.loads(mb);rs=m["reused_readonly_records"];assert len(rs)==69 and sum(r["bytes"] for r in rs)<1073741824
for r in rs:
 p=P(r["path"]);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r["bytes"],str(p)
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 assert h.hexdigest()==r["sha256"],str(p)
print(json.dumps(dict(status="REUSED69_EXACT_PASS",files=69,server_writes=0)))
