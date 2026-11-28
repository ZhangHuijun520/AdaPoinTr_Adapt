"""Single bounded CPU regression using the unchanged worker's real authorize()."""
from pathlib import Path
import copy,hashlib,importlib.util,json,runpy
d=Path(__file__).resolve().parent
h=lambda b:hashlib.sha256(b).hexdigest()
# d = .../d1_r_d_preparation_v2/transport_h7vvrr_v2
worker=d.parent.parent/'ejtc_train_r_d_v2.py'
assert h(worker.read_bytes())=='0d797a8c0d910d139f0b21186eb35f069f468157babf3fbd9dedf98773199043'
env=runpy.run_path(str(worker),run_name='cpu_contract_validation')
authorize=env['authorize']
spec=importlib.util.spec_from_file_location('materialization_candidate',d/'materialize_rd_authorization_v3.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
qraw=(d.parent/'EJTC_D1_R_D_training_execution_request_h7vvrr_v2.json').read_bytes()
rid=h(qraw);q=json.loads(qraw)
results=[]
def check(name,fn,expected_error=False):
 try:fn()
 except ValueError:
  assert expected_error,name
 else:assert not expected_error,name
 results.append(dict(name=name,passed=True))
old_raw=(d.parent/'failed_authorization_freeze_v2/frozen_remote_files/R_D_authorization_v1.json').read_bytes()
old_runtime=json.loads((d.parent/'failed_authorization_freeze_v2/frozen_remote_files/R_D_runtime_v1.json').read_bytes())
check('frozen_failed_material_reproduces_real_rejection',lambda:authorize(q,rid,json.loads(old_raw),h(old_raw),old_runtime),True)
def validate(text):
 a,r=module.materialize(qraw,text,execution_authorized=True)
 authorize(json.loads(qraw),rid,json.loads(a),h(a),json.loads(r))
 return a,r
check('missing_hash_is_materialized_and_real_authorize_passes',lambda:validate('CPU fixture only, not execution approval'))
check('existing_correct_hash_real_authorize_passes',lambda:validate('CPU fixture '+rid))
a,r=validate('CPU fixture 中文')
check('serialized_authorization_runtime_hash_chain',lambda:authorize(q,rid,json.loads(a),h(a),json.loads(r)))
bad=json.loads(r);bad['authorization_sha256']='0'*64
check('tampered_runtime_hash_rejected',lambda:authorize(q,rid,json.loads(a),h(a),bad),True)
badq=copy.deepcopy(q);badq['arm']='J'
check('wrong_arm_rejected',lambda:authorize(badq,rid,json.loads(a),h(a),json.loads(r)),True)
check('wrong_request_authorization_rejected',lambda:module.materialize(qraw,'CPU fixture '+('0'*64),execution_authorized=True),True)
check('no_new_execution_authorization_rejected',lambda:module.materialize(qraw,'CPU fixture',execution_authorized=False),True)
check('empty_instruction_rejected',lambda:module.materialize(qraw,'',execution_authorized=True),True)
assert module.materialize(qraw,'CPU fixture 中文',execution_authorized=True)==(a,r)
results.append(dict(name='deterministic_exact_byte_materialization',passed=True))
receipt=dict(status='ACTUAL_AUTHORIZE_CPU_REGRESSION_PASS',checks=results,passed=len(results),
 request_sha256=rid,worker_sha256=h(worker.read_bytes()),candidate_sha256=h((d/'materialize_rd_authorization_v3.py').read_bytes()),
 test_sha256=h(Path(__file__).read_bytes()),model_calls=0,server_operations=0,new_execution_authorization=False,
 scope='CPU fixtures only; no live authorization or runtime files generated; existing failed attempt preserved')
with (d/'authorization_materialization_CPU_receipt_v3.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
