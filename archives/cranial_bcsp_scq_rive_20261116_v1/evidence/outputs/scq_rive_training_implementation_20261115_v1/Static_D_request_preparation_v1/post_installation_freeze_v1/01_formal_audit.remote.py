import pathlib,json,hashlib,tarfile,io,os,socket,stat
P=pathlib.Path
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=P('/home/jovyan/bcsp_rive_Static_D_pending_20261115_v1.tar.gz')
assert not any(x.is_symlink() for x in (p,*p.parents))
b=p.read_bytes()
assert len(b)==8031 and hashlib.sha256(b).hexdigest()=='1f349b82560ace2e04af6982fbdeb6dcd489f11618eae1769521308e5941e39b'
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 assert len(t.getmembers())==2
 mb=t.extractfile('installation_mapping_v1.json').read()
 assert hashlib.sha256(mb).hexdigest()=='f20428fad63d08e8483c07be97ed2a733b1986b50a48feee5a6d56af42e78272'
 m=json.loads(mb);assert len(m['files'])==1
 expected=t.extractfile(m['files'][0]['member']).read()
root=P(m['existing_install_root'])
assert root.is_dir() and not any(x.is_symlink() for x in (root,*root.parents))
r=m['files'][0];p=P(r['target']);s=p.lstat()
assert p.parent==root and stat.S_ISREG(s.st_mode) and s.st_uid==1000 and s.st_size==r['bytes']
b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
assert h==r['sha256']==m['request']['sha256'] and b==expected
z=p.lstat()
assert all(getattr(s,k)==getattr(z,k) for k in ('st_ino','st_dev','st_size','st_mtime_ns','st_ctime_ns','st_mode','st_uid'))
q=json.loads(b)
assert q['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and q['execution_authorized'] is False
for x in m['must_remain_absent']:assert not os.path.lexists(x),x
listing=sorted(x.name for x in root.iterdir())
print(json.dumps(dict(status='SINGLE_REQUEST_FORMAL_POST_INSTALLATION_AUDIT_PASS',files=[dict(path=str(p),bytes=len(b),sha256=h,uid=s.st_uid,mode=oct(stat.S_IMODE(s.st_mode)))],pending_authorization=True,absent_paths=m['must_remain_absent'],root_listing=listing,server_writes=0,tests=0,training=0)))
