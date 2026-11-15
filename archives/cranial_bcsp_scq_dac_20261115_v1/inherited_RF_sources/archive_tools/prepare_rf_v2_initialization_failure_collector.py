"""Prepare the same bounded readonly collector for v2 initialization evidence."""
from pathlib import Path
import ast,hashlib,json

R=Path(__file__).resolve().parent.parent
S=R/'local_tools'
old=S/'collect_rf_cuda_failed_freeze_v1.py'
src=old.read_text(encoding='utf-8')
for a,b in [('scq_rf_cuda_preparation_20261114_v1','scq_rf_cuda_preparation_20261114_v2'),
            ('failed_freeze_hook_review_v1','failed_freeze_initialization_review_v1'),('pending_transport_v1','pending_transport_v2'),
            ('SCQ_RF_artificial_cuda_execution_request_v1.json','SCQ_RF_artificial_cuda_execution_request_v2.json'),
            ('85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32','09de6045f2ecc760558039c2c25724e94eae078b52f744aef6e25574575e1bcf'),
            ('bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz','bcsp_scq_rf_artificial_cuda_pending_20261114_v2.tar.gz'),
            ('READONLY_FAILURE_FREEZE_AND_HOOK_CONTRACT_SCOPE','READONLY_FAILURE_FREEZE_AND_INITIALIZATION_BYTES_CONTRACT_SCOPE')]:
    assert a in src;src=src.replace(a,b)
mapping=json.loads((R/'outputs/scq_rf_cuda_preparation_20261114_v1/pending_transport_v1/installation_mapping_v1.json').read_bytes())
manifest=next(r for r in mapping['files'] if r['member']=='payload/rf_initialization_manifest_v1.json')
record=dict(path=manifest['target'],bytes=manifest['bytes'],sha256=manifest['sha256'])
oldlist="[q['implementation']['scq_factory'],q['implementation']['lqi_decoder'],next(r for r in q['reused_readonly_bindings'] if r['path']==q['model_root']+'/models/AdaPoinTr.py')]"
newlist="[q['implementation']['rf_residual'],q['implementation']['rf_factory'],q['rf_initialization'],"+repr(record)+",q['implementation']['scq_residual']]"
assert src.count(oldlist)==2;src=src.replace(oldlist,newlist)
target=S/'collect_rf_cuda_v2_initialization_failure_v1.py'
compile(src,str(target),'exec')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(src)
print('READONLY_V2_INITIALIZATION_COLLECTOR_PREPARED')
