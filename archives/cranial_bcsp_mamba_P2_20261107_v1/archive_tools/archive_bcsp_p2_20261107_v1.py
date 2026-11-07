"""Non-executing archive of P2 code/results, plus private saved prediction archives."""
import hashlib
import json
import os
import re
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT/'deliverables/cranial_bcsp_mamba_P2_20261107_v1'
PUBLIC=DEST/'public_payload'
PRIVATE=DEST/'local_attachments'
assert not DEST.exists(), 'do not overwrite an archive attempt'


def long(p):
    s=str(p.absolute())
    return Path('\\\\?\\'+s) if os.name=='nt' and not s.startswith('\\\\?\\') else Path(s)


def read(p): return long(p).read_bytes()
def sha(b): return hashlib.sha256(b).hexdigest()
def write(p,b):
    long(p.parent).mkdir(parents=True,exist_ok=True)
    with long(p).open('xb') as f:f.write(b)


allowed={'.py','.json','.jsonl','.csv','.tsv','.md','.txt','.yaml','.yml','.sh','.ps1','.log','.bin','.sha256','.bytes','.pid','.html','.svg','.png'}
patterns={
 'private_key':re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'github_token':re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})'),
 'aws_access':re.compile(rb'AKIA[0-9A-Z]{16}'),
 'bearer':re.compile(rb'Bearer\s+[A-Za-z0-9_.-]{30,}'),
 'credential_url':re.compile(rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@'),
 'jwt':re.compile(rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}'),
 'token_url':re.compile(rb'https?://[^\s\x22\x27]+[?&](?:access_token|auth_token|token)=[A-Za-z0-9_.%-]{20,}')}
selected={};excluded=[]


def collect(base,dst_prefix='',only_python=False):
    for directory,dirs,files in os.walk(long(base),followlinks=False):
        dirs[:]=sorted(d for d in dirs if d not in {'__pycache__','.git','.pytest_cache'})
        for name in sorted(files):
            lp=Path(directory)/name
            assert not lp.is_symlink(), str(lp)
            source=Path(str(lp).removeprefix('\\\\?\\'))
            relative=source.relative_to(ROOT).as_posix()
            if (only_python and source.suffix.lower()!='.py') or (not only_python and source.suffix.lower() not in allowed):
                excluded.append(dict(path=relative,bytes=lp.stat().st_size,reason='not selected source type' if only_python else 'weights_arrays_archives_or_unlisted_binary'))
                continue
            target=(dst_prefix+'/'+relative).lstrip('/')
            selected[target]=source


collect(ROOT/'docs/cranial_bcsp_mamba_p2_20261106','evidence')
collect(ROOT/'outputs/cranial_bcsp_mamba_p2_20261106','evidence')
collect(ROOT/'outputs/cranial_bcsp_mamba_p1_20261104','evidence',only_python=True)
# Needed inherited contract/adapter/runtime and metric sources; retain their original path.
geo=ROOT/'outputs/cranial_bcsp_geov1_20261024'
for directory,dirs,files in os.walk(long(geo),followlinks=False):
    dirs[:]=[d for d in dirs if d not in {'__pycache__','fixtures','downloads','transport_payload','artificial_cpu_batch_v1','artificial_cpu_batch_v2'}]
    for name in files:
        if name.startswith(('bcsp_training_','bcsp_eval_metrics_')) and name.endswith('.py'):
            source=Path(str(Path(directory)/name).removeprefix('\\\\?\\'))
            selected['evidence/'+source.relative_to(ROOT).as_posix()]=source
snapshot=ROOT/'deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot'
for p in snapshot.rglob('*'):
    if p.is_file():selected['parent_source_snapshot/'+p.relative_to(snapshot).as_posix()]=p
adapter=geo/'implementation_candidate_v4/overlay/tools/bcsp_adapter.py'
assert adapter.is_file()
selected['evidence/'+adapter.relative_to(ROOT).as_posix()]=adapter
selected['archive_tools/'+Path(__file__).name]=Path(__file__)
license_path=ROOT/'work/PoinTr/LICENSE'
if license_path.is_file():selected['parent_source_snapshot/LICENSE']=license_path

# Pattern scan every selected text/capture before creating the destination.
findings=[]
for target,source in selected.items():
    b=read(source)
    for kind,pattern in patterns.items():
        if pattern.search(b): findings.append(dict(path=target,kind=kind))
