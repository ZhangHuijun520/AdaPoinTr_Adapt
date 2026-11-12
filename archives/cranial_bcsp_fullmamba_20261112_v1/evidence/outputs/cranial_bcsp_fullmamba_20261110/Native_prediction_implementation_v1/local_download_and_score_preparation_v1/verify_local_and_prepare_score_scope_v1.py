"""Local archive restoration in memory and unexecuted score scope; no metrics/GT decode."""
import ast,collections,copy,hashlib,io,json,tarfile,time
from pathlib import Path,PurePosixPath
import numpy as np
S=Path(__file__).resolve().parent;R=S.parents[2];F=S.parent/'resource_rebind_v2/post_prediction_freeze_audit_v1';T=S.parent/'resource_rebind_v2/transport_payload'
START=time.monotonic();HASHED=0
def digest(p):
 global HASHED
 p=Path(p);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p);h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):
   HASHED+=len(b);assert HASHED<4*1024**3 and time.monotonic()-START<300;h.update(b)
 return h.hexdigest()
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=digest(p))
def exact(r):
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],str(p);return p
def read(p):return json.loads(p.read_bytes())
def emit(n,v):
 with (S/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def member_bytes(t,m):
 global HASHED
 assert m.isfile() and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts and 0<m.size<=20*1024**2,m.name
 b=t.extractfile(m).read();assert len(b)==m.size;HASHED+=len(b);assert HASHED<4*1024**3 and time.monotonic()-START<300;return b
def arrays(blob,want):
 with np.load(io.BytesIO(blob),allow_pickle=False) as z:
  assert len(z.files)==len(want) and set(z.files)==set(want)
  a={k:z[k] for k in z.files}
  for k,shape in want.items():assert a[k].shape==shape and a[k].dtype==np.float32 and np.isfinite(a[k]).all(),k
 return a
def main():
 audit=read(F/'post_prediction_freeze_audit_result_v1.json');assert audit['status']=='FORMAL_F0_CD_POST_PREDICTION_FREEZE_AUDIT_PASS' and all(audit['checks'].values())
 plan=read(F/'download_four_files_manifest_v1.json');back=Path(plan['suggested_local_directory']);download=read(S/'four_file_download_receipt_v1.json')
 assert download['status']=='FOUR_FILES_DOWNLOADED_AND_BYTE_HASH_VERIFIED_AWAITING_MEMBER_RESTORE_VERIFICATION'
 index=read(T/'F0_CD_Native_input_index_candidate_v1.json');scope=read(F/'audit_scope_v1.json');remotehash={r['name']:r for r in read(F/'hashes_after_result_v1.json')['files']}
 emit('local_verification_scope_v1.json',dict(status='FROZEN_LOCAL_VERIFY_AND_SCORE_PREPARATION_ONLY',files=plan['files'],backup=str(back),prediction_audit=bind(F/'post_prediction_freeze_audit_result_v1.json'),archive_members=246,maximum_hash_read_bytes=4*1024**3,maximum_wall_seconds=300,archive_member_limit_bytes=20*1024**2,restore='Stream member bytes and arrays in memory, no filesystem extraction',reference_policy='Only exact frozen byte identities; no GT/reference array decoding or metric evaluation',baseline_policy='Existing T0/M0 two-fold frozen archives; no new inference',server_operations=0,scoring=False))
 before={};file_records=[]
 for r in plan['files']:
  p=back/r['name'];st=p.stat();before[p.name]=(st.st_size,st.st_mtime_ns,st.st_ctime_ns);assert p.stat().st_size==r['bytes'] and digest(p)==r['sha256'];file_records.append(bind(p))
 arc=back/'development_predictions_v1.tar.gz'
 assert (back/(arc.name+'.sha256')).read_text().split()==[audit['archive']['sha256'],arc.name] and int((back/(arc.name+'.bytes')).read_text())==arc.stat().st_size
 inner={}
 for line in (back/(arc.name+'.contents.sha256')).read_text().splitlines():
  h,n=line.split(None,1);assert len(h)==64 and n not in inner;inner[n]=h
 lookup={r['prediction_filename']:r for r in index['inputs']};ctx_lookup={'context/'+r['run']+'__'+r['case_id']+'.npz':r for r in index['inputs'] if r['cache_context']};tr_lookup={'traces/'+r['run']+'__'+r['case_id']+'.npz':r for r in index['inputs'] if r['save_full_decoder_trace']}
 expected=set(lookup)|set(ctx_lookup)|set(tr_lookup)|{'forward_attempts.jsonl','inference_manifest.jsonl','geometry_summary.jsonl','cache_manifest.jsonl','inference_complete.json','resources.jsonl'}
 logs={};verified=[];counts=collections.Counter();coarse_fingerprints={};context_X={}
 with tarfile.open(arc,'r:gz') as t:
  ms=t.getmembers();assert len(ms)==len({m.name for m in ms})==246 and {m.name for m in ms}==set(inner)==expected
  for m in ms:
   b=member_bytes(t,m);h=hashlib.sha256(b).hexdigest();assert h==inner[m.name]==remotehash[m.name]['sha256'] and len(b)==remotehash[m.name]['bytes'];verified.append(dict(name=m.name,bytes=len(b),sha256=h))
   if m.name in lookup:
    a=arrays(b,dict(prediction=(8192,3),coarse=(256,3)));row=lookup[m.name];coarse_fingerprints[(row['fold'],row['case_id'])]=hashlib.sha256(a['coarse'].tobytes()).hexdigest();counts['predictions']+=1;counts['coarse']+=1
   elif m.name in ctx_lookup:
    a=arrays(b,dict(F=(1,256,384),S=(1,256,3),z=(1,1024),Q=(1,256,3),X=(1,256,384)));row=ctx_lookup[m.name];key=(row['fold'],row['case_id']);context_X[key]=(hashlib.sha256(a['Q'][0].tobytes()).hexdigest(),hashlib.sha256(a['X'].tobytes()).hexdigest());counts['context']+=1
   elif m.name in tr_lookup:
    want={f'layer_{i}__{k}':(1,256,384) for i in range(8) for k in ['input','after_self','prefix_suffix','after_cross','output']};a=arrays(b,want);row=tr_lookup[m.name];key=(row['fold'],row['case_id'])
    assert all(np.array_equal(a[f'layer_{i}__output'],a[f'layer_{i+1}__input']) for i in range(7))
    # Archive order may precede context. Keep only a small tensor fingerprint.
    counts['trace']+=1
    logs['trace_X__'+row['fold']+'__'+row['case_id']]=hashlib.sha256(a['layer_0__input'].tobytes()).hexdigest()
   else:logs[m.name]=b
 assert counts==dict(predictions=210,coarse=210,context=20,trace=10)
 for key,(Q,X) in context_X.items():
  assert Q==coarse_fingerprints[key]
  tracekey='trace_X__'+key[0]+'__'+key[1]
  if tracekey in logs:assert logs[tracekey]==X
 manifest=[json.loads(x) for x in logs['inference_manifest.jsonl'].splitlines()];assert len(manifest)==210
 for row,m in zip(index['inputs'],manifest):assert all(row[k]==m[k] for k in ['run','case_id','source_id','fold','normalization']) and m['prediction']['sha256']==inner[row['prediction_filename']]
 done=json.loads(logs['inference_complete.json']);assert done['request_sha256']==audit['request_sha256'] and done['forwards']==210 and all(m['state_before']==m['state_after'] and m['RNG_before']==m['RNG_after'] for m in done['models'])
 assert all(before[p.name]==(p.stat().st_size,p.stat().st_mtime_ns,p.stat().st_ctime_ns) for p in (back/r['name'] for r in plan['files']))
 verified_receipt=dict(status='LOCAL_F0_FOUR_FILES_246_MEMBER_RESTORE_VERIFICATION_PASS',files=file_records,member_records=verified,counts=dict(counts),archive_members=246,context_Q_and_X_trace_parity=True,state_RNG_evidence_matches=True,archive_extracted=False,backup_unchanged_excluding_atime=True,scoring_executed=False,GT_arrays_read=0,checkpoint_loaded=False,seconds=time.monotonic()-START)
 emit('local_archive_restore_verification_v1.json',verified_receipt);print(json.dumps(dict(status=verified_receipt['status'],counts=dict(counts)),ensure_ascii=False),flush=True)
 # Reuse original case/reference contracts and both baseline arms, without reading scores.
 oldreq=R/'outputs/cranial_bcsp_mamba_p2_20261106/H1_scoring_implementation_20261107_v1/local_scoring_execution_request_v1.json';old=read(oldreq)
 refp=exact(old['reference_manifest']);refs=read(refp);oldcases=read(exact(old['score_case_index']))['cases'];cases=copy.deepcopy(oldcases);assert len(cases)==len(refs['cases'])==210
 assert len({c['case_id'] for c in cases})==210 and len({c['source_id'] for c in cases})==42
 f0byid={r['case_id']:r for r in index['inputs']};refbyid={r['case_id']:r for r in refs['cases']}
 for c in cases:
  exact(c['reference']);exact(c['point_file']);r=f0byid[c['case_id']];ref=refbyid[c['case_id']]
  assert all(c[k]==r[k]==ref[k] for k in ['case_id','source_id','fold','normalization','target_array_sha256'])
  assert c['normalization_source']==r['normalization_source']=='defective_bbox' and all(c['point_file'][k]==r['input'][k] for k in ['bytes','sha256'])
 baseline_specs={};baseline_verification=[];baseline_coarse={};prediction_records=[]
 for fold in ['C','D']:
  spec=copy.deepcopy(old['archive_inputs'][fold]);exact(spec['archive'])
  for r in spec['sidecars']:exact(r)
  pi=read(exact(spec['prediction_index']));proto=read(exact(spec['prediction_protocol']));runs={r['label']:r for r in pi['runs']};coarse_cases=set(proto['coarse_tensor_cases']);byname={'predictions/'+r['run']+'__'+r['case_id']+'.npz':r for r in pi['inputs']}
  assert [r['label'] for r in pi['runs']]==[fold+'_T0',fold+'_M0'] and len(byname)==210
  for run in pi['runs']:assert run['dev_case_ids']==next(r['dev_case_ids'] for r in index['runs'] if r['fold']==fold)
  expectedbase=set(byname)|{'forward_attempts.jsonl','inference_manifest.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl'}
  side=next(Path(r['path']) for r in spec['sidecars'] if r['path'].endswith('.contents.sha256'));baselist={}
  for line in side.read_text().splitlines():h,n=line.split(None,1);assert n not in baselist;baselist[n]=h
  rawlogs={};array_count=coarse_count=0
  with tarfile.open(spec['archive']['path'],'r:gz') as t:
   ms=t.getmembers();assert len(ms)==len({m.name for m in ms})==215 and {m.name for m in ms}==expectedbase==set(baselist)
   for m in ms:
    b=member_bytes(t,m);assert hashlib.sha256(b).hexdigest()==baselist[m.name]
    if m.name in byname:
     row=byname[m.name];want=dict(prediction=(8192,3));hascoarse=row['case_id'] in coarse_cases
     if hascoarse:want['coarse']=(256,3)
     arrays(b,want);array_count+=1;coarse_count+=int(hascoarse)
     prediction_records.append(dict(arm=row['variant'],fold=fold,case_id=row['case_id'],archive_key=fold,member=m.name,bytes=m.size,sha256=baselist[m.name],coarse_saved=hascoarse))
    else:rawlogs[m.name]=b
  bm=[json.loads(x) for x in rawlogs['inference_manifest.jsonl'].splitlines()];assert len(bm)==210
  for row,m in zip(pi['inputs'],bm):
   rr=runs[row['run']];case=f0byid[row['case_id']]
   assert all(row[k]==case[k] for k in ['case_id','source_id','fold','normalization','normalization_source','target_array_sha256'])
   assert all(row['input'][k]==case['input'][k] for k in ['bytes','sha256']) and all(m[k]==row[k] for k in ['run','case_id','source_id','fold','normalization'])
   assert m['prediction']['sha256']==baselist[m['prediction']['name']] and m['checkpoint_sha256']==rr['checkpoint']['sha256']
  bd=json.loads(rawlogs['inference_complete.json']);assert bd['request_sha256']==spec['prediction_request_sha256'] and bd['forwards']==210 and all(m['state_before']==m['state_after'] and m['RNG_before']==m['RNG_after'] for m in bd['models'])
  baseline_specs[fold]=spec;baseline_coarse[fold]=dict(cases=sorted(coarse_cases),T0=len(coarse_cases),M0=len(coarse_cases));baseline_verification.append(dict(fold=fold,archive=spec['archive'],members=215,prediction_arrays=array_count,coarse_arrays=coarse_count))
 for row,m in zip(index['inputs'],manifest):prediction_records.append(dict(arm='F0',fold=row['fold'],case_id=row['case_id'],archive_key='F0',member=row['prediction_filename'],bytes=m['prediction']['bytes'],sha256=m['prediction']['sha256'],coarse_saved=True))
 assert len(prediction_records)==630 and len({(r['arm'],r['fold'],r['case_id']) for r in prediction_records})==630
 metric=exact(old['implementation']['metrics']);assert digest(metric)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
 counts=dict(unique_cases=210,sources=42,model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210)
 scoreindex=dict(schema='bcsp-f0-T0-M0-twofold-score-index-candidate-v1',status='METADATA_PREPARED_NOT_EXECUTABLE',cases=cases,prediction_records=prediction_records,archive_inputs=dict(F0=dict(archive=bind(arc),sidecars=[bind(back/r['name']) for r in plan['files'] if not r['name'].endswith('.tar.gz')],prediction_index=bind(T/'F0_CD_Native_input_index_candidate_v1.json'),prediction_protocol=bind(T/'F0_CD_210_Native_prediction_scope_draft_v1.json'),prediction_request_sha256=audit['request_sha256']),**baseline_specs),reference_manifest=bind(refp),metric=bind(metric),model_arms=['T0','M0','F0'],controls=['Nop_D','GT_8192'],counts=counts,coarse_availability=dict(F0=210,baseline_by_fold=baseline_coarse,restriction='Use saved coarse summary for all model cases; paired tensor-only coarse comparisons on pre-existing common subset only. No inference to fill missing baseline Q.'),scoring_started=False)
 emit('F0_T0_M0_score_case_index_candidate_v1.json',scoreindex)
 protocol=dict(schema='bcsp-f0-T0-M0-three-arm-local-scoring-protocol-candidate-v1',status='PENDING_IMPLEMENTATION_AND_SEPARATE_EXECUTION_AUTHORIZATION',arms=['T0','M0','F0'],folds=['C','D'],counts=counts,primary_metric='A1 area-weighted E_P95 mm',paired_directions=['F0 minus M0','F0 minus T0','M0 minus T0'],secondary_metrics=['J_P95','E/J Cover@0.5/1/2mm','CD-L1, half sum of bidirectional unsquared Euclidean means','Pred-to-A2 P95 and >20mm outlier fraction','centroid offset, radius ratio, coarse/dense summaries'],aggregation='First five defects per source equally; then21sources per fold equally; report folds separately and pooled descriptively;1050rows are not independent patients',geometry_labels=dict(placement_tail='centroid>20mm',compact_distribution='radius_ratio<0.9',severe_geometry='E_P95>20mm OR J_Cover2mm==0'),reporting='Keep every case/type including frontoorbital; paired source/case/defect summaries, new/rescued/shared severe cases; no result-based exclusion',references='Original frozen A1/A2/B bank and target8192; D-only normalization to Native world mm; same metric implementation',coarse='All F0 Q retained; baselines only12 actual-Q cases per arm across C/D; do not imply complete paired coarse tensor evaluation',bootstrap=0,p_values=False,formal_gate_execution=False,ICP=False,GT_alignment=False,postfilter=False,limits=dict(wall_seconds=18000,RSS_bytes=8589934592,output_bytes=2147483648,threads=2),budget_reason='Same1050-row scope as inherited H2 three-arm scorer; same CPU/thread/RSS/output/wall limits',prohibited=['Execute scoring before implementation/CPU/P3 and separate full request hash authorization','New forward/training/BNCal/checkpoint/GPU','Changing metrics, references, thresholds, cases, sampling, normalization','Oracle alignment, parameter search, bootstrap or formal gate','Writing/deleting/extracting backup payloads'])
 emit('F0_T0_M0_scoring_protocol_candidate_v1.json',protocol)
 scorer=R/'outputs/cranial_bcsp_mamba_p2_20261106/H2_scoring_implementation_v1/bcsp_p2_h2_M0_three_arm_score_v1.py';text=scorer.read_text(encoding='utf-8');ast.parse(text)
 assert "ARMS=['M0','H2_AUX','H2_COUPLE']" in text and 'def h2_offline_geometry' in text
 compatibility=dict(status='EXISTING_H2_SCORER_INCOMPATIBLE_F0_T0_M0_SCOPE',existing_scorer=bind(scorer),metric_unchanged=bind(metric),issues=['Hardcoded H2 model arms, schema and checkpoint modes','425-member H2 archive differs from246-member F0 archive with20context10trace files','Baseline selection currently retains M0 only; must include existing T0 without reinference','F0 saves Q for all210 cases; T0/M0 have12 actual-Q cases per arm; preserve missing values and common-subset pairing','Remove H2 delta/scale assumptions; map F0 original summary and Native saved Q; no metric changes','Keep1050 rows,420 shared controls and source grouping; adapt only fixed pair labels and exact archive/read bindings'],next_implementation_scope=dict(new_production_files=1,new_test_files=1,CPU_tests=['Actual authorize/archive loading path and exact F0/baseline schemas','Synthetic three-arm1050-row/control and source counts','F0 all-Q and baseline optional-Q handling, extra diagnostic members not scored','Pair directions, risk transitions, immutable metric functions','Wrong hash/frame/case/arm rejection, fail stop'],P3_required=True),execution_request_created=False,real_scoring_executed=False)
 emit('scoring_compatibility_and_minimal_scope_v1.json',compatibility)
 emit('score_preparation_receipt_v1.json',dict(status='LOCAL_RESTORE_VERIFIED_SCORE_SCOPE_PREPARED_IMPLEMENTATION_REQUIRED',verification=bind(S/'local_archive_restore_verification_v1.json'),score_index=bind(S/'F0_T0_M0_score_case_index_candidate_v1.json'),protocol=bind(S/'F0_T0_M0_scoring_protocol_candidate_v1.json'),counts=counts,baseline_archives=baseline_verification,reference_files_hashed=210,point_files_hashed=210,metric_source_unchanged=True,real_scores_computed=0,real_GT_arrays_read=0,server_operations_in_verification=0,execution_request_created=False,hashed_bytes=HASHED,seconds=time.monotonic()-START))
 print(json.dumps(dict(status='LOCAL_RESTORE_VERIFIED_SCORE_SCOPE_PREPARED_IMPLEMENTATION_REQUIRED',counts=counts,baseline_coarse=baseline_coarse,real_scores=0)),flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as exc:emit('verification_preparation_failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),seconds=time.monotonic()-START,hashed_bytes=HASHED));raise
