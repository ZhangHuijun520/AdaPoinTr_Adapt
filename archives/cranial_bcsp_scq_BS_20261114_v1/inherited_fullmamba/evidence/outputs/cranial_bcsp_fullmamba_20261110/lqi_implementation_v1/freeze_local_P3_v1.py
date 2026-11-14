"""Post-implementation local evidence freeze. No test repeat, arrays, GPU or server."""
import ast,difflib,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;B=S.parent;R=S.parents[2]
def rec(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def read(p):return json.loads(p.read_bytes())
def emit(name,x):
 with (S/name).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def normalized_function_map(source):
 tree=ast.parse(source)
 return {(c.name.replace('LQI','F0'),m.name):m for c in tree.body if isinstance(c,ast.ClassDef) for m in c.body if isinstance(m,ast.FunctionDef)}
def main():
 result=read(S/'artificial_cpu_batch_v1/result.json');static=read(S/'static_review_v1.json');spec=read(B/'query_aligned_condition_spec_v1/formula_interface_freeze_v1.json')
 assert result['status']=='F0_LQI_ARTIFICIAL_CPU_CONTRACT_PASS' and result['count']==len(result['checks'])==55
 assert not (S/'artificial_cpu_batch_v1/failure.json').exists()
 sources=[S/'bcsp_lqi_decoder_v1.py',S/'bcsp_lqi_factory_v1.py',S/'test_lqi_cpu_v1.py']
 assert result['source_records']==static['candidate_sources']==[rec(p) for p in sources]
 assert rec(Path(spec['document']['path']))==spec['document']
 oldpath=B/'implementation_v1/bcsp_f0_decoder_v1.py';oldfactory=B/'implementation_v1/bcsp_f0_factory_v1.py'
 assert rec(oldpath)==spec['parent_decoder']
 old=oldpath.read_text(encoding='utf-8');new=sources[0].read_text(encoding='utf-8')
 before=normalized_function_map(old);after=normalized_function_map(new)
 assert set(before)==set(after)
 for key in before:
  assert ast.dump(before[key].args)==ast.dump(after[key].args)
  if key!=('F0Block','forward'):assert ast.unparse(before[key])==ast.unparse(after[key]).replace('LQIBlock','F0Block')
 x=ast.unparse(before[('F0Block','forward')]);y=ast.unparse(after[('F0Block','forward')])
 assert y.startswith(x[:x.index('prefix =')]) and y[y.index('f = cq'):]==x[x.index('f = cq'):]
 # Factory changes are import dispatch and explicit candidate metadata only.
 a=ast.parse(oldfactory.read_text(encoding='utf-8'));b=ast.parse(sources[1].read_text(encoding='utf-8'))
 def normalize_factory(tree):
  for node in ast.walk(tree):
   if isinstance(node,ast.ImportFrom) and node.module=='bcsp_lqi_decoder_v1':node.module='bcsp_f0_decoder_v1';node.names=[ast.alias(name='F0Decoder',asname=None),ast.alias(name='require',asname=None)]
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='dict':
    node.keywords=[kw for kw in node.keywords if kw.arg not in ('variant','conditional_sequence','trace_prefix_suffix_semantics','additional_learned_parameters')]
    for kw in node.keywords:
     if kw.arg=='version' and isinstance(kw.value,ast.Constant) and kw.value.value=='F0-LQI-implementation-v1':kw.value.value='F0-P-v2-implementation-v1'
  return ast.dump(tree,include_attributes=False)
 assert normalize_factory(a)==normalize_factory(b)
 for p in sources+[Path(__file__)]:compile(ast.parse(p.read_text(encoding='utf-8')),str(p),'exec')
 (S/'factory_delta_v1.diff').write_text(''.join(difflib.unified_diff(oldfactory.read_text(encoding='utf-8').splitlines(True),sources[1].read_text(encoding='utf-8').splitlines(True),fromfile='frozen_F0_factory',tofile='isolated_LQI_factory')),encoding='utf-8')
 emit('post_implementation_P3_v1.json',dict(status='F0_LQI_LOCAL_IMPLEMENTATION_ONLY_P3_PASS',candidate='F0-LQI-v1',scope='Frozen unique formula, two isolated sources, one artificial CPU batch, local static/evidence verification only',
  specification=spec['document'],specification_record=rec(B/'query_aligned_condition_spec_v1/formula_interface_freeze_v1.json'),sources=[rec(p) for p in sources],
  parent_sources=[rec(oldpath),rec(oldfactory),rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_mamba_encoder_v1.py'),rec(R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1/bcsp_p1_model_factory_v1.py')],
  evidence=[rec(S/'static_review_v1.json'),rec(S/'artificial_cpu_batch_v1/result.json'),rec(S/'decoder_delta_v1.diff'),rec(S/'factory_delta_v1.diff')],
  checks=dict(final_source_hashes_equal_static_and_executed_test=True,all55_assertions_pass=True,one_CPU_batch_no_rerun=True,parent_F0_unchanged=True,only_conditional_sequence_and_readout_changed=True,surrounding_forward_graph_AST_identical=True,all_public_method_signatures_preserved=True,factory_delta_only_import_and_explicit_variant_metadata=True,k8_shared_existing_cross_idx=True,batched_formula_independent_reference_all8_layers=True,odd_output_inverse_sort=True,parameters_and_full_state_initialization_identical_artificial_model=True,strict_state_compatibility_both_directions=True,local_graph_F_S_Q_KNN_preserved=True,gradients_X_F_S_Q_PE_norm_v_conditional_mixers_finite_nonzero=True,no_optimizer_step=True,trace_state_RNG_eval_contract=True,candidate_trace_semantics_explicit=True,original_F0_trace_unchanged=True,no_model_or_loss_hyperparameter_changed=True,no_new_attention_or_learned_parameters=True),
  CPU_assertions=55,CPU_seconds=result['seconds'],CPU_torch=result['torch'],real_data_access=False,checkpoint_load=False,CUDA_calls=0,server_operations=0,optimizer_steps=0,execution_request_created=False,
  gaps=['Native Mamba/CUDA forward/backward, actual production loss, peak GPU memory and kernel behavior unverified for the new token layout.','CPU construction exercises the actual factory with an artificial mother fixture; full frozen mother-source/provider loading is not yet run for LQI.','Dedicated zero-update entry and candidate-specific version/read bindings are not implemented or authorized here.','No Native predictions or scientific efficacy evidence for LQI.','No training admission, trained checkpoint or execution authorization is implied by this local P3.'],
  next_minimal_scope='Separately authorize a dedicated short zero-update GPU entry plus its targeted CPU contract/P3, then freeze a pending request; bind existing provider and current container read-only as needed. Do not extend generic audit or sampling frameworks.'))
 emit('local_implementation_manifest_v1.json',dict(status='LOCAL_F0_LQI_IMPLEMENTATION_CPU_P3_COMPLETE',files=[rec(p) for p in sorted(S.rglob('*')) if p.is_file() and p.name!='local_implementation_manifest_v1.json'],server_operations=0,GPU_calls=0))
 print(json.dumps(dict(status='F0_LQI_LOCAL_IMPLEMENTATION_ONLY_P3_PASS',CPU_assertions=55,P3_SHA256=rec(S/'post_implementation_P3_v1.json')['sha256'])))
if __name__=='__main__':main()
