"""Archive EJTC code/evidence locally; stage text-only GitHub payload, no execution."""
from pathlib import Path
import gzip,hashlib,io,json,os,re,shutil,tarfile
R=Path(__file__).resolve().parents[1];base=R/'outputs/bcsp_ejtc_20261127_v2'
dest=Path('E:/ResearchBackups/AdaPoinTr/BCSP_EJTC/2026-11-28_code_results_archive_v1');dest.mkdir(exist_ok=True)
pub=R/'outputs/p1pub/archives/bcsp_ejtc_20261128_v1';pub.mkdir(exist_ok=True)
h=lambda raw:hashlib.sha256(raw).hexdigest()
def put(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b;return
 with p.open('xb') as f:f.write(b)
def write(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
files=sorted(p for p in base.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
files += list((R/'outputs').glob('*EJTC*报告*.md'))+list((R/'outputs').glob('BCSP-EJTC*正式实验计划*md'))+[Path(__file__).resolve()]
public_ext={'.py','.json','.jsonl','.md','.txt','.log','.sha256','.bytes','.yaml','.yml','.csv','.tsv','.ps1','.sh'}
patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'gh[pousr]_[A-Za-z0-9]{25,}',rb'github_pat_[A-Za-z0-9_]{30,}',rb'Bearer\s+[A-Za-z0-9_.-]{30,}',rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@']
selected={p.relative_to(R).as_posix():p for p in files};unresolved=[]
# Preserve exact inherited source/config dependencies from last installation map.
mapping=json.loads((base/'native_rtj315_preparation_v1/transport_h7vvrr_v2/EJTC_RTJ_D_native315_h7vvrr_install_mapping_v2.json').read_bytes())
wanted={p:r for p,r in mapping['reused_assets'].items() if Path(p).suffix in ('.py','.json','.yaml','.yml')}
byname={}
for directory,dirs,names in os.walk(R):
 dirs[:]=[n for n in dirs if n not in ('p1pub','.git','deliverables','__pycache__','.codex','.agents')]
 for name in names:
  if name in {Path(x).name for x in wanted}:
   p=Path(directory)/name
   if p.is_file():byname.setdefault(p.name,[]).append(p)
extra=list((R/'outputs/p1pub/archives/cranial_bcsp_fullmamba_20261112_v1/support_sources').rglob('*'))
resolved=[]
for remote,rec in wanted.items():
 matches=[p for p in byname.get(Path(remote).name,[])+extra if p.is_file() and p.stat().st_size==rec['bytes'] and h(p.read_bytes())==rec['sha256']]
 if not matches:unresolved.append(dict(remote_path=remote,**rec));continue
 p=sorted(matches,key=lambda p:(len(str(p)),str(p)))[0];selected[p.relative_to(R).as_posix()]=p
 resolved.append(dict(remote_path=remote,archived_path=p.relative_to(R).as_posix(),**rec))
assert all('/site-packages/' in r['remote_path'] or '/provider/' in r['remote_path'] for r in unresolved),unresolved
local_manifest=[];public_manifest=[];excluded=[]
payload=dest/'payload'
for name,p in sorted(selected.items()):
 assert not p.is_symlink();raw=p.read_bytes();put(payload/name,raw);local_manifest.append(dict(name=name,bytes=len(raw),sha256=h(raw)))
 if p.suffix.lower() in public_ext:
  for pattern in patterns:assert not re.search(pattern,raw),('Potential credential requires review',name)
  assert len(raw)<50*1024**2
  public_name='evidence/'+name
  if len(str(pub/public_name))>235:public_name='long_path_evidence/'+h(name.encode())[:24]+p.suffix
  put(pub/public_name,raw);public_manifest.append(dict(name=public_name,original_relative_path=name,bytes=len(raw),sha256=h(raw)))
 else:excluded.append(dict(name=name,bytes=len(raw),reason='Binary/runtime payload retained locally; not published'))
write(dest/'local_manifest_v1.json',local_manifest);write(pub/'public_manifest_v1.json',public_manifest)
write(pub/'dependency_source_mapping_v1.json',resolved);write(pub/'public_exclusions_v1.json',excluded)
write(pub/'environment_dependencies_not_vendored_v1.json',unresolved)
write(dest/'environment_dependencies_not_vendored_v1.json',unresolved)
readme='''# Cranial-BCSP-FullMamba · BCSP-EJTC

Frozen Fold D R/T/J experiment, archived 2026-11-28. D1 decision: **FAIL_STOP** under the original preregistered gates.

J improves shared-wall Cover@2 versus both R and T. J-T fails coarse far20 (+0.390625 pp; limit +0.25) and dense free-surface E Cover@2 (-0.877242 pp; limit -0.50). No Fold C, second-seed or SkullFix follow-on was run. This is not a claim of cross-seed stability or clinical implantation validity.

Includes protocol/report, implementation and tests, label replay identities, CUDA/training/prediction/scoring freeze evidence, source bootstrap summaries and bounded existing-prediction review. Files retain original relative workspace paths under `evidence/`. Dependencies are mapped by SHA256. These historical authorization/request records document prior runs; they do not authorize any new execution. Environment-specific paths require a new reviewed execution contract.

No real checkpoint, point arrays, binary predictions or raw medical segmentation is uploaded. The full local archive includes runtime binaries and artificial CPU fixtures; true R/T/J weights and Native archive have separate local backups and SHA256 manifests.

Report: `evidence/outputs/Cranial_BCSP_FullMamba_BCSP_EJTC_完整实验报告_zh_2026-11-28_v1.md`.
'''
put(pub/'README.md',readme.encode());put(dest/'README.md',readme.encode())
archive=dest/'BCSP_EJTC_code_results_full_v1.tar.gz'
with tarfile.open(archive,'x:gz',compresslevel=6) as t:
 for row in local_manifest:t.add(payload/row['name'],arcname=row['name'],recursive=False)
with tarfile.open(archive,'r:gz') as t:
 members=t.getmembers();assert len(members)==len(local_manifest)
 for member,row in zip(members,local_manifest):
  raw=t.extractfile(member).read();assert member.name==row['name'] and len(raw)==row['bytes'] and h(raw)==row['sha256']
archive_sha=h(archive.read_bytes());put(Path(str(archive)+'.sha256'),(archive_sha+'  '+archive.name+'\n').encode())
receipt=dict(status='EJTC_LOCAL_ARCHIVE_AND_PUBLIC_PAYLOAD_VERIFIED',local_archive=dict(path=str(archive),bytes=archive.stat().st_size,sha256=archive_sha,members=len(local_manifest)),local_payload=str(payload),public_payload=str(pub),public_files=len(public_manifest)+5,inherited_dependencies_resolved=len(resolved),external_environment_dependencies_recorded_not_vendored=len(unresolved),binary_files_local_only=len(excluded),credential_pattern_scan_pass=True,real_checkpoint_in_public=False,GitHub_pushed=False)
write(dest/'archive_receipt_v1.json',receipt);write(base/'EJTC_local_archive_receipt_v1.json',receipt)
print(json.dumps(receipt))
