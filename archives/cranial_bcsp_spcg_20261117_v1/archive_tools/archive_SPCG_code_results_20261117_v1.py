# -*- coding: utf-8 -*-
"""Archive SPCG code/results locally, separating public evidence and private arrays."""
from pathlib import Path
import importlib.util,json,hashlib,re,shutil,tarfile,os
R=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('archive_utils',R/'local_tools/archive_scq_BS_20261114_v1.py');u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
D=R/'deliverables/spcg_20261117_v1';PUB=D/'public_payload';PRIVATE=D/'local_attachments';BACK=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_code_results_v1')
assert not D.exists() and not BACK.exists();D.mkdir(parents=True)
selected={};private={};excluded=[];public_ext={'.py','.json','.jsonl','.csv','.tsv','.md','.txt','.yaml','.yml','.sh','.ps1','.log','.pid','.patch','.diff','.sha256','.bytes','.png','.svg'}
roots=[p for p in (R/'outputs').iterdir() if p.is_dir() and p.name.startswith('spcg')]+[R/'docs/cranial_bcsp_spcg_20261116_v2']
for root in roots:
 for p in u.inventory(root):
  if any(x in p.parts for x in ['__pycache__','.pytest_cache','mpl_cache','mplconfig','.mypy_cache']):continue
  assert not u.lp(p).is_symlink(),str(p)
  name='evidence/'+p.relative_to(R).as_posix()
  if p.suffix in public_ext:selected[name]=p
  elif p.suffix in {'.bin','.npz','.npy','.html','.gz','.pth','.pt'}:private[name]=p
  else:excluded.append(dict(path=str(p),bytes=u.lp(p).stat().st_size,reason='Unsupported/nonessential runtime artifact'))
for p in (R/'local_tools').glob('*SPCG*'):selected['archive_tools/'+p.name]=p
selected['archive_tools/archive_scq_BS_20261114_v1.py']=R/'local_tools/archive_scq_BS_20261114_v1.py'
base=R/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot'
assert base.is_dir()
for p in u.inventory(base):
 if p.suffix=='.py' or p.name=='LICENSE':selected['parent_source_snapshot/'+p.relative_to(base).as_posix()]=p
# Add exact inherited local code/config assets referenced by current metadata maps.
bindings=[];maps=list((R/'outputs/spcg_native_prediction_preparation_20261117_v1').rglob('local_metadata_map*.json'))
for m in maps:
 mapping=json.loads(u.read(m));assert isinstance(mapping,dict)
 for remote,local in mapping.items():
  if not isinstance(local,str):continue
  p=Path(local)
  if not u.lp(p).is_file() or '/data/' in remote or p.suffix not in {'.py','.json','.yaml','.yml','.sh','.bin'}:continue
  assert p.is_relative_to(R) and not u.lp(p).is_symlink()
  if u.lp(p).stat().st_size>16*1024**2:continue
  key='bound_shared_sources/'+hashlib.sha256(remote.encode()).hexdigest()[:12]+'_'+p.name
  (private if p.suffix=='.bin' else selected)[key]=p
  bindings.append(dict(remote_original=remote,source=str(p),member=('local_attachments/' if p.suffix=='.bin' else 'public_payload/')+key,bytes=u.lp(p).stat().st_size,sha256=u.sha(p)))
for name,rel in [('bcsp_eval_metrics_v1.py','outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py'),('shared_order_foldC_seed0_v1.json','outputs/cranial_bcsp_scq_foldC_training_preparation_20261113_v1/shared_order_foldC_seed0_v1.json')]:
 p=R/rel
 if p.is_file():selected['bound_shared_sources/'+name]=p
# Discover only explicit bound code/config files in selected JSON; never data/reference arrays.
seen=set();pending=[p for p in selected.values() if p.name in {'evidence_manifest_v1.json','implementation_context_v1.json','implementation_P3_v1.json'} and not any(x.startswith(('CPU_','artificial_')) for x in p.parts)];extra=[]
def walk(obj):
 if isinstance(obj,dict):
  if all(k in obj for k in ['path','bytes','sha256']) and isinstance(obj['path'],str):extra.append(obj)
  for v in obj.values():walk(v)
 elif isinstance(obj,list):
  for v in obj:walk(v)
for p in pending:
 try:walk(json.loads(u.read(p)))
 except (json.JSONDecodeError,UnicodeDecodeError):pass
