from pathlib import Path
import json,subprocess,base64,zlib,hashlib
O=Path(__file__).resolve().parent
code="""from pathlib import Path
import json,hashlib,os,socket,time
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba_n0/N0B_seven_20261113_v1');rows=[];retained=[];start=time.monotonic()
def meta(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_nlink==1;return (s.st_size,s.st_mtime_ns,s.st_ino)
for fold in ['C','D']:
 w=r/'weights_restored_v3'/('LQI_'+fold+'_epoch99_step3900.pth');wm=meta(w);parts=sorted((r/('parts_restore_v3_'+fold)).glob('part_*.bin'));assert [x.name for x in parts]==['part_%03d.bin'%i for i in range(29)];whole=hashlib.sha256()
 with w.open('rb') as f:
  for p in parts:
   assert time.monotonic()-start<40;pm=meta(p);b=p.read_bytes();assert b==f.read(len(b)) and len(b)==pm[0];whole.update(b);assert meta(p)==pm;rows.append(dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),retained_full_copy=str(w),segment_equal=True))
  assert f.read(1)==b''
 assert meta(w)==wm;retained.append(dict(path=str(w),bytes=wm[0],sha256=whole.hexdigest()))
print(json.dumps(dict(status='58_PARTS_EXACT_DUPLICATES_OF_RETAINED_FULL_WEIGHTS',files=rows,retained=retained,bytes=sum(x['bytes'] for x in rows))))
"""
compile(code,'duplicate_parts','exec');(O/'duplicate_parts_remote_source.py').write_text(code,encoding='utf-8')
c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','45','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(a).encode())<2048
r=subprocess.run(a,capture_output=True,timeout=50);(O/'duplicate_stdout.bin').write_bytes(r.stdout);(O/'duplicate_stderr.bin').write_bytes(r.stderr);assert r.returncode==0
d=json.loads(r.stdout);d.update(deletion_authorized=False,deleted_files=0,server_writes=0,scope='Only58 part_*.bin files; preserve full weights, manifests, merge scripts, current SPCG assets and all other files.')
(O/'candidate_duplicate_parts_scope_v1.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(dict(status=d['status'],files=len(d['files']),bytes=d['bytes'],retained=d['retained'])))
