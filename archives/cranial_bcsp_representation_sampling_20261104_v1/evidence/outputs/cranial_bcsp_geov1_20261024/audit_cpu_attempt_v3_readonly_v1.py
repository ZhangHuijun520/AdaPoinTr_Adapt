"""Read-only hash/log/AST audit. No imports of tested code, numpy, or torch."""
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
OUT=BASE/'post_test_audit_v3_v1'
ATTEMPT=BASE/'cpu_tensor_attempt_v3'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def read(p):return json.loads(p.read_text(encoding='utf8'))

def check_path(p):
    if not p.resolve().is_relative_to(ROOT.resolve()):raise ValueError('outside project: '+str(p))
    for q in [p]+[q for q in p.parents if q!=ROOT and ROOT in q.parents]:
        if q.lstat().st_file_attributes & 0x400:raise ValueError('reparse point: '+str(q))

def verify(entries, absolute=False):
    rows=[]
    for e in entries:
        p=Path(e['parent_path']) if absolute else ROOT/e['path']
        check_path(p)
        actual=sha(p)
        if actual!=e['sha256']:raise ValueError('hash mismatch: '+str(p))
        if 'bytes' in e and p.stat().st_size!=e['bytes']:raise ValueError('size mismatch: '+str(p))
        rows.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':actual})
    return rows

