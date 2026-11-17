"""Read-only successful CUDA freeze, no tensor imports, SMI or forward calls."""
from pathlib import Path
import json,hashlib,base64,zlib,subprocess,math
V=Path(__file__).resolve().parent;O=V/'post_CUDA_freeze_v3';O.mkdir()
code="""from pathlib import Path
import os,socket,json,hashlib,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v3');q=json.loads((r/'SPCG_CUDA_execution_request_v3.json').read_bytes());o=Path(q['output']);total=0
def record(p,text=False):
 global total
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert s.st_size<8*1024**2;total+=s.st_size;assert total<32*1024**2;b=p.read_bytes();v=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 if text:v['text']=b.decode()
 return v
d=dict(installed={p.name:record(p) for p in r.iterdir() if p.is_file()},controls={p.name:record(p,True) for p in (r/'control').iterdir()},output={},directories=[])
for p in sorted(o.iterdir()):
 if p.is_dir():
  assert not p.is_symlink();d['directories'].append(dict(name=p.name,children=[str(x.relative_to(p)) for x in p.rglob('*')]))
 else:d['output'][p.name]=record(p,p.suffix!='.npz')
d['reused']={}
for x in list(q['implementation'].values())+[q[k] for k in ['entry','helper','parent_helper','timezone_implementation','probe_asset','head_initialization','mother_source']]:
 v=record(Path(x['path']));assert v['bytes']==x['bytes'] and v['sha256']==x['sha256'];d['reused'][x['path']]=v
d['worker_live']=Path('/proc/'+d['output']['worker.pid']['text'].strip()).exists();d['tmux_live']=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==0;d['hashed_bytes']=total
print(json.dumps(d))
"""
b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))"
args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(args).encode())<=2048
(O/'remote_readonly_source.py').write_text(code,encoding='utf-8');p=subprocess.run(args,capture_output=True,timeout=45);(O/'stdout.bin').write_bytes(p.stdout);(O/'stderr.bin').write_bytes(p.stderr);assert p.returncode==0,p.returncode
d=json.loads(p.stdout);(O/'server_evidence.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def output(n):return json.loads(d['output'][n]['text'])
q=json.loads((V/'pending_transport_v3/payload/SPCG_CUDA_execution_request_v3.json').read_text(encoding='utf-8'));mapping=json.loads((V/'pending_transport_v3/installation_mapping_v3.json').read_text(encoding='utf-8'));qh=mapping['request_sha256'];completion=output('completion.json');manifest=output('payload_manifest.json');events=[json.loads(x) for x in d['output']['events.jsonl']['text'].splitlines()];resources=[json.loads(x) for x in d['output']['resources.jsonl']['text'].splitlines()]
c=d['controls'];auth=json.loads(c['authorization_v3.json']['text']);runtime=json.loads(c['runtime_v3.json']['text']);claim=json.loads(c['launch_attempt_v3.json']['text']);expected_outputs={'launcher.pid','worker.pid','launch.log','exit_code.txt','startup_query_attempt.json','startup_query_result.json','events.jsonl','resources.jsonl','completion.json','payload_manifest.json'}|{'real_D_%02d.npz'%i for i in range(5)}
checks=dict(exact_installed_set=set(d['installed'])=={Path(x['target']).name for x in mapping['files']},installed_hashes=all(d['installed'][Path(x['target']).name]['sha256']==x['sha256'] and d['installed'][Path(x['target']).name]['bytes']==x['bytes'] for x in mapping['files']),request_hash=d['installed']['SPCG_CUDA_execution_request_v3.json']['sha256']==qh,one_way_authorization=auth['request_sha256']==qh and auth['explicit_user_authorization'] is True and runtime==dict(schema='bcsp-spcg-runtime-v1',request_sha256=qh,authorization_sha256=c['authorization_v3.json']['sha256']),single_claim=claim==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh),exit_zero=d['output']['exit_code.txt']['text']=='0\n',worker_and_tmux_absent=not d['worker_live'] and not d['tmux_live'],exact_output_set=set(d['output'])==expected_outputs,exact_empty_directories={x['name'] for x in d['directories']}=={'cache','hf_cache','mplconfig','tmp','triton_cache'} and all(not x['children'] for x in d['directories']),completion_binding=completion['request_sha256']==qh and completion['status']=='SPCG_CUDA_COMPLETE_PENDING_FORMAL_FREEZE' and completion['result']['counts']==q['science'])
manifest_names=[x['name'] for x in manifest];checks['manifest_unique']=len(manifest_names)==len(set(manifest_names))
checks['manifest_content_hashes']=all(d['output'][x['name']]['sha256']==x['sha256'] and d['output'][x['name']]['bytes']==x['bytes'] for x in manifest)
# Entry intentionally excludes only log/worker and creates manifest before exit_code.
checks['manifest_exact_scope']=set(manifest_names)==expected_outputs-{'launch.log','worker.pid','exit_code.txt','payload_manifest.json'}
for name,n in [('full_forward',11),('full_loss',3),('full_backward',3),('synthetic_forward',6),('real_D_forward',5)]:checks[name+'_events']=len([e for e in events if e.get('operation')==name])==n
restored=[e for e in events if e.get('kind')=='RESTORED'];real=[e for e in events if e.get('kind')=='REAL_D_ONLY'];phases=[e for e in events if e.get('kind')=='SYNTHETIC_PHASE'];checks['restoration_three_arms']={e['arm'] for e in restored}=={'G0','G1','G2'} and len(restored)==3 and all(e['state'] and e['RNG'] and e['modes'] for e in restored);checks['real_exact_five']=[e['case_id'] for e in real]==[x['case_id'] for x in q['real_inputs']]
checks['six_phase_contract']=len(phases)==6 and {(e['arm'],e['training'],e['batch']) for e in phases}=={(a,t,b) for a in ['G0','G1','G2'] for t,b in [(False,1),(True,8)]} and all(e['parameters_unchanged'] and (bool(e['BN_changed']) if e['training'] else not e['BN_changed']) for e in phases)
gradient_summary={}
for e in phases:
 if not e['training']:continue
 g=e['gradients'];prefixes=[('base_model.coarse_pred.' if e['arm']=='G0' else 'base_model.spcg_head.'),'base_model.encoder.','base_model.decoder.','decode_head.'];active={p:sum(v for n,v in g.items() if n.startswith(p)) for p in prefixes};checks[e['arm']+'_gradient_contract']=bool(g) and all(math.isfinite(v) for v in g.values()) and all(v>0 for v in active.values()) and e['Q_gradient']['origin']=='TOTAL_LOSS_NOT_ISOLATED_COARSE' and math.isfinite(e['Q_gradient']['L2']) and e['Q_gradient']['L2']>0;gradient_summary[e['arm']]=dict(active_prefix_norm_sums=active,Q_gradient=e['Q_gradient'])
