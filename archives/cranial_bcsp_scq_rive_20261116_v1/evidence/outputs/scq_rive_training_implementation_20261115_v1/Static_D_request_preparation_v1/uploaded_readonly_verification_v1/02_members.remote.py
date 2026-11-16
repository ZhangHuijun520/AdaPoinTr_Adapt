import pathlib,json,hashlib,tarfile,io,os,socket
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
p=P("/home/jovyan/bcsp_rive_Static_D_pending_20261115_v1.tar.gz");b=p.read_bytes();assert len(b)==8031 and hashlib.sha256(b).hexdigest()=="1f349b82560ace2e04af6982fbdeb6dcd489f11618eae1769521308e5941e39b"
with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:
 ms=t.getmembers();assert len(ms)==len({m.name for m in ms})==2 and sum(m.size for m in ms)<=65536;data={}
 for x in ms:
  n=pathlib.PurePosixPath(x.name);assert x.isfile() and not n.is_absolute() and ".." not in n.parts
  data[x.name]=t.extractfile(x).read();assert len(data[x.name])==x.size
rows=[dict(member=n,bytes=len(v),sha256=hashlib.sha256(v).hexdigest()) for n,v in sorted(data.items())]
assert P(str(p)+".contents.sha256").read_text()=="".join(x["sha256"]+"  "+x["member"]+"\n" for x in rows)
mb=data["installation_mapping_v1.json"];assert hashlib.sha256(mb).hexdigest()=="f20428fad63d08e8483c07be97ed2a733b1986b50a48feee5a6d56af42e78272"
m=json.loads(mb);assert len(m["files"])==1;r=m["files"][0];v=data[r["member"]];assert len(v)==r["bytes"] and hashlib.sha256(v).hexdigest()==r["sha256"] and r["overwrite"] is False
q=json.loads(v);assert q["status"]=="AWAITING_EXPLICIT_USER_AUTHORIZATION" and not q["execution_authorized"] and q["fold"]=="D" and q["arm"]=="RF-Static"
print(json.dumps(dict(status="EXACT_TWO_MEMBERS_PASS",members=rows,request_sha256=r["sha256"],server_writes=0)))