def main():
    if OUT.exists():raise FileExistsError('audit target already exists')
    # All validation reads happen before creating the new audit report directory.
    manifest=read(BASE/'cpu_tensor_attempt_v3_manifest.json')
    artifact_rows=verify(manifest['files'])
    expected={str((ROOT/e['path']).resolve()) for e in manifest['files']}
    actual={str(p.resolve()) for p in ATTEMPT.rglob('*') if p.is_file()}
    actual.add(str((BASE/'run_cpu_fixture_attempt_v3.py').resolve()))
    if expected!=actual:raise ValueError('strict artifact set mismatch')
    for p in ATTEMPT.rglob('*'):check_path(p)
    fixture_dirs=[p for p in (ATTEMPT/'fixtures').iterdir() if p.is_dir()]
    if len(fixture_dirs)!=18:raise ValueError('fixture directory count mismatch')
    if any(not list(p.iterdir()) for p in fixture_dirs):raise ValueError('empty fixture directory')
    previous=read(BASE/'implementation_candidate_v1_manifest.json')
    failed=read(BASE/'implementation_candidate_v2_failure_freeze_v1.json')
    parents=read(BASE/'consolidated_binding_v1/mother_and_training_design_binding_v1.json')
    prior_rows=verify(previous['files'])+verify(failed['files'])+verify(parents['files'],True)
    result=read(ATTEMPT/'result.json')
    if result!=manifest['results']:raise ValueError('result differs from frozen manifest')
    if sha(ATTEMPT/'result.json')!='c1ca29602d0d99f4fe754158b7757781fc2302f8c42a3acd08d22bae5c529786':
        raise ValueError('result differs from previously reported fingerprint')
    log=(ATTEMPT/'stdout.txt').read_text(encoding='utf8')
    passes=re.findall(r'^(test_\w+) \(([^\r\n]+)\) \.\.\. ok$',log,re.M)
    if len(passes)!=53 or len(set(passes))!=53 or 'Ran 53 tests' not in log or '\nOK\n' not in log:
        raise ValueError('test log count/outcome mismatch')
    if any(x in log for x in ('... skipped','... FAIL','... ERROR','FAILED (')):raise ValueError('test log failed/skipped')
    if (result['tests_run'],result['failures'],result['errors'],result['skipped'])!=(53,0,0,[]):raise ValueError('result counts')
    for key in ('cuda_initialized','real_model_calls','real_data_access','real_optimizer_updates','server_operations','production_edits','training_requests_created'):
        if result[key]:raise ValueError('scope counter not zero: '+key)
    if manifest['process_exit_code']!=0:raise ValueError('recorded process exit not zero')
    # Static-only coverage reconciliation. No compilation/import/execution of candidates/tests.
    sources=[BASE/'implementation_candidate_v1/test_bcsp_adapter.py',BASE/'implementation_candidate_v2/test_cpu_integration_v2.py']
    static_tests=[]
    for path in sources:
        tree=ast.parse(path.read_text(encoding='utf8'))
        for cls in tree.body:
            if isinstance(cls,ast.ClassDef):
                static_tests += [cls.name+'.'+n.name for n in cls.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    if len(static_tests)!=53:raise ValueError('source test count mismatch')
    # Module aliases in the saved log differ from source file names.
    logged={cls.rsplit('.',1)[-1]+'.'+method for method,cls in passes}
    if logged!=set(static_tests):raise ValueError('source/log test identity mismatch')
    report={
        'status':'PASS_READONLY_POST_TEST_FREEZE_AUDIT_WITH_INTEGRATION_GAPS',
        'test_status':'53_PASS_0_FAIL_0_ERROR_0_SKIP',
        'implementation_readiness':'NOT_FULL_P3_NOT_DEPLOYMENT_OR_TRAINING_READY',
        'audit_mode':'hash_bytes_json_log_ast_only_no_candidate_imports',
        'test_reruns':0,'model_calls':0,'GPU_calls':0,'real_dataset_payloads_opened':0,
        'checkpoint_loads':0,'server_operations':0,'implementation_edits':0,
        'artifacts_verified':len(artifact_rows),'prior_and_parent_bindings_verified':len(prior_rows),
        'artifact_exact_set_verified':True,'fixture_directories_retained':18,'fixture_files':sum(p.is_file() for p in (ATTEMPT/'fixtures').rglob('*')),
        'total_artifact_bytes':sum(r['bytes'] for r in artifact_rows),
        'test_log_counts_and_static_identities_match':True,
        'exit_code_evidence':'Prior execution tool reported 0 (chunk 221f9a); existing manifest records 0. This audit did not execute tests or independently reproduce exit code.',
        'execution_count_evidence':'One prior versioned attempt recorded; audit cannot forensically exclude every unrecorded process.',
        'scope_counters_evidence':'Consistent with runner/test source and saved result; not an OS-wide activity trace.',
        'coverage_limits':[
            'Actual PyTorch CPU tensor KNN exercised, including 16k keys and only 257 queries in bounded oracle comparison; not B8 full 16k self-KNN runtime/VRAM test',
            'One synthetic DataLoader traversal (315 records/39 batches); records reuse one synthetic source/NPZ, not 63 real sources',
            'Remaining traversals validate counter protocol using range batches; fake optimizer, not real optimizer state/NN updates',
            'Candidate direct KNN function tested, fork patch not applied to an actual AdaPoinTr module',
            'No full model/production runner, loss/backward/clip/scheduler/checkpoint lifecycle tested',
            'No CUDA FPS/KNN equivalence, AMP/deterministic GPU contract, or VRAM certificate',
        ],
        'remaining_integration_gaps':[
            {'id':'I1','scope':'Isolated BCSP production-call-chain candidate','needed':'Explicit new-stage runner and dataset/builder selection, apply hash-bound KNN replacement in candidate fork only; no edits to frozen parents/legacy paths. CPU facade is not a deployed registry/runner.'},
            {'id':'I2','scope':'Training lifecycle semantics','needed':'Bind exact common data/order and actual optimizer/model lifecycle, seed/determinism, loss/backward/clip, LR/BN scheduler invocation, final-only checkpoint and completion receipt. Guard callback counts are not independent observation of optimizer.step.'},
            {'id':'I3','scope':'Data readiness, separate from implementation','needed':'New BCSP source-level derived assets, world frame/normalization QC, common GT and hashes, source/fold allowlists; 315-case guard only validates conditional design, not actual source semantics.'},
            {'id':'I4','scope':'GPU readiness, separately authorized','needed':'Artificial zero-update real-model path, CUDA operators/equivalence and bounded resource check; no inference from CPU success.'},
        ],
        'nonblocking_caveats':[
            'NPZ whole-file hashing reads bytes of GT members even during inference, though GT arrays are not decoded/used to construct input. Semantic GT independence test does not prove no GT bytes were read.',
            'Schema/frame strings are asserted metadata, not geometric truth certificates.',
            'Counter guard cannot roll back a failed optimizer or prevent arbitrary trusted callback from stepping independently.',
            'CPU entry hard-binds local parent paths and torch CPU device; it is validation scaffolding, not server-portable production entry.',
        ],
        'next_recommended_scope':'One bounded isolated integration-only closure for I1/I2 with artificial CPU call-chain tests; do not expand generic framework. Keep I3/I4 separate; do not create training execution request yet.',
        'artifact_rows':artifact_rows,'prior_and_parent_rows':prior_rows,
        'evidence_manifest_sha256':sha(BASE/'cpu_tensor_attempt_v3_manifest.json'),
        'audit_script_sha256':sha(Path(__file__)),
    }
    OUT.mkdir(exist_ok=False)
    with (OUT/'audit_receipt.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2,ensure_ascii=False)
    print(json.dumps({k:report[k] for k in ('status','test_status','implementation_readiness','artifacts_verified','prior_and_parent_bindings_verified','fixture_directories_retained','fixture_files','total_artifact_bytes')},ensure_ascii=False))

if __name__=='__main__':main()
