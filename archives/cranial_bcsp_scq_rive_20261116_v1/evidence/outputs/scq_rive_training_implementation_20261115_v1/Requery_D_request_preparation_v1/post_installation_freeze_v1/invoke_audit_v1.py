import pathlib,importlib.util
HERE=pathlib.Path(__file__).resolve().parent
root=HERE.parents[1]
s=importlib.util.spec_from_file_location('remote_call',root/'authorized_training_execution_v1'/'call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
rows=t.call('01_formal_audit',(HERE/'audit_source_v1.py').read_text(encoding='utf-8'),30)
assert len(rows)==1 and rows[0]['status']=='TWOFILE_FORMAL_POST_INSTALLATION_AUDIT_PASS'
