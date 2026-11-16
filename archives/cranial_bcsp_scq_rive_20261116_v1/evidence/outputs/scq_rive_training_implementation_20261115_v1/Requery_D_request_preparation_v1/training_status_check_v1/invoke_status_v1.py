import pathlib,importlib.util
HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('remote_call',HERE.parents[1]/'authorized_training_execution_v1'/'call_remote_v1.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t);t.HERE=HERE
t.call('01_readonly_status',(HERE/'status_source_v1.py').read_text(encoding='utf-8'),30)
