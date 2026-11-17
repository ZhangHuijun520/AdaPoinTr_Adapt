"""Local archive/hash and reference-file verification; prepare scoring, never compute scores."""
from pathlib import Path
import json,hashlib,tarfile,copy
V=Path(__file__).resolve().parent;W=V.parents[1];O=W/'outputs/spcg_score_preparation_20261117_v1';O.mkdir()
B=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_native_development_eval')
audit_dir=V/'implementation_v1/post_prediction_freeze_v1';audit=json.loads((audit_dir/'formal_freeze_result_v1.json').read_text(encoding='utf-8'));inventory=json.loads((audit_dir/'01_inventory_before_result.json').read_text(encoding='utf-8'))['files'];index=json.loads((V/'implementation_v1/SPCG_sixmodel_input_index_v1.json').read_text(encoding='utf-8'))
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def record(p):
 assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));s=p.stat();h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 t=p.stat();assert (s.st_size,s.st_mtime_ns)==(t.st_size,t.st_mtime_ns);return dict(path=str(p.resolve()),bytes=s.st_size,sha256=h.hexdigest())
def emit(n,d):
 with (O/n).open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
assert audit['status']=='FORMAL_SPCG_NATIVE630_POST_PREDICTION_FREEZE_PASS' and all(audit['checks'].values())
files=[]
for r in audit['download_files']:
 p=B/Path(r['path']).name;a=record(p);assert (a['bytes'],a['sha256'])==(r['bytes'],r['sha256']);files.append(a)
arc=B/'development_predictions_v1.tar.gz';assert (B/(arc.name+'.sha256')).read_text().split()[0]==files[0]['sha256'];assert int((B/(arc.name+'.bytes')).read_text())==files[0]['bytes']
listing=[];small={};prediction_records=[]
with tarfile.open(arc) as tar:
 members=tar.getmembers();assert len(members)==635 and len({x.name for x in members})==635
 for m in members:
  assert m.isfile() and m.name in inventory and m.size==inventory[m.name]['bytes'];h=hashlib.sha256();data=[]
  with tar.extractfile(m) as stream:
   for b in iter(lambda:stream.read(1048576),b''):
    h.update(b)
    if not m.name.startswith('predictions/'):data.append(b)
  assert h.hexdigest()==inventory[m.name]['sha256'];listing.append(h.hexdigest()+'  '+m.name+'\n')
  if data:small[m.name]=b''.join(data)
 assert (B/(arc.name+'.contents.sha256')).read_text()==''.join(listing)
M=[json.loads(l) for l in small['inference_manifest.jsonl'].splitlines()];J=[json.loads(l) for l in small['forward_attempts.jsonl'].splitlines()];done=json.loads(small['inference_complete.json'])
assert len(M)==len(J)==done['forwards']==630 and all(x['state_before']==x['state_after'] and x['RNG_before']==x['RNG_after'] and x['forwards']==105 for x in done['models'])
for m,x in zip(M,index['inputs']):
 assert m['run']==x['run'] and m['case_id']==x['case_id'] and m['input_sha256']==x['input']['sha256'] and m['normalization']==x['normalization']
 prediction_records.append(dict(fold=m['fold'],arm=m['variant'],case_id=m['case_id'],archive_key='SPCG',member=m['prediction']['name'],bytes=m['prediction']['bytes'],sha256=m['prediction']['sha256'],coarse_saved=True))
emit('local_archive_verification_v1.json',dict(status='LOCAL_SPCG_FOUR_FILES_AND635_MEMBERS_VERIFIED',files=files,members=635,predictions=630,models=6,state_RNG_all6=True,server_freeze=record(audit_dir/'formal_freeze_result_v1.json'),extracted=False,scoring_started=False))
print('LOCAL_ARCHIVE_PASS635',flush=True)
prior=W/'outputs/scq_rf_score_prep_20261115_v1';old_index=read(prior/'RF_three_arm_score_case_index_candidate_v1.json');cases=copy.deepcopy(old_index['cases']);assert len(cases)==210
lookup={(x['fold'],x['case_id']):x for x in index['inputs'] if x['run'].startswith('G0_')}
for c in cases:
 x=lookup[(c['fold'],c['case_id'])];assert c['source_id']==x['source_id'] and c['normalization']==x['normalization'] and c['point_file']['sha256']==x['input']['sha256']
 for key in ['reference','point_file']:
  r=c[key];a=record(Path(r['path']));assert (a['bytes'],a['sha256'])==(r['bytes'],r['sha256'])
