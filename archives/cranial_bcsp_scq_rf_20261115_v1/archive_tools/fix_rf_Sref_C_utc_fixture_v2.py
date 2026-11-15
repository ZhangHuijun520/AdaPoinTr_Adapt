"""Only supply utc to the artificial policy class environment; version the CPU test."""
from pathlib import Path
import hashlib,json

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1'
old=O/'test_scq_rf_Sref_C_entry_cpu_v1.py';new=O/'test_scq_rf_Sref_C_entry_cpu_v2.py'


def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


prior=json.loads((O/'P3_gap_review_v1.json').read_bytes())
for key in ('entry','bridge','test','unchanged_runtime','unchanged_contract','failure','child_stderr','child_stdout'):
    assert rec(Path(prior[key]['path']))==prior[key]
src=old.read_text(encoding='utf-8')
assert src.count("D=O/'cpu_entry_batch_v1'")==1 and src.count('env=dict(base_policy=base_policy,guard=guard)')==1
updated=src.replace("D=O/'cpu_entry_batch_v1'","D=O/'cpu_entry_batch_v2'").replace('env=dict(base_policy=base_policy,guard=guard)','env=dict(base_policy=base_policy,guard=guard,utc=utc)')
compile(updated,str(new),'exec')
with new.open('x',encoding='utf-8',newline='\n') as f:f.write(updated)
assert updated.replace("D=O/'cpu_entry_batch_v2'","D=O/'cpu_entry_batch_v1'").replace('env=dict(base_policy=base_policy,guard=guard,utc=utc)','env=dict(base_policy=base_policy,guard=guard)')==src
review=dict(status='RF_SREF_UTC_FIXTURE_V2_STATIC_PASS_NOT_EXECUTED',test=rec(new),previous_test=rec(old),preserved=prior,
            changes=['Artificial child exec env adds existing utc object','New output cpu_entry_batch_v2 only'],
            entry_and_bridge_unchanged=True,production_unchanged=True,old_failure_preserved=True,CPU_tests=0,server_operations=0,CUDA_calls=0)
with (O/'fixture_v2_static_review.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
print(json.dumps(dict(status=review['status'],test_SHA256=rec(new)['sha256'])))
