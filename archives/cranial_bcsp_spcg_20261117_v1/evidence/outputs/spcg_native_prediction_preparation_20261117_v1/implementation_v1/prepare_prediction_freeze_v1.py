from pathlib import Path
import ast,base64,zlib,subprocess
V=Path(__file__).resolve().parent
PRE="""from pathlib import Path
import os,socket,json,hashlib
assert socket.gethostname()=='shu-common-25721452-notebook-yxwd3w-0' and os.getuid()==1000
r=Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_spcg_native_prediction_20261117_v1');b=(r/'SPCG_sixmodel_native_execution_request_v1.json').read_bytes();assert hashlib.sha256(b).hexdigest()=='c63ebdfc7e4315e36bb0c65b445925d5496352720fd78db80ff7ed0e5b155dcc';q=json.loads(b);o=Path(q['output'])
def read(p):return json.loads(p.read_bytes())
def record(p):
 assert not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();assert p.is_file() and s.st_size<128*1024**2;h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 t=p.stat();assert (s.st_ino,s.st_size,s.st_mtime_ns)==(t.st_ino,t.st_size,t.st_mtime_ns);return dict(bytes=s.st_size,sha256=h.hexdigest())
idx=read(Path(q['input_index']['path']));assert record(Path(q['input_index']['path']))=={k:q['input_index'][k] for k in ['bytes','sha256']}
"""
inventory="""import subprocess
assert sorted(p.name for p in o.iterdir() if p.is_dir())==['predictions','tmp'] and not list((o/'tmp').iterdir())
for p in [o,o/'predictions',o/'tmp']:assert not any(x.is_symlink() for x in (p,*p.parents))
files={p.name:record(p) for p in o.iterdir() if p.is_file()};files.update({'predictions/'+p.name:record(p) for p in (o/'predictions').iterdir()})
c=read(o/'completion.json');checks=dict(exit_zero=(o/'exit_code.txt').read_text()=='0\\n',worker_absent=not Path('/proc/'+(o/'worker.pid').read_text().strip()).exists(),tmux_absent=subprocess.run(['tmux','has-session','-t',q['launch_contract']['tmux_session']],capture_output=True,timeout=5).returncode==1,completion=c['status']=='PREDICTIONS_ARCHIVED_AWAITING_FREEZE_AUDIT' and c['forwards']==630 and c['request_sha256']==hashlib.sha256(b).hexdigest())
expected={x['prediction_filename'] for x in idx['inputs']}|{'completion.json','inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','resources.jsonl','inference_complete.json','launch.log','worker.pid','exit_code.txt','development_predictions_v1.tar.gz','development_predictions_v1.tar.gz.sha256','development_predictions_v1.tar.gz.bytes','development_predictions_v1.tar.gz.contents.sha256'}
checks['exact_output_set']=set(files)==expected
print(json.dumps(dict(files=files,checks=checks)))
"""
stages=[('01_inventory_before',inventory),('02_manifest_and_controls',"""from collections import Counter
M=[json.loads(l) for l in (o/'inference_manifest.jsonl').read_text().splitlines()];J=[json.loads(l) for l in (o/'forward_attempts.jsonl').read_text().splitlines()];G=[json.loads(l) for l in (o/'geometry_summary.jsonl').read_text().splitlines()];assert len(M)==len(J)==len(G)==630
for i,(m,j,g,x) in enumerate(zip(M,J,G,idx['inputs']),1):
 assert m['forward_index']==j['forward_index']==i and j['status']=='CLAIMED_BEFORE_FORWARD'
 assert all(m[k]==x[k] for k in ['run','case_id','source_id','fold','n_input','n_output','normalization']) and (g['run'],g['case_id'])==(x['run'],x['case_id']) and (j['run'],j['case_id'])==(x['run'],x['case_id'])
 assert m['input_sha256']==x['input']['sha256'] and m['prediction']['name']==x['prediction_filename'] and record(o/x['prediction_filename'])=={k:m['prediction'][k] for k in ['bytes','sha256']}
 pin=next(v for v in idx['runs'] if v['label']==m['run']);assert m['checkpoint_sha256']==pin['checkpoint']['sha256']
json.dumps(G,allow_nan=False);control=Path(q['launch_contract']['authorization']).parent;co={p.name:dict(**record(p),text=p.read_text()) for p in control.iterdir()};installed={p.name:record(p) for p in r.iterdir() if p.is_file()}
print(json.dumps(dict(checks=dict(all630_manifest_journal_geometry=True,each105=dict(Counter(x['run'] for x in M))=={x['label']:105 for x in idx['runs']}),controls=co,installed=installed)))
"""),('03_state_rng_resources',"""c=read(o/'inference_complete.json');assert c['status']=='SPCG_SIXMODEL_630_NATIVE_FORWARD_COMPLETE' and c['forwards']==630 and c['request_sha256']==hashlib.sha256(b).hexdigest() and all(c[k]==0 for k in ['training_updates','BNCal','loss','backward','context_cases','trace_cases'])
assert [x['run'] for x in c['models']]==[x['label'] for x in idx['runs']]
for m,x in zip(c['models'],idx['runs']):
 assert m['forwards']==105 and m['mode']=='eval_inference_mode' and m['state_before']==m['state_after'] and bool(m['state_before']) and m['RNG_before']==m['RNG_after'] and bool(m['RNG_before']['CPU']) and bool(m['RNG_before']['CUDA']) and all(m[k]==0 for k in ['BNCal','optimizer','backward']) and m['construction']['arm']==x['arm'] and not m['construction']['artificial_fixture']
R=[json.loads(l) for l in (o/'resources.jsonl').read_text().splitlines()];expected=[]
for n,x in enumerate(idx['runs']):
 expected.append(('model_start:'+x['label'],n*105))
 for i in range(n*105,(n+1)*105):expected.extend([('before_forward',i),('after_forward',i+1)])
expected.append(('all_complete',630));assert [(x['phase'],x['forwards']) for x in R]==expected
for x in R:
 v=x['values'];L=q['limits'];assert all(x['checks'].values()) and not x['failed_checks'];assert v['RSS_bytes']<=L['RSS_bytes'] and v['output_bytes']<=L['output_bytes'] and v['device_MiB']<=L['device_MiB'] and max(v['peak_allocated'],v['peak_reserved'])<=L['torch_peak_bytes'] and v['elapsed_seconds']<=L['wall_seconds'] and v['free_disk_bytes']>=L['minimum_free_disk_bytes']
print(json.dumps(dict(checks=dict(states_rng_all6=True,zero_updates_loss_BNCal=True,exact1267_resources=True,resource_values_recomputed=True),states=c['models'],peaks={k:max(x['values'][k] for x in R) for k in R[0]['values'] if k!='free_disk_bytes'})))
"""),('04_archive',"""import tarfile
c=read(o/'completion.json')['archive'];a=Path(c['path']);assert a==o/'development_predictions_v1.tar.gz' and record(a)=={k:c[k] for k in ['bytes','sha256']};records=c['members'];expected={x['prediction_filename'] for x in idx['inputs']}|{'inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl'};assert len(records)==len({x['name'] for x in records})==635 and {x['name'] for x in records}==expected
with tarfile.open(a) as t:
 members=t.getmembers();assert len(members)==635 and [x.name for x in members]==[x['name'] for x in records]
 for m,x in zip(members,records):
  assert m.isfile() and m.name in expected and m.size==x['bytes'];h=hashlib.sha256()
  with t.extractfile(m) as f:
   for z in iter(lambda:f.read(1048576),b''):h.update(z)
  assert h.hexdigest()==x['sha256'] and record(o/m.name)=={k:x[k] for k in ['bytes','sha256']}
assert (o/(a.name+'.sha256')).read_text()==c['sha256']+'  '+a.name+'\\n' and int((o/(a.name+'.bytes')).read_text())==c['bytes']
assert (o/(a.name+'.contents.sha256')).read_text()==''.join(x['sha256']+'  '+x['name']+'\\n' for x in records)
print(json.dumps(dict(checks=dict(archive_hash_bytes=True,members635_exact=True,all_archive_members_match_live=True,sidecars=True),archive={k:c[k] for k in ['path','bytes','sha256']},download_files=[dict(path=str(p),**record(p)) for p in [a,*[o/(a.name+x) for x in ['.sha256','.bytes','.contents.sha256']]]])))
"""),('05_prediction_array_contract',"""import zipfile,struct,ast,array,sys,math
assert sys.byteorder=='little';count=0
for row in idx['inputs']:
 with zipfile.ZipFile(o/row['prediction_filename']) as z:
  assert set(z.namelist())=={'prediction.npy','coarse.npy'} and len(z.namelist())==2
  for key,n in [('prediction',8192),('coarse',256)]:
   b=z.read(key+'.npy');assert b[:6]==b'\\x93NUMPY';version=b[6];assert version in [1,2,3];size=2 if version==1 else 4;hlen=int.from_bytes(b[8:8+size],'little');assert hlen<4096;end=8+size+hlen;header=ast.literal_eval(b[8+size:end].decode());assert header['descr']=='<f4' and header['shape']==(n,3) and header['fortran_order'] is False and len(b)-end==n*12
   values=array.array('f');values.frombytes(b[end:]);assert all(math.isfinite(x) for x in values)
 count+=1
print(json.dumps(dict(checks=dict(all630_arrays_shape_dtype_finite=True,no_extra_RF_GT_arrays=True),files=count)))
"""),('06_inventory_after',inventory)]
lengths={}
for label,body in stages:
 code=PRE+body;compile(code,label,'exec');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";a=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c];lengths[label]=len(subprocess.list2cmdline(a).encode());assert lengths[label]<=2048,(label,lengths[label])
