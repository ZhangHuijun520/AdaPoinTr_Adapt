"""Create isolated SPCG scorer; never execute real scoring."""
from pathlib import Path
import ast,json,hashlib
R=Path(__file__).resolve().parents[2]
O=R/'outputs/spcg_score_implementation_20261117_v1'
O.mkdir(exist_ok=False)
old=(R/'outputs/scq_rf_score_impl_20261115_v1/bcsp_scq_rf_three_arm_score_v1.py').read_text(encoding='utf-8')
tree=ast.parse(old)
replacements={}
replacements['validate_index']='''def validate_index(index,references,score_index):
 require(index['schema']=='bcsp-spcg-sixmodel-native-index-v1' and [r['label'] for r in index['runs']]==RUNS,'six SPCG runs')
 cases=score_index['cases'];refs={r['case_id']:r for r in references['cases']}
 require(len(cases)==len(refs)==len(references['cases'])==len({c['case_id'] for c in cases})==210,'210 unique reference cases')
 require(len(index['inputs'])==630,'630 inputs')
 lookup={(r['fold'],r['variant'],r['case_id']):r for r in index['inputs']};require(len(lookup)==630,'unique native inputs')
 for run in index['runs']:
  f=run['fold'];arm=run['arm'];part=[c for c in cases if c['fold']==f];rr=[r for r in index['inputs'] if r['run']==run['label']]
  require(arm in ARMS and run['label']==arm+'_'+f and len(part)==len(rr)==105 and [r['case_id'] for r in rr]==[c['case_id'] for c in part]==run['dev_case_ids'],'ordered105/fold/model')
  ids={c['source_id'] for c in part};require(len(ids)==21,'21 sources/fold')
  for sid in ids:require({c['case_id'].split('__',2)[-1] for c in part if c['source_id']==sid}==DEFECTS,'five defects/source')
  for c in part:
   a=lookup[f,arm,c['case_id']];ref=refs[c['case_id']]
   require(all(c[k]==ref[k] for k in ['case_id','source_id','fold','normalization','target_array_sha256']),'fixed reference and target')
   require(all(c['reference'][k]==ref[k] for k in ['path','bytes','sha256']),'fixed reference file')
   require(all(c[k]==a[k] for k in ['case_id','source_id','fold','normalization','normalization_source']) and c['normalization_source']=='defective_bbox','D-only frame')
   require(np.asarray(c['normalization']['center']).shape==(3,) and np.isfinite(c['normalization']['center']).all() and np.isfinite(c['normalization']['scale']) and c['normalization']['scale']>0,'finite frame')
   require(all(c['point_file'][k]==a['input'][k] for k in ['bytes','sha256']) and a['n_input']==a['n_output']==8192 and a['save_coarse'] is True and a['save_Qraw'] is False and a['cache_context'] is a['save_full_decoder_trace'] is False,'point identities and minimal tensors')
 require(len({c['source_id'] for c in cases})==42,'42 disjoint sources')
 rs=score_index['prediction_records'];require(score_index['model_arms']==ARMS and score_index['controls']==CONTROLS and len(rs)==630 and len({(r['fold'],r['arm'],r['case_id']) for r in rs})==630,'630 frozen members')
 require({(r['fold'],r['arm'],r['case_id']) for r in rs}=={(c['fold'],a,c['case_id']) for c in cases for a in ARMS},'full paired design')
 return index['runs'],index['inputs'],cases
'''
# Keep the proven archive/order/state/hash reader, replacing only actual SPCG contracts.
f=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='validate_archive')
v=ast.get_source_segment(old,f)
v=v.replace("+['inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','cache_manifest.jsonl','inference_complete.json','resources.jsonl']","+['inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl']")
v=v.replace('==636','==635').replace("empty=m.name=='cache_manifest.jsonl'","empty=False")
v=v.replace(" require(tar.extractfile('cache_manifest.jsonl').read()==b'','no caches')\n",'')
a=v.index("  ev=m['construction']");b=v.index(" require(len(records)",a)
v=v[:a]+'''  ev=m['construction'];arm=runs[m['run']]['arm'];parent=ev['parent'];change=ev['change']
  require(ev['arm']==arm and ev['artificial_fixture'] is False and parent['version']=='F0-LQI-implementation-v1' and parent['variant']=='F0-LQI-v1' and parent['artificial_fixture'] is False and parent['additional_learned_parameters']==0 and parent['inventory']['forbidden_registered_modules']==[],'LQI/SPCG identity')
  if arm=='G0':require(change is None,'G0 original coarse')
  else:require(change['arm']==arm and change['old_head_removed'] is True and change['artificial_fixture'] is False and change['head_parameters']==1845763 and change['additional_parameters']==8963,'SPCG replaced head identity')
'''+v[b:]
v=v.replace("i['save_coarse'] is i['save_Qraw'] is True","i['save_coarse'] is True and i['save_Qraw'] is False")
replacements['validate_archive']=v
replacements['load_prediction_arrays']='''def load_prediction_arrays(tar,record):
 blob=tar.extractfile(record['prediction']['name']).read()
 require(len(blob)==record['prediction']['bytes'] and hashlib.sha256(blob).hexdigest()==record['prediction']['sha256'],'prediction bytes/hash')
 require(record['coarse_expected'] is True,'coarse required')
 with np.load(io.BytesIO(blob),allow_pickle=False) as z:
  require(z.files==['prediction','coarse'],'exact two native arrays');arrays={k:z[k].copy() for k in z.files}
 for k,v in arrays.items():require(v.shape==((8192,3) if k=='prediction' else (256,3)) and v.dtype==np.float32 and np.isfinite(v).all(),'finite FP32 shapes')
 return arrays
'''
lines=old.splitlines(keepends=True)
for n in reversed(tree.body):
 if isinstance(n,ast.FunctionDef) and n.name in replacements:lines[n.lineno-1:n.end_lineno]=[replacements[n.name]+'\n']
