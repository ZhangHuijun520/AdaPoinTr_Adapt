import pathlib,sys,json,hashlib,importlib.util
HERE=pathlib.Path(__file__).resolve().parent
root=HERE.parents[1];plan=json.loads((HERE/'installation_call_plan_v1.json').read_text());name=sys.argv[1];names=[r['stage'] for r in plan['calls']];i=names.index(name)
for j,previous in enumerate(names[:i]):
 r=json.loads((HERE/(previous+'.result.json')).read_text());assert r['returncode']==0 and not r['local_timeout'] and any(x.get('status')==plan['calls'][j]['success'] for x in r['rows'])
c=plan['calls'][i];b=(HERE/(name+'.source.py')).read_bytes();assert hashlib.sha256(b).hexdigest()==c['source_sha256']
s=importlib.util.spec_from_file_location('remote_call',root/'authorized_training_execution_v1'/'call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
rows=t.call(name,b.decode('utf-8'),c['seconds']);assert any(x.get('status')==c['success'] for x in rows)
if i==2:
 r=next(x for x in rows if x.get('status')==c['success']);assert len(r['files'])==2 and r['tests']==r['training']==0
