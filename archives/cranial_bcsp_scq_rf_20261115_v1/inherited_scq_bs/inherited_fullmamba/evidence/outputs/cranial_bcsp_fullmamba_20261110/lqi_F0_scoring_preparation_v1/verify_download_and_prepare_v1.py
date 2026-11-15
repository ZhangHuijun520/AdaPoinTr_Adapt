"""Local archive integrity and frozen metadata preparation only; no scoring."""
import copy,hashlib,json,tarfile,time
from collections import Counter
from pathlib import Path,PurePosixPath
S=Path(__file__).resolve().parent;B=S.parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def read(p):return json.loads(p.read_bytes())
def emit(name,v):
 with (S/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def bind(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def exact(r):
 p=Path(r['path']);assert p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)) and p.is_file()
 assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],str(p)
 return p
def verify_archive(arm,local_root,audit_dir):
 manifest=read(audit_dir/'download_four_files_manifest_v1.json');records=[]
 for r in manifest['files']:
  local=dict(path=str(local_root/r['name']),bytes=r['bytes'],sha256=r['sha256']);exact(local);records.append(local)
 archive=local_root/'development_predictions_v1.tar.gz'
 assert (local_root/(archive.name+'.sha256')).read_text().split()==[sha(archive),archive.name]
 assert int((local_root/(archive.name+'.bytes')).read_text())==archive.stat().st_size
 # Bind archived metadata to independently frozen server hash records.
 completion_path=audit_dir/'downloads/output/completion.json';complete=read(completion_path)
 hashes={r['name']:r for r in read(audit_dir/'hashes_after_result_v1.json')['files']}
 assert sha(completion_path)==hashes['completion.json']['sha256']
 members=complete['archive']['members'];expected={r['name']:r for r in members}
 assert len(expected)==len(members) and complete['archive']['sha256']==sha(archive)
 assert (local_root/(archive.name+'.contents.sha256')).read_text()==''.join(r['sha256']+'  '+r['name']+'\n' for r in members)
 total=0;names=set()
 with tarfile.open(archive,'r:gz') as tar:
  entries=tar.getmembers();assert len(entries)==len(expected)
  for m in entries:
   p=PurePosixPath(m.name)
   assert m.isfile() and not p.is_absolute() and '..' not in p.parts and m.name not in names and m.name in expected
   assert m.size==expected[m.name]['bytes'] and m.size<20971520
   h=hashlib.sha256();n=0
   with tar.extractfile(m) as f:
    for block in iter(lambda:f.read(1048576),b''):h.update(block);n+=len(block)
   assert n==m.size and h.hexdigest()==expected[m.name]['sha256']==hashes[m.name]['sha256']
   total+=n;names.add(m.name)
 assert names==set(expected)
 return dict(status='LOCAL_FOUR_FILES_AND_ALL_MEMBERS_VERIFIED',arm=arm,local_directory=str(local_root),files=records,archive_members=len(members),uncompressed_member_bytes=total,server_audit=bind(audit_dir/'post_prediction_freeze_audit_result_v1.json'),local_extractions=0),expected

