"""Read-only zip member-name check for the preregistered coarse representatives."""
import json,shlex,subprocess
from pathlib import Path
S=Path(__file__).resolve().parent;F=S/'post_prediction_freeze_audit_v1';q=json.loads((S/'pending_request_v1/transport_payload/H2_C_D_fourmodel_native_prediction_execution_request_v1.json').read_bytes());p=json.loads((S/'pending_request_v1/transport_payload/H2_fourmodel_native_prediction_protocol_v1.json').read_bytes())
expected=sorted('predictions/'+label+'__'+case+'.npz' for label in p['model_order'] for case in p['coarse_tensor_cases_by_fold'][label[0]])
code="import tarfile,zipfile,io,json,socket; assert socket.gethostname()==HOST; found=[]\nwith tarfile.open(ARCHIVE,'r:gz') as t:\n for m in t:\n  if m.name.endswith('.npz'):\n   with zipfile.ZipFile(io.BytesIO(t.extractfile(m).read())) as z:\n    if 'coarse.npy' in z.namelist():found.append(m.name)\nprint(json.dumps(sorted(found)))"
code=code.replace('HOST',repr(q['identity']['hostname'])).replace('ARCHIVE',repr(q['output']+'/development_predictions_v1.tar.gz'));cmd=shlex.join([q['identity']['python_realpath'],'-I','-S','-B','-c',code]);assert len(cmd.encode())<=2048
r=subprocess.run(['wsl.exe','-d','Ubuntu-20.04','--exec','/home/zhj/.local/bin/hpc5000','exec','--timeout','20','--',cmd],capture_output=True,timeout=30)
for k,b in [('stdout',r.stdout),('stderr',r.stderr)]:
 with (F/('coarse_positions_'+k+'.bin')).open('xb') as f:f.write(b)
assert r.returncode==0;actual=json.loads(r.stdout);assert actual==expected and len(actual)==20
with (F/'coarse_positions_receipt_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(status='EXACT20_PREREGISTERED_COARSE_MEMBERS_PASS',members=actual,server_writes=0,new_forward=0),f,indent=2)
print('EXACT20_PREREGISTERED_COARSE_MEMBERS_PASS')
