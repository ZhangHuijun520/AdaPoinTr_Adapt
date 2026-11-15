import array,ast,base64,hashlib,io,json,math,pathlib,struct,sys,tarfile,time,zipfile
N=pathlib.Path(__file__).resolve().parent.parent;V=N/'local_download_verification_v1';A=N/'post_prediction_freeze_audit_v1';D=pathlib.Path('E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_FoldD_paired_development_eval');start=time.monotonic()
def need(v,t):
 if not v:raise RuntimeError(t)
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf8'))
def emit(p,v):
 with pathlib.Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2,ensure_ascii=False)
def record(p):return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def stamp(p):
 st=p.stat();return (st.st_size,st.st_mtime_ns)
need(D.is_dir() and not any(x.is_symlink() for x in (D,*D.parents)),'backup directory/link')
audit=load(A/'audit_report_v1.json');need(audit['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS','formal audit');need(sha(A/'audit_report_v1.json')=='b95682ee53e5e17cc72f6746d0162e36523daa2653dfef62987225fc924ee7b7','audit hash')
files=[];before={}
for r in audit['download_files']:
 p=D/pathlib.PurePosixPath(r['path']).name;need(p.is_file() and not p.is_symlink(),'download path');before[str(p)]=stamp(p);need(p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'download size/hash '+p.name);files.append(record(p))
complete=load(A/'frozen_metadata/completion.json');members=complete['archive']['members'];protocol=load(N/'transport_payload/paired_development_protocol_v1.json');representatives=set(protocol['coarse_tensor_cases']);need(len(representatives)==5,'five fixed coarse cases')
source=(A/'readonly_audit_source_v1.py').read_text(encoding='utf8');node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='array_contract');ns=dict(need=need,budget=lambda n:None,zipfile=zipfile,io=io,struct=struct,ast=ast,array=array,sys=sys,math=math);exec(compile(ast.get_source_segment(source,node),'<frozen_NPZ_integrity_validator>','exec'),ns)
counts={'D_T0':0,'D_M0':0};coarse=0;a=D/'development_predictions_v1.tar.gz'
with tarfile.open(a,'r:gz') as tf:
 ms=tf.getmembers();need(len(ms)==len(set(m.name for m in ms))==215 and [m.name for m in ms]==[r['name'] for r in members],'strict215 members/order')
 for m,r in zip(ms,members):
  need(m.isfile() and m.size==r['bytes'] and m.size<=4194304 and not m.name.startswith('/') and '..' not in pathlib.PurePosixPath(m.name).parts,'member path/type/size');data=tf.extractfile(m).read();need(hashlib.sha256(data).hexdigest()==r['sha256'],'member SHA '+m.name)
  if m.name.startswith('predictions/'):
   label,cid=pathlib.PurePosixPath(m.name).stem.split('__',1);need(label in counts,'D model label');keep=cid in representatives;ns['array_contract'](data,keep);counts[label]+=1;coarse+=int(keep)
  else:need(data==(A/'frozen_metadata'/m.name).read_bytes(),'frozen metadata exact')
need(counts=={'D_T0':105,'D_M0':105} and coarse==10,'prediction/coarse counts')
need((D/(a.name+'.sha256')).read_text(encoding='ascii')==sha(a)+'  '+a.name+'\n','SHA sidecar');need((D/(a.name+'.bytes')).read_text(encoding='ascii')==str(a.stat().st_size)+'\n','bytes sidecar');need((D/(a.name+'.contents.sha256')).read_text(encoding='ascii')==''.join(r['sha256']+'  '+r['name']+'\n' for r in members),'all215 content sidecar')
need(all(stamp(pathlib.Path(p))==st for p,st in before.items()),'files stable')
verification=dict(status='LOCAL_DOWNLOAD_AND_ALL_MEMBER_VERIFICATION_PASS',backup_directory=str(D),download_files=files,archive_members_verified=215,predictions_verified=210,coarse_arrays_verified=10,per_model=counts,full_metadata_matches_formal_audit=True,formal_audit_sha256=sha(A/'audit_report_v1.json'),verification_script_sha256=sha(__file__),prediction_archive_sha256=sha(a),backup_writes=0,server_writes=0,GPU_calls=0,scoring_executed=False,seconds=time.monotonic()-start)
emit(V/'verification_result_v1.json',verification)
# Prepare metadata and hash-only reference bindings; do not decode GT or real input arrays.
S=N/'CPU_scoring_preparation_v1';S.mkdir(exist_ok=False);G=N.parents[1]/'cranial_bcsp_geov1_20261024';P1=N.parent;index=load(N/'transport_payload/paired_development_input_index_v1.json');refs_manifest=G/'development_eval_v1/reference_bank_v2/reference_manifest_v1.json';full=load(refs_manifest);refs={r['case_id']:r for r in full['cases']};rows=index['inputs'][:105];cases=[];selected=[]
for row in rows:
 r=refs[row['case_id']];need(r['fold']=='D' and r['source_id']==row['source_id'] and all(r[k]==row[k] for k in ['normalization','target_array_sha256']),'D reference metadata')
 ref={k:r[k] for k in ['path','bytes','sha256']};point=r['point_files']['8192'];need(all(point[k]==row['input'][k] for k in ['bytes','sha256']),'V1 point identity')
 for bound in [ref,point]:
  p=pathlib.Path(bound['path']);need(p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==bound['bytes'] and sha(p)==bound['sha256'],'reference/point opaque hash')
 selected.append(r);cases.append(dict(case_id=row['case_id'],source_id=row['source_id'],fold='D',normalization=row['normalization'],normalization_source=row['normalization_source'],target_array_sha256=row['target_array_sha256'],reference=ref,point_file=point))