script='''from pathlib import Path
import json,hashlib,subprocess,base64,zlib
V=Path(__file__).resolve().parent;O=V/'post_prediction_freeze_v1';O.mkdir()
PRE=PRE_VALUE
STAGES=STAGES_VALUE
results={}
for label,body in STAGES:
 code=PRE+body;compile(code,label,'exec');(O/(label+'_source.py')).write_text(code,encoding='utf-8');c="import base64,zlib;exec(zlib.decompress(base64.b64decode('"+base64.b64encode(zlib.compress(code.encode())).decode()+"')))";args=['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','60','--','/usr/bin/python3','-I','-S','-B','-c',c]
 assert len(subprocess.list2cmdline(args).encode())<=2048
 p=subprocess.run(args,capture_output=True,timeout=65);(O/(label+'_stdout.bin')).write_bytes(p.stdout);(O/(label+'_stderr.bin')).write_bytes(p.stderr);assert p.returncode==0,(label,p.stdout[-1600:]);d=json.loads(p.stdout);(O/(label+'_result.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');results[label]=d;print(label+': READONLY_PASS',flush=True)
checks={k:v for d in results.values() for k,v in d['checks'].items()};checks['inventory_unchanged']=results['01_inventory_before']['files']==results['06_inventory_after']['files']
q=json.loads((V/'pending_transport_v1/payload/SPCG_sixmodel_native_execution_request_v1.json').read_bytes());mapping=json.loads((V/'pending_transport_v1/installation_mapping_v1.json').read_bytes());binding=results['02_manifest_and_controls'];co=binding['controls'];a=json.loads(co['authorization_v1.json']['text']);rt=json.loads(co['runtime_v1.json']['text']);qh=mapping['request_sha256']
checks['exact_control_set']=set(co)=={'authorization_v1.json','runtime_v1.json','launch_once_v1.sh','attempt_claim_v1.json'}
checks['one_way_authorization_runtime']=a['request_sha256']==qh and a['explicit_user_authorization'] is True and 'runtime_sha256' not in a and rt==dict(schema='bcsp-development-runtime-v1',request_sha256=qh,authorization_sha256=co['authorization_v1.json']['sha256'])
checks['single_claim']=json.loads(co['attempt_claim_v1.json']['text'])==dict(status='CLAIMED_BEFORE_TMUX',request_sha256=qh)
checks['installed_exact_set']=set(binding['installed'])=={Path(x['target']).name for x in mapping['files']}
checks['installed_hashes']=all(binding['installed'][Path(x['target']).name]==dict(bytes=x['bytes'],sha256=x['sha256']) for x in mapping['files'])
result=dict(status='FORMAL_SPCG_NATIVE630_POST_PREDICTION_FREEZE_PASS' if all(checks.values()) else 'FORMAL_FREEZE_STOP',request_sha256=qh,checks=checks,models=6,per_model=105,predictions=630,forward_attempts=630,unique_inputs=210,archive=results['04_archive']['archive'],download_files=results['04_archive']['download_files'],state_rng_models=6,resource_records=1267,resources=results['03_state_rng_resources']['peaks'],server_writes=0,model_calls=0,checkpoint_loads=0,scoring_executed=False,limitations=q['comparison_qualification'])
(O/'formal_freeze_result_v1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result));assert all(checks.values()),[k for k,v in checks.items() if not v]
'''.replace('PRE_VALUE',repr(PRE)).replace('STAGES_VALUE',repr(stages))
ast.parse(script)
with (V/'post_prediction_freeze_v1.py').open('x',encoding='utf-8') as f:f.write(script)
print(lengths)
