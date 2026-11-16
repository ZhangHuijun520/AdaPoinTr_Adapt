import pathlib,importlib.util,json,sys
HERE=pathlib.Path(__file__).resolve().parent
root=HERE.parents[1]
spec=importlib.util.spec_from_file_location('call_remote',root/'authorized_training_execution_v1'/'call_remote_v1.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);t.HERE=HERE
name=sys.argv[1]
seq=['01_resource_absence','02_assets','03_train315','04_authorization','05_runtime','06_launcher','07_actual_authorize','08_single_tmux_launch','09_startup_observation']
i=seq.index(name)
for previous in seq[:i]:
 r=json.loads((HERE/(previous+'.result.json')).read_text())
 assert r['returncode']==0 and not r['local_timeout'] and r['rows'],previous
source=(HERE/(name+'.source.py')).read_text(encoding='utf-8')
rows=t.call(name,source,50 if name in ('02_assets','03_train315','07_actual_authorize') else 30)
assert rows
