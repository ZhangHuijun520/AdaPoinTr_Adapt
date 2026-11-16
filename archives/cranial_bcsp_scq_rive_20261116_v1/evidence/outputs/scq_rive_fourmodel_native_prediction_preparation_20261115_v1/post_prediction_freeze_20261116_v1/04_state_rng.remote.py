from pathlib import Path, PurePosixPath
import json, hashlib, os, socket, math
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1')
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_fourmodel_native_development_20261115_v1')
b = (I / 'RIVE_fourmodel_native_prediction_execution_request_v1.json').read_bytes()
assert hashlib.sha256(b).hexdigest() == 'ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q = json.loads(b)
done = json.loads((O / 'inference_complete.json').read_bytes())
labels = ['Static_C', 'Requery_C', 'Static_D', 'Requery_D']
assert done['status'] == 'SCQ_RIVE_FOURMODEL_420_NATIVE_FORWARD_COMPLETE' and done['forwards'] == 420 and (done['request_sha256'] == hashlib.sha256(b).hexdigest())
assert all((done[k] == 0 for k in ('training_updates', 'BNCal', 'loss', 'backward', 'context_cases', 'trace_cases')))
assert [s['run'] for s in done['models']] == labels
rows = []
for s in done['models']:
    assert s['forwards'] == 105 and s['mode'] == 'eval_inference_mode' and all((s[k] == 0 for k in ('BNCal', 'optimizer', 'backward')))
    assert s['state_before'] == s['state_after'] and len(s['state_before']) == 64
    (a, z) = (s['RNG_before'], s['RNG_after'])
    assert a == z and set(a) == {'CPU', 'CUDA', 'Python', 'numpy'} and all((isinstance(v, str) and v for v in a.values())) and (len(a['CPU']) == len(a['CUDA']) == 64)
    rf = s['construction']['rf']
    assert rf['variant'] == ('RF-Static' if s['run'].startswith('Static') else 'RF-Requery') and rf['additional_parameters'] == 231171 and (rf['total_parameters'] == 40827847) and rf['common_state_preserved'] and rf['CPU_RNG_preserved'] and (rf['initialization_sha256'] == q['rf_initialization']['sha256'])
    rows.append(dict(run=s['run'], forwards=105, state_before=s['state_before'], state_after=s['state_after'], RNG_before_sha256=hashlib.sha256(json.dumps(a, sort_keys=True).encode()).hexdigest(), RNG_after_sha256=hashlib.sha256(json.dumps(z, sort_keys=True).encode()).hexdigest()))
print(json.dumps(dict(status='FOUR_MODEL_STATE_RNG_PASS', models=rows, forward=420, server_writes=0)))
