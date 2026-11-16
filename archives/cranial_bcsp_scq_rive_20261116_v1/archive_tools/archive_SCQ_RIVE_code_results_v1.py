"""Immutable local RIVE code/results archive. Public evidence separated from binaries."""
from pathlib import Path
import importlib.util,json,hashlib,re,shutil,tarfile
R=Path(__file__).resolve().parent.parent
sp=importlib.util.spec_from_file_location('archive_utils',R/'local_tools/archive_scq_BS_20261114_v1.py');u=importlib.util.module_from_spec(sp);sp.loader.exec_module(u)
D=R/'deliverables/scq_RIVE_20261116_v1';PUB=D/'public_payload';PRIVATE=D/'local_attachments'
BACK=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RIVE/2026-11-16_code_results_v1')
assert not D.exists() and not BACK.exists();D.mkdir(parents=True)
selected={};private={};excluded=[]
public_extensions={'.py','.json','.jsonl','.csv','.tsv','.md','.txt','.yaml','.yml','.sh','.ps1','.log','.pid','.patch','.diff','.sha256','.bytes','.png','.svg'}
roots=[p for p in (R/'outputs').iterdir() if p.is_dir() and p.name.startswith('scq_rive')]
roots += [R/'docs/cranial_bcsp_scq_rive_20261115',R/'docs/cranial_bcsp_scq_rive_20261116_final']
for root in roots:
    for p in u.inventory(root):
        if any(k in p.parts for k in ['__pycache__','.pytest_cache','mplconfig','.mypy_cache']):continue
        assert not u.lp(p).is_symlink(),str(p)
        key='evidence/'+p.relative_to(R).as_posix()
        if p.suffix in public_extensions:selected[key]=p
        elif p.suffix in {'.bin','.npz','.html','.gz'}:private[key]=p
        else:excluded.append(dict(path=p.relative_to(R).as_posix(),bytes=u.lp(p).stat().st_size,reason='Regenerable artificial fixture/checkpoint or unsupported runtime artifact; not a real final checkpoint.'))
for p in (R/'local_tools').glob('*RIVE*.py'):selected['archive_tools/'+p.name]=p
selected['archive_tools/archive_scq_BS_20261114_v1.py']=R/'local_tools/archive_scq_BS_20261114_v1.py'
# Exact inherited base package structure; no checkpoint/data/environment files.
base=R/'deliverables/cranial_bcsp_fullmamba_20261112_v1/public_payload/parent_source_snapshot'
for p in u.inventory(base):
    if p.suffix=='.py' or p.name=='LICENSE':selected['parent_source_snapshot/'+p.relative_to(base).as_posix()]=p
contexts=[json.loads(u.read(R/p)) for p in ['outputs/scq_rive_training_implementation_20261115_v1/implementation_context_v1.json','outputs/scq_rive_fourmodel_native_prediction_preparation_20261115_v1/implementation_v1/implementation_context_v1.json']]
mirror={};expected={}
def walk(x):
    if isinstance(x,dict):
        if all(k in x for k in ['path','bytes','sha256']) and isinstance(x['path'],str):expected.setdefault(x['path'],x)
        for v in x.values():walk(v)
    elif isinstance(x,list):
        for v in x:walk(v)
for ctx in contexts:mirror.update(ctx['mirror']);walk(ctx['candidate'])
bindings=[]
for remote,local in sorted(mirror.items()):
    p=Path(local)
    if '/data/' in remote or p.suffix in {'.pth','.npz','.so','.dll','.pyd'} or not u.lp(p).is_file():continue
    if p.suffix not in {'.py','.json','.jsonl','.yaml','.yml','.bin'}:continue
    if u.lp(p).stat().st_size>16*1024**2:continue
    digest=u.sha(p)
    if remote in expected:assert digest==expected[remote]['sha256'] and u.lp(p).stat().st_size==expected[remote]['bytes'],remote
    key='bound_shared_sources/'+hashlib.sha256(remote.encode()).hexdigest()[:12]+'_'+p.name
    (private if p.suffix=='.bin' else selected)[key]=p
    bindings.append(dict(remote_original=remote,source=str(p),member=('local_attachments/' if p.suffix=='.bin' else 'public_payload/')+key,bytes=u.lp(p).stat().st_size,sha256=digest))
