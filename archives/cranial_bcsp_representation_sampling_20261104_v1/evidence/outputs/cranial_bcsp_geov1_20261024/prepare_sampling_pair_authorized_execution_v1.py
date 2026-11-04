"""Render the exact authorized prediction controller; no remote calls."""
import ast,base64,datetime,hashlib,json
from pathlib import Path
B=Path(__file__).resolve().parent;N=B/'sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1'
A=N/'authorized_execution_v1';SHA='76673ba94626253161dc70f0a33006d21c8094bced8148496c68c6c3490f0f4c'
def h(b):return hashlib.sha256(b).hexdigest()
def save(n,b):
 with (A/n).open('xb') as f:f.write(b)
def bound(r):
 raw=Path(r['path']).read_bytes();assert len(raw)==r['bytes'] and h(raw)==r['sha256'];return raw
def main():
 raw=(N/'development_execution_request_v1.json').read_bytes();assert h(raw)==SHA;s=json.loads(raw)
 assert s['status']=='AWAITING_EXPLICIT_USER_AUTHORIZATION' and s['execution_authorized'] is False
 entry=bound(s['entry_request']);controller=bound(s['controller_template']);bound(s['local_upload']);bound(s['protocol']);p3=json.loads(bound(s['local_P3']))
 for r in p3['implementation'].values():bound(r)
 bound(p3['CPU_tests']);bound(p3['controller_readback']);bound(p3['input_index']);bound(p3['data_receipt']);bound(p3['reference_manifest'])
 A.mkdir()
 user='已上传，单独授权上述完整哈希。'
 grant=user+'\nReference resolution (not quotation): current paired Fold C prediction execution request SHA256 '+SHA+'; exactly213 exclusive file installs and one210-forward prediction batch; no scoring/BNCal/training/retry.'
 save('explicit_grant.json',json.dumps(dict(schema='bcsp-human-contextual-execution-grant-v1',request_sha256=SHA,user_message_verbatim=user,explicit_user_authorization=True,reference_resolution=grant,recorded_UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()),ensure_ascii=True,indent=2).encode())
 tail='\nimport base64\nrun(base64.b64decode('+repr(base64.b64encode(raw).decode())+'),'+repr(SHA)+',base64.b64decode('+repr(base64.b64encode(entry).decode())+'),base64.b64decode('+repr(base64.b64encode(grant.encode()).decode())+').decode("utf-8"))\n'
 payload=controller+b'\n'+tail.encode('ascii');ast.parse(payload);save('materialize_and_start_once.py',payload)
 tp=B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py';template=tp.read_bytes();assert h(template)=='c705224bc0ffa2e094ff0b4a69ed4ba582480178a63a2bb3fa2e91757e31fd26'
 driver=template.replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',h(payload).encode());ast.parse(driver);save('invoke_short_once.py',driver)
 save('operation_plan_v1.json',json.dumps(dict(request_sha256=SHA,payload_sha256=h(payload),driver_sha256=h(driver),only_one_attempt=True,install_files=213,total_forwards=210,controller_unchanged_sha256=h(controller),not_started=True),indent=2).encode())
 print('AUTHORIZED_PAIR_EXECUTION_RENDERED_NO_SERVER_ACTION')
if __name__=='__main__':main()
