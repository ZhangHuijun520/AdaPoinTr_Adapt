"""Downloaded four-file verification and metadata-only score preparation. No scoring."""
from pathlib import Path,PurePosixPath
from collections import Counter
import ast,copy,hashlib,json,tarfile,time
R=Path(__file__).resolve().parent.parent;O=R/'outputs/scq_rf_score_prep_20261115_v1';O.mkdir()
F=R/'outputs/scq_rf_pred_freeze_20261115_v2'
BACKUP=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_native_development_eval')
OLD=R/'outputs/scq_score_impl_20261114_v1'
def read(p):return json.loads(p.read_bytes())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def record(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def exact(r):
 p=Path(r['path']);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p);return p
def emit(n,j):
 with (O/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(j,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
stage='four_downloaded_files';start=time.monotonic()
try:
 audit=read(F/'post_prediction_freeze_audit_result_v1.json');assert audit['status']=='FORMAL_SCQ_RF_SIXMODEL_POST_PREDICTION_FREEZE_AUDIT_PASS' and all(audit['checks'].values())
 download=read(F/'download_four_files_manifest_v1.json');files=[]
 for r in download['files']:
  local=dict(path=str(BACKUP/r['name']),bytes=r['bytes'],sha256=r['sha256']);exact(local);files.append(local)
 archive=BACKUP/'development_predictions_v1.tar.gz'
 assert (BACKUP/(archive.name+'.sha256')).read_text().split()==[sha(archive),archive.name]
 assert int((BACKUP/(archive.name+'.bytes')).read_text())==archive.stat().st_size
 hashes=read(F/'inventory_after_result_v1.json')['output']['files'];cp=F/'downloads/output/completion.json';assert sha(cp)==hashes['completion.json']['sha256']
 complete=read(cp);members=complete['archive']['members'];expected={r['name']:r for r in members}
 assert len(expected)==len(members)==636 and complete['archive']['sha256']==sha(archive)
 assert (BACKUP/(archive.name+'.contents.sha256')).read_text()==''.join(r['sha256']+'  '+r['name']+'\n' for r in members)
 stage='archive_members';seen=set();total=0
 with tarfile.open(archive) as t:
  ms=t.getmembers();assert len(ms)==636
  for m in ms:
   p=PurePosixPath(m.name);assert m.isfile() and not p.is_absolute() and '..' not in p.parts and m.name not in seen and m.name in expected
   assert m.size==expected[m.name]['bytes'] and m.size<8388608
   h=hashlib.sha256();size=0
   with t.extractfile(m) as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b);size+=len(b)
   assert size==m.size and h.hexdigest()==expected[m.name]['sha256']==hashes[m.name]['sha256']
   total+=size;seen.add(m.name)
  assert seen==set(expected)
  inference=[json.loads(x) for x in t.extractfile('inference_manifest.jsonl').read().splitlines()]
 assert len(inference)==630 and Counter(r['run'] for r in inference)=={r:105 for r in ['Sref_C','Static_C','Requery_C','Sref_D','Static_D','Requery_D']}
 verification=dict(status='LOCAL_SCQ_RF_FOUR_FILES_ALL636_MEMBERS_VERIFIED',local_directory=str(BACKUP),files=files,archive_members=636,predictions=630,uncompressed_member_bytes=total,formal_server_audit=record(F/'post_prediction_freeze_audit_result_v1.json'),local_extractions=0,real_arrays_decoded=0,scoring=0,server_operations=0)
 emit('local_archive_verification_v1.json',verification)
 stage='scoring_metadata'
 oldq=read(OLD/'local_scoring_execution_request_v1.json');oldindex=read(exact(oldq['score_case_index']));refs=read(exact(oldq['reference_manifest']))
 cases=copy.deepcopy(oldindex['cases']);assert len(cases)==210
 idxfile=F/'downloads/installed/RF_sixmodel_input_index_v2.json';index=read(idxfile)
 assert sha(idxfile)==read(F/'downloads/installed/SCQ_RF_sixmodel_native_prediction_execution_request_v2.json')['input_index']['sha256']
 imap={(r['fold'],r['variant'],r['case_id']):r for r in index['inputs']};predmap={(r['fold'],r['variant'],r['case_id']):r for r in inference}
 assert len(imap)==len(predmap)==630
 manifestfile=R/'outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/candidate_payload/manifest_8192.jsonl';manifest={r['case_id']:r for r in map(json.loads,manifestfile.read_text().splitlines())}
 predictions=[]
 for c in cases:
  raw=manifest[c['case_id']]
  assert c['normalization']==raw['normalization'] and c['target_array_sha256']==raw['target_array_sha256'] and c['normalization_source']==raw['normalization_source']=='defective_bbox'
  for arm,variant in [('S-ref','S'),('RF-Static','RF-Static'),('RF-Requery','RF-Requery')]:
   row=imap[c['fold'],variant,c['case_id']];pred=predmap[c['fold'],variant,c['case_id']]
   assert all(c[k]==row[k] for k in ['case_id','source_id','fold','normalization','normalization_source'])
   assert all(c['point_file'][k]==row['input'][k] for k in ['bytes','sha256']) and pred['input_sha256']==row['input']['sha256']
   r=expected[row['prediction_filename']];assert all(pred['prediction'][k]==r[k] for k in ['name','bytes','sha256'])
   predictions.append(dict(arm=arm,fold=c['fold'],case_id=c['case_id'],archive_key='SCQ_RF',member=r['name'],bytes=r['bytes'],sha256=r['sha256'],coarse_saved=True,Qraw_saved=True,delta_saved=True,RF_stage_arrays_saved=True,native_variant=variant))
 assert Counter(c['fold'] for c in cases)=={'C':105,'D':105} and len({c['source_id'] for c in cases})==42 and set(Counter(c['source_id'] for c in cases).values())=={5}
 assert len(predictions)==len({(r['arm'],r['fold'],r['case_id']) for r in predictions})==630
 stage='frozen_reference_point_hashes';reference_files={}
 for c in cases:
  for k in ['reference','point_file']:
   r=c[k];exact(r);reference_files[r['path']]=r
 metric=oldq['implementation']['metrics'];exact(metric);assert metric['sha256']=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
 counts=dict(unique_cases=210,sources=42,model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210)
 scoreindex=dict(schema='bcsp-scq-rf-three-arm-twofold-score-index-candidate-v1',status='FROZEN_METADATA_NOT_EXECUTABLE',cases=cases,prediction_records=predictions,archive_inputs={'SCQ_RF':files},reference_manifest=oldq['reference_manifest'],metric=metric,model_arms=['S-ref','RF-Static','RF-Requery'],controls=['Nop_D','GT_8192'],counts=counts,scoring_started=False)
 emit('RF_three_arm_score_case_index_candidate_v1.json',scoreindex)
 protocol=copy.deepcopy(read(R/'outputs/scq_score_prep_20261114_v1/SCQ_BS_unified_CPU_scoring_scope_v1.json'))
 protocol.update(schema='bcsp-scq-rf-local-scoring-protocol-v1',status='FROZEN_SCOPE_AWAITING_IMPLEMENTATION_NOT_EXECUTION_REQUEST',arms=['S-ref','RF-Static','RF-Requery'],counts=counts,paired_directions=['RF-Requery minus RF-Static','RF-Static minus S-ref','RF-Requery minus S-ref'],coarse_availability='All630 Native outputs have actual Qused256/P8192 and same-forward Q0/Q1/Q2/delta0/delta1; score Native dense and actual coarse with unchanged metrics.',score_index=record(O/'RF_three_arm_score_case_index_candidate_v1.json'),inherited_protocol=record(R/'outputs/scq_score_prep_20261114_v1/SCQ_BS_unified_CPU_scoring_scope_v1.json'))
 protocol['scientific_constraints']=['Same210 opened cases/42sources; no model-outcome selection','Fixed reference bank/metric code/thresholds; D-only inverse normalization to world mm','630 model rows plus420 shared controls counted once per case, total1050; five defects/source equally weighted','C and D separately, then descriptive pooled source-equal summaries; cases are not independent patients','Core contrast RF-Requery minus RF-Static; both versus S-ref are supporting comparisons','C same-device pair is primary mechanism evidence. D Static training GPU/driver differs; D and pooled contrasts must disclose confounding','No registration/Oracle/TTA/postfilter/bootstrap/p-values/formal gate or parameter search','Qraw/stage arrays are diagnostics, never substitute corrected outputs for Native scores','Separate three-arm entry/artificial CPU tests/P3 and separate full-hash execution authorization before scoring']
 protocol['comparison_qualification']=audit['comparison_qualification']
 protocol['archive_binding']=dict(archive_bytes=archive.stat().st_size,uncompressed_member_bytes=total,archive_members=636,source='All636 members independently streamed and hash matched; freeze exact observed archive footprint, do not reuse old64MiB ceiling.')
 protocol['budget_reason']='Retain inherited18000-second/two-thread/8GiB RSS/2GiB output CPU budget for1050 rows; no extra cases or metric changes. Actual runtime remains unknown until execution.'
 emit('RF_three_arm_unified_CPU_scoring_scope_v1.json',protocol)
 scorer=Path(oldq['implementation']['scorer']['path']);exact(oldq['implementation']['scorer']);src=scorer.read_text(encoding='utf-8')
 assert "ARMS=['B','S']" in src and "keys=['prediction','coarse','Qraw','delta']" in src and '67108864' in src
 emit('scorer_compatibility_review_v1.json',dict(status='DEDICATED_RF_THREE_ARM_ENTRY_REQUIRED',existing_scorer=record(scorer),frozen_metric=metric,gaps=['Old B/S labels, two-arm lookup and840-row contract require S-ref/Static/Requery dispatch and1050 rows','RF six-model index,630 records,636 archive members and nested RF construction schema require precise validation','Prediction loader must validate nine saved keys and Q0/Q1/Q2 equations, scoring only Native prediction and actual coarse','Old uncompressed64MiB archive cap is smaller than verified current archive members; freeze exact observed bytes rather than reuse it blindly','Preserve metrics, references, thresholds, five-defect/source aggregation, controls once per case, and explicit D device confound','Full authorization/accounting plus targeted artificial CPU tests/P3 before final score request'],metric_or_threshold_changes=False,production_source_changes=0,scoring=0,request_created=False))
 emit('preparation_validation_receipt_v1.json',dict(status='LOCAL_RF_BACKUP_VERIFIED_AND_CPU_SCORE_SCOPE_PREPARED_NOT_EXECUTED',verification=record(O/'local_archive_verification_v1.json'),input_index=record(O/'RF_three_arm_score_case_index_candidate_v1.json'),scope=record(O/'RF_three_arm_unified_CPU_scoring_scope_v1.json'),reference_point_files_hashed=len(reference_files),reference_point_bytes_hashed=sum(r['bytes'] for r in reference_files.values()),metric_sha256=metric['sha256'],counts=counts,scoring=0,GT_arrays_decoded=0,archive_extractions=0,GPU_calls=0,server_operations=0,execution_request_created=False,seconds=time.monotonic()-start))
 print(json.dumps(dict(status='LOCAL_RF_BACKUP_VERIFIED_SCORE_SCOPE_PREPARED',archive_members=636,predictions=630,reference_point_files_hashed=len(reference_files),counts=counts,seconds=time.monotonic()-start)))
except BaseException as exc:
 emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',stage=stage,error=repr(exc),scoring=0));raise