old_request=read(W/'outputs/scq_rf_score_impl_20261115_v1/local_scoring_execution_request_v1.json');baseline=old_request['frozen_baseline_scores'];a=record(Path(baseline['path']));assert (a['bytes'],a['sha256'])==(baseline['bytes'],baseline['sha256'])
metric=read(prior/'RF_three_arm_unified_CPU_scoring_scope_v1.json')['metric'];a=record(Path(metric['path']));assert (a['bytes'],a['sha256'])==(metric['bytes'],metric['sha256'])
emit('SPCG_three_arm_score_case_index_draft_v1.json',dict(schema='bcsp-spcg-three-arm-twofold-score-index-draft-v1',status='DRAFT_PENDING_IMPLEMENTATION_CPU_P3',cases=cases,prediction_records=prediction_records,model_arms=['G0','G1','G2'],controls=['Nop_D','GT_8192'],counts=dict(unique_cases=210,sources=42,model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210),archive_inputs=dict(SPCG=dict(archive=files[0],sidecars=files[1:],prediction_index=record(V/'implementation_v1/SPCG_sixmodel_input_index_v1.json'),prediction_protocol=record(V/'implementation_v1/SPCG_native_scope_v1.json'),prediction_request_sha256=audit['request_sha256'])),metric=metric,scoring_started=False))
scope=read(prior/'RF_three_arm_unified_CPU_scoring_scope_v1.json');scope.update(schema='bcsp-spcg-local-scoring-protocol-draft-v1',status='DRAFT_PENDING_IMPLEMENTATION_CPU_P3_NOT_EXECUTABLE',arms=['G0','G1','G2'],paired_directions=['G2 minus G1','G2 minus G0','G1 minus G0'],coarse_availability='Actual Native Q256 and dense8192 only; no Qraw/stage/Memory arrays.',bootstrap=dict(required_by_original_protocol=True,replicates=2000,RNG='Generator(PCG64)',numpy='1.26.4',seeds=dict(C=2026111601,D=2026111602),unit='21 source means/fold; five defects and paired arms move together',source_order='canonical_source_id lexicographic',draw_shape=[2000,21],reuse='Same index matrix per fold for all metrics and all3 comparisons.',CI='2.5/97.5 percentile; quantile(method=linear)',save_indices_and_SHA256=True),comparison_qualification=dict(C_three_arms_same_training_device=True,D_G1_G2_same_training_device=True,D_G0_cross_device_reference=True,common_inference_device_does_not_remove_training_confound=True))
scope['metric']=metric;scope['score_index']=record(O/'SPCG_three_arm_score_case_index_draft_v1.json');scope['frozen_baseline_scores']=baseline;scope['environment']=old_request['environment'];scope['archive_binding']=dict(archive=files[0],members=635,uncompressed_member_bytes=sum(inventory[m.name]['bytes'] for m in members))
scope['scientific_constraints']=['Same opened210cases/42sources; all five defect types retained, no outcome selection.','Frozen A1/A2/B/GT references and original metrics/risk thresholds; physical mm after D-only inverse normalization.','G2-G1 primary; G2-G0 practical and G1-G0 explanatory.','Required fixed source-paired bootstrap retained; no p-values or automatic formal/clinical gate.','G0_D cross-device limitation persists; bootstrap excludes training seed variation and development-selection bias.','No GT/Oracle registration, postfilter, extra inference, model/checkpoint access or training.']
scope['protocol_completeness_note']='Original plan requests same-forward Memory for30 observations; authorized Native scope saved coarse/dense only. Mark Memory NOT_COLLECTED; do not fabricate or add forward automatically.'
scope['inherited_protocol']=record(W/'docs/cranial_bcsp_spcg_20261116_v2/Cranial_BCSP_FullMamba_BCSP_SPCG_正式实验计划书_审阅修订v2_2026-11-16.md')
emit('SPCG_unified_CPU_scoring_scope_draft_v1.json',scope)
emit('scorer_compatibility_review_v1.json',dict(status='NEEDS_SPCG_SCORER_AND_PREREGISTERED_BOOTSTRAP_CPU_P3',existing_scorer=record(W/'outputs/scq_rf_score_impl_20261115_v1/bcsp_scq_rf_three_arm_score_v1.py'),metric=metric,reference_and_point_files_verified=420,baseline_controls_bound=baseline,findings=['Existing metric/aggregation/risk/source-difference functions reusable; no metric changes.','RF scorer pins RF archives/labels/initializers/Q stage arrays and has no-bootstrap summaries; incompatible without isolated adaptation.','Need SPCG635-member Native archive, G0/G1/G2 labels, coarse/dense-only input and required2000 source-paired bootstrap.','Preserve original reference and shared-control recomputation/equality, fixed source unit and save RNG indices; do not inherit RF device qualification.'],server_operations=0,model_calls=0,score_calculations=0))
print('REFERENCES420_AND_SCORING_SCOPE_READY_NOT_EXECUTABLE')
