"""Read-only local backup/geometry binding verification; no scores or model imports."""
import ast,hashlib,io,json,math,struct,tarfile,time,zipfile
from collections import Counter
from pathlib import Path,PurePosixPath
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
P2=HERE.parent;H=P2/'H1_prediction_implementation_v1';P1=ROOT/'outputs/cranial_bcsp_mamba_p1_20261104'
START=time.monotonic();files={};stamps={}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def stamp(p):
 s=p.stat();return s.st_size,s.st_mtime_ns,s.st_ctime_ns
def rec(p,expected=None):
 p=p.absolute();assert p.is_file() and not any(x.is_symlink() for x in (p,*p.parents)),str(p)
 if str(p) not in files:
  before=stamp(p);r=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p));assert stamp(p)==before
  files[str(p)]=r;stamps[str(p)]=before
 r=files[str(p)]
 if expected:assert r['bytes']==expected['bytes'] and r['sha256']==expected['sha256'],str(p)
 return r
def read(p):rec(p);return json.loads(p.read_bytes())
def emit(n,x):
 with (HERE/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def arrays(raw,coarse):
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  wanted={'prediction.npy'}|({'coarse.npy'} if coarse else set());assert set(z.namelist())==wanted and len(z.namelist())==len(wanted)
  for name in wanted:
   b=z.read(name);assert b[:6]==b'\x93NUMPY' and tuple(b[6:8]) in [(1,0),(2,0)]
   offset=10 if b[6]==1 else 12;length=int.from_bytes(b[8:offset],'little')
   header=ast.literal_eval(b[offset:offset+length].decode('latin1'));n=8192 if name=='prediction.npy' else 256
   assert header==dict(descr='<f4',fortran_order=False,shape=(n,3));data=b[offset+length:]
   assert len(data)==n*3*4 and all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',data))
def verify_archive(directory,downloads,index,protocol,request_sha,expected_status):
 directory=Path(directory);records=[]
 for r in downloads:records.append(rec(directory/PurePosixPath(r['path']).name,r))
 A=directory/'development_predictions_v1.tar.gz'
 side=(directory/(A.name+'.contents.sha256')).read_text().splitlines()
 pairs=[line.split(None,1) for line in side];assert all(len(x)==2 for x in pairs)
 expected={n:h for h,n in pairs};assert len(pairs)==len(expected)==215
 names=['predictions/'+r['run']+'__'+r['case_id']+'.npz' for r in index['inputs']]+['inference_manifest.jsonl','forward_attempts.jsonl','geometry_summary.jsonl','inference_complete.json','resources.jsonl']
 assert set(expected)==set(names) and len(names)==215
 metadata={};npzcount=0;coarsecount=0
 with tarfile.open(A) as t:
  ms=t.getmembers();assert [m.name for m in ms]==names and len(ms)==len(set(m.name for m in ms))==215
  for m in ms:
   assert m.isfile() and 0<m.size<=4194304 and not PurePosixPath(m.name).is_absolute() and '..' not in PurePosixPath(m.name).parts
   raw=t.extractfile(m).read();assert len(raw)==m.size and hashlib.sha256(raw).hexdigest()==expected[m.name]
   if m.name.startswith('predictions/'):
    label,cid=PurePosixPath(m.name).stem.split('__',1);fold=label[0]
    representatives=protocol['coarse_tensor_cases_by_fold'][fold] if 'coarse_tensor_cases_by_fold' in protocol else protocol['coarse_tensor_cases']
    keep=cid in representatives;arrays(raw,keep);npzcount+=1;coarsecount+=int(keep)
   else:metadata[m.name]=raw
 assert npzcount==210
 assert (directory/(A.name+'.sha256')).read_text()==rec(A)['sha256']+'  '+A.name+'\n'
 assert (directory/(A.name+'.bytes')).read_text()==str(A.stat().st_size)+'\n'
 done=json.loads(metadata['inference_complete.json']);assert done['status']==expected_status and done['forwards']==210 and done['request_sha256']==request_sha
 assert all(done[k]==0 for k in ['training_updates','BNCal','loss','backward'])
 assert all(m['state_before']==m['state_after'] and m['RNG_before']==m['RNG_after'] for m in done['models'])
 manifest=[json.loads(s) for s in metadata['inference_manifest.jsonl'].splitlines()]
 assert len(manifest)==210
 for i,(row,source) in enumerate(zip(manifest,index['inputs']),1):
  assert row['forward_index']==i and all(row[k]==source[k] for k in ['run','case_id','source_id','fold','normalization'])
  assert row['input_sha256']==source['input']['sha256'] and row['prediction']['sha256']==expected[row['prediction']['name']]
  run=next(r for r in index['runs'] if r['label']==row['run']);assert row['checkpoint_sha256']==run['checkpoint']['sha256']
 return dict(status='LOCAL_ARCHIVE_ALL_MEMBERS_ARRAYS_PASS',directory=str(directory),files=records,archive=rec(A),members=215,predictions=210,coarse_arrays=coarsecount,manifest=manifest,metadata_sha256={k:hashlib.sha256(v).hexdigest() for k,v in metadata.items()})

try:
 auditpath=H/'post_prediction_freeze_audit_20261107_v1/audit_report_v1.json';audit=read(auditpath)
 assert audit['status']=='FORMAL_P2_H1_TWOFOLD_POST_PREDICTION_FREEZE_AUDIT_PASS' and all(audit['checks'].values())
 idx=read(H/'H1_C_D_input_index_v1.json');pro=read(H/'H1_C_D_prediction_protocol_v1.json')
 directory=Path('E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P2_H1/2026-11-07_C_D_development_eval')
 h1=verify_archive(directory,audit['evidence']['archive']['download_files'],idx,pro,audit['request_sha256'],'P2_H1_TWOFOLD_210_FORWARD_COMPLETE')
 assert h1['coarse_arrays']==12
 print(json.dumps(dict(stage='H1_LOCAL_DOWNLOAD_PASS',predictions=210,members=215)),flush=True)
 baselines={};cases=[];selected={};reference_bindings=[]
 for fold,sub,scorefile in [('C','paired_development_evaluator_v2','P1_score_case_index_v1.json'),('D','FoldD_paired_development_entry_v1','P1_D_score_case_index_v1.json')]:
  S=P1/sub;oldidx=read(S/'transport_payload/paired_development_input_index_v1.json');oldpro=read(S/'transport_payload/paired_development_protocol_v1.json');oldaudit=read(S/'post_prediction_freeze_audit_v1/audit_report_v1.json')
  assert oldaudit['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS'
  bdir=Path('E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1')/('2026-11-06_Fold'+fold+'_paired_development_eval')
  base=verify_archive(bdir,oldaudit['download_files'],oldidx,oldpro,oldaudit['request_sha256'],'P1_PAIR_210_FORWARD_COMPLETE')
  baselines[fold]=base
  oldrows=[r for r in oldidx['inputs'] if r['run']==fold+'_M0'];newrows=[r for r in idx['inputs'] if r['fold']==fold]
  caseidx=read(S/'CPU_scoring_preparation_v1'/scorefile);assert len(caseidx['cases'])==105
  for c,a,b in zip(caseidx['cases'],oldrows,newrows):
   assert all(c[k]==a[k]==b[k] for k in ['case_id','source_id','fold','normalization','normalization_source','target_array_sha256'])
   assert a['input']==b['input'] and all(c['point_file'][k]==a['input'][k] for k in ['bytes','sha256'])
   rec(Path(c['reference']['path']),c['reference']);rec(Path(c['point_file']['path']),c['point_file'])
   reference_bindings.extend([c['reference'],c['point_file']]);cases.append(c)
  selected[fold]=dict(baseline_label=fold+'_M0',H1_label=fold+'_M_H1',cases=105,sources=21,baseline_archive=base['archive'])
  print(json.dumps(dict(stage='BASELINE_REFERENCE_PAIR_PASS',fold=fold,cases=105,opaque_reference_point_files=210)),flush=True)
 assert len(cases)==len({c['case_id'] for c in cases})==210 and len({c['source_id'] for c in cases})==42
 assert set(Counter(c['source_id'] for c in cases).values())=={5}
 assert all(stamp(Path(p))==s for p,s in stamps.items())
 metric=ROOT/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py'
 assert rec(metric)['sha256']=='af938519125b25b6d22d862dd4967dabef3be6d97d38e60eb9995ee7e9ce9766'
 scorer=P1/'paired_development_evaluator_v2/scoring_implementation_v1/bcsp_p1_pair_score_v1.py'
 source=scorer.read_text(encoding='utf-8');anchors={n.name:dict(start=n.lineno,end=n.end_lineno) for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in ['authorize','validate_index','validate_archive','score_case','case_differences','source_summary','main']}
 emit('local_archive_and_pair_verification_v1.json',dict(status='LOCAL_H1_AND_BASELINE_ARCHIVES_REFERENCE_PAIR_PASS',H1=h1,baselines=baselines,unique_cases=210,unique_sources=42,reference_point_files_rehashed=420,reference_GT_or_input_arrays_decoded=False,all_input_stamps_unchanged=True,backup_writes=0,server_operations=0,scoring_executed=False,seconds=time.monotonic()-START))
 emit('H1_M0_twofold_score_case_index_candidate_v1.json',dict(schema='bcsp-p2-H1-M0-twofold-score-index-candidate-v1',status='FROZEN_METADATA_SCORING_NOT_EXECUTED',cases=cases,pairing=selected,H1_archive=h1['archive'],metric=rec(metric),input_references_unchanged=True))
 emit('unified_CPU_scoring_protocol_candidate_v1.json',dict(status='PENDING_SCORER_ADAPTATION_NOT_EXECUTABLE',arms=['M0','M_H1'],folds=['C','D'],unique_cases=210,sources=42,defects_per_source=5,model_rows=420,shared_control_rows=420,total_case_rows=840,total_source_rows=168,controls=['Nop_D','GT_8192'],delta='M_H1 minus M0',primary='A1 area-weighted E_P95 mm; five defects/source then21sources equally within each fold',geometry_labels=dict(placement_tail='centroid>20mm',compact_distribution='radius_ratio<0.9',severe_geometry='E_P95>20mm OR J_Cover2mm==0'),metrics='Exact inherited E/J/CD/reverse A2/coarse-dense metrics; frozen units/references/thresholds',reporting='Per fold, source, case, defect and new/rescued/shared severe transitions; no case filtering',bootstrap=0,p_values=False,formal_gate_execution=False,limits=dict(wall_seconds=14400,RSS_bytes=8589934592,output_bytes=2147483648,threads=2),budget_reason='Two folds/840 rows rather than prior singlefold420 rows; wall budget twice7200, same RAM/output/thread limits; no accuracy threshold change',prohibited=['server/WSL/network','Torch/GPU/checkpoint','training/new forward/BNCal','ICP/GT alignment','threshold/reference/GT/point changes','backup extraction/writes/deletion','scoring before final implementation/P3 and separate hash authorization']))
 emit('scoring_request_preparation_draft_v1.json',dict(status='REQUIRES_LIMITED_SCORER_ADAPTATION',is_execution_request=False,final_execution_request_created=False,existing_scorer=rec(scorer),source_anchors=anchors,metric_engine=rec(metric),compatibility_blockers=['Hardcoded T0/M0 arms and delta names','One fold105cases/21sources and one210prediction archive; new task uses H1 twofold archive plus two baseline archives','H1 eval completion status/labels and per-fold7/5coarse differ','Per-fold geometry/reference/index/source summary routing must be exact;840 score rows168source rows'],minimum_implementation='One isolated H1/M0 twofold scoring entry, targeted artificial CPU contracts, P3 then final pending request; metric core unchanged',scoring_executed=False,implementation_modified=False,server_operations=0))
 print(json.dumps(dict(status='LOCAL_VERIFICATION_PASS_SCORER_ADAPTATION_REQUIRED',H1_predictions=210,baseline_archives=2,reference_point_files=420,planned_case_rows=840,scoring_executed=False)))
except BaseException as e:
 emit('failure_v1.json',dict(status='VERIFICATION_FAILED_STOP',error=repr(e),seconds=time.monotonic()-START));raise
