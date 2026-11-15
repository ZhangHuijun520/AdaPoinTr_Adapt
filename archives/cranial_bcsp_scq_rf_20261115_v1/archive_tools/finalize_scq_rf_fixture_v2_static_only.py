"""Finalize unexecuted test fixture v2 hashes after static bias-path review."""
from pathlib import Path
import ast
import hashlib
import json

R = Path(__file__).resolve().parent.parent
O = R / 'outputs/scq_rf_implementation_20261114_v1'


def rec(p):
    return dict(path=str(p.resolve()), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())


test = O / 'test_scq_rf_cpu_v2.py'
compile(test.read_bytes(), str(test), 'exec')
tree = ast.parse(test.read_text(encoding='utf-8'))
src = test.read_text(encoding='utf-8')
assert "self.bias_holder.bias = nn.Parameter" in src
assert "marker['bias_holder.bias']['weight_decay']" in src
assert "m.base_model.scq.W2.weight.copy_" in src
assert "out = O / 'cpu_batch_v2'" in src
assert not (O / 'cpu_batch_v2').exists()
assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'step' for n in ast.walk(tree))
review_path = O / 'static_review_v2.json'
review = json.loads(review_path.read_bytes())
for row in review['preserved_artifacts']:
    assert rec(Path(row['path'])) == row
for row in review['frozen_files']:
    if row['path'] == str(test.resolve()):
        row.update(rec(test))
    else:
        assert rec(Path(row['path'])) == row
review['checks']['bias_fixture_uses_actual_dot_bias_name_contract'] = True
review_path.write_text(json.dumps(review, indent=2, allow_nan=False), encoding='utf-8')
scope_path = O / 'CPU_validation_scope_v2.json'
scope = json.loads(scope_path.read_bytes())
assert scope['status'] == 'AWAITING_EXPLICIT_USER_AUTHORIZATION' and not scope['execution_authorized']
scope['test'] = rec(test)
scope['static_review'] = rec(review_path)
scope_path.write_text(json.dumps(scope, indent=2, allow_nan=False), encoding='utf-8')
print(json.dumps(dict(status='V2_FINAL_STATIC_PASS_NOT_EXECUTED', test=rec(test), pending_scope=rec(scope_path),
                     production_initialization_and_old_failure_unchanged=True, CPU_tests_run=0)))
