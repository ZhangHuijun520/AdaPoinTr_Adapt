"""Local archive verification and unexecuted scoring scope. No metric evaluation/extraction."""
import collections,copy,hashlib,io,json,tarfile,time
from pathlib import Path
import numpy as np
S=Path(__file__).resolve().parent;R=S.parents[2];P2=S.parent;PRE=P2/'H2_fourmodel_prediction_preparation_v1';PI=P2/'H2_fourmodel_prediction_implementation_v1';AF=PI/'post_prediction_freeze_audit_v1';H1=P2/'H1_scoring_implementation_20261107_v1';BACK=Path(r'E:\ResearchBackups\AdaPoinTr\BCSP_MAMBA_P2_H2\2026-11-07_native_development_eval')
start=time.monotonic()
def digest(p):
 p=Path(p);assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents));h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bind(p):return dict(path=str(p.absolute()),bytes=p.stat().st_size,sha256=digest(p))
def read(p):return json.loads(p.read_bytes())
def emit(n,v):
 with (S/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def exact(r):
 p=Path(r['path']);assert p.stat().st_size==r['bytes'] and digest(p)==r['sha256'],str(p);return p
scope=read(AF/'download_four_files_manifest_v1.json');auditp=AF/'audit_report_v1.json';audit=read(auditp);assert audit['status']=='FORMAL_H2_FOURMODEL_POST_PREDICTION_FREEZE_AUDIT_PASS' and all(audit['checks'].values())
emit('local_verification_scope_v1.json',dict(backup=str(BACK),expected_files=scope['files'],prediction_audit=bind(auditp),archive_policy='Stream all425 regular members, hash/size against saved formal audit; finite FP32 arrays and exact coarse cases; no extraction',reference_policy='Exact210 frozen reference/point byte hashes only, no reference array decoding or scoring',M0_policy='Existing two M0-containing archives and3 sidecars byte hashes only; no baseline inference',maximum_wall_seconds=120,maximum_total_byte_hashes=2*1024**3,backup_writes=False,server_operations=0))
try:
 records=[];before={}
 for r in scope['files']:
  p=BACK/r['filename'];st=p.stat();before[p.name]=(st.st_size,st.st_mtime_ns);assert st.st_size==r['bytes'] and digest(p)==r['sha256'];records.append(bind(p))
 archive=BACK/'development_predictions_v1.tar.gz';assert (BACK/(archive.name+'.sha256')).read_text().split()==[digest(archive),archive.name] and int((BACK/(archive.name+'.bytes')).read_text())==archive.stat().st_size
 inner={}
 for line in (BACK/(archive.name+'.contents.sha256')).read_text().splitlines():
  h,n=line.split(None,1);assert n not in inner and len(h)==64;inner[n]=h
 assert len(inner)==425
 index=read(PRE/'H2_C_D_fourmodel_input_index_v1.json');protocol=read(PRE/'H2_fourmodel_native_prediction_protocol_v1.json');lookup={r['run']+'__'+r['case_id']:r for r in index['inputs']};expected={'predictions/'+k+'.npz' for k in lookup}|{'inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl'}
 predictions=0;coarse=[];totalbytes=0;logs={};verified=[]
 with tarfile.open(archive,'r:gz') as t:
  members=t.getmembers();assert len(members)==len({m.name for m in members})==425 and {m.name for m in members}==set(inner)==expected
  for m in members:
   assert m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts and 0<m.size<=4*1024**2
   b=t.extractfile(m).read();totalbytes+=len(b);assert totalbytes<=128*1024**2 and len(b)==m.size and hashlib.sha256(b).hexdigest()==inner[m.name]
   assert hashlib.sha256(b).hexdigest()==read(AF/'remote_readonly_receipt_v1.json')['output_SHA256']['./'+m.name]
   verified.append(dict(name=m.name,bytes=m.size,sha256=inner[m.name]))
   if m.name.endswith('.npz'):
    key=m.name.removeprefix('predictions/').removesuffix('.npz');row=lookup[key];want=row['case_id'] in protocol['coarse_tensor_cases_by_fold'][row['fold']]
    with np.load(io.BytesIO(b),allow_pickle=False) as z:
     assert z.files==(['prediction','coarse'] if want else ['prediction']);x=z['prediction'];assert x.shape==(8192,3) and x.dtype==np.float32 and np.isfinite(x).all()
     if want:x=z['coarse'];assert x.shape==(256,3) and x.dtype==np.float32 and np.isfinite(x).all();coarse.append(m.name)
    predictions+=1
   else:logs[m.name]=b
 assert predictions==420 and len(coarse)==20
 manifest=[json.loads(x) for x in logs['inference_manifest.jsonl'].splitlines()];assert len(manifest)==420 and collections.Counter(x['run'] for x in manifest)=={r['label']:105 for r in index['runs']}
 for x in manifest:assert x['prediction']['sha256']==inner[x['prediction']['name']]
 done=json.loads(logs['inference_complete.json']);assert done['request_sha256']==audit['request_sha256'] and done['forwards']==420 and all(m['state_before']==m['state_after'] and m['RNG_before']==m['RNG_after'] for m in done['models'])
 for p in records:
  st=Path(p['path']).stat();assert before[Path(p['path']).name]==(st.st_size,st.st_mtime_ns)
 emit('local_download_verification_v1.json',dict(status='LOCAL_H2_NATIVE_ARCHIVE_FOUR_FILES_AND425_MEMBERS_PASS',files=records,archive_members=425,prediction_arrays=420,coarse_arrays=20,archive_member_records=verified,execution_identity=audit['request_sha256'],state_RNG_evidence_matches=True,backup_unchanged_excluding_atime=True,backup_extracted=False,archive_deleted=False,server_operations=0,scoring_executed=False,seconds=time.monotonic()-start))
 print('LOCAL_H2_NATIVE_ARCHIVE_FOUR_FILES_AND425_MEMBERS_PASS',flush=True)
 # Freeze exact existing references and M0 inputs, no metrics called.
 oldplan=read(H1/'local_scoring_execution_request_v1.json');refp=exact(oldplan['reference_manifest']);refs=read(refp);casep=exact(oldplan['score_case_index']);oldcases=read(casep)['cases'];cases=copy.deepcopy(oldcases)
 assert len(cases)==len(refs['cases'])==210 and len({c['source_id'] for c in cases})==42
 for c in cases:
  exact(c['reference']);exact(c['point_file']);row=next(r for r in index['inputs'] if r['case_id']==c['case_id'])
  assert all(c[k]==row[k] for k in ['case_id','source_id','fold','normalization','target_array_sha256','normalization_source']) and all(c['point_file'][k]==row['input'][k] for k in ['bytes','sha256'])
 oldarchives={}
 for fold in ['C','D']:
  spec=copy.deepcopy(oldplan['archive_inputs'][fold]);exact(spec['archive'])
  for rec in spec['sidecars']:exact(rec)
  exact(spec['prediction_index']);exact(spec['prediction_protocol']);oldarchives[fold]=spec
  pi=read(Path(spec['prediction_index']['path']));m0=[r for r in pi['runs'] if r['label'].endswith('_M0')];assert len(m0)==1 and m0[0]['dev_case_ids']==next(r for r in index['runs'] if r['fold']==fold)['dev_case_ids']
 metric=exact(oldplan['implementation']['metrics']);assert digest(metric)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
 scoreindex=dict(schema='bcsp-p2-H2-M0-twofold-score-index-candidate-v1',status='METADATA_FROZEN_NOT_EXECUTABLE',cases=cases,H2_archive=records[0],M0_archive_inputs=oldarchives,reference_manifest=bind(refp),H2_prediction_index=bind(PRE/'H2_C_D_fourmodel_input_index_v1.json'),H2_prediction_protocol=bind(PRE/'H2_fourmodel_native_prediction_protocol_v1.json'),metric=bind(metric),model_arms=['M0','H2_AUX','H2_COUPLE'],controls=['Nop_D','GT_8192'],counts=dict(unique_cases=210,sources=42,model_rows=630,shared_control_rows=420,case_score_rows=1050,source_score_rows=210),original_case_reference_point_records_unchanged=True)
 emit('H2_M0_twofold_score_case_index_candidate_v1.json',scoreindex)
 oldprotocol=read(H1/'frozen_scoring_protocol_v1.json');protocol=copy.deepcopy(oldprotocol);protocol.update(schema='bcsp-p2-H2-M0-twofold-local-scoring-protocol-candidate-v1',status='FROZEN_PENDING_IMPLEMENTATION_AND_SEPARATE_EXECUTION_AUTHORIZATION',arms=['M0','H2_AUX','H2_COUPLE'],model_rows=630,shared_control_rows=420,total_case_rows=1050,total_source_rows=210,delta='Primary H2_COUPLE minus H2_AUX; secondary H2_COUPLE minus M0, H2_AUX minus M0',budget_reason='1050 rows vs inherited840: proposed wall18000s=14400*1.25; same RSS8GiB/output2GiB/threads2. No metric or risk threshold change.')
 protocol['limits']['wall_seconds']=18000;protocol['H2_mechanism']='Use saved D-only Native H2 delta/scale/raw-used moments; GT radius/centroid comparison only offline. No new forward or intervention, no fitting or probe scan.';protocol['risk_reporting']='Per fold/case/source/defect; new/rescued/shared severe changes for COUPLE-AUX and COUPLE-M0, frontoorbital retained. No formal gate calculation or bootstrap/pvalue.'
 emit('H2_M0_frozen_scoring_protocol_candidate_v1.json',protocol)
 scorer=H1/'bcsp_p2_h1_M0_twofold_score_v1.py';text=scorer.read_text();assert "ARMS=['M0','M_H1']" in text and 'exact215 bounded archive' in text
 gap=dict(status='H1_SCORER_INCOMPATIBLE_H2_THREE_ARM_SCOPE',existing_scorer=bind(scorer),issues=['Hardcoded M0/M_H1 arms and H1 archive schema/status','H2 archive425 members420 predictions vs old215/210','H2 same-fold paired index repeats each of210 cases twice; old assumes210unique input rows','Need3 model arms630 rows plus420shared controls,1050 total; source groups210 vs168','Primary COUPLE-AUX and secondary baseline comparisons must remain separate; no pvalue/bootstrap/gate','H2 fixed coarse representatives5/fold vs old H1 C7; saved condition/moment summary schema needs exact adaptation'],metric_source_unchanged=bind(metric),next_scope=dict(maximum_new_production_files=1,maximum_new_test_files=1,description='Dedicated H2/M0 three-arm scorer plus targeted artificial CPU contracts and P3, reuse metric implementations unchanged; then create pending scoring request',tests=['Real archive/index metadata validation without actual scoring','Exact3-arm lookup/1050 row and shared-control counts on artificial geometry','Primary/secondary pair directions, risk transition and defect/source aggregation','H2 archive schema and coarse tensors/summary handling; wrong frame/mode/hash rejection','No new inference, bootstrap, gate, threshold/reference/GT changes']),execution_request_created=False,scoring_executed=False)
 emit('scoring_compatibility_and_minimal_implementation_scope_v1.json',gap)
 emit('preparation_receipt_v1.json',dict(status='LOCAL_ARCHIVE_VERIFIED_SCORING_METADATA_PREPARED_IMPLEMENTATION_REQUIRED',local_archive_verification=bind(S/'local_download_verification_v1.json'),references=210,point_files=210,M0_archives_verified=2,score_case_index=bind(S/'H2_M0_twofold_score_case_index_candidate_v1.json'),counts=scoreindex['counts'],no_metrics_computed=True,model_or_checkpoint_loaded=False,server_operations=0,execution_request_created=False,seconds=time.monotonic()-start))
 print(json.dumps(dict(status='LOCAL_ARCHIVE_VERIFIED_SCORING_METADATA_PREPARED_IMPLEMENTATION_REQUIRED',counts=scoreindex['counts'],real_scores=0),ensure_ascii=False),flush=True)
except BaseException as exc:
 emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),seconds=time.monotonic()-start));raise