s=''.join(lines)
s=s.replace("ARMS=['S-ref','RF-Static','RF-Requery']","ARMS=['G0','G1','G2']").replace("PAIRS=[('RF-Static','RF-Requery'),('S-ref','RF-Static'),('S-ref','RF-Requery')]","PAIRS=[('G1','G2'),('G0','G2'),('G0','G1')]")
s=s.replace("RUNS=['Sref_C', 'Static_C', 'Requery_C', 'Sref_D', 'Static_D', 'Requery_D']","RUNS=['G0_C','G1_C','G2_C','G0_D','G1_D','G2_D']")
for name in ['ARM_BY_VARIANT','VARIANT_BY_ARM','PREFIX_BY_ARM']:
 s='\n'.join((name+"={a:a for a in ARMS}") if l.startswith(name+'=') else l for l in s.split('\n'))
scope=json.loads((Path(__file__).parent/'SPCG_unified_CPU_scoring_scope_draft_v1.json').read_bytes())
s='\n'.join(('QUALIFICATION='+repr(scope['comparison_qualification'])) if l.startswith('QUALIFICATION=') else l for l in s.split('\n'))
s=s.replace('ARCHIVE_MEMBER_BYTE_LIMIT=74282604','ARCHIVE_MEMBER_BYTE_LIMIT=60933613')
s=s.replace('SCQ_RF','SPCG').replace('bcsp-scq-rf','bcsp-spcg').replace('LOCAL_SCQ_RF','LOCAL_SPCG')
s=s.replace("pro['inference']['forward_attempt_budget']","pro['counts']['forward_attempts']")
s=s.replace("summary=paired_summary(ss,pair)","summary=paired_summary(ss,pair,bootstrap_indices=bootstraps[fold])")
s=s.replace("comparison={};risks={};defects={};deltas=[];rankings={}","comparison={};risks={};defects={};deltas=[];rankings={}\n bootstraps={}\n for fold in ['C','D']:\n  ids=sorted({r['source_id'] for r in sources if r['fold']==fold});indices=make_bootstrap_indices(ids,fold);bootstraps[fold]=indices\n  p=out/('bootstrap_indices_'+fold+'.npy')\n  with p.open('xb') as f:np.save(f,indices,allow_pickle=False)\n  emit(out/('bootstrap_index_record_'+fold+'.json'),dict(fold=fold,sources=ids,seed=BOOTSTRAP['seeds'][fold],shape=[2000,21],dtype=str(indices.dtype),sha256=digest(p),bootstrap_contract=BOOTSTRAP))")
s=s.replace('def paired_summary(sources,pair):','def paired_summary(sources,pair,bootstrap_indices):')
s=s.replace("d['source_deltas']=[dict(source_id=s,delta=v) for s,v in zip(ids,d.pop('deltas'))];result[key]=d","d['bootstrap']=bootstrap_ci(d['deltas'],bootstrap_indices)\n  d['source_deltas']=[dict(source_id=s,delta=v) for s,v in zip(ids,d.pop('deltas'))];result[key]=d")
s=s.replace('no_bootstrap=True','no_bootstrap=False').replace('bootstrap=0,formal_gate=False',"bootstrap=dict(replicates_per_fold=2000,folds=2,contract=BOOTSTRAP),formal_gate=False")
s=s.replace("require(plan['comparison_qualification']==QUALIFICATION,'D device confound qualification')","require(plan['comparison_qualification']==QUALIFICATION,'D device qualification')\n require(plan['statistics']==BOOTSTRAP,'exact preregistered bootstrap')")
bootstrap='''
BOOTSTRAP=CONTRACT

def make_bootstrap_indices(source_ids,fold):
 require(np.__version__=='1.26.4' and fold in ['C','D'],'frozen numpy and fold')
 require(len(source_ids)==len(set(source_ids))==21 and source_ids==sorted(source_ids),'canonical21 source IDs')
 return np.random.Generator(np.random.PCG64(BOOTSTRAP['seeds'][fold])).integers(0,21,size=(2000,21),dtype=np.int64)

def bootstrap_ci(deltas,indices):
 require(indices.shape==(2000,21) and indices.dtype==np.int64 and indices.min()>=0 and indices.max()<21,'fixed source draw matrix')
 require(len(deltas)==21,'retain21 sources')
 if any(v is None or not np.isfinite(v) for v in deltas):return dict(status='UNDEFINED_NONFINITE_PAIRS_RETAINED',CI95=None,replicates=2000)
 x=np.asarray(deltas,dtype=np.float64);means=x[indices].mean(axis=1)
 return dict(status='OK',CI95=np.quantile(means,[.025,.975],method='linear').tolist(),replicates=2000,estimator='equal source mean candidate minus reference',quantile_method='linear')

'''.replace('CONTRACT',repr(scope['bootstrap']))
s=s.replace('def require(ok,message):',bootstrap+'def require(ok,message):')
s=s.replace('"""SCQ B/S CPU-only Native scoring. Inert with respect to real scores until separate authorization."""','"""SPCG three-arm twofold CPU scoring with preregistered paired-source bootstrap. Separate execution authorization required."""')
ast.parse(s)
(O/'bcsp_spcg_three_arm_score_v1.py').write_text(s,encoding='utf-8',newline='\n')
case=json.loads((Path(__file__).parent/'SPCG_three_arm_score_case_index_draft_v1.json').read_bytes());case.update(schema='bcsp-spcg-three-arm-twofold-score-index-v1',status='FROZEN_IMPLEMENTATION_PENDING_TEST')
(O/'SPCG_score_case_index_v1.json').write_text(json.dumps(case,indent=2),encoding='utf-8')
scope.update(schema='bcsp-spcg-local-scoring-protocol-v1',status='FROZEN_PENDING_CPU_P3_AND_EXECUTION_AUTHORIZATION')
scope['prohibited']=[x.replace('/bootstrap/formal gate','/unregistered bootstrap/formal gate') for x in scope['prohibited']]
(O/'SPCG_scoring_protocol_v1.json').write_text(json.dumps(scope,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status':'IMPLEMENTATION_CREATED_NOT_EXECUTED','directory':str(O)}))