assert not findings, json.dumps({'secret_pattern_findings':findings})
print(json.dumps(dict(stage='scope_and_secret_scan_pass',selected=len(selected)),ensure_ascii=True),flush=True)
manifest=[]
for target,source in sorted(selected.items()):
    b=read(source);write(PUBLIC/target,b)
    assert read(PUBLIC/target)==b
    manifest.append(dict(path=target,source=str(source),bytes=len(b),sha256=sha(b)))


def jwrite(p,obj): write(p,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())


jwrite(PUBLIC/'source_file_manifest_v1.json',manifest)
jwrite(PUBLIC/'excluded_inventory_v1.json',excluded)
report=ROOT/'docs/cranial_bcsp_mamba_p2_20261106/Cranial_BCSP_Mamba_P2_完整实验报告_zh_2026-11-07_v1.md'
portable=read(report).decode('utf-8')
for entry in manifest:
    source=Path(entry['source']).as_posix()
    portable=portable.replace(']('+source+')',']('+entry['path']+')')
write(PUBLIC/'REPORT_zh.md',portable.encode())

private_specs=[
 ('H1_native','E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P2_H1/2026-11-07_C_D_development_eval',None),
 ('H2_native','E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P2_H2/2026-11-07_native_development_eval','e2b28e7243531428ec7192c522bf87fe6855e01c4196be6d38d614bcc1511180'),
 ('M0_C_parent','E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_FoldC_paired_development_eval','068dd9812c410c2b84451740a3ed2eb2f12326d8a66fe3bc3ee4623ab3f9b733'),
 ('M0_D_parent','E:/ResearchBackups/AdaPoinTr/BCSP_MAMBA_P1/2026-11-06_FoldD_paired_development_eval','8e9c7d5bc49ee91819a7c555ba6b34c5a936f60fcc6f468eadbfcbe4467b9af3'),
 ('frozen_feature_probe',str(ROOT/'outputs/cranial_bcsp_mamba_p2_20261106/condition_probe_implementation_v1/post_run_freeze_audit_20261107_v1/downloads'),None)]
attachments=[]
for label,folder,expected in private_specs:
    folder=Path(folder);name='development_predictions_v1.tar.gz'
    archive=folder/name;b=read(archive);actual=sha(b)
    sidecar=folder/(name+'.sha256')
    if sidecar.is_file():assert actual==read(sidecar).decode().split()[0].lower()
    if expected:assert actual==expected
    # H1/probe are additionally bound by their existing formal audit archive field.
    if label=='H1_native':
        audit=json.loads(read(ROOT/'outputs/cranial_bcsp_mamba_p2_20261106/H1_prediction_implementation_v1/post_prediction_freeze_audit_20261107_v1/audit_report_v1.json'))
        assert actual in json.dumps(audit)
    if label=='frozen_feature_probe':
        audit=json.loads(read(ROOT/'outputs/cranial_bcsp_mamba_p2_20261106/condition_probe_implementation_v1/post_run_freeze_audit_20261107_v1/formal_audit_report_v1.json'))
        assert actual in json.dumps(audit)
    for suffix in ['', '.sha256','.bytes','.contents.sha256']:
        source=folder/(name+suffix)
        if not source.is_file():continue
        content=read(source);target=label+'/'+name+suffix
        write(PRIVATE/target,content)
        assert sha(read(PRIVATE/target))==sha(content)
        attachments.append(dict(path='local_attachments/'+target,source=str(source),bytes=len(content),sha256=sha(content)))
