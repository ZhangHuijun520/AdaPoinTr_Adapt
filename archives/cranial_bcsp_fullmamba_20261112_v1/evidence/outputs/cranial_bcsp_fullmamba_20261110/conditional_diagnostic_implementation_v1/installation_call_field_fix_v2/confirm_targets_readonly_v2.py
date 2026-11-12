"""One bounded read-only target check after the previous failed operation."""
import base64,hashlib,json,shlex,subprocess,zlib
from pathlib import Path
A=Path(__file__).resolve().parent;S=A.parent
def main():
 review=json.loads((A/'static_fix_review_v2.json').read_bytes())
 archive=S/'frozen_pending_transport_v1/bcsp_f0_CD_condition_diagnostic_pending_20261111_v1.tar.gz'
 records=[]
 for p in [archive]+[Path(str(archive)+s) for s in ('.sha256','.bytes','.contents.sha256')]:
  records.append(dict(path='/home/jovyan/'+p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
 src=r'''
import os,socket,pathlib,hashlib,json,subprocess,shutil,time
P=pathlib.Path;t=time.monotonic();root=P('/home/jovyan/adapointr_work/PoinTr');base=root/'third_party/bcsp_f0_CD_condition_diagnostic_20261111_v1'
assert socket.gethostname()=='shu-common-25721452-notebook-zv9bqd-0' and os.getuid()==1000
def clean(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));return p
for r in RECORDS:
 p=clean(P(r['path']));assert p.is_file() and p.stat().st_size==r['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
arc=P(RECORDS[0]['path'])
import tarfile
with tarfile.open(arc,'r:gz') as tar:
 mapping=json.loads(tar.extractfile('installation_mapping_v1.json').read())
assert len(mapping['files'])==7 and mapping['remote_root']==str(base)
targets=[base,base/'control',root/'logs/cranial_bcsp_fullmamba/F0_CD_condition_diagnostic_20261111_v1',root/'third_party/f0_condition_authorized_operation_20261111_v2.py']+[P(r['target']) for r in mapping['files']]+[P(s) for s in mapping['not_materialized']]
for p in targets:assert not clean(p).exists(),str(p)
old=clean(root/'third_party/f0_condition_authorized_operation_20261111_v1.py');assert old.is_file() and hashlib.sha256(old.read_bytes()).hexdigest()==OLDHASH
session=subprocess.run(['tmux','has-session','-t','f0_cd_condition_20261111_v1'],capture_output=True,timeout=5);assert session.returncode==1
assert shutil.disk_usage(root).free>=4294967296 and time.monotonic()-t<=30
print(json.dumps(dict(status='READONLY_TARGET_CONFIRMATION_PASS',hostname=socket.gethostname(),uid=os.getuid(),free_disk_bytes=shutil.disk_usage(root).free,uploaded_four_files_match=True,seven_install_targets_absent=True,control_runtime_launcher_claim_output_absent=True,tmux_absent=True,old_operation_preserved=True,new_operation_target_absent=True,targets=[str(p) for p in targets],server_writes=0,model_calls=0,seconds=time.monotonic()-t)))
'''
 src='R='+repr(records)+'\n'+src.replace('RECORDS','R').replace('OLDHASH',repr(review['old_operation']['sha256']))
 encoded=base64.b64encode(zlib.compress(src.encode(),9)).decode()
 wrapper='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(encoded)+')),"<target-confirmation-readonly>","exec"))'
 command=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',wrapper])
 assert len(command.encode())<=2048,len(command.encode())
 with (A/'frozen_readonly_command_v2.json').open('x') as f:json.dump(dict(command=command,bytes=len(command.encode()),timeout_seconds=40,server_writes=0),f,indent=2)
 result=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','40','--',command],capture_output=True,timeout=50)
 for k,v in [('stdout',result.stdout),('stderr',result.stderr)]:
  with (A/('readonly_'+k+'_v2.bin')).open('xb') as f:f.write(v)
 if result.returncode:raise RuntimeError('read-only failed; no retry: '+str(result.returncode)+' '+repr(result.stdout[-1500:]))
 data=json.loads(result.stdout)
 with (A/'readonly_target_result_v2.json').open('x') as f:json.dump(data,f,indent=2)
 print(json.dumps(data))
if __name__=='__main__':main()
