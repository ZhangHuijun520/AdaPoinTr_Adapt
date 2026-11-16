import pathlib,json,hashlib,tarfile,io,os,socket,stat
P=pathlib.Path;assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
p=P("/home/jovyan/bcsp_rive_Requery_C_pending_20261115_v1.tar.gz");assert not any(x.is_symlink() for x in (p,*p.parents))
b=p.read_bytes();assert len(b)==11331 and hashlib.sha256(b).hexdigest()=="a9ade27d44d8ab13ae121bee131051b6e43b363b2f0080df2ed35901a070c7d4"
with tarfile.open(fileobj=io.BytesIO(b),mode="r:gz") as t:b=t.extractfile("installation_mapping_v1.json").read()
assert hashlib.sha256(b).hexdigest()=="edf429cb4e7169907e3b93399353822bda4b0bb3c7d96f90d36fb7961a2c9d54"
m=json.loads(b);assert len(m["files"])==2
root=P(m["existing_install_root"]);assert root.is_dir() and not any(x.is_symlink() for x in (root,*root.parents))
rows=[];objects={}
for r in m["files"]:
 p=P(r["target"]);s=p.lstat();assert p.parent==root and stat.S_ISREG(s.st_mode) and s.st_uid==1000 and s.st_size==r["bytes"]
 b=p.read_bytes();h=hashlib.sha256(b).hexdigest();assert h==r["sha256"]
 z=p.stat();assert all(getattr(s,k)==getattr(z,k) for k in ("st_ino","st_dev","st_size","st_mtime_ns","st_ctime_ns","st_mode","st_uid"))
 rows.append(dict(path=str(p),bytes=len(b),sha256=h,mode=oct(stat.S_IMODE(s.st_mode)),uid=s.st_uid));objects[r["role"]]=json.loads(b)
q=objects["request"];a=objects["Static_C_formal_freeze"]
assert q["status"]=="AWAITING_EXPLICIT_USER_AUTHORIZATION" and q["execution_authorized"] is False
assert q["paired_baseline"]["freeze"]["sha256"]==rows[1]["sha256"] and a["status"]=="FORMAL_RIVE_POST_TRAINING_FREEZE_AUDIT_PASS" and all(a["checks"].values())
for p in m["must_remain_absent"]:assert not os.path.lexists(p),p
print(json.dumps(dict(status="TWOFILE_FORMAL_POST_INSTALLATION_AUDIT_PASS",files=rows,paired_freeze_bound=True,Requery_controls_output_absent=True,server_writes=0)))
