"""Prepare RF CPU test v2 and inspect syntax/AST only; never import or run the test."""
from pathlib import Path
import ast
import hashlib
import json

R = Path(__file__).resolve().parent.parent
O = R / 'outputs/scq_rf_implementation_20261114_v1'


def rec(p):
    p = p.resolve()
    return dict(path=str(p), bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def emit(p, value):
    with p.open('x', encoding='utf-8') as f:
        json.dump(value, f, indent=2, allow_nan=False)


prior = json.loads((O / 'static_review_v1.json').read_bytes())
for row in prior['frozen_files']:
    assert rec(Path(row['path']))['sha256'] == row['sha256']
protected = [O / n for n in ('bcsp_scq_rf_residual_v1.py', 'bcsp_scq_rf_factory_v1.py',
                             'initialization_v1.bin', 'initialization_manifest_v1.json',
                             'test_scq_rf_cpu_v1.py', 'cpu_batch_v1/failure_v1.json', 'P3_gap_review_v1.json')]
before = [rec(p) for p in protected]
src = (O / 'test_scq_rf_cpu_v1.py').read_text(encoding='utf-8')
assert hashlib.sha256((O / 'test_scq_rf_cpu_v1.py').read_bytes()).hexdigest() == '9879eee2f2ced66ab49f8d4fb608404deffacc7bf76a78063b70b9ab2dfb2318'


def replace(old, new):
    global src
    assert src.count(old) == 1, old[:100]
    src = src.replace(old, new)


replace('Single retained artificial CPU batch.', 'Version2 retained artificial CPU batch; separately authorized execution only.')
replace("out = O / 'cpu_batch_v1'", "out = O / 'cpu_batch_v2'")
replace("static_review_v1.json", "static_review_v2.json")
replace("failure_v1.json", "failure_v2.json")
replace("result_v1.json", "result_v2.json")
replace('checks, start = [], time.monotonic()', '''checks, start = [], time.monotonic()
    gradient_events = []
    def record_gradients(stage, named_tensors):
        rows = []
        for name, tensor in named_tensors:
            grad = tensor.grad
            present = grad is not None
            finite = present and bool(torch.isfinite(grad).all())
            rows.append(dict(name=name, shape=list(tensor.shape), present=present, finite=finite,
                             nonzero_elements=int(torch.count_nonzero(grad)) if present else None,
                             L1=float(grad.abs().sum()) if finite else None,
                             L2=float(grad.norm()) if finite else None,
                             max_abs=float(grad.abs().max()) if finite else None))
        event = dict(stage=stage, tensors=rows)
        # Persist before assertions; an assertion failure must leave individual evidence.
        with (out / 'gradient_evidence_v2.jsonl').open('a', encoding='utf-8') as f:
            f.write(json.dumps(event, allow_nan=False) + '\\n')
        gradient_events.append(stage)
        return {row['name']: row for row in rows}''')
replace("a(*inputs, N0)[0].square().mean().backward()\n        check('initial V2", "a(*inputs, N0)[0].square().mean().backward()\n        record_gradients('RF_zero_output_initial', list(a.named_parameters()))\n        check('initial V2")
replace("a(*inputs, N0)[0].square().mean().backward()\n        check('nonzero diagnostic V2", "a(*inputs, N0)[0].square().mean().backward()\n        record_gradients('RF_nonzero_diagnostic', list(a.named_parameters()) + list(zip(('M', 'F', 'z', 'Q1'), inputs)))\n        check('nonzero diagnostic V2")
replace('m.base_model.scq.W2.bias.copy_(torch.tensor([.18, -.1, .07]))', '''# Diagnostic artificial model only: open the original first-head hidden gradient.
                m.base_model.scq.W2.weight.copy_(torch.sin(torch.arange(1152).reshape(3, 384)) * .002)
                m.base_model.scq.W2.bias.copy_(torch.tensor([.18, -.1, .07]))''')
replace("parent_groups = [dict(params=[p for p in common if p.ndim > 1], weight_decay=5e-4), dict(params=[p for p in common if p.ndim <= 1], weight_decay=0.)]", '''# Compile the exact inherited grouping function only; no runtime module import/execution.
        runtime_path = R / 'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/bcsp_p1_training_runtime_v1.py'
        runtime_tree = ast.parse(runtime_path.read_text(encoding='utf-8'))
        group_function = next(n for n in runtime_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'optimizer_groups')
        group_scope = dict(require=lambda ok, message: None if ok else (_ for _ in ()).throw(ValueError(message)))
        exec(compile(ast.Module([group_function], []), str(runtime_path) + ':optimizer_groups_only', 'exec'), group_scope)
        inherited_groups = group_scope['optimizer_groups']
        class MarkerFixture(nn.Module):
            def __init__(self):
                super().__init__()
                self.flagged = nn.Parameter(torch.ones(2, 2)); self.flagged._no_weight_decay = True
                self.matrix = nn.Parameter(torch.ones(2, 2))
                self.vector = nn.Parameter(torch.ones(2))
                self.bias_holder = nn.Module()
                self.bias_holder.bias = nn.Parameter(torch.ones(2, 2))
                self.frozen = nn.Parameter(torch.ones(2, 2), requires_grad=False)
        marker_groups, marker_rows = inherited_groups(MarkerFixture())
        marker = {row['name']: row for row in marker_rows}
        with (out / 'inherited_no_decay_evidence_v2.json').open('x', encoding='utf-8') as f:
            json.dump(dict(source_sha256=hashlib.sha256(runtime_path.read_bytes()).hexdigest(), rows=marker_rows), f, indent=2)
        check('exact inherited no-decay marker exempts matrix', marker['flagged']['weight_decay'] == 0 and marker['flagged']['reason'] == 'explicit_no_weight_decay')
        check('inherited vector bias matrix and frozen classification', marker['vector']['weight_decay'] == marker['bias_holder.bias']['weight_decay'] == 0 and marker['matrix']['weight_decay'] == .0005 and 'frozen' not in marker)
        # Mark one artificial shared matrix and verify RF grouping preserves that exact exemption.
        marked_name, marked_parameter = next((n, p) for n, p in model.named_parameters() if id(p) not in ids and p.ndim > 1)
        marked_parameter._no_weight_decay = True
        class CommonView:
            def named_parameters(self):
                return ((n, p) for n, p in model.named_parameters() if id(p) not in ids)
        parent_groups, shared_rows = inherited_groups(CommonView())
        with (out / 'shared_optimizer_policy_evidence_v2.json').open('x', encoding='utf-8') as f:
            json.dump(dict(marked_artificial_parameter=marked_name, rows=shared_rows), f, indent=2)''')
replace("check('both heads weights decay biases no decay', [g['weight_decay'] for g in groups[-4:]] == [5e-4, 0., 5e-4, 0.])", """check('both heads weights decay biases no decay', [g['weight_decay'] for g in groups[-4:]] == [5e-4, 0., 5e-4, 0.])
        check('RF adapter preserves explicit inherited matrix exemption', next(g['weight_decay'] for g in groups if any(p is marked_parameter for p in g['params'])) == 0.)""")
replace("check('original complete loss reaches Q2 and both full heads', ret[0].grad is not None and ret[0].grad.abs().sum() > 0 and all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0 for p in [*base.scq.parameters(), *base.rf.parameters()]))", '''gradient_rows = record_gradients('original_full8192_loss_nonzero_both_heads',
                                        [('Q2', ret[0])] + [('scq.' + n, p) for n, p in base.scq.named_parameters()]
                                        + [('rf.' + n, p) for n, p in base.rf.named_parameters()])
        check('original complete loss reaches Q2', gradient_rows['Q2']['finite'] and gradient_rows['Q2']['nonzero_elements'] > 0)
        for name in ('scq.W1.weight', 'scq.W1.bias', 'scq.W2.weight', 'scq.W2.bias',
                     'rf.V1.weight', 'rf.V1.bias', 'rf.V2.weight', 'rf.V2.bias'):
            row = gradient_rows[name]
            check('original complete loss finite active gradient ' + name, row['finite'] and row['nonzero_elements'] > 0)''')
replace("torch=torch.__version__, initialization_sha256=init['sha256'], artificial_parameter_totals=totals,", "torch=torch.__version__, initialization_sha256=init['sha256'], artificial_parameter_totals=totals,\n                      gradient_events=gradient_events, no_decay_policy='exact inherited optimizer_groups AST; artificial marker and full shared partition',")
replace('Parent optimizer policy retained as supplied; synthetic CPU grouping does not certify native SSM no-decay classification.', 'Exact inherited grouping and explicit marker checked on artificial tensors; actual native SSM parameter object inventory remains for CUDA admission.')
replace("error=repr(exc), traceback=traceback.format_exc()", "error=repr(exc), gradient_events=gradient_events, traceback=traceback.format_exc()")
target = O / 'test_scq_rf_cpu_v2.py'
with target.open('x', encoding='utf-8', newline='\n') as f:
    f.write(src)
# All checks below are syntax, AST, literal source and hash inspections, never test calls.
compile(target.read_bytes(), str(target), 'exec')
tree = ast.parse(target.read_text(encoding='utf-8'))
calls = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, ast.Call)]
assert any('scq.W2.weight.copy_' in c for c in calls)
assert any('scq.W2.bias.copy_' in c for c in calls)
assert any('record_gradients' in c and 'original_full8192_loss_nonzero_both_heads' in c for c in calls)
assert "RF_zero_output_initial" in src and "RF_nonzero_diagnostic" in src
assert "explicit_no_weight_decay" in src and "marked_parameter._no_weight_decay = True" in src
assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'step' for n in ast.walk(tree))
assert [rec(p) for p in protected] == before
assert not (O / 'cpu_batch_v2').exists()
runtime = R / 'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/bcsp_p1_training_runtime_v1.py'
emit(O / 'static_review_v2.json', dict(status='RF_FIXTURE_V2_STATIC_PASS_NOT_CPU_EXECUTED',
     frozen_files=prior['frozen_files'] + [rec(target), rec(runtime)],
     preserved_artifacts=before, diff_from=rec(O / 'test_scq_rf_cpu_v1.py'),
     checks=dict(syntax_pass=True, only_new_test_version=True, original_first_head_nonzero_diagnostic_weight=True,
                 per_parameter_gradient_persisted_before_assertions=True, zero_initial_gradient_expectation_retained=True,
                 exact_inherited_no_decay_function_selected=True, flagged_matrix_and_partition_regressions_defined=True,
                 all_old_sources_and_initialization_unchanged=True, no_optimizer_step_call=True,
                 new_output_not_created=True),
     execution_status='AWAITING_EXPLICIT_USER_AUTHORIZATION', tests_executed=0,
     CPU_validation_result=None, P3_pass=False, CUDA=False, server_operations=0))
scope = dict(status='AWAITING_EXPLICIT_USER_AUTHORIZATION', execution_authorized=False,
             scope='one new artificial CPU validation batch only; fail-stop, no automatic repair/retry',
             test=rec(target), static_review=rec(O / 'static_review_v2.json'),
             python=r'E:\RelocatedData\zhj\.conda\envs\adapointr\python.exe', python_flags=['-I', '-B'],
             output=str(O / 'cpu_batch_v2'), production_and_initialization_unchanged=True,
             no_CUDA=True, no_server=True, no_real_data=True, no_checkpoint=True, optimizer_steps=0,
             post_success='Only review P3 from saved results; no automatic CUDA execution or training')
emit(O / 'CPU_validation_scope_v2.json', scope)
print(json.dumps(dict(status='FIXTURE_V2_STATIC_PASS_NOT_EXECUTED', test=rec(target),
                     pending_scope=rec(O / 'CPU_validation_scope_v2.json'), output_created=False)))
