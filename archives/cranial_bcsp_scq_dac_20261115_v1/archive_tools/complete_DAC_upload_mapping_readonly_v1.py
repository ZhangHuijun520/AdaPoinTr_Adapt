"""Complete ONLY failed pure metadata mapping check; preserve prior failed call, no rehash/replay."""
from pathlib import Path
import ast,base64,hashlib,json,shlex,subprocess,zlib
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_dac_r01_preparation_20261115_v1/uploaded_transport_readonly_v1'
local=R/'server_uploads/scq_dac_r1_frozen20_20261115_v1/install_manifest_v1.json'
pin=hashlib.sha256(local.read_bytes()).hexdigest();size=local.stat().st_size
first=json.loads((O/'four_files_stdout_v1.bin').read_bytes());assert first['status']=='FOUR_UPLOAD_FILES_HASH_PASS' and len(first['files'])==4
error=(O/'archive_members_stdout_v1.bin').read_bytes().decode();assert "has no attribute 'removeprefix'" in error
script=(O/'archive_members_source_v1.py').read_text(encoding='utf-8');assert script.index('assert set(seen)==set(catalog)')<script.index('.removeprefix(')
code='''from pathlib import Path,PurePosixPath
import socket,os,hashlib,json,tarfile
assert socket.gethostname()=='shu-common-25721452-notebook-qx2k0r-0' and os.getuid()==1000
p=Path('/home/jovyan/scq_dac_r1_frozen20_transport_20261115_v1.tar.gz')
assert p.stat().st_size==906620311 and not any(x.is_symlink() for x in (p,*p.parents))
with tarfile.open(p,'r|gz') as t:
 m=next(iter(t));assert m.name=='metadata/install_manifest_v1.json' and m.isfile() and m.size=='''+repr(size)+'''
 raw=t.extractfile(m).read();assert hashlib.sha256(raw).hexdigest()=='''+repr(pin)+'''
v=json.loads(raw);root=PurePosixPath(v['root']);assert str(root)=='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1'
rows=v['files'];assert len(rows)==28 and len({r['member'] for r in rows})==len({r['target'] for r in rows})==28
for r in rows:
 assert r['member'].startswith('payload/') and '..' not in PurePosixPath(r['member']).parts
 assert str(PurePosixPath(r['target']).relative_to(root))==r['member'][8:]
print(json.dumps(dict(status='REMAINING28_MEMBER_TARGET_MAPPINGS_PASS',manifest_sha256=hashlib.sha256(raw).hexdigest(),files=28,request_sha256=v['request_sha256'],server_writes=0,installs=0,forwards=0)))
'''
ast.parse(code);blob=base64.b85encode(zlib.compress(code.encode(),9)).decode();command=shlex.join(['/usr/bin/python3','-I','-S','-B','-c','import base64,zlib;exec(zlib.decompress(base64.b85decode('+repr(blob)+')))']);assert len(command.encode())<=2048
with (O/'mapping_completion_source_v1.py').open('x',encoding='utf-8') as f:f.write(code)
x=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','30','--',command],capture_output=True,timeout=45)
for k,v in [('stdout',x.stdout),('stderr',x.stderr)]:
 with (O/('mapping_completion_'+k+'_v1.bin')).open('xb') as f:f.write(v)
assert x.returncode==0,('MAPPING_COMPLETION_FAILED_STOP',x.returncode,x.stdout.decode(errors='replace')[-1000:])
v=json.loads(x.stdout);qsha='129afea067a01802185719480591845e5918d52c4d28b9ec675012b1794e14a8';assert v['request_sha256']==qsha
result=dict(status='UPLOAD_BYTES_AND_MEMBER_TARGETS_VERIFIED_WITH_RECORDED_AUXILIARY_FAILURE',request_sha256=qsha,files=first['files'],archive_bytes=906620311,archive_sha256='350717ccaa584b93faa49b808355a762a94563f842f9e5f3352bf9a7973e0e01',members=30,payload_files=28,mapping_completion=v,prior_auxiliary_call=dict(returncode=1,error="system Python str.removeprefix unavailable",failed_record_retained=True,archive_hash_and30_member_assertions_completed_before_error=True),full_archive_verification_repeated=False,server_writes=0,installs=0,checkpoint_loads=0,forwards=0,authorization_materialized=False,runtime_materialized=False,launcher_materialized=False,execution_status='AWAITING_EXPLICIT_USER_AUTHORIZATION')
with (O/'upload_verification_completed_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=result['status'],payload_files=28,members=30,request_sha256=qsha,installs=0,forwards=0)))
