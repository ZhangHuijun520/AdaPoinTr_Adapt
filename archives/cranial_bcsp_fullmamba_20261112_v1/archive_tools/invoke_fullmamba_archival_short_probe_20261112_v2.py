"""Short read-only archive probes, no inline Python/base64 payload."""
from pathlib import Path
import json,subprocess,shlex,time
R=Path(__file__).resolve().parent.parent;O=R/'outputs/cranial_bcsp_fullmamba_20261110/final_archival_20261112_v1'
S=json.loads((O/'archive_scope_v1.json').read_bytes());items=S['weights']+S['result_archives']
def call(label,cmd,seconds=90):
 assert len(cmd.encode())<2048
 with (O/(label+'_command_v2.json')).open('x',encoding='utf-8') as f:json.dump(dict(command=cmd,bytes=len(cmd.encode())),f)
 try:r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout',str(seconds),'--',cmd],capture_output=True,timeout=seconds+15)
 except subprocess.TimeoutExpired as e:
  for n,b in [('stdout',e.stdout or b''),('stderr',e.stderr or b'')]:
   with (O/(label+'_'+n+'_v2.bin')).open('xb') as f:f.write(b)
  raise
 for n,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (O/(label+'_'+n+'_v2.bin')).open('xb') as f:f.write(b)
 assert r.returncode==0,('READONLY_FAILURE_STOP',label,r.returncode,r.stdout.decode(errors='replace')[:1000])
 return r.stdout.decode('utf-8').strip()
start=time.monotonic()
identity=call('identity',"hostname; id -u; readlink -f /home/jovyan/adapointr_work/PoinTr",30).splitlines()
assert identity==[S['hostname'],'1000','/home/jovyan/adapointr_work/PoinTr'],identity
rows=[]
for label,group in [('weights',S['weights']),('diagnostic',S['result_archives'])]:
 paths=[r['path'] for r in group]
 stat=call(label+'_stat',shlex.join(['/usr/bin/stat','--format=%s %n','--',*paths]),30)
 sizes={line.split(' ',1)[1]:int(line.split(' ',1)[0]) for line in stat.splitlines()}
 hashes=call(label+'_hash',shlex.join(['/usr/bin/sha256sum','--',*paths]),120)
 actual={line.split('  ',1)[1]:line.split('  ',1)[0] for line in hashes.splitlines()}
 for item in group:
  assert sizes[item['path']]==item['bytes'] and actual[item['path']]==item['sha256']
  rows.append({k:item[k] for k in ['path','bytes','sha256']})
 print(json.dumps(dict(stage=label+'_readonly_hash_verified',files=len(group))),flush=True)
result=dict(status='FROZEN_ARCHIVAL_ASSETS_READONLY_REHASH_PASS',hostname=S['hostname'],uid=1000,root=identity[2],files=rows,seconds=time.monotonic()-start,server_writes=0,checkpoint_deserialization=False,short_probe_version=2,prior_long_command_timeout_preserved=True)
with (O/'remote_hash_verification_v1.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result))