contract=json.loads(u.read(R/'outputs/scq_rive_training_implementation_20261115_v1/RIVE_modeA_pair_contract_v1.json'))
for role,rec in contract['implementation_core'].items():
    assert any(b['remote_original']==rec['path'] and b['sha256']==rec['sha256'] for b in bindings),('Missing exact core',role)
metric=R/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py';selected['bound_shared_sources/'+metric.name]=metric
# Verify original downloaded prediction archive and every member, then include local-only copy.
native=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RIVE/2026-11-16_native_development_eval')
archive=native/'development_predictions_v1.tar.gz';assert u.sha(archive)=='4be9df6d5a5bf5620a14a6242c3c145fb198ae050e4a8abbef75247eafbe8b07' and archive.stat().st_size==45697569
expected_native={line.split('  ',1)[1]:line.split('  ',1)[0] for line in u.read(native/(archive.name+'.contents.sha256')).decode().splitlines() if line}
seen=set()
with tarfile.open(archive,'r|gz') as tar:
    for m in tar:
        assert m.isfile() and m.name in expected_native and m.name not in seen
        h=hashlib.sha256();count=0
        with tar.extractfile(m) as f:
            for b in iter(lambda:f.read(4194304),b''):h.update(b);count+=len(b)
        assert count==m.size and h.hexdigest()==expected_native[m.name];seen.add(m.name)
