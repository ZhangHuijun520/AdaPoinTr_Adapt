from pathlib import Path,PurePosixPath
import socket,os,hashlib,json,tarfile
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=Path('/home/jovyan/scq_dac_r1_frozen20_transport_20261115_v1.tar.gz')
assert p.stat().st_size==906620311 and not any(x.is_symlink() for x in (p,*p.parents))
with tarfile.open(p,'r|gz') as t:
 m=next(iter(t));assert m.name=='metadata/install_manifest_v1.json' and m.isfile() and m.size==10028
 raw=t.extractfile(m).read();assert hashlib.sha256(raw).hexdigest()=='3ad689a73763caa52805e69c60e923955cbbd42a8d20d4c34aaead81998cafa0'
v=json.loads(raw);root=PurePosixPath(v['root']);assert str(root)=='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1'
rows=v['files'];assert len(rows)==28 and len({r['member'] for r in rows})==len({r['target'] for r in rows})==28
for r in rows:
 assert r['member'].startswith('payload/') and '..' not in PurePosixPath(r['member']).parts
 assert str(PurePosixPath(r['target']).relative_to(root))==r['member'][8:]
print(json.dumps(dict(status='REMAINING28_MEMBER_TARGET_MAPPINGS_PASS',manifest_sha256=hashlib.sha256(raw).hexdigest(),files=28,request_sha256=v['request_sha256'],server_writes=0,installs=0,forwards=0)))
