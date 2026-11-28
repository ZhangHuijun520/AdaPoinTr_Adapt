"""Bounded P3 review and final pending scoring request freeze; no scoring execution."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys
d=Path(__file__).resolve().parent
h=lambda raw:hashlib.sha256(raw).hexdigest()
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=h(p.read_bytes()))
def write(p,value):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
q=json.loads((d/'EJTC_CPU_scoring_request_fixture_v1.json').read_bytes());entry=d/'ejtc_score315_v1.py';cpu=d/'cpu_validation_v1/CPU_validation_receipt_v1.json';c=json.loads(cpu.read_bytes())
assert c['status']=='EJTC_SCORE315_TARGETED_CPU_VALIDATION_PASS' and c['passed']==22 and c['real_prediction_distance_scores']==0 and c['torch_imported'] is False and c['entry']==rec(entry)
assert rec(Path(q['scorer']['path']))==q['scorer'] and q['scorer']['sha256']=='c174aeac1ac58558b2cb00395e96a9d2b36d19d417a2dff5d40a7b18ff9625c6'
assert rec(Path(q['metrics']['path']))==q['metrics'] and q['metrics']['sha256']=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
tree=ast.parse(entry.read_bytes());compile(entry.read_bytes(),str(entry),'exec');compile((d/'verify_ejtc_score315_cpu_v1.py').read_bytes(),'CPU-test','exec')
imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
assert not any('torch' in ast.unparse(n) or 'subprocess' in ast.unparse(n) for n in imports)
attrs=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
assert not set(attrs)&{'forward','backward','step','train','extractall'}
comparison=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='comparison')
assert 'core.summarize' in ast.unparse(comparison) and 'FunctionType' in ast.unparse(comparison)
text=entry.read_text();assert '2026112807' in text and 'v>1.' in text and 'v<=3.' in text
assert not Path(q['output']).exists()
p3=dict(status='EJTC_SCORE315_LIMITED_P3_REVIEW_PASS',review_type='Local bounded source, frozen dependency and CPU evidence review; not an independent external peer review',
 entry=rec(entry),CPU=rec(cpu),unchanged_scorer=q['scorer'],unchanged_metrics=q['metrics'],protocol=q['protocol'],
 checks=['22 targeted CPU checks pass, zero true-case distance scores','Original score_prediction, endpoint, summarize and geometry module reused by exact SHA256; no edits','No model/Torch/network/subprocess or archive extraction in scoring entry','315 model rows, 105 paired cases, 21 sources, J-R/J-T/T-R comparisons','One shared PCG64 seed2026112807, 2000 source bootstrap replicates','Area weighted A1 and A2/world-mm, strict far20 and exact-zero severe definition unchanged','J Cover@1/@3 and (1,3] area are preregistered diagnostics; reuse existing dense distances, preserve original metric outputs','Three-arm alias signs, coverage pp, parent indexing, numeric finiteness, scope and checkpoint identity checked','Actual main, failure evidence, wall/RSS stopping and no-overwrite output checked','Gate decision not executed; no model changes, GPU preflight or training'],
 limits=q['limits'],numeric_versions=q['numeric_versions'],CPU_interpreter=q['interpreter'],real_prediction_scores=0,server_operations=0,limitations=c['limitations'])
p3path=d/'EJTC_CPU_scoring_P3_review_v1.json';write(p3path,p3)
q['CPU_validation']=rec(cpu);q['P3_review']=rec(p3path);q['asset_preparation']=rec(d/'scoring_asset_preparation_receipt_v1.json')
q['runtime_versions']=[sys.version.split()[0],*q['numeric_versions']]
q['expected_outputs']=['model_scores.jsonl','paired_summary.json','diagnostic_summary.json','source_bootstrap_indices.npy','completion.json']
q['execution_policy']='Separately authorize final full SHA256, recheck exact code/interpreter/runtime, all archive/sidecar/audit/reference bindings and fresh output; one local CPU run, stop on failure, no automatic retry. Do not perform formal gate decision or follow-on experiment.'
final=d/'EJTC_RTJ_D_CPU_scoring_execution_request_v1.json';write(final,q);raw=final.read_bytes();rid=h(raw)
spec=importlib.util.spec_from_file_location('score_entry',entry);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
# Exercise final serialized request authorization without writing live authorization material.
w.authorize(json.loads(raw),rid,dict(schema='bcsp-development-authorization-v1',request_sha256=rid,explicit_user_authorization=True,user_authorization_text='Final-byte artificial CPU fixture only '+rid))
with Path(str(final)+'.sha256').open('x',encoding='ascii') as f:f.write(rid+'  '+final.name+'\n')
receipt=dict(status='EJTC_RTJ_CPU_SCORING_FINAL_PENDING_REQUEST_FROZEN',request=rec(final),P3=rec(p3path),CPU=rec(cpu),counts=q['counts'],comparisons=q['comparisons'],bootstrap=q['bootstrap'],limits=q['limits'],final_serialized_authorize_CPU_PASS=True,live_authorization_materialized=False,execution_authorized=False,real_prediction_scores=0,server_operations=0)
write(d/'final_request_freeze_receipt_v1.json',receipt)
print(json.dumps(receipt,ensure_ascii=False))
