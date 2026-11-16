import pathlib,json,hashlib,sys,importlib.util
HERE=pathlib.Path(__file__).resolve().parent
name=sys.argv[1];plan=json.loads((HERE/'call_static_review_v1.json').read_bytes());names=[r['stage'] for r in plan['calls']];i=names.index(name)
if i:
 r=json.loads((HERE/(names[0]+'.result.json')).read_bytes());assert r['returncode']==0 and not r['local_timeout'] and r['rows'][0]['status']=='FOUR_UPLOADED_FILES_PASS'
b=(HERE/(name+'.source.py')).read_bytes();assert hashlib.sha256(b).hexdigest()==plan['calls'][i]['source_sha256']
s=importlib.util.spec_from_file_location('remote_call',HERE.parents[1]/'scq_rive_training_implementation_20261115_v1/authorized_training_execution_v1/call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
t.call(name,b.decode('utf-8'),30)
