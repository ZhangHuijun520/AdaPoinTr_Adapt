"""Exercise actual worker.main through startup to a non-CUDA run sentinel."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,importlib.util,json,os,sys
d=Path(__file__).resolve().parent
out=d/'cpu_startup_validation_v2';out.mkdir(exist_ok=False)
h=lambda b:hashlib.sha256(b).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
w=load('worker',d/'ejtc_native_rtj315_v2.py')
q=json.loads((d/'Native315_execution_request_CPU_fixture_v2.json').read_bytes())
scope=json.loads((d/'EJTC_RTJ_D_native315_scope_v2.json').read_bytes())
base=d.parent;project=base.parents[1]
parent_path=base.parent/'bcsp_oasg_20261124_v1/p3_a_d_v1/OASG_A_D_training_execution_request_v1.json'
local={'worker':d/'ejtc_native_rtj315_v2.py','scope':d/'EJTC_RTJ_D_native315_scope_v2.json','parent':parent_path,
 'prefix':base.parent/'bcsp_rbss_20261126_v2/p0b_prefix16_v1/rbss_prefix16_v1.py',
 'native_loader':base.parent/'bcsp_oasg_20261124_v1/skullfix_prediction_v2/oasg_sf_native_v2.py'}
local.update({'receipt_'+arm:Path(r['local_path']) for arm,r in scope['training_freeze_receipts'].items()})
for key,p in local.items():
 old=q['files'][key];raw=p.read_bytes();assert h(raw)==old['sha256'] and len(raw)==old['bytes']
 q['files'][key]['path']=str(p)
q['binding']['output']=str(out/'output')
q['binding']['identity'].update(hostname='CPU_FIXTURE',python_realpath=str(Path(sys.executable).resolve()),python_version=sys.version.split()[0])
for key in ('request','authorization','runtime'):q['launch'][key+'_path']=str(out/(key+'.json'))
raw=json.dumps(q).encode();digest=h(raw)
mat=load('mat',Path(q['authorization_materializer']['local_path']))
auth,runtime=mat.materialize(raw,'Artificial CPU startup only',execution_authorized=True)
for key,data in [('request',raw),('authorization',auth),('runtime',runtime)]:Path(q['launch'][key+'_path']).write_bytes(data)
geo=base.parent/'cranial_bcsp_geov1_20261024';parent=json.loads(parent_path.read_bytes())
mapped={parent['fold']['path']:geo/'consolidated_binding_v1/fold_binding.json',parent['point_manifest']['path']:geo/'real_data_qc_v1/manifest_8192.jsonl'}
mapped.update({r['input']['path']:geo/'real_data_qc_v1/points'/Path(r['input']['path']).name for r in scope['inputs']})
checked=[]
def exact(rec):
 if rec['path'] in {v['path'] for v in scope['checkpoints'].values()}:
  checked.append(('checkpoint_metadata_fixture',rec['path']));return Path(rec['path'])
 p=mapped[rec['path']];assert p.stat().st_size==rec['bytes'] and h(p.read_bytes())==rec['sha256'];checked.append(('actual_local_bytes',rec['path']));return p
original_source=w.source
def source(rec):
 m=original_source(rec)
 if rec==q['files']['prefix']:
  m.load_support=lambda p:SimpleNamespace(exact=exact)
  m.gpu_sample=lambda *a:dict(CPU_GPU_QUERY_FIXTURE=True)
 return m
called=[]
def sentinel(*args):
 called.append(args);assert args[1]==scope and args[3]==digest
 assert (args[2]/'started.json').is_file() and (args[2]/'predictions').is_dir()
w.source=source;w.run=sentinel
w.os=SimpleNamespace(getuid=lambda:q['binding']['identity']['uid'],environ=dict(os.environ,CUDA_VISIBLE_DEVICES=q['binding']['identity']['gpu_uuid']),path=os.path)
w.socket=SimpleNamespace(gethostname=lambda:'CPU_FIXTURE')
argv=['CPU_WORKER']
for key,data in [('request',raw),('authorization',auth),('runtime',runtime)]:argv+=['--'+key,q['launch'][key+'_path'],'--'+key+'-sha256',h(data)]
w.sys=SimpleNamespace(platform='linux',flags=SimpleNamespace(isolated=True,no_site=True),dont_write_bytecode=True,executable=sys.executable,version=sys.version)
original_argv=sys.argv
try:
 sys.argv=argv;w.main()
finally:sys.argv=original_argv
assert len(called)==1 and len(checked)==110
receipt=dict(status='ACTUAL_WORKER_MAIN_CPU_STARTUP_PASS',local_hashed_records=107,checkpoint_metadata_fixtures=3,run_sentinel_calls=1,remote_operations=0,CUDA_calls=0,
 worker_sha256=h((d/'ejtc_native_rtj315_v2.py').read_bytes()),test_sha256=h(Path(__file__).read_bytes()),
 limitations=['Linux identity, GPU sample and checkpoint existence use explicit fixtures','Actual main performs authorization, source binding, receipt pairing, fold selection, 105 local input hashes, fresh output/cache creation and started evidence','run is a non-CUDA sentinel; checkpoint deserialization and observation tested separately in 28-check batch'])
(out/'startup_receipt_v1.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt))