def main():
 started=time.monotonic()
 try:
  lqi_audit=B/'lqi_native_prediction_implementation_v1/post_prediction_freeze_audit_v1'
  f0_audit=B/'Native_prediction_implementation_v1/resource_rebind_v2/post_prediction_freeze_audit_v1'
  lqi_local=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_LQI/2026-11-11_native_development_eval')
  f0_local=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_F0/2026-11-11_native_development_eval')
  lqi,lr=verify_archive('LQI',lqi_local,lqi_audit);assert lqi['archive_members']==216
  f0,fr=verify_archive('F0',f0_local,f0_audit);assert f0['archive_members']==246
  emit('local_LQI_and_F0_archive_verification_v1.json',dict(status='LOCAL_LQI_AND_F0_BACKUPS_VERIFIED',archives=[lqi,f0],scoring=0,real_model_calls=0,checkpoint_loads=0,GT_arrays_decoded=0))
  oldq=read(B/'Native_scoring_implementation_v1/local_scoring_execution_request_v1.json')
  exact(oldq['score_case_index']);old_index=read(Path(oldq['score_case_index']['path']))
  li_path=B/'lqi_native_prediction_implementation_v1/pending_request_final_v1/transport_payload/LQI_CD_Native_input_index_candidate_v1.json';li=read(li_path)
  fi=read(exact(oldq['prediction_index']));refs=read(exact(oldq['reference_manifest']))
  cases=copy.deepcopy(old_index['cases']);assert len(cases)==210 and len(li['inputs'])==len(fi['inputs'])==210
  prediction_records=[]
  for c,l,f in zip(cases,li['inputs'],fi['inputs']):
   assert all(c[k]==l[k]==f[k] for k in ['case_id','source_id','fold','normalization','normalization_source','target_array_sha256'])
   assert l['input']==f['input'] and all(c['point_file'][k]==l['input'][k] for k in ['bytes','sha256'])
   for arm,row,records in [('F0',f,fr),('LQI',l,lr)]:
    rec=records[row['prediction_filename']]
    prediction_records.append(dict(arm=arm,fold=c['fold'],case_id=c['case_id'],archive_key=arm,member=rec['name'],bytes=rec['bytes'],sha256=rec['sha256'],coarse_saved=True))
  assert Counter(c['fold'] for c in cases)=={'C':105,'D':105}
  assert len({c['source_id'] for c in cases})==42 and set(Counter(c['source_id'] for c in cases).values())=={5}
  assert len(prediction_records)==420 and len({(r['arm'],r['fold'],r['case_id']) for r in prediction_records})==420
  # Rehash frozen reference banks and partial/GT8192 containers; do not decode arrays.
  seen={}
  for c in cases:
   for k in ['reference','point_file']:
    r=c[k];exact(r);seen[r['path']]=r
  metric=oldq['implementation']['metrics'];exact(metric)
  expected_metric='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
  assert metric['sha256']==expected_metric
  counts=dict(unique_cases=210,sources=42,model_rows=420,shared_control_rows=420,case_score_rows=840,source_score_rows=168)
  index=dict(schema='bcsp-lqi-F0-twofold-score-index-candidate-v1',status='FROZEN_METADATA_NOT_EXECUTABLE',cases=cases,prediction_records=prediction_records,archive_inputs=dict(F0=f0['files'],LQI=lqi['files']),reference_manifest=oldq['reference_manifest'],metric=metric,model_arms=['F0','LQI'],controls=['Nop_D','GT_8192'],counts=counts,coarse_availability='All420 model/case predictions contain actual coarse[256,3] and dense[8192,3]',scoring_started=False)
  emit('LQI_F0_score_case_index_candidate_v1.json',index)
  protocol=copy.deepcopy(read(B/'Native_scoring_implementation_v1/frozen_scoring_protocol_v1.json'))
  protocol.update(schema='bcsp-lqi-F0-two-arm-local-scoring-protocol-v1',status='FROZEN_SCOPE_AWAITING_IMPLEMENTATION_NOT_EXECUTION_REQUEST',arms=['F0','LQI'],counts=counts,paired_directions=['LQI minus F0'],coarse_availability=index['coarse_availability'],budget_reason='Inherited two-thread CPU upper budget retained, no GPU;840case rows instead of1050; no additional cases/metrics.')
  protocol['limits']=dict(wall_seconds=18000,RSS_bytes=8589934592,output_bytes=2147483648,threads=2)
  protocol['inherited_protocol']=bind(B/'Native_scoring_implementation_v1/frozen_scoring_protocol_v1.json')
  protocol['metric']=metric;protocol['score_index']=bind(S/'LQI_F0_score_case_index_candidate_v1.json')
  protocol['scientific_constraints']=['No scoring until dedicated entry/artificial CPU contracts/P3 and separate complete request SHA256 execution authorization','Same210 opened cases, same frame/reference/metrics/thresholds, no case exclusion or refitting','Compare native frozen predictions only; no ICP/Oracle/TTA/postfilter','Source-equal paired summaries, five defects per source; C/D separately then descriptive pooled results','Keep all severe/regression cases; no bootstrap/p-values/formal gate in this scope']
  emit('LQI_F0_unified_scoring_scope_v1.json',protocol)
  emit('preparation_validation_receipt_v1.json',dict(status='LOCAL_BACKUPS_VERIFIED_AND_SCORING_SCOPE_PREPARED_NOT_EXECUTED',archive_verification=bind(S/'local_LQI_and_F0_archive_verification_v1.json'),input_index=bind(S/'LQI_F0_score_case_index_candidate_v1.json'),scope=bind(S/'LQI_F0_unified_scoring_scope_v1.json'),reference_point_files_hashed=len(seen),reference_point_bytes_hashed=sum(r['bytes'] for r in seen.values()),identical210_case_source_input_normalization_target_metadata=True,metric_sha256=expected_metric,existing_scorer=oldq['implementation']['scorer'],implementation_gap='Existing scorer locks F0/T0/M0 three arms,1050rows and F0/C/D archive roles; needs dedicated LQI/F0 two-arm entry plus CPU contracts/P3 before executable request.',scoring=0,GPU_calls=0,GT_arrays_decoded=0,archive_extractions=0,seconds=time.monotonic()-started))
  print(json.dumps(dict(status='LOCAL_BACKUPS_VERIFIED_SCORING_SCOPE_PREPARED',LQI_members=216,F0_members=246,prediction_records=420,counts=counts,files_hashed=len(seen),seconds=time.monotonic()-started)))
 except BaseException as exc:
  emit('failure_v1.json',dict(status='FAILED_STOP_NO_RETRY',error=repr(exc),scoring=0));raise
if __name__=='__main__':main()
