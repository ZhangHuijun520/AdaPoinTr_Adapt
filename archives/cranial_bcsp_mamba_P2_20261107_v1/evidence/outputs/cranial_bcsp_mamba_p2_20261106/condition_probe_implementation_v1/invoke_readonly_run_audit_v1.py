import base64,hashlib,json,shlex,subprocess,zlib
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;F=S/'post_run_freeze_audit_20261107_v1';F.mkdir();D=F/'downloads';D.mkdir()
BASE=['wsl.exe','-d','Ubuntu-20.04','--exec'];CLIENT='/home/zhj/.local/bin/hpc5000'
code=(S/'audit_remote_outputs_readonly_v1.py').read_bytes();blob=base64.b64encode(zlib.compress(code,9)).decode()
source='import base64,zlib;exec(compile(zlib.decompress(base64.b64decode('+repr(blob)+')),"<readonly_freeze_audit>","exec"))'
command=shlex.join(['/opt/conda/envs/adapointr-mamba/bin/python3.10','-I','-S','-B','-c',source])
assert max(map(len,command.splitlines()))<=8192
r=subprocess.run(BASE+[CLIENT,'exec','--timeout','65','--',command],capture_output=True,timeout=75)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (F/('remote_audit_'+k+'.bin')).open('xb') as f:f.write(b)
if r.returncode:print(r.stdout.decode(errors='replace'));print(r.stderr.decode(errors='replace'));raise SystemExit(r.returncode)
report=json.loads(r.stdout.decode().strip());assert report['status']=='REMOTE_READONLY_OUTPUT_FREEZE_PASS'
with (F/'remote_audit_report_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report),flush=True)
q=json.loads((S/'condition_probe_execution_request_v1.json').read_text());out=PurePosixPath(q['output'])
for name in ['development_predictions_v1.tar.gz','development_predictions_v1.tar.gz.sha256','development_predictions_v1.tar.gz.bytes','development_predictions_v1.tar.gz.contents.sha256','completion.json','exit_code.txt','launch.log']:
 target=D/name;path=subprocess.run(BASE+['wslpath','-a',str(target)],capture_output=True,timeout=10);assert path.returncode==0
 r=subprocess.run(BASE+[CLIENT,'get',str(out/name),path.stdout.decode().strip()],capture_output=True,timeout=45)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (F/(name+'.get_'+k+'.bin')).open('xb') as f:f.write(b)
 if r.returncode:raise RuntimeError('read-only download failed '+name)
 print(json.dumps(dict(downloaded=name,bytes=target.stat().st_size)),flush=True)