jwrite(PUBLIC/'local_attachment_reference_manifest_v1.json',attachments)
readme='''# Cranial-BCSP-Mamba P2 frozen code and results archive

Start with [the complete Chinese report](REPORT_zh.md). P2 completed six new training runs (H1 C/D and H2 AUX/COUPLE C/D), 23,400 updates, 630 new Native predictions, 1,680 frozen-model prefix extractions and two unified CPU score batches. The fixed H1 and H2 candidates did not establish stable complete-bone/interface improvement and are closed. H3 is a draft only, never implemented/trained in P2.

## Public contents

`evidence/` preserves original code, CPU test sources/results, protocols, consumed requests, implementation/P3 records, training metrics, prediction manifests/summaries, saved case/source scores, failure history, formal audits, interpretation and final report. `parent_source_snapshot/` contains the exact inherited model/helper snapshots; original AdaPoinTr SHA256 is 1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4. Selected inherited P1 and BCSP contract/metric Python sources retain their original paths. `source_file_manifest_v1.json` maps bytes to original local paths; `files.sha256` binds this public payload. Historical absolute paths are provenance, not automatic synchronization or runnable instructions.

The parent publication is annotated tag `cranial-bcsp-mamba-p1-20261106-final`, commit `8c638d04e53b6c2a7dfccef39488875bbcdd532d` in ZhangHuijun520/AdaPoinTr_Adapt. The parent experiment and representation archive remain separate evidence, not new P2 runs.

## Local-only contents and limits

The full local tar additionally holds `local_attachments/`: already downloaded H1/H2 Native predictions, reused M0 C/D predictions and the frozen-feature probe archive. Their hashes appear in `local_attachment_reference_manifest_v1.json`. These binary arrays are NOT published here. All five source archives were hash-checked against sidecars/frozen evidence before copying. The full tar is then streamed back member-by-member and SHA256 checked.

No final model checkpoint, original NRRD/STL/input/reference point datasets, compiled provider, environment or credentials are included. Generated NPZ/PTH fixtures, transport tarballs and unlisted binaries are excluded and inventoried. Exact hashes of six final weights are provenance, NOT proof of local checkpoint backup. This is a code/results archive, not a self-contained inference/retraining environment. Re-scoring also requires the separately bound geometry references. No server file is deleted or modified by this archive.

Single seed/fold, repeated development use and finite native Mamba gradient nondeterminism constrain the conclusions. No p-values, bootstrap, formal gate or clinical certification. Native scores contain no GT registration. Existing requests are consumed historical evidence, not replay authorization. Secret pattern scanning is bounded detection, not a guarantee against all possible sensitive strings.
'''
write(PUBLIC/'README.md',readme.encode())


def payload_entries(base,prefix):
    result=[]
    for directory,dirs,files in os.walk(long(base)):
        for name in files:
            p=Path(str(Path(directory)/name).removeprefix('\\\\?\\'))
            b=read(p);result.append(dict(path=prefix+p.relative_to(base).as_posix(),bytes=len(b),sha256=sha(b)))
    return sorted(result,key=lambda x:x['path'])


public_entries=payload_entries(PUBLIC,'')
assert all(e['bytes']<50*1024**2 for e in public_entries)
write(PUBLIC/'files.sha256',''.join(e['sha256']+'  '+e['path']+'\n' for e in public_entries).encode())
public_entries=payload_entries(PUBLIC,'public_payload/')
full_entries=sorted(public_entries+payload_entries(PRIVATE,'local_attachments/'),key=lambda e:e['path'])
archive=DEST/'cranial_bcsp_mamba_P2_20261107_v1.tar.gz'
print(json.dumps(dict(stage='write_archive',public_files=len(public_entries),private_files=len(attachments),members=len(full_entries))),flush=True)
with tarfile.open(long(archive),'w:gz',compresslevel=6,format=tarfile.PAX_FORMAT) as tar:
    for e in full_entries:
        p=DEST/e['path'];assert sha(read(p))==e['sha256']
        tar.add(str(long(p)),arcname=e['path'],recursive=False)
expected={e['path']:e for e in full_entries};seen=set()
with tarfile.open(long(archive),'r:gz') as tar:
    for member in tar:
        assert member.isfile() and member.name in expected and member.name not in seen
        b=tar.extractfile(member).read();e=expected[member.name]
        assert len(b)==e['bytes'] and sha(b)==e['sha256'];seen.add(member.name)
assert seen==set(expected)
b=read(archive)
write(DEST/(archive.name+'.sha256'),(sha(b)+'  '+archive.name+'\n').encode())
write(DEST/(archive.name+'.bytes'),(str(len(b))+'\n').encode())
write(DEST/(archive.name+'.contents.sha256'),''.join(e['sha256']+'  '+e['path']+'\n' for e in full_entries).encode())
verification=dict(status='FULL_LOCAL_ARCHIVE_STREAM_READBACK_PASS',archive=dict(name=archive.name,bytes=len(b),sha256=sha(b)),members=len(full_entries),public_files=len(public_entries),public_bytes=sum(e['bytes'] for e in public_entries),local_attachments=len(attachments),excluded_files=len(excluded),source_files=len(manifest),secret_scan=dict(status='NO_PATTERN_MATCHES',rules=list(patterns),files=len(selected)),checkpoint_included=False,model_calls=0,server_operations=0,archive_all_members_stream_verified=True)
jwrite(DEST/'archive_verification_v1.json',verification)
print(json.dumps(verification,ensure_ascii=True),flush=True)
