import pathlib,json,hashlib,os,socket
P=pathlib.Path
assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
expected=[('bcsp_rive_Requery_C_pending_20261115_v1.tar.gz', 11331, 'a9ade27d44d8ab13ae121bee131051b6e43b363b2f0080df2ed35901a070c7d4'), ('bcsp_rive_Requery_C_pending_20261115_v1.tar.gz.bytes', 6, 'f2b49a5b48bbda5d44f3566493fe19045793ab76d8e68ce562e2bdbc3d68d2f3'), ('bcsp_rive_Requery_C_pending_20261115_v1.tar.gz.contents.sha256', 356, '701ab959a7030c93f44a42e679603e97dab1cc0da71f18be065d73ebe37d1b04'), ('bcsp_rive_Requery_C_pending_20261115_v1.tar.gz.sha256', 113, '6ee4db25e403f309bdf3af7006347e8614335097edd2ff858e3755657e038458')]
rows=[]
for n,size,h in expected:
 p=P("/home/jovyan")/n;assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==size
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==h
 rows.append(dict(path=str(p),bytes=len(b),sha256=h))
print(json.dumps(dict(status="FOUR_UPLOADED_FILES_PASS",hostname=socket.gethostname(),uid=os.getuid(),files=rows,server_writes=0)))
