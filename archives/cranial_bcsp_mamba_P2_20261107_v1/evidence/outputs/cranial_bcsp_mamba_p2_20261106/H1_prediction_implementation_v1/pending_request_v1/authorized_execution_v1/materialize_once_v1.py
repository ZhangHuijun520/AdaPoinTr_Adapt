import hashlib,json,os,pathlib,shlex,socket
R=pathlib.Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_p2_H1_twofold_prediction_20261106_v1')
Q='90df035abba6cb6651f323ce65f5477f2a9bd0b3a7a505a5ebcc376b7436c147'
qfile=R/'H1_C_D_development_execution_request_v1.json';assert hashlib.sha256(qfile.read_bytes()).hexdigest()==Q
q=json.loads(qfile.read_bytes());c=q['launch_contract'];I=q['identity']
assert socket.gethostname()==I['hostname'] and os.getuid()==I['uid']
def clean(p):
 assert not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 return p
control=clean(pathlib.Path(c['authorization']).parent);out=clean(pathlib.Path(q['output']))
assert control==R/'control' and not control.exists() and not out.exists() and not clean(pathlib.Path(q['launch_attempt'])).exists()
auth=dict(schema='bcsp-development-authorization-v1',request_sha256=Q,explicit_user_authorization=True,user_authorization_text='Explicit full-hash authorization: one C105+D105 H1 prediction execution only. Stop on failure; no retry, training, scoring or BNCal.')
ab=json.dumps(auth,indent=2,ensure_ascii=True).encode();ah=hashlib.sha256(ab).hexdigest()
rb=json.dumps(dict(schema='bcsp-development-runtime-v1',request_sha256=Q,authorization_sha256=ah),indent=2).encode();rh=hashlib.sha256(rb).hexdigest()
replace={'<THIS_REQUEST_SHA256>':Q,'<AUTHORIZATION_SHA256>':ah,'<RUNTIME_SHA256>':rh}
argv=[replace.get(s,s) for s in c['launcher_argv_template']]
assert argv[:4]==['/usr/bin/timeout','--signal=TERM','--kill-after=5s','7200s']
env=[k+'='+v.replace('<owned_output>',str(out)) for k,v in q['environment'].items()]
parent=out.parent
lines=['#!/bin/bash','set -u','umask 077','cd /home/jovyan/adapointr_work/PoinTr || exit 120']
for p in (parent,*parent.parents):lines.append('[ ! -L '+shlex.quote(str(p))+' ] || exit 121')
lines+=['mkdir -p -- '+shlex.quote(str(parent))+' || exit 122','mkdir -- '+shlex.quote(str(out))+' || exit 123',
 'exec >>'+shlex.quote(c['log'])+' 2>&1',' '.join(shlex.quote(s) for s in ['env']+env+argv),
 'result=$?','printf "%s\\n" "$result" > '+shlex.quote(c['exit_code']),'exit "$result"']
lb=('\n'.join(lines)+'\n').encode('ascii');assert lines.index('mkdir -p -- '+str(parent)+' || exit 122')<lines.index('exec >>'+c['log']+' 2>&1')
files=[(pathlib.Path(c['authorization']),ab),(pathlib.Path(c['runtime']),rb),(pathlib.Path(c['launcher']),lb)]
assert all(p.parent==control and not clean(p).exists() for p,_ in files)
control.mkdir(mode=0o700)
for p,b in files:
 with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 os.chmod(p,0o600);assert p.read_bytes()==b
print(json.dumps(dict(status='H1_CONTROLS_MATERIALIZED_NOT_STARTED',files=[dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for p,b in files])),flush=True)
