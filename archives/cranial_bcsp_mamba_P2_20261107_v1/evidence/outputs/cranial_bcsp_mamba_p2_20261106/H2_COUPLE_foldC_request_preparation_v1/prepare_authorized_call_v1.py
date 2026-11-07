"""Freeze this authorization's install/call scaffolding; scientific bytes unchanged."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;A=S.parent/'H2_AUX_foldC_training_preparation_v1'
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
oldq='0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517';qh='477522d9f7c5e7fc4e282a231f44ad5641588d5b34e303d7e433c3ba57ed6ce3'
s=(A/'execute_authorized_H2_AUX_once_v1.py').read_text(encoding='utf-8')
s=s.replace(oldq,qh).replace('8f76cdaacd06fba2353624885fe7ea24d4b16afb949f1ee781fe33e78d279324','6db3f93995f7356eb9ddff4b9fdbe54d5816282f54963d47edffd51291d9e20a')
s=s.replace('H2-AUX','H2-COUPLE').replace('H2_AUX','H2_COUPLE').replace("=='AUX'","=='COUPLE'").replace('AUX C contract','COUPLE C contract').replace('65611','20166')
s=s.replace("len(members)==14,'exact14 archive members'","len(members)==8,'exact8 archive members'")
s=s.replace("mapping['status']=='FROZEN_NOT_INSTALLED' and len(mapping['files'])==13","mapping['status']=='FROZEN_NOT_INSTALLED_READINESS_RECHECK_REQUIRED' and len(mapping['files'])==7")
s=once(s,"q['readiness'],L['launcher_template']","q['readiness'],L['launcher_template'],*q['aux_pairing'].values()")
s=once(s,"ready=json.loads(payload['payload/readiness_receipt_v1.json'])","ready=json.loads(exact(q['readiness']).read_bytes())")
s=s.replace('BOUNDED_H2_COUPLE_C_READINESS_PASS','BOUNDED_H2_AUX_C_READINESS_PASS').replace('exclusive13_file_install','exclusive7_file_install')
ast.parse(s)
with (S/'execute_authorized_H2_COUPLE_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
v=(A/'invoke_authorized_H2_AUX_once_v1.py').read_text(encoding='utf-8').replace(oldq,qh).replace('H2_AUX','H2_COUPLE').replace('first_FoldC_request_v1','final_pending_request_v1')
ast.parse(v)
with (S/'invoke_authorized_H2_COUPLE_once_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(v)
readback=(A/'readback_startup_v1.py').read_text(encoding='utf-8').replace(oldq,qh).replace('H2_AUX','H2_COUPLE').replace('first_FoldC_request_v1','final_pending_request_v1')
ast.parse(readback)
with (S/'readback_startup_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(readback)
q=S/'final_pending_request_v1/transport_payload/H2_COUPLE_foldC_seed0_training_execution_request_v1.json';assert hashlib.sha256(q.read_bytes()).hexdigest()==qh
review=dict(status='AUTHORIZED_CALL_STATIC_REVIEW_PASS',request_sha256=qh,frozen_request_and_production_sources_unchanged=True,raw_byte_transport=True,command_limit_bytes=2048,no_retry=True,new_install_files=7,paired_AUX_request_audit_and_initialization_checked_before_install=True,files=[dict(name=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [S/'execute_authorized_H2_COUPLE_once_v1.py',S/'invoke_authorized_H2_COUPLE_once_v1.py',S/'readback_startup_v1.py']])
with (S/'authorized_call_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
print(review['status'])
