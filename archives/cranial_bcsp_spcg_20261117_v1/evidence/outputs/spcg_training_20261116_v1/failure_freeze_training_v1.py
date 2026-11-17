"""Formal read-only startup failure audit; no model imports/payload reads/SMI."""
from pathlib import Path
import json,hashlib,base64,zlib,subprocess,ast
S=Path(__file__).resolve().parent;W=S.parents[1];O=S/'post_failure_freeze_v1';O.mkdir()
code="""from pathlib import Path
import json,hashlib,socket,os,subprocess
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G0C_training_20261116_v1');q=json.loads((r/'SPCG_G0_C_training_execution_request_v1.json').read_bytes());o=Path(q['output']);total=0
def item(p,text=False):
 global total
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));b=p.read_bytes();total+=len(b);assert len(b)<4*1024**2 and total<16*1024**2;v=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 if text:v['text']=b.decode()
 return v
d=dict(installed={p.name:item(p) for p in r.iterdir() if p.is_file()},controls={p.name:item(p,True) for p in Path(q['launch_contract']['authorization_path']).parent.iterdir()},output={},directories=[],sources={})
for p in o.iterdir():
 if p.is_dir():assert not p.is_symlink();d['directories'].append(dict(name=p.name,children=[x.name for x in p.iterdir()]))
 else:assert p.suffix not in ['.pth','.npz','.bin'];d['output'][p.name]=item(p,True)
records=list(q['implementation'].values())+[q['native_helper']]
head=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_cuda_20261116_v1/bcsp_spcg_head_v1.py');records.append(dict(path=str(head)))
for x in records:
 v=item(Path(x['path']),True)
 if 'sha256' in x:assert v['sha256']==x['sha256'] and v['bytes']==x['bytes']
 d['sources'][x['path']]=v
d['worker_live']=Path('/proc/'+d['output']['worker.pid']['text'].strip()).exists();d['tmux_live']=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==0;d['hashed_bytes']=total
print(json.dumps(d))
"""
b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(args).encode())<=2048
(O/'remote_readonly_source.py').write_text(code,encoding='utf-8');r=subprocess.run(args,capture_output=True,timeout=30);(O/'stdout.bin').write_bytes(r.stdout);(O/'stderr.bin').write_bytes(r.stderr);assert r.returncode==0
d=json.loads(r.stdout);(O/'server_evidence.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');q=json.loads((S/'pending_transport_v1/payload/SPCG_G0_C_training_execution_request_v1.json').read_text(encoding='utf-8'));m=json.loads((S/'pending_transport_v1/installation_mapping_v1.json').read_text(encoding='utf-8'));qh=m['request_sha256'];controls=d['controls'];auth=json.loads(controls['authorization_v1.json']['text']);runtime=json.loads(controls['runtime_v1.json']['text']);o=d['output']
head_record=json.loads((W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/pending_transport_v3/payload/SPCG_CUDA_execution_request_v3.json').read_text(encoding='utf-8'))['implementation']['head'];head=d['sources'][head_record['path']]
checks=dict(installed_exact_set=set(d['installed'])=={Path(x['target']).name for x in m['files']},installed_size_hash=all(d['installed'][Path(x['target']).name]['sha256']==x['sha256'] and d['installed'][Path(x['target']).name]['bytes']==x['bytes'] for x in m['files']),request_hash=d['installed']['SPCG_G0_C_training_execution_request_v1.json']['sha256']==qh,authorization=auth['request_sha256']==qh and auth['explicit_user_authorization'] is True,one_way_runtime=runtime==dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256=controls['authorization_v1.json']['sha256']),single_claim=json.loads(controls['attempt_claim_v1.json']['text'])==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh),exit_one=o['exit_code.txt']['text']=='1\n',no_worker_tmux=not d['worker_live'] and not d['tmux_live'],exact_failure_outputs=set(o)=={'worker.pid','launch.log','startup_failure.json','exit_code.txt'},only_tmp_empty=d['directories']==[dict(name='tmp',children=[])],no_training_artifacts=not any(n in o for n in ['initialization.json','resources.jsonl','metrics.jsonl','completion.json','ckpt-last.pth','model_construction.json']),head_exists_frozen_match=head['sha256']==head_record['sha256'] and head['bytes']==head_record['bytes'])
assert all(checks.values()),checks
imports={}
for p,v in d['sources'].items():
 tree=ast.parse(v['text']);imports[p]=[dict(line=n.lineno,module=n.module,names=[a.name for a in n.names]) if isinstance(n,ast.ImportFrom) else dict(line=n.lineno,module=None,names=[a.name for a in n.names]) for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
result=dict(status='FORMAL_READONLY_TRAINING_FAILURE_FREEZE_PASS',checks=checks,request_sha256=qh,primary_failure=json.loads(o['startup_failure.json']['text']),unbound_observation_import=dict(module='bcsp_spcg_head_v1',only_symbol_used='need',source=head_record,present_on_server=True,absent_from_training_request=True,not_loaded_in_sys_modules_by_entry=True,not_in_entryroot_sys_path=True),secondary_failure='guard.close clears fds in finally while installed audit hook still calls guard.allow during unhandled-exception source rendering',training_counts=dict(forward=0,loss=0,backward=0,optimizer_step=0),count_basis='Failure occurs loading observe before frozen runtime import, model construction, Budget creation and dispatch; no training artifacts.',request_consumed=True,imports=imports,hashed_bytes=d['hashed_bytes'],server_writes=0,SMI_queries=0,models=0,real_NPZ_reads=0,limitations=['No model/checkpoint was loaded to verify tensor state.','Current-container process view only.','Static import graph review is not a successful production boot or training admission.'])
(O/'formal_audit_result_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k!='imports'},ensure_ascii=False))
