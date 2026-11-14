"""Explicit metadata-only completion. No archive array rerun, metrics, model or server."""
import copy,hashlib,json,tarfile,time,ast
from pathlib import Path
S=Path(__file__).resolve().parent
R=Path(r'E:\Codex\2026-06-06\mamba-ccf-c-1-high-resolution')
F=S.parent/'resource_rebind_v2/post_prediction_freeze_audit_v1';T=S.parent/'resource_rebind_v2/transport_payload'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def exact(r):
 p=Path(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p);return p
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=sha(p))
def emit(n,v):
 with (S/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
start=time.monotonic()
verification=read(S/'local_archive_restore_verification_v1.json');assert verification['status']=='LOCAL_F0_FOUR_FILES_246_MEMBER_RESTORE_VERIFICATION_PASS'
assert verification['counts']==dict(context=20,trace=10,predictions=210,coarse=210)
plan=read(F/'download_four_files_manifest_v1.json');back=Path(plan['suggested_local_directory']);audit=read(F/'post_prediction_freeze_audit_result_v1.json');index=read(T/'F0_CD_Native_input_index_candidate_v1.json')
for r in verification['files']:exact(r)
assert audit['status']=='FORMAL_F0_CD_POST_PREDICTION_FREEZE_AUDIT_PASS'
original=R/'outputs/cranial_bcsp_mamba_p2_20261106/H1_scoring_implementation_20261107_v1/local_scoring_execution_request_v1.json';old=read(original)
refp=exact(old['reference_manifest']);refs=read(refp);cases=copy.deepcopy(read(exact(old['score_case_index']))['cases'])
assert len(cases)==len(refs['cases'])==210 and len({c['source_id'] for c in cases})==42
byid={r['case_id']:r for r in index['inputs']};refbyid={c['case_id']:c for c in refs['cases']}
for c in cases:
 exact(c['reference']);exact(c['point_file']);r=byid[c['case_id']]
 assert all(c[k]==r[k]==refbyid[c['case_id']][k] for k in ['case_id','source_id','fold','normalization','target_array_sha256'])
 assert c['normalization_source']==r['normalization_source']=='defective_bbox' and all(c['point_file'][k]==r['input'][k] for k in ['bytes','sha256'])
records=[];specs={};baseline_receipts=[];coarse_availability={}
for fold in ['C','D']:
 spec=copy.deepcopy(old['archive_inputs'][fold]);exact(spec['archive'])
 for r in spec['sidecars']:exact(r)
 pi=read(exact(spec['prediction_index']));proto=read(exact(spec['prediction_protocol']));coarse=set(proto['coarse_tensor_cases'])
 assert [r['label'] for r in pi['runs']]==[fold+'_T0',fold+'_M0']
 for run in pi['runs']:assert run['dev_case_ids']==next(r['dev_case_ids'] for r in index['runs'] if r['fold']==fold)
 with tarfile.open(spec['archive']['path'],'r:gz') as t:
  ms=t.getmembers();assert len(ms)==len({m.name for m in ms})==215 and all(m.isfile() for m in ms)
  manifest=[json.loads(x) for x in t.extractfile('inference_manifest.jsonl').read().splitlines()]
 assert len(manifest)==len(pi['inputs'])==210
 for row,m in zip(pi['inputs'],manifest):
  r=byid[row['case_id']]
  assert all(row[k]==r[k] for k in ['case_id','source_id','fold','normalization','normalization_source','target_array_sha256']) and all(row['input'][k]==r['input'][k] for k in ['bytes','sha256'])
  assert m['run']==row['run'] and m['case_id']==row['case_id']
  records.append(dict(arm=row['variant'],fold=fold,case_id=row['case_id'],archive_key=fold,member=m['prediction']['name'],bytes=m['prediction']['bytes'],sha256=m['prediction']['sha256'],coarse_saved=row['case_id'] in coarse))
 specs[fold]=spec;baseline_receipts.append(dict(fold=fold,archive=spec['archive'],fresh_byte_hash_verified=True,sidecars_verified=3,prediction_index=spec['prediction_index'],members=215,predictions=210,reused_frozen_baseline_arrays=True))
 coarse_availability[fold]=dict(cases=sorted(coarse),T0=len(coarse),M0=len(coarse))
fm=read(F/'hashes_after_result_v1.json');hashes={r['name']:r for r in fm['files']}
for row in index['inputs']:
 h=hashes[row['prediction_filename']];records.append(dict(arm='F0',fold=row['fold'],case_id=row['case_id'],archive_key='F0',member=row['prediction_filename'],bytes=h['bytes'],sha256=h['sha256'],coarse_saved=True))
assert len(records)==len({(r['arm'],r['fold'],r['case_id']) for r in records})==630
metric=exact(old['implementation']['metrics']);assert sha(metric)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
counts=dict(unique_cases=210,sources=42,model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210)
scoreindex=dict(schema='bcsp-f0-T0-M0-twofold-score-index-candidate-v1',status='METADATA_PREPARED_NOT_EXECUTABLE',cases=cases,prediction_records=records,archive_inputs=dict(F0=dict(archive=bind(back/'development_predictions_v1.tar.gz'),sidecars=[bind(back/r['name']) for r in plan['files'] if not r['name'].endswith('.tar.gz')],prediction_index=bind(T/'F0_CD_Native_input_index_candidate_v1.json'),prediction_protocol=bind(T/'F0_CD_210_Native_prediction_scope_draft_v1.json'),prediction_request_sha256=audit['request_sha256']),**specs),reference_manifest=bind(refp),metric=bind(metric),model_arms=['T0','M0','F0'],controls=['Nop_D','GT_8192'],counts=counts,coarse_availability=dict(F0=210,baseline_by_fold=coarse_availability,restriction='Summary-based coarse diagnostics for all cases; actual-Q paired comparisons only on frozen common subset, no new inference'),scoring_started=False)
emit('F0_T0_M0_score_case_index_candidate_v1.json',scoreindex)
protocol=dict(schema='bcsp-f0-T0-M0-three-arm-local-scoring-protocol-candidate-v1',status='PENDING_IMPLEMENTATION_AND_SEPARATE_EXECUTION_AUTHORIZATION',arms=['T0','M0','F0'],folds=['C','D'],counts=counts,primary_metric='A1 area-weighted E_P95 mm',paired_directions=['F0 minus M0','F0 minus T0','M0 minus T0'],secondary_metrics=['J_P95','E/J Cover@0.5/1/2mm','CD-L1: half sum of bidirectional unsquared Euclidean means','Pred-to-A2 P95 and >20mm outlier fraction','centroid offset, radius ratio, coarse/dense summaries'],aggregation='Five defects/source equally, then21sources/fold equally; folds separately and pooled descriptive summaries; rows not independent patients',geometry_labels=dict(placement_tail='centroid>20mm',compact_distribution='radius_ratio<0.9',severe_geometry='E_P95>20mm OR J_Cover2mm==0'),reporting='Keep all cases and defect types including frontoorbital; new/rescued/shared severe cases; no outcome-driven exclusion',references='Frozen A1/A2/B bank and GT8192, D-only inverse normalization to world mm',coarse_availability='F0 all210 actual Q; T0/M0 each12 actual Q across C/D. No complete paired tensor claim.',bootstrap=0,p_values=False,formal_gate_execution=False,ICP=False,GT_alignment=False,postfilter=False,limits=dict(wall_seconds=18000,RSS_bytes=8589934592,output_bytes=2147483648,threads=2),budget_reason='Same1050-row scope as inherited three-arm scorer; unchanged limits',prohibited=['Scoring before implementation/CPU/P3 and separate hash authorization','New inference/checkpoint/GPU/training/BNCal','Changes to metrics/reference/threshold/cases/sampling/frame','Oracle alignment/parameter search/bootstrap/formal gate','Backup extraction/deletion/writes'])
emit('F0_T0_M0_scoring_protocol_candidate_v1.json',protocol)
scorer=R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_scoring_implementation_v1/bcsp_p2_h2_M0_three_arm_score_v1.py';text=scorer.read_text(encoding='utf-8');ast.parse(text);assert "ARMS=['M0','H2_AUX','H2_COUPLE']" in text
gap=dict(status='EXISTING_H2_SCORER_REQUIRES_F0_T0_M0_MINIMAL_ADAPTATION',existing_scorer=bind(scorer),metric_source_unchanged=bind(metric),issues=['Hardcoded H2 schemas, arms and mode-specific summaries','F0 exact246-member archive includes context and traces, unlike425-member H2 archive','Reuse both T0 and M0, existing selector keeps only M0','F0 all-case Q vs optional baseline Q: preserve missing values and common subset','Adapt fixed pair labels and Native summary mapping, no metric changes'],next_scope=dict(new_production_files=1,new_test_files=1,CPU_contracts=['Actual authorize/archive load path','Synthetic1050 rows with420 shared controls and source counts','F0 and baseline optional-Q handling; diagnostic cache members not scored','Pair directions/risk transitions; unchanged metric functions','Wrong hash/frame/case/arm rejection and first failure stop'],P3_required=True),execution_request_created=False,real_scores_computed=0)
emit('scoring_compatibility_and_minimal_scope_v1.json',gap)
emit('score_preparation_receipt_v1.json',dict(status='LOCAL_RESTORE_VERIFIED_SCORE_SCOPE_PREPARED_IMPLEMENTATION_REQUIRED',verification=bind(S/'local_archive_restore_verification_v1.json'),score_index=bind(S/'F0_T0_M0_score_case_index_candidate_v1.json'),protocol=bind(S/'F0_T0_M0_scoring_protocol_candidate_v1.json'),counts=counts,baseline_archives=baseline_receipts,reference_files_hashed=210,point_files_hashed=210,metric_source_unchanged=True,real_scores_computed=0,real_GT_arrays_read=0,execution_request_created=False,archive_restoration_not_repeated=True,prior_helper_errors_preserved=['verification_preparation_failure_v1.json','continuation_precheck_correction_v1.json','remaining_preparation_failure_v1.json'],production_changes=0,server_operations=0,seconds=time.monotonic()-start))
print(json.dumps(dict(status='LOCAL_RESTORE_VERIFIED_SCORE_SCOPE_PREPARED_IMPLEMENTATION_REQUIRED',counts=counts,real_scores=0),ensure_ascii=False))
