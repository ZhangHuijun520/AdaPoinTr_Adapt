import pathlib,json,importlib.util,sys
HERE=pathlib.Path(__file__).resolve().parent
root=HERE.parents[1];name=sys.argv[1]
assert name in ('01_four_files','02_archive_members')
if name=='02_archive_members':
 r=json.loads((HERE/'01_four_files.result.json').read_text());assert r['returncode']==0 and not r['local_timeout'] and r['rows'][0]['status']=='FOUR_UPLOADED_FILES_PASS'
s=importlib.util.spec_from_file_location('remote_call',root/'authorized_training_execution_v1'/'call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
t.call(name,(HERE/(name+'.source.py')).read_text(encoding='utf-8'),30)