calls=completion['native_calls'];checks['native396']=len(calls)==66 and sum(calls.values())==396 and all(v==((2 if '.cond_ssm' in n else 4) if not n.startswith('G2:') else (7 if '.cond_ssm' in n else 14)) for n,v in calls.items())
checks['resource_checks']=bool(resources) and all(all(e['checks'].values()) for e in resources);checks['resource_complete']=any(e['phase']=='complete' and e['forwards']==11 for e in resources)
checks['native_origins']=set(completion['native_origins'])<={r['path'] for r in q['dependencies']};checks['no_training_admission_claim']=completion['training_admission'] is False and completion['optimizer_constructed'] is False
result=dict(status='FORMAL_POST_CUDA_FREEZE_PASS' if all(checks.values()) else 'FORMAL_POST_CUDA_FREEZE_STOP',request_sha256=qh,checks=checks,counts=completion['result']['counts'],gradient_summary=gradient_summary,restoration=restored,native_SSM_calls=sum(calls.values()),resources=dict(records=len(resources),peak_allocated_bytes=max(e['values']['peak_allocated'] for e in resources),peak_reserved_bytes=max(e['values']['peak_reserved'] for e in resources),max_RSS_bytes=max(e['values']['RSS_bytes'] for e in resources),max_SMI_MiB=max(e['values']['device_MiB'] for e in resources),max_wall_seconds=max(e['values']['elapsed_seconds'] for e in resources)),hashed_bytes=d['hashed_bytes'],observations='5 NPZ files hashed as opaque bytes, no arrays decoded',limitations=['Restoration events attest state fingerprint equality and CPU/CUDA/Python/NumPy RNG; audit does not reload model or independently regenerate RNG.','Per-arm initial fingerprints recorded, but final per-arm RNG/state fingerprints absent; do not claim a complete independently recalculated before/after fingerprint pair.','Full-run resource evidence is for zero-update admission, not3900-step training proof.','Spatial probe scientific efficacy and clinical accuracy untested.'],server_writes=0,model_calls=0,SMI_queries=0,training_request_created=False)
(O/'formal_audit_result_v3.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));assert all(checks.values()),[k for k,v in checks.items() if not v]
