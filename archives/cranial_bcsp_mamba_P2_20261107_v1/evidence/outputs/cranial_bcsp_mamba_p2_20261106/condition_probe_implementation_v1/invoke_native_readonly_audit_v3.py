"""Fixed short native read-only commands; all numeric auditing remains local."""
import hashlib,json,shlex,subprocess
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;F=S/'post_run_freeze_audit_20261107_v1';D=F/'downloads';BASE=['wsl.exe','-d','Ubuntu-20.04','--exec'];CLIENT='/home/zhj/.local/bin/hpc5000';q=json.loads((S/'condition_probe_execution_request_v1.json').read_text());out=PurePosixPath(q['output'])
def call(label,cmd):
 assert len(cmd.encode())<2048
 r=subprocess.run(BASE+[CLIENT,'exec','--timeout','30','--',cmd],capture_output=True,timeout=40)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (F/(label+'_'+k+'.bin')).open('xb') as f:f.write(b)
 if r.returncode:print(r.stdout.decode(errors='replace'));print(r.stderr.decode(errors='replace'));raise RuntimeError(label+' failed')
 print(json.dumps(dict(stage=label,returncode=0,stdout_bytes=len(r.stdout))),flush=True);return r.stdout.decode().replace('\r','')
prefix='test "$(hostname)" = '+shlex.quote(q['identity']['hostname'])+' && cd '+shlex.quote(str(out))+' && '
before=call('native_metadata_before',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort")
hashes=call('native_output_SHA256',prefix+"find . -type f -print0 | sort -z | xargs -0 sha256sum")
after=call('native_metadata_after',prefix+"find . -printf '%y %i %m %s %T@ %p\\n' | sort")
assert before==after,'output metadata drift (atime excluded)'
paths=[str(PurePosixPath(q['entry']['path']).parent/'condition_probe_execution_request_v1.json')]+[q[k]['path'] for k in ['entry','core','capture','input_index','P3','parent_entry','helper','static_config','preflight_scope','numeric_policy']]+[q['launch_contract'][k] for k in ['authorization_path','runtime_path','launcher_path']]+[q['launch_attempt']]
# Two exact groups keep every command comfortably below2048 bytes.
controls=''
for i,group in enumerate([paths[:8],paths[8:]]):controls+=call('native_controls_SHA256_'+str(i),'sha256sum '+' '.join(shlex.quote(p) for p in group))
state=call('native_process_state',prefix+'test "$(cat exit_code.txt)" = 0 && test ! -e failure.json && test ! -d /proc/$(cat worker.pid) && ! tmux has-session -t '+shlex.quote(q['launch_contract']['tmux_session'])+' 2>/dev/null && printf "EXIT0_WORKER_ABSENT_TMUX_ABSENT_NO_FAILURE\\n"')
assert 'EXIT0_WORKER_ABSENT_TMUX_ABSENT_NO_FAILURE' in state
with (F/'native_remote_evidence_v3.json').open('x',encoding='utf-8') as f:json.dump(dict(status='SHORT_NATIVE_READONLY_EVIDENCE_COLLECTED',metadata=before,output_hashes=hashes,control_hashes=controls,process_state=state,atime_excluded=True,server_writes=0),f,indent=2)
for name in ['development_predictions_v1.tar.gz','development_predictions_v1.tar.gz.sha256','development_predictions_v1.tar.gz.bytes','development_predictions_v1.tar.gz.contents.sha256','completion.json','exit_code.txt','launch.log']:
 target=D/name;assert not target.exists();p=subprocess.run(BASE+['wslpath','-a',str(target)],capture_output=True,timeout=10);assert p.returncode==0
 r=subprocess.run(BASE+[CLIENT,'get',str(out/name),p.stdout.decode().strip()],capture_output=True,timeout=45)
 for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
  with (F/(name+'.get_'+k+'.bin')).open('xb') as f:f.write(b)
 if r.returncode:raise RuntimeError('download '+name)
 print(json.dumps(dict(downloaded=name,bytes=target.stat().st_size)),flush=True)
# Reconcile native records with exact frozen local expected output/control records.
def parse(text):
 ans={}
 for line in text.splitlines():
  h,p=line.split(None,1);p=p.strip();assert len(h)==64 and p not in ans;ans[p]=h
 return ans
e=json.loads((F/'native_remote_evidence_v3.json').read_text());actual=parse(e['output_hashes']);c=json.loads((D/'completion.json').read_text());files=c['archive']['members'];archive=D/'development_predictions_v1.tar.gz';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={'./'+r['name']:r['sha256'] for r in files}
for p in D.iterdir():expected['./'+p.name]=sha(p)
assert './worker.pid' in actual and len(actual)==1700
assert set(actual)==set(expected)|{'./worker.pid'} and all(actual[n]==h for n,h in expected.items())
meta=[line.split(' ',5) for line in e['metadata'].splitlines()];assert all(x[0] in ['f','d'] for x in meta) and {x[5] for x in meta if x[0]=='d'}=={'.','./features','./tmp'}
sizes={x[5]:int(x[3]) for x in meta if x[0]=='f'}
for r in files:assert sizes['./'+r['name']]==r['bytes']
assert sizes['./'+archive.name]==archive.stat().st_size==c['archive']['bytes'] and sha(archive)==c['archive']['sha256']
control=parse(e['control_hashes']);assert control[str(PurePosixPath(q['entry']['path']).parent/'condition_probe_execution_request_v1.json')]==sha(S/'condition_probe_execution_request_v1.json')
for k in ['entry','core','capture','input_index','P3','parent_entry','helper','static_config','preflight_scope','numeric_policy']:assert control[q[k]['path']]==q[k]['sha256']
rb=json.loads((S/'authorized_execution_v1/startup_control_readback_receipt_v2.json').read_text())
for r in rb['files']:
 if Path(r['path']).name in ['authorization_v1.json','runtime_v1.json','launch_once_v1.sh']:
  name=Path(r['path']).name;key={'authorization_v1.json':'authorization_path','runtime_v1.json':'runtime_path','launch_once_v1.sh':'launcher_path'}[name];assert control[q['launch_contract'][key]]==r['sha256']
assert control[q['launch_attempt']]==hashlib.sha256(json.dumps(dict(status='CLAIMED_BEFORE_TMUX',request_sha256=sha(S/'condition_probe_execution_request_v1.json')),indent=2).encode()).hexdigest()
report=dict(status='REMOTE_READONLY_OUTPUT_FREEZE_PASS',method='Fixed short native find/sha256sum commands, reconciled locally; no remote Python audit',request_sha256=sha(S/'condition_probe_execution_request_v1.json'),archive=sha(archive),archive_bytes=archive.stat().st_size,archived_members=len(files),exact_output_files=len(actual),worker_absent=True,tmux_absent=True,exit_code=0,controls_verified=True,stable_content_fingerprints=True,atime_excluded=True,completion_sha256=sha(D/'completion.json'),server_writes=0,forward_calls=0,prior_two_transport_timeouts_retained=True)
with (F/'remote_audit_report_v1.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
print(json.dumps(report),flush=True)
