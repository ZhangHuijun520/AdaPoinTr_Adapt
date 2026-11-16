import pathlib,json,sys,hashlib,importlib.util
HERE=pathlib.Path(__file__).resolve().parent
W=HERE.parents[1];scope=json.loads((HERE/'bounded_readiness_scope_v1.json').read_text());name=sys.argv[1];names=[r['stage'] for r in scope['stages']];i=names.index(name)
for previous in names[:i]:
 r=json.loads((HERE/(previous+'.result.json')).read_text());assert r['returncode']==0 and not r['local_timeout'] and r['rows']
b=(HERE/(name+'.source.py')).read_bytes();assert hashlib.sha256(b).hexdigest()==scope['stages'][i]['source_sha256']
s=importlib.util.spec_from_file_location('remote_call',W/'scq_rive_training_implementation_20261115_v1/authorized_training_execution_v1/call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
t.call(name,b.decode('utf-8'),50)
