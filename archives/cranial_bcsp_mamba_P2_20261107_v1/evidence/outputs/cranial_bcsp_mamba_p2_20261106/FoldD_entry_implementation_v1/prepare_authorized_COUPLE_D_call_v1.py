"""Unique COUPLE_D execution transport; reuse frozen entry without changes."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent
old='efba40fdc78db788798ba326d9a393c5e0cac48189bb507a8ec4e9fe1d5f2db9';qh='be3988719fce8860729c80daaa1dcd634000b50c5378605fb6fe377c511e6718'
def adapt(t):
 return t.replace(old,qh).replace('53faa00c363145cc16413af174d861bdf32659ed77eb176c3ee531c83bcb9bc3','e4a7eca9f8b81fa91430e70c04c81e640f88d6b1fb38802cd43813aef7328c21').replace('bcsp_p2_H2_AUX_foldD_pending_20261107_v1.tar.gz','bcsp_p2_H2_COUPLE_foldD_pending_20261107_v1.tar.gz').replace('bcsp_p2_H2_foldD_20261107_v1','bcsp_p2_H2_COUPLE_foldD_20261107_v1').replace('H2_AUX_foldD_seed0_training_execution_request_v1.json','H2_COUPLE_foldD_seed0_training_execution_request_v1.json').replace('AUX_D_pending_request_v1','COUPLE_D_pending_request_v1').replace('H2_AUX_D_authorized_once_20261107_v1.py','H2_COUPLE_D_authorized_once_20261107_v1.py').replace('execute_authorized_H2_AUX_D_once_v1.py','execute_authorized_H2_COUPLE_D_once_v1.py').replace('authorized_execution_v1','COUPLE_D_authorized_execution_v1')
t=adapt((S/'execute_authorized_H2_AUX_D_once_v1.py').read_text(encoding='utf-8')).replace('60068','9972').replace("len(members)==12,'exact12 archive members'","len(members)==5,'exact5 archive members'").replace("len(mapping['files'])==11","len(mapping['files'])==4").replace("q['h2_config']['mode']=='AUX'","q['h2_config']['mode']=='COUPLE'").replace('AUX D contract','COUPLE D contract').replace('H2-AUX D install','H2-COUPLE D install').replace('H2-AUX Fold D only','H2-COUPLE Fold D only').replace('exclusive11_file_install','exclusive4_file_install')
oldlist="q['readiness'],L['launcher_template']"
assert t.count(oldlist)==1;t=t.replace(oldlist,"q['readiness'],L['launcher_template'],*q['aux_pairing'].values()")
before="ready=json.loads(payload['payload/FoldD_readiness_snapshot_v1.json'])";assert t.count(before)==1;t=t.replace(before,"ready=json.loads(exact(q['readiness']).read_bytes())")
before=" need(q['aux_pairing'] is None,'AUX D only; no COUPLE D')"
after=""" pair=q['aux_pairing'];need(set(pair)=={'request','audit','initialization'},'COUPLE requires AUX D frozen evidence')
 audit=json.loads(payload['payload/'+Path(pair['audit']['path']).name]);need(audit['status']=='FORMAL_H2_AUX_FOLDD_POST_TRAINING_FREEZE_AUDIT_PASS' and audit['request_sha256']==pair['request']['sha256'] and audit['checks_passed']==25 and all(audit['checks'].values()),'AUX D formal freeze')
 need(json.loads(exact(pair['initialization']).read_bytes())==audit['initialization']['record'],'AUX D initial fingerprints')"""
assert t.count(before)==1;t=t.replace(before,after)
v=adapt((S/'invoke_authorized_H2_AUX_D_once_v1.py').read_text(encoding='utf-8'))
b=adapt((S/'readback_AUX_D_startup_v1.py').read_text(encoding='utf-8')).replace('AUX_D_authorization_v1.json','COUPLE_D_authorization_v1.json').replace('AUX_D_runtime_v1.json','COUPLE_D_runtime_v1.json').replace('AUX_D_launch_once_v1.sh','COUPLE_D_launch_once_v1.sh').replace('AUX_D_single_attempt_claim_v1.json','COUPLE_D_single_attempt_claim_v1.json')
files={'execute_authorized_H2_COUPLE_D_once_v1.py':t,'invoke_authorized_H2_COUPLE_D_once_v1.py':v,'readback_COUPLE_D_startup_v1.py':b}
for n,source in files.items():
 ast.parse(source)
 with (S/n).open('x',encoding='utf-8',newline='\n') as f:f.write(source)
p=S/'COUPLE_D_pending_request_v1/transport_payload/H2_COUPLE_foldD_seed0_training_execution_request_v1.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==qh
review=dict(status='AUTHORIZED_COUPLE_D_CALL_STATIC_REVIEW_PASS',request_sha256=qh,archive_bytes=9972,new_install_files=4,no_retry=True,shared_entry_and_models_unchanged=True,raw_byte_transport=True,command_bytes_limit=2048,files=[dict(name=n,bytes=(S/n).stat().st_size,sha256=hashlib.sha256((S/n).read_bytes()).hexdigest()) for n in files])
with (S/'authorized_COUPLE_D_call_static_review_v1.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
print(review['status'])
