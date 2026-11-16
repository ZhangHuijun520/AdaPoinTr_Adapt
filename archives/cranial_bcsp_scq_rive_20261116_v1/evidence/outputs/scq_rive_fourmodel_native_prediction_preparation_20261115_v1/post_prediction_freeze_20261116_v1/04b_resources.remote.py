from pathlib import Path, PurePosixPath
import json, hashlib, os, socket, math
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
I = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rive_fourmodel_prediction_20261115_v1')
O = Path('/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RIVE_fourmodel_native_development_20261115_v1')
b = (I / 'RIVE_fourmodel_native_prediction_execution_request_v1.json').read_bytes()
assert hashlib.sha256(b).hexdigest() == 'ef7c777af6fceb6836de2516de9bf10b1fc4c7603d71c33de53ef024f167f774'
q = json.loads(b)
labels = ['Static_C', 'Requery_C', 'Static_D', 'Requery_D']
expected = []
n = 0
for label in labels:
    expected.append(('model_start:' + label, n))
    for j in range(105):
        expected.extend([('before_forward', n), ('after_forward', n + 1)])
        n += 1
expected.append(('all_complete', 420))
rs = [json.loads(s) for s in (O / 'resources.jsonl').read_text().splitlines()]
assert len(rs) == len(expected) == 845
L = q['limits']
peaks = {}
minimum = 2 ** 63
last = 0
for (r, e) in zip(rs, expected):
    assert (r['phase'], r['forwards']) == e and r['PID_policy'] == 'DIAGNOSTIC_ONLY_NO_OWNERSHIP_GUARANTEE'
    v = r['values']
    cs = dict(RSS=v['RSS_bytes'] <= L['RSS_bytes'], output=v['output_bytes'] <= L['output_bytes'], device=v['device_MiB'] <= L['device_MiB'], allocated=v['peak_allocated'] <= L['torch_peak_bytes'], reserved=v['peak_reserved'] <= L['torch_peak_bytes'], wall=v['elapsed_seconds'] <= L['wall_seconds'], disk=v['free_disk_bytes'] >= L['minimum_free_disk_bytes'])
    assert cs == r['checks'] and all(cs.values()) and (not r['failed_checks']) and (last <= v['elapsed_seconds'])
    last = v['elapsed_seconds']
    minimum = min(minimum, v['free_disk_bytes'])
    for k in v:
        if k != 'free_disk_bytes':
            peaks[k] = max(peaks.get(k, 0), v[k])
print(json.dumps(dict(status='ALL845_RESOURCES_PASS', resource_records=845, peaks=peaks, minimum_free_bytes=minimum, server_writes=0)))