for r in extra:
 p=Path(r['path'])
 if not p.is_absolute() or not p.is_relative_to(R) or not u.lp(p).is_file() or p.suffix not in {'.py','.yaml','.yml','.sh'}:continue
 if str(p) in seen:continue
 seen.add(str(p));assert u.lp(p).stat().st_size==r['bytes'] and u.sha(p)==r['sha256'],'bound inherited code drift '+str(p)
 key='bound_shared_sources/'+hashlib.sha256(str(p).encode()).hexdigest()[:12]+'_'+p.name;selected[key]=p
 bindings.append(dict(local_original=str(p),member='public_payload/'+key,bytes=r['bytes'],sha256=r['sha256']))
native=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_native_development_eval');archive=native/'development_predictions_v1.tar.gz'
assert archive.stat().st_size==58926842 and u.sha(archive)=='a2f3384a95906cad6523cd0eb0c0c9954a4bd4252017934b825da1f0d49f07c7'
expected={line.split('  ',1)[1]:line.split('  ',1)[0] for line in u.read(native/(archive.name+'.contents.sha256')).decode().splitlines() if line};seen_native=set()
with tarfile.open(archive,'r|gz') as t:
 for m in t:
  assert m.isfile() and m.name in expected and m.name not in seen_native
  h=hashlib.sha256();count=0
  with t.extractfile(m) as f:
   for b in iter(lambda:f.read(4194304),b''):h.update(b);count+=len(b)
  assert count==m.size and h.hexdigest()==expected[m.name];seen_native.add(m.name)
