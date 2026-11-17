"""Bounded read-only audit: stream checkpoint bytes, inspect logs; never torch.load/model/SMI."""
from pathlib import Path
import json,hashlib,base64,zlib,subprocess
V=Path(__file__).resolve().parent;S=V.parent;W=S.parents[1];O=V/'post_training_freeze_v1';O.mkdir()
PREFIX="""from pathlib import Path
import json,hashlib,os,socket
assert socket.gethostname()=='shu-common-25721452-notebook-lwwgl9-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_G0D_training_20261116_v1');qp=r/'SPCG_G0_D_training_execution_request_v1.json';qb=qp.read_bytes();assert hashlib.sha256(qb).hexdigest()=='a877093becfd3e9763da36565c9401275e2f5ddd4f6d4f223fb4964ddf1d7fea';q=json.loads(qb);o=Path(q['output'])
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
q=json.loads((V/'pending_transport_v1/payload/SPCG_G0_D_training_execution_request_v1.json').read_text(encoding='utf-8'));mapping=json.loads((V/'pending_transport_v1/installation_mapping_v1.json').read_text());qh=mapping['request_sha256'];checks={**inventory['checks'],**binding['checks'],**logs['checks']};c=inventory['completion'];co=binding['controls'];a=json.loads(co['authorization_v1.json']['text']);rt=json.loads(co['runtime_v1.json']['text'])
checks['installed_exact_set']=set(binding['installed'])=={Path(r['target']).name for r in mapping['files']};checks['installed_hashes']=all(binding['installed'][Path(r['target']).name]==dict(bytes=r['bytes'],sha256=r['sha256']) for r in mapping['files']);checks['reused_source_hashes']=all(binding['sources'][k]==dict(bytes=r['bytes'],sha256=r['sha256']) for k,r in q['implementation'].items());checks['authorization']=a['request_sha256']==qh and a['explicit_user_authorization'] is True and rt==dict(schema='bcsp-spcg-training-runtime-v1',request_sha256=qh,authorization_sha256=co['authorization_v1.json']['sha256']);checks['single_claim']=json.loads(co['attempt_claim_v1.json']['text'])==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh)
checks['exact_final_counts']=c['counts']==dict(forward=3900,backward=3900,clip=3900,step=3900,lr_scheduler=100,bn_scheduler=100) and (c['optimizer_updates'],c['traversals'],c['case_exposures'])==(3900,100,31200);checks['no_BNCal_evaluation_resume']=not any(c[k] for k in ['bncal_executed','evaluation_executed','resume'])
state=binding['initialization'];checks['order_canonical_binding']=state['order_sha256']==c['order_sha256']==binding['exposure']['order_sha256'] and state['seed']==0
cuda=json.loads((W/'outputs/spcg_implementation_20261116_v1/output_policy_hotfix_v3/post_CUDA_freeze_v3/server_evidence.json').read_text());native=json.loads(cuda['output']['completion.json']['text']);model=binding['construction'];checks['admitted_initialization']=model['factory']==native['result']['models']['G0']['construction']['parent'] and model['expected_initial_state_sha256']==q['expected_initial_state_sha256']==native['result']['models']['G0']['initial_state_sha256'];checks['G0D_identity']=model['arm']=='G0' and model['fold']=='D'
opt=binding['optimizer'];checks['AdamW_defaults']=opt['lr']==.0001 and opt['betas']==[.9,.999] and opt['eps']==1e-8 and opt['amsgrad'] is False;groups=binding['groups'];checks['optimizer_groups']=len(groups)==len({g['name'] for g in groups}) and all(g['weight_decay'] in [0.,.0005] for g in groups) and all(g['weight_decay']==0 for g in groups if g['reason']=='explicit_no_weight_decay') and not any(g['name'].startswith(('base_model.spcg_head.','base_model.scq.','base_model.rf.')) for g in groups)
expected={'SPCG_geometry.jsonl','ckpt-last.pth','completion.json','exit_code.txt','exposure.json','initialization.json','launch.log','metrics.jsonl','model_construction.json','optimizer_actual_defaults.json','optimizer_parameter_groups.json','order_plan.json','payload_manifest.json','resources.jsonl','worker.pid'};checks['exact_output_set']=set(inventory['files'])==expected and inventory['directories']==['tmp']
metadata=remote('04_D_metadata_C_prerequisites',"""qc=q['QC'];records={k:record(Path(qc[k]['path'])) for k in ['qualified_receipt','verification','fold_binding']};records.update({'manifest_'+k:record(Path(v['path'])) for k,v in qc['manifests'].items()})
fold=read(Path(qc['fold_binding']['path']))['folds']['D'];plan=read(o/'order_plan.json');M=[json.loads(l) for l in (o/'metrics.jsonl').read_text().splitlines()];proofs={k:dict(record=record(Path(v['path'])),value=read(Path(v['path']))) for k,v in q['C_matrix_freezes'].items()}
print(json.dumps(dict(records=records,proofs=proofs,D_selected_order=plan['case_ids']==fold['train_case_ids'],D_counts=len(fold['train_case_ids'])==315 and len(fold['train_sources'])==63 and len(fold['dev_sources'])==21,D_train_only=all(set(m['case_ids'])<=set(fold['train_case_ids']) and set(m['source_ids'])<=set(fold['train_sources']) for m in M),D_disjoint=not set(fold['train_sources'])&set(fold['dev_sources']))))
""")
for key,r in metadata['records'].items():
 target=q['QC']['manifests'][key.split('_',1)[1]] if key.startswith('manifest_') else q['QC'][key]
 checks['metadata_'+key]=r==dict(bytes=target['bytes'],sha256=target['sha256'])
for key in ['D_selected_order','D_counts','D_train_only','D_disjoint']:checks[key]=metadata[key]
for arm,item in metadata['proofs'].items():
 proof=item['value'];r=q['C_matrix_freezes'][arm]
 checks['C_matrix_freeze_'+arm]=item['record']==dict(bytes=r['bytes'],sha256=r['sha256']) and proof['status']=='FORMAL_SPCG_'+arm+'_C_POST_TRAINING_FREEZE_PASS' and all(proof['checks'].values())
base=metadata['proofs']['G0']['value']
checks['G0_shared_scratch_initialization']=base['initialization_raw_tensor_fingerprint']==q['expected_initial_state_sha256'] and all(base['initialization'][k]==state[k] for k in ['parameter_sha256','persistent_state_sha256','seed'])
checks['D_data_root']=q['data_root']==q['project']+'/data/bcsp_geov1_foldd_8192_seed0_v1'
result=dict(status='FORMAL_SPCG_G0_D_POST_TRAINING_FREEZE_PASS' if all(checks.values()) else 'FORMAL_FREEZE_STOP',request_sha256=qh,checks=checks,checkpoint=dict(path=q['output']+'/ckpt-last.pth',**inventory['files']['ckpt-last.pth']),fold='D',arm='G0',seed=0,updates=3900,traversals=100,exposures=31200,drops=300,initialization=state,order_plan=q['order_plan'],initialization_raw_tensor_fingerprint=q['expected_initial_state_sha256'],gradient_steps=[g['step'] for g in logs['detailed']],resources=logs['peaks'],wall_seconds=c['elapsed_seconds'],BNCal=False,evaluation=False,resume=False,server_writes=0,model_calls=0,checkpoint_loads=0,limitations=['Checkpoint streamed as bytes only, never deserialized.','Init byte identity corroborated via runtime factory evidence and admitted same-algorithm fingerprint assertion; no model regeneration in audit.','Singlefold training does not establish completion improvement.'])
(O/'formal_freeze_result_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False));assert all(checks.values()),[k for k,v in checks.items() if not v]
