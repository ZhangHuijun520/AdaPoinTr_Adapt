import hashlib,json,os,pathlib,socket,tarfile
P=pathlib.Path('/home/jovyan/adapointr_work/PoinTr');R=P/'third_party/bcsp_p2_h1_foldD_20261106_v1'
A=pathlib.Path('/home/jovyan/bcsp_p2_H1_foldD_pending_20261106_v1.tar.gz')
assert socket.gethostname()=='shu-common-25721452-notebook-v2iwsa-0' and os.getuid()==1000
def clean(p):
 assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 return p
assert clean(A).is_file() and A.stat().st_size==15707
assert hashlib.sha256(A.read_bytes()).hexdigest()=='3c5120d8c3ea8279a1ff8858db12e8f1598e1d51be96f7506b6e6f6064f123e2'
assert not clean(R).exists() and clean(R.parent).is_dir()
with tarfile.open(A) as t:
 members=t.getmembers();assert len(members)==len({m.name for m in members})==5 and all(m.isfile() for m in members)
 mapping=json.load(t.extractfile('installation_mapping_v1.json'));assert mapping['remote_root']==str(R) and len(mapping['files'])==4
 expected={'installation_mapping_v1.json'}|{'payload/'+pathlib.Path(m['target']).name for m in mapping['files']}
 assert {m.name for m in members}==expected
 contents={m.name:hashlib.sha256(t.extractfile(m).read()).hexdigest() for m in members}
 side={line.split(None,1)[1]:line.split(None,1)[0] for line in pathlib.Path(str(A)+'.contents.sha256').read_text().splitlines()}
 assert contents==side
 staged=[]
 for m in mapping['files']:
  p=clean(pathlib.Path(m['target']));assert p.parent==R and not p.exists()
  b=t.extractfile('payload/'+p.name).read();assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256']
  staged.append((p,b,m['sha256']))
R.mkdir(mode=0o700)
for p,b,h in staged:
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 os.chmod(p,0o600);assert hashlib.sha256(p.read_bytes()).hexdigest()==h
assert {p.name for p in R.iterdir()}=={p.name for p,_,_ in staged}
print(json.dumps(dict(status='EXCLUSIVE_INSTALL_AND_HASH_READBACK_PASS',installed_files=4,control_created=False,training_started=False)),flush=True)
