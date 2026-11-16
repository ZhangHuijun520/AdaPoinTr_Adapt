import pathlib,json,sys,importlib.util
HERE=pathlib.Path(__file__).resolve().parent
seq=['01_resource_absence', '02_reused_assets', '03_inputs210', '04_checkpoints', '05_installed15', '06_authorization', '07_runtime', '08_launcher', '09_actual_authorize', '10_single_tmux_launch', '11_startup_observation'];name=sys.argv[1];i=seq.index(name)
for previous in seq[:i]:
 r=json.loads((HERE/(previous+'.result.json')).read_bytes());assert r['returncode']==0 and not r['local_timeout'] and r['rows'],previous
s=importlib.util.spec_from_file_location('remote_call',HERE.parents[1]/'scq_rive_training_implementation_20261115_v1/authorized_training_execution_v1/call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
t.call(name,(HERE/(name+'.source.py')).read_text(encoding='utf-8'),50 if name in ('02_reused_assets','03_inputs210','04_checkpoints','09_actual_authorize') else 30)
