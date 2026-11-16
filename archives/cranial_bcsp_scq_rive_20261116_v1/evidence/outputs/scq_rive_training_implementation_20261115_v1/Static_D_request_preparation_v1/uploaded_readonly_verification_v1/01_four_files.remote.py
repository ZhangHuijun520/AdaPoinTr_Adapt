import pathlib,json,hashlib,os,socket
P=pathlib.Path
assert socket.gethostname()=="shu-common-25721452-notebook-qx2k0r-0" and os.getuid()==1000
expected=[('bcsp_rive_Static_D_pending_20261115_v1.tar.gz', 8031, '1f349b82560ace2e04af6982fbdeb6dcd489f11618eae1769521308e5941e39b'), ('bcsp_rive_Static_D_pending_20261115_v1.tar.gz.bytes', 5, '23a06e6a69fe1e0b335ec3aba2355d55de94ea325f7449f0fd1410eb54e7daf8'), ('bcsp_rive_Static_D_pending_20261115_v1.tar.gz.contents.sha256', 241, 'bf2a6ecab1057c6669c7ddb6d001f79843c226c080d6e3e46bacfb6ca1bb8b2a'), ('bcsp_rive_Static_D_pending_20261115_v1.tar.gz.sha256', 112, 'f3b1cbebc63d31a68f0d6912e741d43146a98e2909949d4e275dcd2b10749549')]
rows=[]
for n,size,h in expected:
 p=P("/home/jovyan")/n;assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==size
 b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==h;rows.append(dict(path=str(p),bytes=len(b),sha256=h))
print(json.dumps(dict(status="FOUR_UPLOADED_FILES_PASS",hostname=socket.gethostname(),uid=os.getuid(),files=rows,server_writes=0)))