assert len(seen_native)==635 and seen_native==set(expected)
for p in [archive,*[native/(archive.name+s) for s in ['.sha256','.bytes','.contents.sha256']]]:private['native_prediction_archive/'+p.name]=p
patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',rb'Bearer\s+[A-Za-z0-9_.-]{30,}',rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@',rb'https?://[^\s\x22\x27]+[?&](?:access_token|auth_token|token)=[A-Za-z0-9_.%-]{20,}']
manifest=[];pm=[]
for name,p in sorted(selected.items()):
 b=u.read(p);assert len(b)<50*1024**2 and not any(re.search(pat,b) for pat in patterns),('SECRET_OR_SIZE_STOP',name)
 u.put(PUB/name,b);manifest.append(dict(path=name,source=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
for name,p in sorted(private.items()):
 if p.suffix=='.bin':assert not any(re.search(pat,u.read(p)) for pat in patterns),('PRIVATE_CAPTURE_SECRET_STOP',name)
 dest=PRIVATE/name;u.lp(dest.parent).mkdir(parents=True,exist_ok=True);shutil.copyfile(u.lp(p),u.lp(dest));assert u.sha(dest)==u.sha(p)
 pm.append(dict(path=dest.relative_to(D).as_posix(),source=str(p),bytes=u.lp(dest).stat().st_size,sha256=u.sha(dest)))
u.js(PUB/'source_file_manifest_v1.json',manifest);u.js(PUB/'local_only_manifest_v1.json',pm);u.js(PUB/'inherited_exact_bindings_v1.json',bindings);u.js(PUB/'excluded_runtime_artifacts_v1.json',excluded)
report=R/'outputs/spcg_experiment_report_20261117_v1/Cranial_BCSP_FullMamba_BCSP_SPCG_完整实验报告_zh_v1.md';content=u.read(report).decode('utf-8')
for name,p in selected.items():content=content.replace(p.as_posix(),name)
content=content.replace((R/'outputs/spcg_coarse_dense_visualization_20261117_v1/index.html').as_posix(),'FIGURES.md');u.put(PUB/'REPORT_zh.md',content.encode())
gallery='# SPCG fixed5 coarse/dense geometry panels\n\nPosthoc explanatory cases only; all3models, same world-mm bounds, no alignment or point deletion. Coarse256 versusdense8192 are unequal point budgets. Color saturation40mm affects display only.\n\n'
geo=json.loads(u.read(R/'outputs/spcg_coarse_dense_visualization_20261117_v1/fixed_case_geometry_metrics_v1.json'))
for c in geo['cases']:
 gallery+='## '+c['fold']+' '+c['case_id']+' / '+c['selection']+'\n\n'
 for name in c['figures']:gallery+='!['+name+'](evidence/outputs/spcg_coarse_dense_visualization_20261117_v1/'+name+')\n\n'
u.put(PUB/'FIGURES.md',gallery.encode())
u.put(PUB/'README.md',b'''# Cranial-BCSP-FullMamba: BCSP-SPCG closure

Read [the comprehensive Chinese report](REPORT_zh.md) and [fixed5 geometry panels](FIGURES.md).

Six G0/G1/G2 x Fold C/D models, 3900 updates each; 630 Native predictions, 1050 scoring rows (630model +420sharedcontrol), preregistered2000 paired-source bootstrap draws per fold. Current fixed local8 candidate is closed: G2 minusG1 E_P95 C +1.527mm, D +1.872mm; newly severe9/7, rescued4/0. C interface coverage gains do not replicate consistently. G1 not promoted. Single seed, exposed development data, D_G0 training-device confounding, finite gradient nondeterminism and missing Memory/probe/index captures remain explicit.

Public: exact code, configs, scalar scores, CSV/JSON, bootstrap index identities, execution/freeze and failure evidence, report, static figures and provenance. Local-only: prediction arrays, initializer/probe bytes, bootstrap NPY matrices, artificial binary fixtures and raw transport captures. All six final checkpoints are separately backed up locally, never uploaded to GitHub. Raw medical datasets, clinical/reference arrays and compiled environments are excluded.

Historical requests/authorization receipts/launchers are inert evidence, not permission to execute. Windows and server paths refer to different filesystems and require explicit rebinding. This is a source/evidence snapshot, not an automatic installer. Annotated tag: cranial-bcsp-spcg-20261117-v1. No server files deleted by archival.
''')
u.put(PUB/'RESTORATION.md',b'''# Restoration boundaries

Recover code/results from the complete local archive and verify its three sidecars plus every member hash. Recover the six final checkpoints from their separate local checkpoint archive and check training-audit identities. Restore the frozen source/fold point arrays and A1/A2/B reference bank from separately licensed original data; they are not bundled here. Restore compatible Mamba/PointNet2 providers, Python/Torch/CUDA and numerical settings from recorded manifests. Binary initializers/probes and bootstrap matrices remain in local attachments. Rebind paths and device identity explicitly before any separately authorized model call; do not run archived launchers unchanged. Archive verification does not establish executable environment recovery or clinical implant suitability.
''')
decision=json.loads(u.read(R/'outputs/spcg_scientific_decision_20261117_v1/scientific_decision_record_v1.json'))
u.js(PUB/'checkpoint_identity_only_v1.json',dict(weights=[dict(run=r['run'],**r['checkpoint']) for r in decision['training_matrix']],weights_not_in_this_archive=True,weights_not_on_GitHub=True,planned_checkpoint_backup='E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/2026-11-17_key_checkpoints_v1'))
print(json.dumps(dict(status='SPCG_PUBLIC_PRIVATE_SNAPSHOTS_READY',public_files=len(u.inventory(PUB)),private_files=len(pm),native_members_verified=635)),flush=True)
archive_result=u.pack(D,u.inventory(PUB)+u.inventory(PRIVATE),D/'spcg_code_results_20261117_v1.tar.gz')
u.js(D/'archive_verification_v1.json',dict(status='SPCG_CODE_RESULTS_ALL_MEMBERS_HASH_VERIFIED',archive=archive_result,public_files=len(u.inventory(PUB)),private_files=len(pm),native_members_verified=635,checkpoint_bytes_in_archive=False,server_operations=0))
BACK.mkdir(parents=True)
for p in [D/'spcg_code_results_20261117_v1.tar.gz',*[D/('spcg_code_results_20261117_v1.tar.gz'+s) for s in ['.sha256','.bytes','.contents.sha256']],D/'archive_verification_v1.json']:
 dest=BACK/p.name;shutil.copyfile(u.lp(p),u.lp(dest));assert u.sha(dest)==u.sha(p)
entries={r['path']:r for r in [u.record(p,D) for p in u.inventory(PUB)+u.inventory(PRIVATE)]};members=u.tar_verify(BACK/'spcg_code_results_20261117_v1.tar.gz',entries)
receipt=dict(status='SPCG_LONG_TERM_BACKUP_ALL_MEMBER_READBACK_PASS',directory=str(BACK),archive=dict(archive_result,path=str(BACK/'spcg_code_results_20261117_v1.tar.gz')),members=members,public_payload=str(PUB),private_payload=str(PRIVATE),server_writes=0,server_deletions=0)
u.js(D/'long_term_backup_receipt_v1.json',receipt);u.js(BACK/'long_term_backup_receipt_v1.json',receipt)
print(json.dumps(dict(status=receipt['status'],archive=receipt['archive'],backup=str(BACK))),flush=True)
