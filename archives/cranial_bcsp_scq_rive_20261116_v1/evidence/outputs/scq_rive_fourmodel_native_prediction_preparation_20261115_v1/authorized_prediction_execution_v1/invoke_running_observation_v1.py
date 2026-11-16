import pathlib,importlib.util
HERE=pathlib.Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('remote_call',HERE.parents[1]/'scq_rive_training_implementation_20261115_v1/authorized_training_execution_v1/call_remote_v1.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t);t.HERE=HERE
t.call('12_actual_prediction_observation',(HERE/'11_startup_observation.source.py').read_text(encoding='utf-8'),30)
