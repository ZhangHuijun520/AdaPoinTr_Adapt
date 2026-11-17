"""Bounded read-only failure freeze; no SMI, model, payload loading or writes remotely."""
from pathlib import Path
import json,hashlib,base64,zlib,subprocess
V=Path(__file__).resolve().parent;S=V.parent;O=V/'post_failure_freeze_v2';O.mkdir()
code="""from pathlib import Path
import json,hashlib,os,socket,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v2');p=r/'SPCG_CUDA_execution_request_v2.json';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()=='a2b1961158b58199e212130654ddd274ce617c90e24448f22ba70a0062c2343e';q=json.loads(b);out=Path(q['output']);result=dict(hostname=socket.gethostname(),installed=[],control={},output={},directories=[],sources=[]);total=0
def item(p,text=False):
 global total
 assert not p.is_symlink() and p.is_file();s=p.stat();assert s.st_size<=8*1024**2;total+=s.st_size;assert total<=16*1024**2;b=p.read_bytes();v=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 if text:v['text']=b.decode('utf-8')
 return v
for p in sorted(r.iterdir()):
 if p.is_file():result['installed'].append(dict(path=str(p),**item(p)))
for p in sorted((r/'control').iterdir()):result['control'][p.name]=item(p,True)
for p in sorted(out.iterdir()):
 if p.is_dir():
  assert not p.is_symlink();result['directories'].append(dict(name=p.name,children=sorted(x.name for x in p.iterdir())))
 else:
  assert p.suffix.lower() not in ['.npz','.pth','.bin'];result['output'][p.name]=item(p,True)
for key in ['parent_helper','helper','entry']:
 x=q[key];v=item(Path(x['path']),True);assert v['sha256']==x['sha256'] and v['bytes']==x['bytes'];result['sources'].append(dict(key=key,path=x['path'],**v))
t=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5);result['tmux_returncode']=t.returncode;result['worker_live']=Path('/proc/'+result['output']['worker.pid']['text'].strip()).exists();result['hashed_bytes']=total
print(json.dumps(result))
"""
b=base64.b64encode(zlib.compress(code.encode())).decode();cmd="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',cmd];assert len(subprocess.list2cmdline(args).encode())<=2048
(O/'remote_readonly_source.py').write_text(code,encoding='utf-8');p=subprocess.run(args,capture_output=True,timeout=30);(O/'stdout.bin').write_bytes(p.stdout);(O/'stderr.bin').write_bytes(p.stderr);assert p.returncode==0,p.returncode
d=json.loads(p.stdout);(O/'server_evidence.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def text(k):return d['output'][k]['text']
mapping=json.loads((V/'pending_transport_v2/installation_mapping_v2.json').read_text(encoding='utf-8'));installed={x['path']:x for x in d['installed']};q=json.loads((V/'pending_transport_v2/payload/SPCG_CUDA_execution_request_v2.json').read_text(encoding='utf-8'))
c=d['control'];auth=json.loads(c['authorization_v2.json']['text']);runtime=json.loads(c['runtime_v2.json']['text']);events=[json.loads(l) for l in text('events.jsonl').splitlines()];resources=[json.loads(l) for l in text('resources.jsonl').splitlines()]
attempts=[x for x in events if x.get('operation')=='full_forward'];loss=[x for x in events if x.get('operation')=='full_loss'];back=[x for x in events if x.get('operation')=='full_backward'];phases=[x for x in events if x.get('kind')=='SYNTHETIC_PHASE'];restored=[x for x in events if x.get('kind')=='RESTORED'];last=attempts[-1]['counts']
checks=dict(installed_exact_set=set(installed)=={x['target'] for x in mapping['files']},installed_hashes=all(installed[x['target']]['sha256']==x['sha256'] and installed[x['target']]['bytes']==x['bytes'] for x in mapping['files']),single_claim=json.loads(c['launch_attempt_v2.json']['text'])==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=mapping['request_sha256']),authorization=auth['request_sha256']==mapping['request_sha256'] and auth['explicit_user_authorization'] is True,one_way_runtime=runtime==dict(schema='bcsp-spcg-runtime-v1',request_sha256=mapping['request_sha256'],authorization_sha256=c['authorization_v2.json']['sha256']),exit_one=text('exit_code.txt')=='1\n',tmux_absent=d['tmux_returncode']==1,worker_absent=not d['worker_live'],startup_SMI_success=json.loads(text('startup_query_result.json'))['status']=='OK',attempt_counts=len(attempts)==7 and len(loss)==len(back)==3 and last==dict(full_forward=7,full_loss=3,full_backward=3,optimizer_steps=0,synthetic_forward=6,real_D_forward=1),six_synthetic_phases=len(phases)==6,three_restore_events=len(restored)==3 and all(x['state'] and x['RNG'] and x['modes'] for x in restored),no_completion='completion.json' not in d['output'],no_partial_real_D_npz=not any(n.endswith('.npz') for n in d['output']),resource_records_present=bool(resources),all_recorded_resource_checks_pass=all(all(x['checks'].values()) for x in resources))
assert all(checks.values()),checks
result=dict(status='FORMAL_READONLY_V2_FAILURE_FREEZE_PASS',checks=checks,request_sha256=mapping['request_sha256'],last_attempt_counts=last,synthetic_phases=[dict(arm=x['arm'],training=x['training'],batch=x['batch'],parameters_unchanged=x['parameters_unchanged']) for x in phases],restoration_events=restored,resources=dict(count=len(resources),peak_allocated=max(x['values']['peak_allocated'] for x in resources),peak_reserved=max(x['values']['peak_reserved'] for x in resources),peak_RSS=max(x['values']['RSS_bytes'] for x in resources),peak_SMI_MiB=max(x['values']['device_MiB'] for x in resources)),primary_failure=json.loads(text('failure.json')),exact_missing_write_allowlist=[q['output']+'/real_D_%02d.npz'%i for i in range(5)],secondary_missing_exact_read=q['parent_helper'],request_consumed=True,SMI_queries=0,forward_calls=0,server_writes=0,real_payload_reads=0,limitations=['Counters are attempt-before-call; first real forward returned to save_memory per traceback, but real-case success record was not emitted.','Resource peaks are recorded samples; incomplete run is not full admission or future training resource proof.','Restoration is confirmed from emitted fingerprints/booleans, not by loading vanished process state.'])
(O/'formal_audit_result_v2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