need(len(cases)==105 and len({c['source_id'] for c in cases})==21,'D105/21')
emit(S/'reference_manifest_foldD_v1.json',dict(status='FROZEN_EXISTING_FOLD_D_105_REFERENCES',cases=selected,parent_reference_manifest=record(refs_manifest)))
emit(S/'P1_D_score_case_index_v1.json',dict(schema='bcsp-p1-paired-score-case-index-preparation-v1',status='METADATA_FROZEN_SCORING_NOT_EXECUTED',cases=cases))
protocol=load(P1/'paired_development_evaluator_v2/CPU_scoring_preparation_v1/unified_CPU_scoring_protocol_preparation_v1.json');protocol.update(schema='bcsp-p1-foldD-local-score-preparation-protocol-v1',fold='D',status='PREPARED_NOT_EXECUTABLE_REQUIRES_FOLDD_ADAPTER');protocol['coarse_dense']=protocol['coarse_dense'].replace('14saved','10saved');protocol['continuation_rule_after_scoring_audit']='Interpret frozen Fold D results then prepare cross-fold synthesis separately; no tuning, filtering, automatic gate or experiments.';emit(S/'unified_CPU_scoring_protocol_preparation_v1.json',protocol)
metric=G/'blue_pair_eval_v1/bcsp_eval_metrics_v1.py';need(sha(metric)=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766','metric engine unchanged')
scorer=P1/'paired_development_evaluator_v2/scoring_implementation_v1/bcsp_p1_pair_score_v1.py';src=scorer.read_text(encoding='utf8');gaps={needle:[i for i,line in enumerate(src.splitlines(),1) if needle in line] for needle in ["['C_T0','C_M0']","run['fold']=='C'","row['fold']=='C'",'FROZEN_EXISTING_FOLD_C_105_REFERENCES',"case['fold']=='C'",'==7']};need(all(gaps.values()),'known scorer compatibility gaps')
prep=dict(status='DRAFT_NOT_EXECUTABLE_REQUIRES_FOLDD_SCORE_ADAPTER',execution_request_created=False,fold='D',archive_verified=record(V/'verification_result_v1.json'),formal_prediction_audit=record(A/'audit_report_v1.json'),score_case_index=record(S/'P1_D_score_case_index_v1.json'),references=record(S/'reference_manifest_foldD_v1.json'),protocol=record(S/'unified_CPU_scoring_protocol_preparation_v1.json'),existing_C_scorer=record(scorer),metric_engine_to_keep_unchanged=record(metric),compatibility_evidence=gaps,cases=105,model_rows=210,shared_control_rows=210,total_case_rows=420,total_source_rows=84,local_references_rehashed=105,local_V1_point_files_rehashed=105,implementation_gaps=['C labels/fold/C reference status hardcoded','7 coarse representatives hardcoded; D has5 and10 saved coarse arrays','Remaining C-specific output labels/authorization and reader binding require bounded source review before final request'],minimum_next_implementation='Isolated Fold D scoring entry + targeted artificial CPU contracts + P3; metric definitions, references, controls and thresholds unchanged; then final pending execution request',real_scoring_executed=False,real_reference_or_point_arrays_decoded=False,server_operations=0,backup_writes=0,GPU_calls=0)
emit(S/'scoring_request_preparation_draft_v1.json',prep)
print(json.dumps(dict(verification_status=verification['status'],archive_sha256=verification['prediction_archive_sha256'],prediction_counts=counts,archive_members=215,coarse_arrays=10,reference_and_point_files_rehashed=210,preparation_status=prep['status'],scoring_executed=False,verification_sha256=sha(V/'verification_result_v1.json'),preparation_sha256=sha(S/'scoring_request_preparation_draft_v1.json')),indent=2))
