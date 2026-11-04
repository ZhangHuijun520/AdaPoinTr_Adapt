"""Verify manual download,then execute already requested fixed local CPU scoring once."""
from pathlib import Path
import datetime,hashlib,json,os,subprocess,tarfile,time
N=Path(__file__).resolve().parent;D=Path('E:/ResearchBackups/AdaPoinTr/BCSP_INPUT_DENSITY_V1/2026-10-26_development_eval')
A=N/'local_scoring_v1';A.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def bind(p):return dict(path=str(Path(p).absolute()),bytes=Path(p).stat().st_size,sha256=sha(p))
def check(r):
 p=Path(r['path']);assert not any(x.is_symlink() for x in (p,*p.parents)) and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],'identity '+str(p);return p
def emit(name,obj):
 p=A/name
 with p.open('x',encoding='ascii') as f:json.dump(obj,f,ensure_ascii=True,indent=2,allow_nan=False)
 return p
phase='download_verification'
try:
 handoff=json.loads((N/'freeze_audit_v1/download_manifest_v1.json').read_bytes())
 audit=json.loads(check(handoff['audit_report']).read_bytes());assert audit['status']=='FORMAL_POST_PREDICTION_FREEZE_AUDIT_PASS'
 files=[]
 for r in handoff['files']:
  local=dict(path=str(D/r['filename']),bytes=r['bytes'],sha256=r['sha256']);check(local);files.append(local)
 archive=Path(files[0]['path']);live={r['name']:r for r in audit['prediction_manifest']}
 assert len(live)==423
 with tarfile.open(archive,'r:gz') as tar:
  members=tar.getmembers();assert len(members)==len({m.name for m in members})==423 and [m.name for m in members]==list(live)
  for m in members:
   assert m.isfile() and m.size==live[m.name]['bytes'] and m.size<=4194304
   data=tar.extractfile(m).read();assert len(data)==m.size and hashlib.sha256(data).hexdigest()==live[m.name]['sha256'],'member '+m.name
 contents=''.join(live[name]['sha256']+'  '+name+'\n' for name in live)
 assert (D/(archive.name+'.contents.sha256')).read_text()==contents
 assert (D/(archive.name+'.sha256')).read_text()==files[0]['sha256']+'  '+archive.name+'\n'
 assert (D/(archive.name+'.bytes')).read_text()==str(files[0]['bytes'])+'\n'
 verification=emit('download_verification.json',dict(status='LOCAL_FOUR_FILE_AND_423_MEMBER_VERIFICATION_PASS',files=files,archive_members=423,server_audit=handoff['audit_report'],Windows_download_confirmed_by_user=True,Windows_files_independently_verified=True,server_calls=0))
 print('LOCAL_DOWNLOAD_VERIFIED four files/423 members',flush=True)
 phase='frozen_implementation_and_reference_verification'
 p3=json.loads((N/'local_P3_v1.json').read_bytes())
 for name in ['bcsp_eval_metrics_v1.py','bcsp_development_score_v1.py']:check(p3['implementation'][name])
 manifest=check(p3['reference_manifest']);refs=json.loads(manifest.read_bytes());assert len(refs['cases'])==210 and len({r['case_id'] for r in refs['cases']})==210 and len({r['source_id'] for r in refs['cases']})==42
 for r in refs['cases']:
  check(r)
  for point in r['point_files'].values():check(point)
 index_path=check(p3['index']);index=json.loads(index_path.read_bytes());assert len(index['inputs'])==420 and len(index['runs'])==4
 assert {r['case_id'] for r in refs['cases']}=={r['case_id'] for r in index['inputs']}
 inner=json.loads((N/'development_entry_request_v1.json').read_bytes())
 plan=emit('scoring_plan_v1.json',dict(schema='bcsp-local-four-model-development-scoring-v1',status='AUTHORIZED_FIXED_CPU_SCORING',
  downloaded_prediction_archive=files[0],download_verification=bind(verification),reference_manifest=bind(manifest),input_index=bind(index_path),
  prediction_entry_request_sha256=audit['inner_request_sha256'],output=str(A/'results'),
  implementation={name:p3['implementation'][name] for name in ['bcsp_eval_metrics_v1.py','bcsp_development_score_v1.py']},
  primary='A1 area-weighted E_G_to_prediction P95 mm',delta='16k minus8k',bootstrap=10000,bootstrap_seed=20261024,
  limits=dict(wall_seconds=7200,RSS_bytes=8589934592,output_bytes=2147483648,threads=2),
  planned_scores=dict(model_predictions=420,controls=630,case_rows=1050,unique_cases=210,unique_sources=42),
  server_calls=0,GPU_calls=0,training=0,BNCal=0,retries=0))
 # The user requested conditional scoring after the formal audit and manual download;
 # the following turn supplied the exact downloaded location. Preserve both as provenance.
 emit('user_scope_provenance.json',dict(prior_user_instruction='下一步是正式只读冻结审计，重新核验预测清单、哈希及计数；通过后下载归档，统一评分，才能回答16k是否改善未知表面补全与接口吻合。',
  current_user_instruction='已下载到“E:\\ResearchBackups\\AdaPoinTr\\BCSP_INPUT_DENSITY_V1\\2026-10-26_development_eval”',
  interpretation='Continue the already requested conditional fixed CPU scoring after successful independent download verification;no new model operation.',UTC=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 auth=emit('scoring_authorization_v1.json',dict(schema='bcsp-local-score-authorization-v1',plan_sha256=sha(plan),explicit_user_authorization=True))
 command=[r'C:\Users\zhj\.conda\envs\adapointr\python.exe','-I','-B',str(N/'bcsp_development_score_v1.py'),'--plan',str(plan),'--plan-sha256',sha(plan),'--authorization',str(auth),'--authorization-sha256',sha(auth)]
 emit('attempt_started.json',dict(plan_sha256=sha(plan),authorization_sha256=sha(auth),command=command,server_calls=0,GPU_calls=0,retries=0))
 env=dict(os.environ);env.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
 phase='single_CPU_scoring';start=time.monotonic();print('FIXED_CPU_SCORING_STARTED 420 model predictions+630 controls',flush=True)
 with (A/'stdout.log').open('xb') as stdout,(A/'stderr.log').open('xb') as stderr:
  try:r=subprocess.run(command,stdout=stdout,stderr=stderr,env=env,timeout=7210);returncode=r.returncode;timed_out=False
  except subprocess.TimeoutExpired:returncode=None;timed_out=True
 status='LOCAL_CPU_SCORING_PROCESS_EXIT0' if returncode==0 and not timed_out else 'FAILED_STOP_NO_RETRY'
 emit('process_result.json',dict(status=status,returncode=returncode,timeout=timed_out,seconds=time.monotonic()-start,stdout=bind(A/'stdout.log'),stderr=bind(A/'stderr.log'),plan_sha256=sha(plan),server_calls=0,GPU_calls=0,retries=0))
 print(json.dumps(dict(status=status,returncode=returncode,timeout=timed_out,seconds=time.monotonic()-start)),flush=True)
 raise SystemExit(0 if returncode==0 and not timed_out else 1)
except Exception as exc:
 emit('wrapper_failure.json',dict(status='FAILED_STOP_NO_RETRY',phase=phase,error=repr(exc),server_calls=0,GPU_calls=0,retries=0));raise
