"""Read saved CPU failure and review P3 gap, no tests or candidate imports."""
from pathlib import Path
import ast,hashlib,json

R=Path(__file__).resolve().parent.parent
O=R/'outputs/scq_rf_Sref_C_training_implementation_20261114_v1'


def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_bytes())


static=read(O/'static_review_v1.json')
for row in [static['entry'],static['bridge'],static['unchanged_runtime'],static['unchanged_contract'],static['base_entry'],static['base_bridge']]:assert rec(Path(row['path']))==row
fail=read(O/'cpu_entry_batch_v1/failure_v1.json');stderr=O/'cpu_entry_batch_v1/policy_stderr.bin'
assert len(fail['checks'])==35 and "NameError: name 'utc' is not defined" in stderr.read_text(encoding='utf-8')
assert not (O/'cpu_entry_batch_v1/result_v1.json').exists()
test=O/'test_scq_rf_Sref_C_entry_cpu_v1.py';src=test.read_text(encoding='utf-8')
assert 'env=dict(base_policy=base_policy,guard=guard)' in src and "utc=types.SimpleNamespace(allow=lambda *a:False)" in src
entry=Path(static['entry']['path']);et=ast.parse(entry.read_text(encoding='utf-8'))
main=next(n for n in et.body if isinstance(n,ast.FunctionDef) and n.name=='main')
text=ast.unparse(main)
assert text.index('utc = timezone.ExactUTCReader')<text.index('class Policy') and 'if utc.allow(filename, write):' in text
p3=dict(status='RF_SREF_C_ENTRY_P3_NOT_PASSED_CPU_POLICY_FIXTURE_FAILURE_STOP',passed_checks=35,
    entry=static['entry'],bridge=static['bridge'],test=rec(test),static_review=rec(O/'static_review_v1.json'),
    failure=rec(O/'cpu_entry_batch_v1/failure_v1.json'),child_stderr=rec(stderr),child_stdout=rec(O/'cpu_entry_batch_v1/policy_stdout.bin'),
    unchanged_runtime=static['unchanged_runtime'],unchanged_contract=static['unchanged_contract'],
    explanation='The CPU child extracts Policy class from main and recompiles it at module scope. Production main defines utc in its enclosing scope; artificial exec env provides base_policy/guard but omits utc. The child NameError occurs before actual source/bin policy read coverage completes.',
    evidence_limits='35 earlier checks do not certify the failed file-policy integration or full CPU/P3 pass. Production policy has not been executed here.',
    next_scope='Only add existing utc object to the artificial child exec environment, version the test/output and run one separately authorized CPU batch; keep entry, bridge, model, runtime and data unchanged.',
    checks=dict(candidate_and_inherited_sources_unchanged=True,original_failure_and_raw_child_output_preserved=True,
                one_CPU_attempt_only=True,no_automatic_repair_retry=True),
    server_operations=0,CUDA_calls=0,training_started=False,execution_request_created=False,controls_materialized=False)
with (O/'P3_gap_review_v1.json').open('x',encoding='utf-8') as f:json.dump(p3,f,indent=2,ensure_ascii=False,allow_nan=False)
print(json.dumps(dict(status=p3['status'],passed_checks=35,request_created=False)))
