"""Freeze local code/results; preserve binary predictions privately, never checkpoints in public Git."""
import os,json,hashlib,re,tarfile,shutil
from pathlib import Path
R=Path(__file__).resolve().parent.parent;B=R/'outputs/cranial_bcsp_fullmamba_20261110'
D=R/'deliverables/cranial_bcsp_fullmamba_20261112_v1';P=D/'public_payload';L=D/'local_attachments'
BACK=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA/2026-11-12_code_results_v1')
assert not D.exists() and not BACK.exists(),'never overwrite a completed/failed archive attempt'
def lp(p):
 s=str(p.absolute());return Path('\\\\?\\'+s) if os.name=='nt' and not s.startswith('\\\\?\\') else p
def read(p):return lp(p).read_bytes()
def sha(p):
 h=hashlib.sha256()
 with lp(p).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def put(p,b):
 lp(p.parent).mkdir(parents=True,exist_ok=True)
 with lp(p).open('xb') as f:f.write(b)
def js(p,v):put(p,(json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
def emit(**v):print(json.dumps(v,ensure_ascii=True),flush=True)
allow={'.py','.json','.jsonl','.csv','.tsv','.md','.txt','.yaml','.yml','.sh','.ps1','.log','.bin','.sha256','.bytes','.pid','.html','.svg','.png','.patch','.diff'}
selected={};private_html={};excluded=[]
def collect(base,prefix='evidence',python_only=False):
 for directory,dirs,files in os.walk(lp(base),followlinks=False):
  dirs[:]=sorted(d for d in dirs if d not in {'__pycache__','.git','.pytest_cache','report_font_cache_v1','final_archival_20261112_v1'})
  for name in sorted(files):
   source=Path(str(Path(directory)/name).removeprefix('\\\\?\\'))
   assert not lp(source).is_symlink(),str(source)
   rel=source.relative_to(R).as_posix();target=prefix+'/'+rel
   if 'lqi_F0_geometry_visualization_v1' in source.parts and source.suffix=='.html':
    private_html['interactive_visualization/'+source.relative_to(B/'lqi_F0_geometry_visualization_v1').as_posix()]=source
   elif (python_only and source.suffix!='.py') or (not python_only and source.suffix not in allow):
    excluded.append(dict(path=rel,bytes=lp(source).stat().st_size,reason='unselected binary/archive/fixture or inherited non-source'))
   else:selected[target]=source
collect(B);collect(R/'docs/cranial_bcsp_fullmamba_20261110');collect(R/'reports/cranial_bcsp_fullmamba_20261112_v1')
collect(R/'outputs/cranial_bcsp_mamba_p1_20261104',python_only=True)
geo=R/'outputs/cranial_bcsp_geov1_20261024'
for directory,dirs,files in os.walk(lp(geo)):
 dirs[:]=[d for d in dirs if d not in {'__pycache__','fixtures','downloads','transport_payload','artificial_cpu_batch_v1','artificial_cpu_batch_v2'}]
 for n in files:
  if n.endswith('.py') and n.startswith(('bcsp_training_','bcsp_eval_metrics_')):
   source=Path(str(Path(directory)/n).removeprefix('\\\\?\\'));selected['evidence/'+source.relative_to(R).as_posix()]=source
snapshot=R/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot'
for p in snapshot.rglob('*'):
 if p.is_file():selected['parent_source_snapshot/'+p.relative_to(snapshot).as_posix()]=p
adapter=geo/'implementation_candidate_v4/overlay/tools/bcsp_adapter.py';assert adapter.is_file()
selected['evidence/'+adapter.relative_to(R).as_posix()]=adapter
license=R/'work/PoinTr/LICENSE';assert license.is_file();selected['parent_source_snapshot/LICENSE']=license
for n in ['archive_fullmamba_code_results_20261112_v1.py','prepare_fullmamba_checkpoint_archive_20261112_v1.py','invoke_fullmamba_archival_hash_probe_20261112_v1.py','invoke_fullmamba_archival_short_probe_20261112_v2.py','download_fullmamba_archival_assets_20261112_v1.py']:
 selected['archive_tools/'+n]=R/'local_tools'/n
for n in ['archive_scope_v1.json','remote_hash_verification_v1.json','diagnostic_local_receipt_v1.json']:
 source=B/'final_archival_20261112_v1'/n
 assert source.is_file()
 selected['evidence/'+source.relative_to(R).as_posix()]=source
patterns={
 'private_key':rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
 'github_token':rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',
 'aws_access':rb'AKIA[0-9A-Z]{16}',
 'bearer':rb'Bearer\s+[A-Za-z0-9_.-]{30,}',
 'credential_url':rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@',
 'jwt':rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',
 'token_url':rb'https?://[^\s\x22\x27]+[?&](?:access_token|auth_token|token)=[A-Za-z0-9_.%-]{20,}'}
findings=[]
for target,source in selected.items():
 b=read(source)
 for key,pat in patterns.items():
  if re.search(pat,b):findings.append(dict(path=target,rule=key))
 assert len(b)<50*1024**2,('public_file_too_large',target)
assert not findings,json.dumps(dict(secret_pattern_findings=findings))
emit(stage='scope_secret_scan_pass',public_source_files=len(selected),private_visualizations=len(private_html))
manifest=[]
for target,source in sorted(selected.items()):
 b=read(source);put(P/target,b);assert read(P/target)==b
 manifest.append(dict(path=target,source=str(source),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
js(P/'source_file_manifest_v1.json',manifest);js(P/'excluded_inventory_v1.json',excluded)
private=[]
for target,source in sorted(private_html.items()):
 b=read(source);put(L/target,b);assert sha(L/target)==sha(source)
 private.append(dict(path='local_attachments/'+target,source=str(source),bytes=len(b),sha256=sha(source)))
for source in (B/'lqi_F0_geometry_visualization_v1/figures').glob('*.png'):
 target='interactive_visualization/figures/'+source.name;b=read(source);put(L/target,b)
 assert sha(L/target)==sha(source)
 private.append(dict(path='local_attachments/'+target,source=str(source),bytes=len(b),sha256=sha(source)))
specs=[
 ('F0_native',Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_F0/2026-11-11_native_development_eval'),'32b80af60b4e3819e98c6bc096282e2bb71e3fe3b253e11c2a1623ec5e4aaac6'),
 ('LQI_native',Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_LQI/2026-11-11_native_development_eval'),'fbb06d406a4fd705df3c30463b32dc31f4b728a33546fed01dd142458f6f876e'),
 ('T0_M0_C_parent',Path('E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_FoldC_paired_development_eval'),'068dd9812c410c2b84451740a3ed2eb2f12326d8a66fe3bc3ee4623ab3f9b733'),
 ('T0_M0_D_parent',Path('E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_FoldD_paired_development_eval'),'8e9c7d5bc49ee91819a7c555ba6b34c5a936f60fcc6f468eadbfcbe4467b9af3'),
 ('F0_decoder_diagnostic',Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA/2026-11-12_decoder_diagnostic_v1'),'5082d0ac49ebc793fa2d8ba29a294b7b63eb17e5082e6c5a97e0b8ddf7cc0b1c')]
for label,folder,expected in specs:
 name='development_predictions_v1.tar.gz';archive=folder/name
 assert sha(archive)==expected and read(folder/(name+'.sha256')).decode().split()[0]==expected
 assert int(read(folder/(name+'.bytes')).decode().strip())==archive.stat().st_size
 checks={line.split('  ',1)[1]:line.split('  ',1)[0] for line in read(folder/(name+'.contents.sha256')).decode().splitlines() if line}
 seen=set()
 with tarfile.open(lp(archive),'r|gz') as tar:
  for m in tar:
   if m.isdir():continue
   assert m.isfile() and m.name in checks and m.name not in seen
   h=hashlib.sha256()
   with tar.extractfile(m) as f:
    for b in iter(lambda:f.read(4194304),b''):h.update(b)
   assert h.hexdigest()==checks[m.name],m.name
   seen.add(m.name)
 assert seen==set(checks)
 for suffix in ['', '.sha256','.bytes','.contents.sha256']:
  source=folder/(name+suffix);target=L/label/(name+suffix)
  lp(target.parent).mkdir(parents=True,exist_ok=True);assert not lp(target).exists()
  shutil.copyfile(lp(source),lp(target));assert sha(target)==sha(source)
  private.append(dict(path=target.relative_to(D).as_posix(),source=str(source),bytes=source.stat().st_size,sha256=sha(source)))
 emit(stage='private_archive_members_reverified',label=label,members=len(seen))
js(P/'local_attachment_reference_manifest_v1.json',private)
report=R/'reports/cranial_bcsp_fullmamba_20261112_v1/Cranial_BCSP_FullMamba_本轮完整实验报告_zh_2026-11-12_v1.md'
portable=read(report).decode('utf-8')
for entry in manifest:portable=portable.replace(']('+Path(entry['source']).as_posix()+')',']('+entry['path']+')')
portable=re.sub(r'\]\(E:/[^)]+\)','](LOCAL_ONLY_RESULTS.md)',portable)
put(P/'REPORT_zh.md',portable.encode())
put(P/'LOCAL_ONLY_RESULTS.md',b'# Local-only data and external evidence\n\nInteractive seven-case HTML, complete Native prediction arrays and decoder diagnostic traces are preserved inside local_attachments/ of the full local archive, not in this GitHub payload. In the root report, links to unselected local-only/external artifacts lead here. Exact original paths, hashes and evidence references remain unchanged in the original report under evidence/reports/ and in the manifests. Raw datasets, compiled environment/provider binaries and checkpoints are not included in this code/results archive. See README.md for separate checkpoint and parent-evidence boundaries.\n')
readme='''# Cranial-BCSP-FullMamba — formally closed round, 2026-11-12

Read [the complete Chinese experiment report](REPORT_zh.md). This round established the attention-free F0 encoder–decoder, performed 30 decoder-only conditional interventions, and evaluated a query-aligned interleaved local-conditioning (LQI) revision. Four new scratch runs (F0 C/D, LQI C/D) each completed 3,900 updates; 420 new Native predictions were scored against frozen T0/M0 references. F0 was not a stable improvement. LQI substantially improved Fold D relative to F0 but introduced serious failures in Fold C. These are closed research candidates, not a certified final method.

## Public code and results

`evidence/` preserves original implementation, tests, protocols, requests/authorizations, static/CPU/CUDA/P3 evidence, training/geometry/resource logs, prediction manifests, case/source scores, diagnostics, seven-case static figures, failed attempts and formal audits. `parent_source_snapshot/` preserves inherited AdaPoinTr/helper sources; selected P1 and BCSP training/metric dependencies retain original paths. The parent publication is `cranial-bcsp-mamba-p2-20261107-v1` (commit 9259190ad252cc0678d2f00f2eb109b8c8289c48); P1 and representation archives remain separate parent evidence.

`source_file_manifest_v1.json` binds exact source bytes to their original paths. `files.sha256` binds the public payload. REPORT_zh.md changes navigation links only; evidence copies retain original bytes and historical status. Historical absolute paths are provenance and do not imply filesystem synchronization or replay authorization.

## Local-only results and weights

The full local archive also includes five existing prediction/diagnostic archives and their sidecars (F0, LQI, reused T0/M0 C/D, and 30-intervention predictions/traces). Every archive member was rehashed without deserializing arrays. Interactive seven-case Plotly HTML is local-only because it embeds point arrays; static PNG figures remain public. `local_attachment_reference_manifest_v1.json` records these files, not their data.

Final checkpoints are excluded from this code/results archive and GitHub. Four exact final epoch99/step3900 F0/LQI C/D weights are handled in a separate local checkpoint archive. Raw NRRD/STL/input/reference datasets, compiled providers and Conda environments are excluded. Thus this archive is not a standalone retraining/inference/re-scoring environment. No server deletion, retraining or re-scoring is performed.

## Scientific limits

One seed, repeatedly used development sets, different training GPU UUID/driver between F0 and LQI, and finite native-Mamba gradient nondeterminism limit causal/reliability claims. No new bootstrap, p-values, formal gate or clinical certification. Conditional sensitivity is not accuracy, and final coarse geometry does not identify the earliest causal source. Future coarse spatial conditioning is a proposal only. Consumed requests are historical evidence, not permission to replay.

Secret-pattern checking found no listed patterns; this is bounded detection, not an unlimited guarantee. Public files are deliberately stored with Git text conversion disabled to retain hashes. Binary prediction archives and checkpoints are not pushed to GitHub.
'''
put(P/'README.md',readme.encode())
def entries(base,prefix=''):
 out=[]
 for directory,dirs,files in os.walk(lp(base)):
  for n in files:
   p=Path(str(Path(directory)/n).removeprefix('\\\\?\\'));out.append(dict(path=prefix+p.relative_to(base).as_posix(),bytes=lp(p).stat().st_size,sha256=sha(p)))
 return sorted(out,key=lambda x:x['path'])
public=entries(P);put(P/'files.sha256',''.join(e['sha256']+'  '+e['path']+'\n' for e in public).encode())
all_entries=entries(P,'public_payload/')+entries(L,'local_attachments/');all_entries.sort(key=lambda e:e['path'])
archive=D/'cranial_bcsp_fullmamba_code_results_20261112_v1.tar.gz'
emit(stage='compressing_local_archive',members=len(all_entries),public_bytes=sum(e['bytes'] for e in public),private_files=len(private))
with tarfile.open(lp(archive),'x:gz',compresslevel=3,format=tarfile.PAX_FORMAT) as tar:
 for e in all_entries:tar.add(str(lp(D/e['path'])),arcname=e['path'],recursive=False)
expected={e['path']:e for e in all_entries};seen=set()
with tarfile.open(lp(archive),'r|gz') as tar:
 for m in tar:
  assert m.isfile() and m.name in expected and m.name not in seen
  h=hashlib.sha256();size=0
  with tar.extractfile(m) as f:
   for b in iter(lambda:f.read(4194304),b''):size+=len(b);h.update(b)
  assert size==expected[m.name]['bytes'] and h.hexdigest()==expected[m.name]['sha256'];seen.add(m.name)
assert seen==set(expected)
ah=sha(archive)
put(D/(archive.name+'.sha256'),(ah+'  '+archive.name+'\n').encode())
put(D/(archive.name+'.bytes'),(str(archive.stat().st_size)+'\n').encode())
put(D/(archive.name+'.contents.sha256'),''.join(e['sha256']+'  '+e['path']+'\n' for e in all_entries).encode())
verification=dict(status='FULL_LOCAL_ARCHIVE_STREAM_READBACK_PASS',archive=dict(name=archive.name,bytes=archive.stat().st_size,sha256=ah),members=len(seen),public_files=len(entries(P)),public_bytes=sum(e['bytes'] for e in entries(P)),private_files=len(private),source_files=len(manifest),excluded_files=len(excluded),secret_scan=dict(status='NO_PATTERN_MATCHES',rules=list(patterns),files=len(selected)),checkpoint_included=False,model_calls=0,new_scoring=0,server_writes=0)
js(D/'archive_verification_v1.json',verification)
BACK.mkdir(parents=True);copies=[]
for n in [archive.name,archive.name+'.sha256',archive.name+'.bytes',archive.name+'.contents.sha256','archive_verification_v1.json']:
 source=D/n;target=BACK/n;shutil.copyfile(lp(source),lp(target));assert sha(source)==sha(target)
 copies.append(dict(path=str(target),bytes=target.stat().st_size,sha256=sha(target)))
receipt=dict(status='LOCAL_LONG_TERM_ARCHIVE_COPY_AND_INDEPENDENT_HASH_PASS',directory=str(BACK),files=copies,server_deletions=0)
js(D/'long_term_backup_receipt_v1.json',receipt);js(BACK/'long_term_backup_receipt_v1.json',receipt)
emit(**verification,backup_directory=str(BACK))
