import hashlib,json,os,socket
from pathlib import Path
assert socket.gethostname()=='shu-common-25721452-notebook-o9mz8z-0' and os.getuid()==1000
B=Path('/home/jovyan')
expected_uploads=[('bcsp_gpu_preflight_v3.tar.gz',86262,'dc5ccbfdb92c2321bcbb7f0b3c7806e753993be26d880790ffb7f521621d630d'),('bcsp_gpu_preflight_v3.bytes',6,'d6ea2515d21e1f0a52bd39a575506649bd6579e2ba52428eb98a783e338a59c6'),('bcsp_gpu_preflight_v3.contents.sha256',2406,'3b5cf48a982443c80f1210962759696f5bda05aface141f2688ef8bd7557ade5'),('bcsp_gpu_preflight_v3.contents.sha256.sha256',104,'4b3f4f9e35883f8da0c61e0a285ad9a43ac940550f8cbcd44e0049b8d44211f9'),('bcsp_gpu_preflight_v3.tar.gz.sha256',95,'0a65224308a4e9d8b6b8c9b9681aaeb932c310815e6b246e588a2a9fe8f21bcb')]
for name,size,digest in expected_uploads:
 p=B/name;assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==size and hashlib.sha256(p.read_bytes()).hexdigest()==digest,str(p)
print(json.dumps({'status':'FIVE_EXACT_UPLOAD_HASHES_PASS','files':len(expected_uploads),'server_writes':0}))
