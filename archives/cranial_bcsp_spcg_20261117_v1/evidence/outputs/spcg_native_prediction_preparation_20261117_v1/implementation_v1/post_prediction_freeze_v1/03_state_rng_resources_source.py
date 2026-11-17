from pathlib import Path
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
c=read(o/'inference_complete.json');assert c['status']=='SPCG_SIXMODEL_630_NATIVE_FORWARD_COMPLETE' and c['forwards']==630 and c['request_sha256']==hashlib.sha256(b).hexdigest() and all(c[k]==0 for k in ['training_updates','BNCal','loss','backward','context_cases','trace_cases'])
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
