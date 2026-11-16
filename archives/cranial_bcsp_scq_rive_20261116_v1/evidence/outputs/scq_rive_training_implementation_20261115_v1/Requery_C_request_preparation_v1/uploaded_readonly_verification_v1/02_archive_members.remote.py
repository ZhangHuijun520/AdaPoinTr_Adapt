import pathlib,json,hashlib,tarfile,io,socket,os
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
p=P("/home/jovyan/bcsp_rive_Requery_C_pending_20261115_v1.tar.gz");b=p.read_bytes();assert len(b)==11331 and hashlib.sha256(b).hexdigest()=="a9ade27d44d8ab13ae121bee131051b6e43b363b2f0080df2ed35901a070c7d4"
with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:
 ms=t.getmembers();assert len(ms)==len({m.name for m in ms})==3 and sum(m.size for m in ms)<=65536
 data={}
 for m in ms:
  n=pathlib.PurePosixPath(m.name);assert m.isfile() and not n.is_absolute() and ".." not in n.parts
  data[m.name]=t.extractfile(m).read();assert len(data[m.name])==m.size
rows=[dict(member=n,bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for n,v in sorted(data.items())]
contents="".join(r["sha256"]+"  "+r["member"]+"\n" for r in rows);assert P(str(p)+".contents.sha256").read_text()==contents
mb=data["installation_mapping_v1.json"];assert hashlib.sha256(mb).hexdigest()=="edf429cb4e7169907e3b93399353822bda4b0bb3c7d96f90d36fb7961a2c9d54"
m=json.loads(mb);assert len(m["files"])==2
for r in m["files"]:
 v=data[r["member"]];assert len(v)==r["bytes"] and hashlib.sha256(v).hexdigest()==r["sha256"] and r["overwrite"] is False
qr=next(r for r in m["files"] if r["role"]=="request");q=json.loads(data[qr["member"]]);assert q["status"]=="AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["execution_authorized"] is False
fr=next(r for r in m["files"] if r["role"]=="Static_C_formal_freeze");assert q["paired_baseline"]["freeze"]["sha256"]==fr["sha256"]
print(json.dumps(dict(status="THREE_MEMBER_MAPPING_PASS",members=rows,request_sha256=qr["sha256"],freeze_sha256=fr["sha256"],server_writes=0)))
