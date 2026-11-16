import pathlib,importlib.util,sys,json
HERE=pathlib.Path(__file__).resolve().parent
root=HERE.parents[1]
plan=json.loads((HERE/'audit_plan_v1.json').read_text())
names=[r['stage'] for r in plan['stages']];name=sys.argv[1];i=names.index(name)
for prev in names[:i]:
 r=json.loads((HERE/(prev+'.result.json')).read_text());assert r['returncode']==0 and not r['local_timeout'] and r['rows']
s=importlib.util.spec_from_file_location('remote_call',root/'authorized_training_execution_v1'/'call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
t.call(name,(HERE/(name+'.source.py')).read_text(encoding='utf-8'),50)
