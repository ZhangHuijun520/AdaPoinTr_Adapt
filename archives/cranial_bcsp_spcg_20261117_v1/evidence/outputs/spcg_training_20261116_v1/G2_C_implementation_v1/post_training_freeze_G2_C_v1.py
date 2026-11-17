"""Bounded read-only audit: stream checkpoint bytes, inspect logs; never torch.load/model/SMI."""
from pathlib import Path
import json,hashlib,base64,zlib,subprocess
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'post_training_freeze_v1';O.mkdir()
PREFIX="""from pathlib import Path
import json,hashlib,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G2C_training_20261116_v1');qp=r/'SPCG_G2_C_training_execution_request_v1.json';qb=qp.read_bytes();assert hashlib.sha256(qb).hexdigest()=='f55806333bf52eef358aa718a77b3e7bbc58f2dd59e5de341d56f8ab9df73322';q=json.loads(qb);o=Path(q['output'])
def read(p):return json.loads(p.read_text())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<600*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_size,s.st_mtime_ns,s.st_ino)==(t.st_size,t.st_mtime_ns,t.st_ino);return dict(bytes=s.st_size,sha256=h.hexdigest())
"""
def remote(label,body):
 code=(PREFIX.split('def record(p):')[0] if label=='03_all3900_order_numeric' else PREFIX)+body;compile(code,label,'exec');b=base64.b64encode(zlib.compress(code.encode())).decode();c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+b+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];assert len(subprocess.list2cmdline(args).encode())<=2048,(label,len(subprocess.list2cmdline(args).encode()))
 (O/(label+'_source.py')).write_text(code,encoding='utf-8');p=subprocess.run(args,capture_output=True,timeout=65);(O/(label+'_stdout.bin')).write_bytes(p.stdout);(O/(label+'_stderr.bin')).write_bytes(p.stderr);assert p.returncode==0,(label,p.stdout[-2000:]);d=json.loads(p.stdout);(O/(label+'_result.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');return d
inventory=remote('01_inventory_checkpoint',"""import subprocess
files={p.name:record(p) for p in o.iterdir() if p.is_file()};dirs={p.name:list(p.iterdir()) for p in o.iterdir() if p.is_dir()};assert all(not v for v in dirs.values())
manifest=read(o/'payload_manifest.json')['files'];checks=dict(manifest_unique=len(manifest)==len({x['name'] for x in manifest}),manifest_hashes=all(files[x['name']]==dict(bytes=x['bytes'],sha256=x['sha256']) for x in manifest),manifest_scope={x['name'] for x in manifest}==set(files)-{'launch.log','worker.pid','exit_code.txt','payload_manifest.json'},exit_zero=(o/'exit_code.txt').read_text()=='0\\n',worker_absent=not Path('/proc/'+(o/'worker.pid').read_text().strip()).exists())
checks['tmux_absent']=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1
c=read(o/'completion.json');checks['checkpoint_hash']=files['ckpt-last.pth']['sha256']==c['checkpoint_sha256'];print(json.dumps(dict(files=files,directories=list(dirs),checks=checks,completion=c)))
""")
binding=remote('02_binding_initialization',"""c=Path(q['launch_contract']['authorization_path']).parent;control={p.name:dict(**record(p),text=p.read_text()) for p in c.iterdir()};sources={k:record(Path(v['path'])) for k,v in q['implementation'].items()};installed={p.name:record(p) for p in r.iterdir() if p.is_file()}
expected=Path(q['order_plan']['path']);assert record(expected)['sha256']==q['order_plan']['sha256'];checks=dict(order_raw_bytes=(o/'order_plan.json').read_bytes()==expected.read_bytes())
print(json.dumps(dict(controls=control,sources=sources,installed=installed,checks=checks,initialization=read(o/'initialization.json'),construction=read(o/'model_construction.json'),optimizer=read(o/'optimizer_actual_defaults.json'),groups=read(o/'optimizer_parameter_groups.json'),exposure=read(o/'exposure.json'))))
""")
logs=remote('03_all3900_order_numeric',"""from collections import Counter
import math
plan=read(o/'order_plan.json');exp=read(o/'exposure.json');M=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()];G=[json.loads(l) for l in (o/'SPCG_geometry.jsonl').read_text().splitlines()];checks=dict(metrics3900=len(M)==3900,geometry3900=len(G)==3900);cases=Counter();sources=Counter();drop=Counter()
def close(a,b):return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-10)
for i,(m,g) in enumerate(zip(M,G),1):
 ep,ba=divmod(i-1,39);ids=plan['epochs'][ep]['batches'][ba];assert m['step']==g['step']==i and m['epoch']==g['epoch']==ep and m['batch']==g['batch']==ba and m['case_ids']==g['case_ids']==ids
 assert len(ids)==8 and m['source_ids']==['train:'+x.split('__')[1] for x in ids] and m['optimizer_step_committed'] and m['loss_sparse']==m['loss_denoise']==0 and close(m['loss'],m['loss_dense']) and m['loss']==__import__('struct').unpack('f',__import__('struct').pack('f',sum(g['loss_components'].values())))[0]
 assert all(close(x,1e-4*max(.9**(ep/21),.02)) for x in m['LR']) and close(m['BN_momentum'],max(.9*.5**(ep/21),.01)) and m['clip_max_norm']==10 and all(math.isfinite(m[k]) for k in ['loss','grad_norm_before_clip'])
 cases.update(ids);sources.update(m['source_ids'])
for row in plan['epochs']:drop.update(row['dropped'])
checks.update(exposure=exp['case']==dict(cases) and exp['source']==dict(sources) and exp['dropped_case']==dict(drop),counts=sum(cases.values())==31200 and sum(drop.values())==300)
assert all(g['frame']=='D_only_normalized' and set(g['loss_components'])=={'coarse_CD','dense_CD'} for g in G)
json.dumps(G,allow_nan=False)
detailed=[g for g in G if 'total_loss_Q_gradient' in g];checks['five_gradient_steps']=[g['step'] for g in detailed]==[1,39,390,1950,3900] and all(g['total_loss_Q_gradient']['origin']=='TOTAL_LOSS_NOT_ISOLATED_COARSE' and g['total_loss_Q_gradient']['L2']>0 and math.isfinite(g['total_loss_Q_gradient']['L2']) for g in detailed)
R=[json.loads(l) for l in (o/'resources.jsonl').read_text().splitlines()];checks['resources']=len(R)==3902 and all(x['resource_guard_passed'] and all(x['checks'].values()) for x in R)
print(json.dumps(dict(checks=checks,metrics_count=len(M),geometry_count=len(G),resource_count=len(R),sources=len(sources),cases=len(cases),exposures=sum(cases.values()),drops=sum(drop.values()),detailed=detailed,first=M[0],last=M[-1],resource_last=R[-1],peaks={k:max(x[k] for x in R) for k in ['RSS','output_bytes','peak_allocated','peak_reserved','device_MiB']})))
""")
q=json.loads((V/'pending_transport_v1/payload/SPCG_G2_C_training_execution_request_v1.json').read_text(encoding='utf-8'));mapping=json.loads((V/'pending_transport_v1/installation_mapping_v1.json').read_text());qh=mapping['request_sha256'];checks={**inventory['checks'],**binding['checks'],**logs['checks']};c=inventory['completion'];co=binding['controls'];a=json.loads(co['authorization_v1.json']['text']);rt=json.loads(co['runtime_v1.json']['text'])
checks['installed_exact_set']=set(binding['installed'])=={Path(r['target']).name for r in mapping['files']};checks['installed_hashes']=all(binding['installed'][Path(r['target']).name]==dict(bytes=r['bytes'],sha256=r['sha256']) for r in mapping['files']);checks['reused_source_hashes']=all(binding['sources'][k]==dict(bytes=r['bytes'],sha256=r['sha256']) for k,r in q['implementation'].items());checks['authorization']=a['request_sha256']==qh and a['explicit_user_authorization'] is True and rt==dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256=co['authorization_v1.json']['sha256']);checks['single_claim']=json.loads(co['attempt_claim_v1.json']['text'])==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh)
checks['exact_final_counts']=c['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100) and (c['optimizer_updates'],c['traversals'],c['case_exposures'])==(3900,100,31200);checks['no_BNCal_evaluation_resume']=not any(c[k] for k in ['bncal_executed','evaluation_executed','resume'])
state=binding['initialization'];checks['order_canonical_binding']=state['order_sha256']==c['order_sha256']==binding['exposure']['order_sha256'] and state['seed']==0
cuda=json.loads((W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/post_CUDA_freeze_v3/server_evidence.json').read_text());native=json.loads(cuda['output']['completion.json']['text']);model=binding['construction'];checks['admitted_initialization']=model['factory']['parent']==native['result']['models']['G0']['construction']['parent'] and model['expected_initial_state_sha256']==q['expected_initial_state_sha256']==native['result']['models']['G2']['initial_state_sha256'];checks['G2C_identity']=model['arm']=='G2' and model['fold']=='C'
opt=binding['optimizer'];checks['AdamW_defaults']=opt['lr']==.0001 and opt['betas']==[.9,.999] and opt['eps']==1e-8 and opt['amsgrad'] is False;groups=binding['groups'];checks['optimizer_groups']=len(groups)==len({g['name'] for g in groups}) and all(g['weight_decay'] in [0.,.0005] for g in groups) and all(g['weight_decay']==0 for g in groups if g['reason']=='explicit_no_weight_decay') and not any(g['name'].startswith(('base_model.scq.','base_model.rf.')) for g in groups)
expected={'SPCG_geometry.jsonl','ckpt-last.pth','completion.json','exit_code.txt','exposure.json','initialization.json','launch.log','metrics.jsonl','model_construction.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','order_plan.json','payload_manifest.json','resources.jsonl','worker.pid'};checks['exact_output_set']=set(inventory['files'])==expected and inventory['directories']==['tmp']
pairing=remote('04_pair_G1_G2',"""g1=Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SPCG_G1_foldC_seed0_train_20261116_v1')
m1=[json.loads(l) for l in (g1/'metrics.jsonl').read_text().splitlines()];m2=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()]
print(json.dumps(dict(order_identical=(g1/'order_plan.json').read_bytes()==(o/'order_plan.json').read_bytes(),exposure_identical=read(g1/'exposure.json')==read(o/'exposure.json'),initialization=read(g1/'initialization.json'),optimizer=read(g1/'optimizer_actual_defaults.json'),groups=read(g1/'optimizer_parameter_groups.json'),pair_rows=len(m1)==len(m2)==3900 and all(all(a[k]==b[k] for k in ['step','epoch','batch','case_ids','source_ids','LR','BN_momentum','clip_max_norm']) for a,b in zip(m1,m2)),parent_records={n:record(g1/n) for n in ['metrics.jsonl','initialization.json','order_plan.json','exposure.json','model_construction.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json']},construction=read(g1/'model_construction.json'))))
""")
assets=remote('05_fixed_probe_head_and_parent_proofs',"""items={k:record(Path(q[k]['path'])) for k in ['probe_asset','head_initialization','mother_source','G0_C_freeze','G1_C_freeze']}
print(json.dumps(dict(records=items,free_bytes=os.statvfs(o).f_bavail*os.statvfs(o).f_frsize)))
""")
parent_dir=S/'G1_C_implementation_v1/post_training_freeze_v1'
parent=json.loads((parent_dir/'formal_freeze_result_v1.json').read_text(encoding='utf-8'))
parent_inv=json.loads((parent_dir/'01_inventory_checkpoint_result.json').read_text(encoding='utf-8'))
checks['G1_formal_freeze']=parent['status']=='FORMAL_SPCG_G1_C_POST_TRAINING_FREEZE_PASS' and all(parent['checks'].values())
checks['G1_evidence_unchanged']=all(v==parent_inv['files'][k] for k,v in pairing['parent_records'].items())
checks['paired_order_exposure_numeric']=all(pairing[k] for k in ['order_identical','exposure_identical','pair_rows'])
checks['same_full_initialization']=pairing['initialization']==state and q['expected_initial_state_sha256']==parent['initialization_raw_tensor_fingerprint']
checks['same_optimizer_defaults_and_groups']=pairing['optimizer']==opt and pairing['groups']==groups
checks['same_scratch_parent']=pairing['construction']['factory']['parent']==model['factory']['parent']
checks['G2_head_replaces_original']=model['factory']['change']['arm']=='G2' and model['factory']['change']['old_head_removed'] and model['factory']['change']['head_parameters']==1845763 and model['factory']['change']['additional_parameters']==8963
checks['one_coarse_expression_only']=model['factory']['change']['patch']['replaced_assignments']==1
for k,r in assets['records'].items():checks['asset_'+k]=r==dict(bytes=q[k]['bytes'],sha256=q[k]['sha256'])
pq=json.loads((S/'G1_C_implementation_v1/pending_transport_v1/payload/SPCG_G1_C_training_execution_request_v1.json').read_text(encoding='utf-8'))
for key in ['data_root','order_plan','static_config','identity','environment','probe_asset','head_initialization','mother_source','parent_G0_initial_state_sha256','counts','resources','science']:
 checks['paired_request_'+key]=q[key]==pq[key]
checks['G0_mother_same_as_G1']=q['parent_G0_initial_state_sha256']==pq['parent_G0_initial_state_sha256']
result=dict(status='FORMAL_SPCG_G2_C_POST_TRAINING_FREEZE_PASS' if all(checks.values()) else 'FORMAL_FREEZE_STOP',request_sha256=qh,checks=checks,checkpoint=dict(path=q['output']+'/ckpt-last.pth',**inventory['files']['ckpt-last.pth']),fold='C',arm='G2',seed=0,updates=3900,traversals=100,exposures=31200,drops=300,initialization=state,order_plan=q['order_plan'],initialization_raw_tensor_fingerprint=q['expected_initial_state_sha256'],gradient_steps=[g['step'] for g in logs['detailed']],resources=logs['peaks'],wall_seconds=c['elapsed_seconds'],BNCal=False,evaluation=False,resume=False,server_writes=0,model_calls=0,checkpoint_loads=0,limitations=['Checkpoint streamed as bytes only, never deserialized.','Init byte identity corroborated via runtime factory evidence and admitted same-algorithm fingerprint assertion; no model regeneration in audit.','Singlefold training does not establish completion improvement.'])
(O/'formal_freeze_result_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));assert all(checks.values()),[k for k,v in checks.items() if not v]
