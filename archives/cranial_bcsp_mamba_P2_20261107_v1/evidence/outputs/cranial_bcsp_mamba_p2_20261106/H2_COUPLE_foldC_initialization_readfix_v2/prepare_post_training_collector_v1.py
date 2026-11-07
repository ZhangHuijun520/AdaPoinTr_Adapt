"""Scope the existing read-only collector to COUPLE v2 and frozen AUX pair."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent;A=S.parent/'H2_AUX_foldC_training_preparation_v1'
text=(A/'collect_post_training_audit_v1.py').read_text(encoding='utf-8')
text=text.replace('H2-AUX outputs','H2-COUPLE v2 outputs').replace('0ca0aeea9f918d037e5cff0e1f0e9af95ed3b17b9979ff63c6789a3672991517','da96af70b5e3018c4a64c13815348f70f61575b3c455139fab155f2bd801fd90').replace('first_FoldC_request_v1','final_pending_request_v2').replace('H2_AUX_foldC_seed0_training_execution_request_v1.json','H2_COUPLE_foldC_seed0_training_execution_request_v2.json').replace("C=S/'authorized_execution_v1/readback'","C=S/'authorized_execution_v2/readback'").replace("S/'server_readiness_v1/readiness_receipt_v1.json'","S.parent/'H2_AUX_foldC_training_preparation_v1/server_readiness_v1/readiness_receipt_v1.json'").replace('REMOTE_H2_AUX_POST_TRAINING_FILES_PASS','REMOTE_H2_COUPLE_POST_TRAINING_PAIR_FILES_PASS')
anchor="def emit(n,v):"
extra='''# Rehash the already-frozen AUX outputs as well, including its checkpoint, without loading it.
A=S.parent/'H2_AUX_foldC_training_preparation_v1'
aq=json.loads((A/'first_FoldC_request_v1/transport_payload/H2_AUX_foldC_seed0_training_execution_request_v1.json').read_bytes())
audit=A/'post_training_freeze_audit_v1/audit_report_v1.json';assert hashlib.sha256(audit.read_bytes()).hexdigest()=='580a0b195c5730e56f260e357e135966e2ab954b9cef7582ff7298b35d33ee1c'
ar=json.loads(audit.read_bytes());assert ar['status']=='FORMAL_H2_AUX_FOLDC_POST_TRAINING_FREEZE_AUDIT_PASS'
for r in ar['files']:add(dict(path=str(PurePosixPath(aq['output'])/r['name']),bytes=r['bytes'],sha256=r['sha256']))
for r in json.loads((A/'post_training_freeze_audit_v1/remote_readonly_receipt_v1.json').read_bytes())['frozen_asset_records']:add(r)
for r in q['aux_pairing'].values():add(r)
'''
assert text.count(anchor)==1;text=text.replace(anchor,extra+anchor)
ast.parse(text)
with (S/'collect_post_training_pair_audit_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
print('READONLY_PAIR_COLLECTOR_STATIC_PASS')
