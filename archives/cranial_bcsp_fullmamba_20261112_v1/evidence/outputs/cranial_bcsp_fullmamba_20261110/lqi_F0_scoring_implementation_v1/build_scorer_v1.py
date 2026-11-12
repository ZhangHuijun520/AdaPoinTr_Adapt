"""Dedicated two-arm adaptation; immutable metric and original scorer."""
import ast,hashlib,json
from pathlib import Path
S=Path(__file__).resolve().parent;B=S.parent
P=B/'Native_scoring_implementation_v1/bcsp_f0_T0_M0_three_arm_score_v1.py'
text=P.read_text(encoding='utf-8')
for a,b in [("ARMS=['T0','M0','F0']","ARMS=['F0','LQI']"),("PAIRS=[('M0','F0'),('T0','F0'),('T0','M0')]","PAIRS=[('F0','LQI')]"),('bcsp-f0-T0-M0-three-arm-local-scoring-request-v1','bcsp-lqi-F0-two-arm-local-scoring-request-v1'),('bcsp-f0-T0-M0-score-authorization-v1','bcsp-lqi-F0-score-authorization-v1'),('bcsp-f0-T0-M0-twofold-score-index-candidate-v1','bcsp-lqi-F0-twofold-score-index-candidate-v1'),('model_rows=630','model_rows=420'),('case_score_rows=1050','case_score_rows=840'),('source_score_rows=210','source_score_rows=168'),('len(records})==630','len(records})==420'),('len(records)==len({(r[\'fold\'],r[\'arm\'],r[\'case_id\']) for r in records})==630',"len(records)==len({(r['fold'],r['arm'],r['case_id']) for r in records})==420"),('LOCAL_F0_T0_M0_SCORING_P3_PASS','LOCAL_LQI_F0_SCORING_P3_PASS'),("set(plan['archive_inputs'])=={'F0','C','D'}","set(plan['archive_inputs'])=={'F0','LQI'}")]:text=text.replace(a,b)
start=text.index('def validate_archive(');end=text.index('\ndef load_prediction_arrays',start)
replacement='''def validate_archive(tar,index,inner_sha256,coarse_cases,kind):
 require(kind in ('F0','LQI'),'only frozen Native archive roles')
 f0=kind=='F0';labels=['C_'+kind,'D_'+kind];variant='F0-P-v2' if f0 else 'F0-LQI-v1'
 require(index['schema']==('bcsp-f0-native-development-index-candidate-v1' if f0 else 'bcsp-lqi-native-development-index-candidate-v1'),'Native index schema')
 require([r['label'] for r in index['runs']]==labels and len(index['inputs'])==210,'twofold exact labels/count')
 members=tar.getmembers();names=[m.name for m in members];expected=[]
 for row in index['inputs']:
  require(row['variant']==variant and row['save_coarse'] is True,'all actual coarse tensors')
  if f0 and row['cache_context']:
   expected.append('context/'+row['run']+'__'+row['case_id']+'.npz')
   if row['save_full_decoder_trace']:expected.append('traces/'+row['run']+'__'+row['case_id']+'.npz')
  if not f0:require(row['cache_context'] is False and row['save_full_decoder_trace'] is False,'LQI no mechanism cache')
  expected.append('predictions/'+row['run']+'__'+row['case_id']+'.npz')
 expected+=['inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','cache_manifest.jsonl','inference_complete.json','resources.jsonl']
 require(len(members)==len(set(names))==(246 if f0 else 216) and names==expected,'exact archive names/order')
 for m in members:
  limit=20971520 if m.name.startswith('traces/') else 2097152 if m.name.startswith('context/') else 4194304
  empty_log=(not f0 and m.name=='cache_manifest.jsonl')
  require(m.isfile() and (m.size==0 if empty_log else 0<m.size<=limit) and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts,'bounded exact archive member; zero only frozen LQI cache log')
 require(sum(m.size for m in members)<=(536870912 if f0 else 67108864),'archive byte budget')
 records=[json.loads(x) for x in tar.extractfile('inference_manifest.jsonl').read().splitlines()]
 claims=[json.loads(x) for x in tar.extractfile('forward_attempts.jsonl').read().splitlines()]
 geometry=[json.loads(x) for x in tar.extractfile('geometry_summary.jsonl').read().splitlines()]
 done=json.loads(tar.extractfile('inference_complete.json').read());runs={r['label']:r for r in index['runs']}
 require(done['status']==('F0_CD_210_NATIVE_FORWARD_COMPLETE' if f0 else 'LQI_CD_210_NATIVE_FORWARD_COMPLETE') and done['forwards']==210 and done['request_sha256']==inner_sha256 and all(done[k]==0 for k in ['training_updates','BNCal','loss','backward']),'completed Native execution')
 require([r['run'] for r in done['models']]==labels,'fixed model execution order')
 for m in done['models']:
  require(m['forwards']==105 and len(m['state_before'])==64 and m['state_before']==m['state_after'] and set(m['RNG_before'])=={'CPU','CUDA','Python','numpy'} and m['RNG_before']==m['RNG_after'] and all(m['RNG_before'].values()),'state/RNG invariants')
  require(m['mode']=='eval_inference_mode' and m['BNCal']==m['optimizer']==m['backward']==0,'eval only')
  v=m['construction'];require(v['version']==('F0-P-v2-implementation-v1' if f0 else 'F0-LQI-implementation-v1') and v['artificial_fixture'] is False,'frozen native construction')
  if not f0:require(v['variant']=='F0-LQI-v1' and v['conditional_sequence']=='query_aligned_local_memory_interleaving' and v['trace_prefix_suffix_semantics']=='interleaved conditional query-position output' and v['additional_learned_parameters']==0,'LQI construction semantics')
 require(len(records)==len(claims)==len(geometry)==210,'210 ordered records')
 lookup={}
 for k,(r,i,c,g) in enumerate(zip(records,index['inputs'],claims,geometry),1):
  require(r['forward_index']==k and all(r[key]==i[key] for key in ['run','variant','case_id','source_id','fold','n_input','normalization']) and r['n_output']==8192 and r['input_sha256']==i['input']['sha256'] and r['checkpoint_sha256']==runs[i['run']]['checkpoint']['sha256'],'prediction provenance')
  require(c==dict(forward_index=k,run=r['run'],case_id=r['case_id'],status='CLAIMED_BEFORE_FORWARD'),'claim order')
  require(g['run']==r['run'] and g['case_id']==r['case_id'] and g['frame']=='native_D_only_normalized_no_GT','Native summary')
  require(r['prediction']['name']=='predictions/'+r['run']+'__'+r['case_id']+'.npz','member identity')
  key=(r['fold'],kind,r['case_id']);require(key not in lookup,'duplicate prediction')
  lookup[key]=dict(r,geometry=g,coarse_expected=True,archive_key=kind)
 require(len(lookup)==210,'all210 selected predictions')
 return lookup
'''
text=text[:start]+replacement+text[end:]
text=text.replace("coarse={f:[r['case_id'] for r in predindex['inputs'] if r['fold']==f] for f in ['C','D']} if k=='F0' else {spec['fold']:pro['coarse_tensor_cases']}","coarse={f:[r['case_id'] for r in predindex['inputs'] if r['fold']==f] for f in ['C','D']}\n   require([r['case_id'] for r in predindex['inputs']]==[c['case_id'] for c in cases],'same ordered cases across arms')\n   for r,c in zip(predindex['inputs'],cases):\n    require(all(r[key]==c[key] for key in ['fold','source_id','normalization','normalization_source','target_array_sha256']) and all(r['input'][key]==c['point_file'][key] for key in ['bytes','sha256']),'same input/reference frame across arms')")
for a,b in [('len(lookup)==630','len(lookup)==420'),('len(frozen)==len(prediction_bindings)==630','len(frozen)==len(prediction_bindings)==420'),('len(rows)==1050','len(rows)==840'),('len(sources)==210','len(sources)==168'),('len(selected)==525 and len(ss)==105','len(selected)==420 and len(ss)==84'),('model_predictions=630','model_predictions=420'),('score_rows=1050,source_rows=210','score_rows=840,source_rows=168'),('LOCAL_F0_T0_M0_THREE_ARM_TWOFOLD_CPU_SCORING_COMPLETE','LOCAL_LQI_F0_TWO_ARM_TWOFOLD_CPU_SCORING_COMPLETE'),('F0_T0_M0_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS','LQI_F0_TWOFOLD_SINGLE_SEED_DESCRIPTIVE_COMPARISONS'),("fixed_comparisons=['F0_minus_M0','F0_minus_T0','M0_minus_T0']","fixed_comparisons=['LQI_minus_F0']")]:text=text.replace(a,b)
# Verify unchanged baseline/control values before aggregation and successful completion.
anchor=" sources=aggregate_source(rows);"
insert=""" baseline=[json.loads(line) for line in check(plan['frozen_baseline_scores']).read_text(encoding='utf-8').splitlines()]
 old={(r['fold'],r['arm'],r['case_id']):r for r in baseline if r['arm'] in ['F0']+CONTROLS}
 current=[r for r in rows if r['arm'] in ['F0']+CONTROLS]
 require(len(old)==len(current)==630,'exact frozen F0/control baseline rows')
 require(all(old.get((r['fold'],r['arm'],r['case_id']))==metric.json_safe(r) for r in current),'recomputed F0 and controls differ from frozen baseline; stop')
"""
assert anchor in text;text=text.replace(anchor,insert+anchor)
text=text.replace('controls=420,score_rows=840','controls=420,frozen_baseline_rows_verified=630,score_rows=840')
text=text.replace('F0/T0/M0 CPU-only','LQI/F0 CPU-only')
# Only diagnostics strings, never scientific formula changes.
text=text.replace('exact1050 scope','exact840 scope').replace('fixed three-arm pairs','fixed two-arm pair').replace('fixed630 prediction bindings','fixed420 prediction bindings').replace('exact630model lookups','exact420model lookups').replace('all630 frozen prediction identities','all420 frozen prediction identities').replace('630 models plus420 shared controls','420 models plus420 shared controls').replace('42 sources times5 arms','42 sources times4 roles').replace('perfold525rows105sources','perfold420rows84sources').replace('exact three source archives','exact two Native archives')
target=S/'bcsp_lqi_F0_two_arm_score_v1.py'
ast.parse(text)
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
with (S/'source_derivation_v1.json').open('x',encoding='utf-8') as f:json.dump(dict(parent=str(P.resolve()),parent_sha256=hashlib.sha256(P.read_bytes()).hexdigest(),scorer_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),metric_changed=False,model_arms=['F0','LQI'],model_rows=420,case_rows=840),f,indent=2)
print('LQI_F0_SCORER_CREATED_NOT_EXECUTED')
