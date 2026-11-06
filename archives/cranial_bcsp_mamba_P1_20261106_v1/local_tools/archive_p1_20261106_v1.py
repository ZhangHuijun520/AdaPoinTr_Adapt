import pathlib,json,hashlib,tarfile,re
R=pathlib.Path(__file__).resolve().parents[1];B=R/'outputs/cranial_bcsp_mamba_p1_20261104';O=R/'deliverables/cranial_bcsp_mamba_P1_20261106_v2';assert not O.exists();P=pathlib.Path('\\\\?\\'+str(O/'payload'));P.mkdir(parents=True)
allow={'.py','.md','.json','.jsonl','.csv','.yaml','.yml','.sh','.ps1','.png','.txt','.sha256','.bytes','.log'}
patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',rb'(?i)Bearer[ \t]+[A-Za-z0-9_.-]{24,}',rb'https?://[^\s/:@]+:[^\s/@]+@']
records=[];excluded=[]
def h(b):return hashlib.sha256(b).hexdigest()
def copy(p,rel):
 b=p.read_bytes();assert len(b)<50*1024**2;assert not any(re.search(x,b) for x in patterns),('sensitive_pattern',str(p));q=P/rel;q.parent.mkdir(parents=True,exist_ok=True)
 with q.open('xb') as f:f.write(b)
 assert q.read_bytes()==b;records.append(dict(path=rel,bytes=len(b),sha256=h(b)))
for p in sorted(B.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(R).as_posix();parts=p.relative_to(B).parts
 skip=any(x in {'__pycache__','mplconfig','transport_payload','frozen_evidence'} or x.startswith(('cpu_contract','CPU_contracts')) for x in parts[:-1])
 skip=skip or any(x in p.name for x in ['capture_v','status_observation','decoded_status','envelope_'])
 if skip or p.suffix.lower() not in allow or p.is_symlink():excluded.append(dict(path=rel,bytes=p.stat().st_size,reason='fixture/cache/duplicate/raw transport/array/weight/archive'));continue
 copy(p,rel)
scope=json.loads((R/'outputs/cranial_bcsp_geov1_20261024/gpu_preflight_plotting_lazy_v3/artificial_gpu_zero_update_frozen_scope_v3.json').read_text(encoding='utf8'))
for r in scope['bindings']['isolated_model_project_sources']:
 p=pathlib.Path(r['path']);assert h(p.read_bytes())==r['sha256'];copy(p,'parent_source_snapshot/'+r['relative_path'])
for r in scope['bindings']['candidate']:
 p=pathlib.Path(r['path']);assert h(p.read_bytes())==r['sha256'];copy(p,'parent_source_snapshot/'+r['relative_target'])
for rel in ['outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py','local_tools/invoke_bcsp_stage_trace_remote_once_v2.py','local_tools/archive_p1_20261106_v1.py']:copy(R/rel,rel)
readme='''# Cranial-BCSP-Mamba P1 frozen archive

P1 formally closed: four scratch runs T0/M0 x Fold C/D, seed0,3900updates/run,8192input/output,420development predictions. Stable Mamba superiority was not established. Fold C improves; Fold D regresses on E P95/CD; frontoorbital is a repeated risk.

Start at outputs/cranial_bcsp_mamba_p1_20261104/P1_full_experiment_report_20261106_v1 and P1_closeout_20261106_v1. Code, test sources, protocols, numeric policy, audits, saved scores, reports and14figures are included. Generated fixtures, caches, raw terminal captures and duplicate transport payloads are omitted. Finite parent model source and metric engine are included.

No weights or raw data redistributed. Prediction archives are separately verified in E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_FoldC_paired_development_eval and corresponding FoldD directory; evidence binds their hashes/member inventories. Weight hashes are provenance, not proof of local backup. This archive alone cannot restore model inference without external weights/data/providers. Historical Windows/server paths do not synchronize automatically.

H1 is an unimplemented next-phase draft, not a P1 result. Requests are consumed historical records, not replay instructions. No clinical certification or server deletion implied.
'''
(P/'README.md').write_text(readme,encoding='utf8');(P/'file_manifest_v1.json').write_text(json.dumps(records,indent=2),encoding='utf8');(O/'excluded_inventory_v1.json').write_text(json.dumps(excluded,indent=2),encoding='utf8')
a=O/'cranial_bcsp_mamba_P1_20261106_v1.tar.gz'
with tarfile.open(a,'x:gz') as t:
 for p in sorted(P.rglob('*')):
  if p.is_file():t.add(p,arcname=p.relative_to(P).as_posix(),recursive=False)
with tarfile.open(a) as t:
 ms=t.getmembers();assert len(ms)==len({m.name for m in ms})
 for m in ms:assert m.isfile() and t.extractfile(m).read()==(P/m.name).read_bytes()
for suffix,text in [('.sha256',h(a.read_bytes())+'  '+a.name+'\n'),('.bytes',str(a.stat().st_size)+'\n'),('.contents.sha256',''.join(h(p.read_bytes())+'  '+p.relative_to(P).as_posix()+'\n' for p in sorted(P.rglob('*')) if p.is_file()))]:(O/(a.name+suffix)).write_text(text,encoding='utf8')
r=dict(status='P1_ARCHIVE_ALL_MEMBERS_VERIFIED',archive=dict(path=str(a),bytes=a.stat().st_size,sha256=h(a.read_bytes())),members=len(ms),selected_source_files=len(records),payload_bytes=sum(p.stat().st_size for p in P.rglob('*') if p.is_file()),secrets_scan='PASS_NO_MATCH',weights_included=False,raw_data_included=False,server_operations=0)
(O/'archive_verification_v1.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps(r))
