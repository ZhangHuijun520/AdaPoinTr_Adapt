"""Correct local Windows LF/CRLF hash binding; remote payload bytes unchanged."""
import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;B=N.parent
payload=(N/'server_readiness_payload_v1.py').read_bytes()
template=B/'resource_rebind_implementation_v1/first_training_request_foldC_8192_v1/local_byte_serialization_v2/short_driver_template_v2.py'
driver=template.read_bytes().replace(b'__DERIVED_CONTROLLER_PAYLOAD_SHA256__',hashlib.sha256(payload).hexdigest().encode())
assert hashlib.sha256(payload).hexdigest().encode() in driver
with (N/'server_readiness_short_driver_v2.py').open('xb') as f:f.write(driver)
s=(N/'invoke_server_readiness_v1.py').read_text().replace('server_readiness_short_driver_v1.py','server_readiness_short_driver_v2.py')
for stem in ['server_readiness_attempt','server_readiness_capture','server_readiness_events','server_readiness_report']:s=s.replace(stem+'_v1',stem+'_v2')
with (N/'invoke_server_readiness_v2.py').open('x') as f:f.write(s)
with (N/'readiness_byte_binding_diagnosis_v2.json').open('x') as f:json.dump(dict(status='LOCAL_BYTE_BINDING_FIXED',actual_payload_sha256=hashlib.sha256(payload).hexdigest(),prior_driver_unchanged=False,reason='Windows text write changed LF to CRLF; bind original file bytes rather than source.encode()',remote_payload_changed=False,server_report_in_v1=False,network_invocation_not_reached_in_v1=True),f,indent=2)
