"""Prepare bounded post-CUDA success audit from existing readonly collector."""
from pathlib import Path

R=Path(__file__).resolve().parent.parent
S=R/'local_tools'
src=(S/'collect_rf_cuda_failed_freeze_v1.py').read_text(encoding='utf-8')
for old,new in [('scq_rf_cuda_preparation_20261114_v1','scq_rf_initialization_loader_20261114_v2'),
                ('failed_freeze_hook_review_v1','post_CUDA_freeze_audit_v3'),('pending_transport_v1','pending_transport_v3'),
                ('SCQ_RF_artificial_cuda_execution_request_v1.json','SCQ_RF_artificial_cuda_execution_request_v3.json'),
                ('85854f243d29000cc7a0ee87b03f4ce23974fc92d94d6fd479fd695e68c7ab32','8a3d0173fa3cec9e737e384c9af99f37e996c79ef3e60bb5e99b14dc275f2cac'),
                ("root=q['entry']['path'].rsplit('/',1)[0]","root=q['launch_contract']['request_path'].rsplit('/',1)[0]"),
                ('bcsp_scq_rf_artificial_cuda_pending_20261114_v1.tar.gz','bcsp_scq_rf_artificial_cuda_pending_20261114_v3.tar.gz'),
                ('READONLY_FAILURE_FREEZE_AND_HOOK_CONTRACT_SCOPE','READONLY_POST_CUDA_FREEZE_SCOPE'),
                ("(O/'exit_code.txt').read_text().strip()=='1' and (O/'failure.json').is_file() and not (O/'completion.json').exists()", "(O/'exit_code.txt').read_text().strip()=='0' and not (O/'failure.json').exists() and not (O/'monitor_failure.json').exists() and (O/'completion.json').is_file()"),
                ('FAILED_EXIT1_TMUX_AND_WORKER_ABSENT','EXIT0_TMUX_AND_WORKER_ABSENT'),
                ('BOUNDED_STABLE_FAILURE_INVENTORY','BOUNDED_STABLE_POST_CUDA_INVENTORY'),
                ('BOUNDED_FAILURE_METADATA_READ','BOUNDED_POST_CUDA_METADATA_READ'),
                ('READONLY_FAILURE_COLLECTION_COMPLETE','READONLY_POST_CUDA_COLLECTION_COMPLETE'),
                ('before.st_size<=2097152','before.st_size<=8388608'),('p.stat().st_size<=2097152','p.stat().st_size<=8388608')]:
    assert old in src,old
    src=src.replace(old,new)
old="[q['implementation']['scq_factory'],q['implementation']['lqi_decoder'],next(r for r in q['reused_readonly_bindings'] if r['path']==q['model_root']+'/models/AdaPoinTr.py')]"
new="[q['entry'],q['implementation']['rf_factory'],q['rf_initialization'],q['initialization'],q['implementation']['scq_residual'],q['implementation']['scq_factory'],q['implementation']['lqi_decoder'],q['parent_helper']]"
assert src.count(old)==2;src=src.replace(old,new)
target=S/'collect_rf_v3_post_cuda_freeze.py';compile(src,str(target),'exec')
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(src)
print('POST_CUDA_READONLY_COLLECTOR_PREPARED')
