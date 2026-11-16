import pathlib,json,hashlib,sys,importlib.util
HERE=pathlib.Path(__file__).resolve().parent
plan=json.loads((HERE/'bounded_scope_v1.json').read_bytes());name=sys.argv[1];names=[r['stage'] for r in plan['stages']];i=names.index(name)
for prev in names[:i]:
 r=json.loads((HERE/(prev+'.result.json')).read_bytes());assert r['returncode']==0 and not r['local_timeout'] and r['rows'],prev
b=(HERE/(name+'.source.py')).read_bytes();assert hashlib.sha256(b).hexdigest()==plan['stages'][i]['source_sha256']
s=importlib.util.spec_from_file_location('remote_call',HERE.parents[1]/'scq_rive_training_implementation_20261115_v1/authorized_training_execution_v1/call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
rows=t.call(name,b.decode('utf-8'),50);print(json.dumps(dict(stage=name,statuses=[v.get('status') for v in rows])))
