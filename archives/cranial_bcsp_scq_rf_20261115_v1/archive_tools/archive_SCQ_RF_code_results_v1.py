"""Local immutable SCQ-RF archival; public text/static figures separate from binary arrays."""
from pathlib import Path
import importlib.util,json,hashlib,os,re,shutil,sys
R=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('scq_archive_utils',R/'local_tools/archive_scq_BS_20261114_v1.py');u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
D=R/'deliverables/scq_RF_20261115_v1';PUB=D/'public_payload';PRIVATE=D/'local_attachments'
BACK=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_code_results_v1')
assert not D.exists() and not BACK.exists();D.mkdir(parents=True)
read=u.read;sha=u.sha;put=u.put;js=u.js;inventory=u.inventory
report=R/'docs/cranial_bcsp_scq_rf_20261115_final/Cranial_BCSP_FullMamba_SCQ_RF_完整实验报告_zh_2026-11-15_v1.md'
manifest=json.loads(read(report.parent/'report_evidence_manifest_v1.json'));assert sha(report)==manifest['report']['sha256']
for r in manifest['source_evidence']:assert sha(Path(r['path']))==r['sha256']
selected={};private={};excluded=[]
text={'.py','.json','.jsonl','.csv','.tsv','.md','.txt','.yaml','.yml','.sh','.ps1','.log','.pid','.patch','.diff','.sha256','.bytes','.png','.svg'}
roots=[p for p in (R/'outputs').iterdir() if p.is_dir() and p.name.startswith('scq_rf')]
roots += [R/'docs/cranial_bcsp_scq_rf_20261114',report.parent]
for root in roots:
 for p in inventory(root):
  if set(p.parts)&{'__pycache__','.pytest_cache','mpl_cache'}:continue
  assert not u.lp(p).is_symlink();target='evidence/'+p.relative_to(R).as_posix()
  if p.suffix in text:selected[target]=p
  elif p.suffix in {'.bin','.npz','.html','.pth'} or p.name.endswith('.tar.gz'):private[target]=p
  else:excluded.append(dict(path=p.relative_to(R).as_posix(),bytes=u.lp(p).stat().st_size,reason='unsupported type, no runtime environment or raw datasets included'))
# Preserve exact local operational scripts without modifying scientific source.
for p in (R/'local_tools').glob('*.py'):
 if any(x in p.name.lower() for x in ['scq_rf','_rf_','static_d_','rf_six','rf_three','rf_fixed','rf_native','rf_input','rf_prediction','rf_score','scq_rf_final']):selected['archive_tools/'+p.name]=p
selected['archive_tools/'+Path(__file__).name]=Path(__file__)
metric=R/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py';selected['evidence/'+metric.relative_to(R).as_posix()]=metric
# A self-contained source snapshot of inherited Python classes, not old prediction/weight arrays.
parent=R/'deliverables/scq_BS_20261114_v1/public_payload'
for p in inventory(parent):
 if p.suffix=='.py' or p.name=='LICENSE':selected['inherited_scq_bs/'+p.relative_to(parent).as_posix()]=p
# Bound shared source/config/initializer files from actual training+prediction mirrors.
mirrorfile=R/'outputs/scq_rf_sixmodel_native_prediction_preparation_20261115_v1/implementation_v1/input_path_fix_v2/pending_request_v2/local_mirror_v2.json'
mirror=json.loads(read(mirrorfile));bindings=[]
for remote,local in mirror.items():
 p=Path(local)
 if not u.lp(p).is_file():continue
 if '/data/' in remote or p.suffix in {'.pth','.npz'}:continue
 if p.suffix in {'.py','.yaml','.yml','.json','.jsonl','.bin'} and u.lp(p).stat().st_size<16*1024**2:
  key='bound_shared_sources/'+hashlib.sha256(remote.encode()).hexdigest()[:12]+'_'+p.name
  if p.suffix=='.bin':private[key]=p
  else:selected[key]=p
  bindings.append(dict(remote_original=remote,archive_member=('local_attachments/' if p.suffix=='.bin' else 'public_payload/')+key,bytes=u.lp(p).stat().st_size,sha256=sha(p)))
patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',rb'Bearer\s+[A-Za-z0-9_.-]{30,}',rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@',rb'https?://[^\s\x22\x27]+[?&](?:access_token|auth_token|token)=[A-Za-z0-9_.%-]{20,}']
public_manifest=[]
for target,p in sorted(selected.items()):
 b=read(p);assert len(b)<50*1024**2,('public size',target);assert not any(re.search(pat,b) for pat in patterns),('credential_pattern_stop',target)
 put(PUB/target,b);public_manifest.append(dict(path=target,source=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
js(PUB/'source_file_manifest_v1.json',public_manifest);js(PUB/'bound_shared_source_mapping_v1.json',bindings);js(PUB/'excluded_inventory_v1.json',excluded)
print(json.dumps(dict(stage='PUBLIC_SNAPSHOT_AND_CREDENTIAL_SCAN_PASS',files=len(public_manifest))),flush=True)
private_manifest=[]
for target,p in sorted(private.items()):
 dest=PRIVATE/target;u.lp(dest.parent).mkdir(parents=True,exist_ok=True);shutil.copyfile(u.lp(p),u.lp(dest));assert sha(dest)==sha(p)
 private_manifest.append(dict(path=dest.relative_to(D).as_posix(),source=str(p),bytes=u.lp(p).stat().st_size,sha256=sha(dest)))
native=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_native_development_eval')
verification=json.loads(read(R/'outputs/scq_rf_score_prep_20261115_v1/local_archive_verification_v1.json'))
assert verification['status']=='LOCAL_SCQ_RF_FOUR_FILES_ALL636_MEMBERS_VERIFIED'
for r in verification['files']:
 p=Path(r['path']);assert p.parent==native and sha(p)==r['sha256'] and p.stat().st_size==r['bytes'];dest=PRIVATE/'native_predictions'/p.name
 u.lp(dest.parent).mkdir(parents=True,exist_ok=True);shutil.copyfile(u.lp(p),u.lp(dest));assert sha(dest)==r['sha256'];private_manifest.append(dict(path=dest.relative_to(D).as_posix(),source=str(p),bytes=r['bytes'],sha256=r['sha256']))
js(PUB/'local_only_reference_manifest_v1.json',private_manifest)
portable=read(report).decode('utf-8')
def replace(m):
 target=m.group(1)
 if target.startswith(('https:','http:','#')):return m.group(0)
 p=Path(target)
 try:key='evidence/'+p.relative_to(R).as_posix()
 except ValueError:return '](LOCAL_ONLY_RESULTS.md)'
 return ']('+key+')' if key in selected else '](LOCAL_ONLY_RESULTS.md)'
portable=re.sub(r'\]\(([^)]+)\)',replace,portable);put(PUB/'REPORT_zh.md',portable.encode())
put(PUB/'LOCAL_ONLY_RESULTS.md',b'# Local-only SCQ-RF assets\n\nFull prediction/Memory arrays, binary raw readbacks and initialization files, interactive point-cloud HTML, synthetic binary fixtures and transport archives are in local_attachments/ of the verified local archive. Six key final checkpoints are backed up separately, never to GitHub. Source manifests preserve exact original byte identities. Original absolute bindings remain historical provenance, not automatically executable paths. No datasets, compiled environments or credentials are included.\n')
readme='''# Cranial-BCSP-FullMamba: SCQ-RF closed round, 2026-11-15

Read [the complete Chinese report](REPORT_zh.md). This snapshot preserves the spatial re-query feedback study: ten-case actual Memory feasibility, isolated RF code, artificial CPU/native CUDA evidence, six3900-step training runs,630 Native prediction identities,1050-case-row scoring, formal freeze audits, seven-case stage diagnostics and failure history.

S-ref uses the frozen first SCQ head; Static and Requery add matched231171-parameter heads with the sole neighbor-selection branch. Fold C supports a developmental average benefit from Requery, while severe regressions and type-specific failures remain. Static_D training migrated GPU UUID/driver; D comparisons involving Static are confounded supplementary evidence. One seed per fold, reused development cases; no significance/clinical or formal-gate claim.

Public files contain code, configurations, scalar evidence and static figures. Arrays, binary initializers, raw readbacks, interactive HTML and all checkpoints are local-only. Clinical/raw datasets and compiled dependency binaries are not part of this snapshot. Historical authorizations are evidence, not permission to rerun. Root REPORT_zh.md changes navigation only; original evidence bytes remain unaltered. No new model execution/scoring/server deletion is performed by this archive.

The complete local archive (public_payload + local_attachments) is independently verified member-by-member, with SHA256, byte count and member sidecars, and copied to E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RF/2026-11-15_code_results_v1. The GitHub snapshot is not a substitute for local arrays/weights or a portable complete runtime. See source_file_manifest_v1.json, bound_shared_source_mapping_v1.json and local_only_reference_manifest_v1.json.
'''
put(PUB/'README.md',readme.encode());files=inventory(PUB);put(PUB/'public_files.sha256',''.join(sha(p)+'  '+p.relative_to(PUB).as_posix()+'\n' for p in files).encode())
print(json.dumps(dict(stage='LOCAL_ARCHIVE_COMPRESSION',public_files=len(files)+1,private_files=len(private_manifest))),flush=True)
archive=u.pack(D,inventory(PUB)+inventory(PRIVATE),D/'scq_RF_code_results_20261115_v1.tar.gz')
receipt=dict(status='SCQ_RF_LOCAL_CODE_RESULTS_ALL_MEMBERS_VERIFIED',archive=archive,public_files=len(inventory(PUB)),private_files=len(private_manifest),checkpoint_included=False,secret_scan='NO_PATTERN_MATCHES',server_writes=0,server_deletions=0)
js(D/'archive_verification_v1.json',receipt);BACK.mkdir(parents=True);copies=[]
for p in [D/'scq_RF_code_results_20261115_v1.tar.gz',*(D/('scq_RF_code_results_20261115_v1.tar.gz'+s) for s in ['.sha256','.bytes','.contents.sha256']),D/'archive_verification_v1.json']:
 dst=BACK/p.name;shutil.copyfile(u.lp(p),u.lp(dst));assert sha(dst)==sha(p);copies.append(u.record(dst,BACK))
local_archive=BACK/'scq_RF_code_results_20261115_v1.tar.gz'
expected={}
for p in inventory(PUB)+inventory(PRIVATE):expected[p.relative_to(D).as_posix()]=dict(bytes=u.lp(p).stat().st_size,sha256=sha(p))
assert u.tar_verify(local_archive,expected)==archive['members']
backup_receipt=dict(status='SCQ_RF_LONG_TERM_COPY_AND_MEMBER_READBACK_PASS',directory=str(BACK),files=copies,archive_member_count=archive['members'])
js(D/'long_term_backup_receipt_v1.json',backup_receipt);js(BACK/'long_term_backup_receipt_v1.json',backup_receipt)
print(json.dumps(dict(status=backup_receipt['status'],archive=archive,public_files=receipt['public_files'],private_files=receipt['private_files'])),flush=True)
