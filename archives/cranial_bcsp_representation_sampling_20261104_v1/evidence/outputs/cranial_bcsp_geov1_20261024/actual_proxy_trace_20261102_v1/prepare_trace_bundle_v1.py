import json,pathlib,hashlib,ast,tarfile
N=pathlib.Path(__file__).resolve().parent;E=N.parent/'development_eval_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s=(E/'bcsp_development_predict_v1.py').read_text(encoding='utf-8')
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change("q['schema']=='bcsp-four-model-development-prediction-v1'","q['schema']=='bcsp-actual-proxy-trace-v1'")
change(' return runs,rows',' rows=[r for r in rows if r[\'case_id\']=={\'C\':\'train__001__bilateral\',\'D\':\'train__004__bilateral\'}[r[\'fold\']]]\n require(len(rows)==4 and len({r[\'run\'] for r in rows})==4,\'four fixed own-fold trace cases\')\n return runs,rows')
change('def predict_once(torch,model,x):','def predict_once(torch,model,x):\n global LAST_TRACE')
change(' with torch.inference_mode():',' with TraceCapture(model) as capture, torch.inference_mode():')
change('  return dense.detach().cpu().numpy().copy()','  value=dense.detach().cpu().numpy().copy()\n LAST_TRACE=capture.arrays\n require(LAST_TRACE[\'fps512_indices\'].shape==(1,512) and LAST_TRACE[\'fps256_indices\'].shape==(1,256),\'actual FPS shapes\')\n return value')
change(" I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])"," global TraceCapture\n I=q['identity'];out=clean(q['output']);root=clean(q['model_root'])\n TraceCapture=module('actual_trace_capture',q['trace_capture']).TraceCapture")
change("  policy=make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in rows],[r['checkpoint']['path'] for r in runs],predictions)","  tracefiles=[p.with_name(p.stem+'_trace.npz') for p in predictions]\n  policy=make_policy(helper,[root,envroot,provider,Path(__file__).parent,'/usr/lib','/proc/'+str(os.getpid()),'/dev/null','/dev/urandom'],out,[r['input']['path'] for r in rows],[r['checkpoint']['path'] for r in runs],predictions+tracefiles)")
change("    with path.open('xb') as f:np.savez_compressed(f,prediction=y[0])","    with path.open('xb') as f:np.savez_compressed(f,prediction=y[0])\n    with path.with_name(path.stem+'_trace.npz').open('xb') as f:np.savez_compressed(f,**LAST_TRACE)\n    require(helper.tensor_sha(torch.get_rng_state())==rng_before,'CPU RNG changed during frozen single-case trace')")
change("  require(forwards==420,'exact420 forwards');budget.sample('all_complete',forwards)","  require(forwards==4,'exact four forwards');budget.sample('all_complete',forwards)")
s=s.replace("status='FOUR_MODEL_420_FORWARD_COMPLETE',forwards=420","status='FOUR_MODEL_FOUR_TRACE_COMPLETE',forwards=4").replace("forwards=420,archive=archive","forwards=4,archive=archive").replace('pack(out,predictions+[manifest,done,budget.path])','pack(out,predictions+tracefiles+[manifest,done,budget.path])')
ast.parse(s);entry=N/'bcsp_actual_proxy_trace_v1.py';entry.write_text(s,encoding='utf-8')
remote='/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_actual_proxy_trace_20261102_v1'
def bind(local,dest):return {'path':dest,'bytes':local.stat().st_size,'sha256':sha(local)}
q=json.loads((E/'development_entry_request_v1.json').read_text());q.update(schema='bcsp-actual-proxy-trace-v1',run_id='bcsp_actual_proxy_trace_20261102_v1',entry=bind(entry,remote+'/'+entry.name),trace_capture=bind(N/'trace_capture_v1.py',remote+'/trace_capture_v1.py'),control=remote+'/control',output='/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_geov1/actual_proxy_trace_20261102_v1',launch_attempt=remote+'/control/launch_attempt.json')
q['identity'].update(hostname='shu-common-25721452-notebook-v2iwsa-0',gpu_uuid='GPU-34a1b996-2bd7-88e6-9dca-164b718caea6')
q['environment']['CUDA_VISIBLE_DEVICES']=q['identity']['gpu_uuid'];q['limits']['wall_seconds']=900
q['science'].update(forwards_per_model=1,total_forwards=4,unique_cases=2,unique_sources=2,scope='one fixed own-fold case per model; not cross-fold seen-source inference')
q['science']['actual_trace_fields']='two FPS index/coordinate sets; four graph query/key coordinates and KNN indices; final prediction'
request=N/'trace_execution_request_v1.json';request.write_text(json.dumps(q,indent=2),encoding='utf-8')
mapping=[bind(entry,q['entry']['path']),bind(N/'trace_capture_v1.py',q['trace_capture']['path']),bind(request,remote+'/trace_execution_request_v1.json')]
manifest=N/'transport_manifest_v1.json';manifest.write_text(json.dumps({'status':'AWAITING_MANUAL_UPLOAD_NOT_INSTALLED','no_overwrite':True,'remote_root':remote,'files':mapping,'request_sha256':sha(request),'CPU_contract_count':9,'not_full_GPU_P3':True},indent=2),encoding='utf-8')
archive=N/'actual_proxy_trace_transport_v1.tar.gz'
with tarfile.open(archive,'x:gz') as t:
 for p in [entry,N/'trace_capture_v1.py',request,manifest]:t.add(p,arcname=p.name,recursive=False)
(N/(archive.name+'.sha256')).write_text(sha(archive)+'  '+archive.name+'\n')
print(json.dumps({'request_sha256':sha(request),'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'status':'AWAITING_UPLOAD_AND_EXECUTION_AUTHORIZATION'}))
