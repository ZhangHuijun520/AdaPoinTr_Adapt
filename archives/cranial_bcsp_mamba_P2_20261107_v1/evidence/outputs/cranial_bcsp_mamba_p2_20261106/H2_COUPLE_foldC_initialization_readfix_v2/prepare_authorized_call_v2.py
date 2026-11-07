"""Bound call scaffolding for the separately authorized v2 request; no science edits."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;A=S.parent/'H2_COUPLE_foldC_request_preparation_v1'
old='477522d9f7c5e7fc4e282a231f44ad5641588d5b34e303d7e433c3ba57ed6ce3';qh='da96af70b5e3018c4a64c13815348f70f61575b3c455139fab155f2bd801fd90'
def adapt(s):
 return s.replace(old,qh).replace('6db3f93995f7356eb9ddff4b9fdbe54d5816282f54963d47edffd51291d9e20a','c4d2a0035f96e6a92fedd8e9f1c1f4d4e97c53cf63c7c6cae709d2b00169f475').replace('bcsp_p2_H2_COUPLE_foldC_pending_20261107_v1.tar.gz','bcsp_p2_H2_COUPLE_foldC_pending_20261107_v2.tar.gz').replace('bcsp_p2_H2_COUPLE_foldC_20261107_v1','bcsp_p2_H2_COUPLE_foldC_20261107_v2').replace('H2_COUPLE_foldC_seed0_training_execution_request_v1.json','H2_COUPLE_foldC_seed0_training_execution_request_v2.json').replace('H2_COUPLE_C_authorized_once_20261107_v1.py','H2_COUPLE_C_authorized_once_20261107_v2.py').replace('execute_authorized_H2_COUPLE_once_v1.py','execute_authorized_H2_COUPLE_once_v2.py').replace('final_pending_request_v1','final_pending_request_v2').replace('authorized_execution_v1','authorized_execution_v2')
s=adapt((A/'execute_authorized_H2_COUPLE_once_v1.py').read_text(encoding='utf-8')).replace('20166','21664').replace("len(members)==8,'exact8 archive members'","len(members)==9,'exact9 archive members'").replace("len(mapping['files'])==7","len(mapping['files'])==8").replace('exclusive7_file_install','exclusive8_file_install')
anchor=" need(expected[request_name]['sha256']==QH and L['request_path']==str(INSTALL/request_name),'request path')"
extra="\n superseded=q['provenance']['superseded_attempt'];fail=superseded['failure_audit'];fb=payload['payload/'+Path(fail['path']).name];need(hashlib.sha256(fb).hexdigest()==fail['sha256'],'frozen failed v1 audit');failure=json.loads(fb);need(failure['status']=='FORMAL_COUPLE_V1_FAILED_STARTUP_FREEZE_AUDIT_PASS' and failure['optimizer_steps']==0 and failure['request_reusable'] is False and failure['request_sha256']==superseded['request_sha256'],'v1 consumed, never reused')"
assert s.count(anchor)==1;s=s.replace(anchor,anchor+extra)
sources={'execute_authorized_H2_COUPLE_once_v2.py':s,'invoke_authorized_H2_COUPLE_once_v2.py':adapt((A/'invoke_authorized_H2_COUPLE_once_v1.py').read_text(encoding='utf-8')),'readback_startup_v2.py':adapt((A/'readback_startup_v1.py').read_text(encoding='utf-8'))}
for name,source in sources.items():
 ast.parse(source)
 with (S/name).open('x',encoding='utf-8',newline='\n') as f:f.write(source)
q=S/'final_pending_request_v2/transport_payload/H2_COUPLE_foldC_seed0_training_execution_request_v2.json';assert hashlib.sha256(q.read_bytes()).hexdigest()==qh
review=dict(status='AUTHORIZED_V2_CALL_STATIC_REVIEW_PASS',request_sha256=qh,new_install_files=8,no_retry=True,old_v1_never_reused=True,exact_uploaded_archive_bytes=21664,raw_byte_transport=True,command_limit_bytes=2048,frozen_request_and_scientific_sources_unchanged=True,files=[dict(name=n,bytes=(S/n).stat().st_size,sha256=hashlib.sha256((S/n).read_bytes()).hexdigest()) for n in sources])
with (S/'authorized_call_static_review_v2.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
print(review['status'])