assert len(seen)==426 and seen==set(expected_native)
for p in [archive,*[native/(archive.name+s) for s in ['.bytes','.sha256','.contents.sha256']]]:private['native_prediction_archive/'+p.name]=p
patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',rb'Bearer\s+[A-Za-z0-9_.-]{30,}',rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@',rb'https?://[^\s\x22\x27]+[?&](?:access_token|auth_token|token)=[A-Za-z0-9_.%-]{20,}']
manifest=[]
for name,p in sorted(selected.items()):
    b=u.read(p);assert len(b)<50*1024**2 and not any(re.search(pat,b) for pat in patterns),('SECRET_OR_SIZE_STOP',name)
    u.put(PUB/name,b);manifest.append(dict(path=name,source=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
pm=[]
for name,p in sorted(private.items()):
    dest=PRIVATE/name;u.lp(dest.parent).mkdir(parents=True,exist_ok=True);shutil.copyfile(u.lp(p),u.lp(dest));assert u.sha(dest)==u.sha(p)
    pm.append(dict(path=dest.relative_to(D).as_posix(),source=str(p),bytes=u.lp(p).stat().st_size,sha256=u.sha(p)))
u.js(PUB/'source_file_manifest_v1.json',manifest);u.js(PUB/'local_only_manifest_v1.json',pm);u.js(PUB/'inherited_exact_bindings_v1.json',bindings);u.js(PUB/'excluded_regenerable_fixtures_v1.json',excluded)
report=next((R/'docs/cranial_bcsp_scq_rive_20261116_final').glob('*.md'));text=u.read(report).decode()
# Portable top-level reading copy; exact original report remains under evidence/.
for name,p in selected.items():text=text.replace(p.as_posix(),name)
text=text.replace((R/'outputs/scq_rive_stage_visual_20261116_v1/index.html').as_posix(),'FIGURES.md')
u.put(PUB/'REPORT_zh.md',text.encode())
panels=json.loads(u.read(R/'outputs/scq_rive_stage_visual_20261116_v1/stage_diagnostic_result_v1.json'))['panels']
gallery='# Fixed11 stage geometry panels\n\nExisting predictions only. Shared world bounds per case, static display subsampling only. Selected diagnostic cases, not unbiased efficacy evaluation.\n\n'
for p in panels:gallery+='## '+p['fold']+' '+p['case_id']+'\n\n!['+p['case_id']+'](evidence/outputs/scq_rive_stage_visual_20261116_v1/'+p['image']+')\n\n'
u.put(PUB/'FIGURES.md',gallery.encode())
u.put(PUB/'README.md',b'''# Cranial-BCSP-FullMamba: SCQ-RIVE, mode A closure

Read [the complete Chinese report](REPORT_zh.md). Four valid same-device, same-initialization paired Static/Requery models, Fold C/D, 3900 updates each; 420 Native predictions; 840 scoring rows including reused controls; all nine newly severe cases and two fixed improved controls diagnosed using existing Q0/Q1/Q2/dense predictions. No new model calls by archival.

Requery gains were fold-dependent: E_P95 delta C +0.586mm, D -0.655mm. Interface Cover@2mm decreased in both folds; nine newly severe and eight rescued cases. Current candidate closed, not promoted as reliably superior. Single seed, repeatedly exposed development sources, finite Mamba gradient nondeterminism, unexecuted bootstrap and incomplete planned Memory analysis are disclosed. No significance, equivalence or clinical reliability claim.

Public: exact source, configurations, scalar results, CPU/P3 and execution/freeze evidence, static PNG figures, full report and provenance manifests. Local-only: prediction/diagnostic arrays, raw captures, binary initializers and compressed transport artifacts. Four final paired checkpoints have their own local backup; never published here. Raw skull datasets, geometry-reference arrays and compiled runtime dependencies are excluded. Historical requests and launchers are inert provenance, not permission to rerun. All historical absolute paths require explicit rebinding; this is an archival source snapshot, not an automatically runnable environment.

Local complete code/results archive is individually member-hash verified. Annotated tag: cranial-bcsp-scq-rive-20261116-v1. No server files deleted.
''')
u.js(PUB/'checkpoint_identity_only_v1.json',dict(weights=[dict(run=r['arm']+'_'+r['fold'],**r['checkpoint']) for r in json.loads(u.read(R/'outputs/scq_rive_closure_decision_20261116_v1/RIVE_closure_decision_v1.json'))['training']],checkpoint_backup_directory='E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SCQ_RIVE/2026-11-16_key_checkpoints_v1',weights_not_in_this_archive=True,weights_not_on_GitHub=True))
print(json.dumps(dict(status='RIVE_PUBLIC_PRIVATE_SNAPSHOTS_READY',public_files=len(u.inventory(PUB)),private_files=len(pm),native_members_verified=426)),flush=True)
result=u.pack(D,u.inventory(PUB)+u.inventory(PRIVATE),D/'scq_RIVE_code_results_20261116_v1.tar.gz')
receipt=dict(status='RIVE_CODE_RESULTS_ALL_ARCHIVE_MEMBERS_VERIFIED',archive=result,public_files=len(u.inventory(PUB)),private_files=len(pm),source_files=len(manifest),core_bindings=len(contract['implementation_core']),native_members_verified=426,public_secret_pattern_scan='NO_MATCHES',weights_included=False,raw_datasets_included=False,server_calls=0,server_writes=0,forward=0)
u.js(D/'archive_verification_v1.json',receipt)
BACK.mkdir(parents=True)
files=[D/'scq_RIVE_code_results_20261116_v1.tar.gz',*[D/('scq_RIVE_code_results_20261116_v1.tar.gz'+s) for s in ['.bytes','.sha256','.contents.sha256']],D/'archive_verification_v1.json']
for p in files:
    dest=BACK/p.name;shutil.copyfile(p,dest);assert u.sha(dest)==u.sha(p)
expected={p.relative_to(D).as_posix():dict(bytes=u.lp(p).stat().st_size,sha256=u.sha(p)) for p in u.inventory(PUB)+u.inventory(PRIVATE)}
assert u.tar_verify(BACK/'scq_RIVE_code_results_20261116_v1.tar.gz',expected)==result['members']
backup=dict(status='RIVE_LONG_TERM_BACKUP_COPY_AND_ALL_MEMBER_READBACK_PASS',directory=str(BACK),archive=result,member_count=result['members'])
u.js(D/'long_term_backup_receipt_v1.json',backup);u.js(BACK/'long_term_backup_receipt_v1.json',backup)
print(json.dumps(dict(status=backup['status'],archive=result,backup=str(BACK))),flush=True)
