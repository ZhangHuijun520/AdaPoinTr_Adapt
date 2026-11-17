# -*- coding: utf-8 -*-
"""TRACE local archive/public snapshot and four parent weights. No model/server calls."""
from pathlib import Path
import hashlib,json,os,re,shutil,sys,tarfile

R=Path(__file__).resolve().parent.parent
D=R/'deliverables/trace_20261117_v1'
B=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_TRACE')
V=R/'outputs/trace_D0_implementation_20261117_v1'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4194304),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p))
def put(p,b):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(b)
def js(p,x):put(p,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def copy(p,d):
    d.parent.mkdir(parents=True,exist_ok=True)
    assert not d.exists() and not p.is_symlink()
    with p.open('rb') as source,d.open('xb') as dest:shutil.copyfileobj(source,dest,4194304)
    assert rec(p)['bytes']==rec(d)['bytes'] and sha(p)==sha(d)
def allfiles(root):
    return sorted((p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts),key=str)
def pack(root,files,dest):
    entries=[dict(name=p.relative_to(root).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in files]
    with tarfile.open(dest,'x:gz',compresslevel=1,format=tarfile.PAX_FORMAT) as tf:
        for p in files:tf.add(p,arcname=p.relative_to(root).as_posix(),recursive=False)
    verify_tar(dest,entries)
    ar=rec(dest);ar['members']=len(entries)
    put(Path(str(dest)+'.sha256'),(ar['sha256']+'  '+dest.name+'\n').encode())
    put(Path(str(dest)+'.bytes'),(str(ar['bytes'])+'\n').encode())
    put(Path(str(dest)+'.contents.sha256'),''.join(r['sha256']+'  '+r['name']+'\n' for r in entries).encode())
    return ar,entries
def verify_tar(path,entries):
    lookup={r['name']:r for r in entries};seen=set();assert len(lookup)==len(entries)
    with tarfile.open(path,'r|gz') as tf:
        for m in tf:
            assert m.isfile() and m.name in lookup and m.name not in seen and '..' not in Path(m.name).parts
            h=hashlib.sha256();size=0
            with tf.extractfile(m) as f:
                for b in iter(lambda:f.read(4194304),b''):h.update(b);size+=len(b)
            assert h.hexdigest()==lookup[m.name]['sha256'] and size==m.size==lookup[m.name]['bytes'];seen.add(m.name)
    assert seen==set(lookup)

def code_results():
    assert not D.exists();D.mkdir(parents=True)
    pub=D/'public_payload';private=D/'local_attachments';pub.mkdir();private.mkdir()
    roots=[R/'outputs'/n for n in ['trace_plan_review_20261117_v1','trace_P0_readiness_20261117_v1','trace_D0_implementation_20261117_v1','trace_scientific_closure_20261117_v1','trace_experiment_report_20261117_v1']]+[R/'docs/cranial_bcsp_trace_20261117_v2']
    public_ext={'.py','.json','.jsonl','.md','.txt','.csv','.tsv','.log','.sha256','.bytes','.sh','.ps1','.yaml','.yml','.png','.svg'}
    private_ext={'.npz','.npy','.bin','.pth','.pt','.html','.gz'}
    patterns=[rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',rb'(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{30,})',rb'Bearer\s+[A-Za-z0-9_.-]{30,}',rb'eyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',rb'https?://[^\s/\x22\x27]+:[^\s/@\x22\x27]+@']
    selected={};private_selected={};excluded=[]
    for root in roots:
        assert root.is_dir()
        for p in allfiles(root):
            name='evidence/'+p.relative_to(R).as_posix()
            # Artificial state_dict files are local evidence, never real TRACE weights.
            if p.suffix.lower() in public_ext:selected[name]=p
            elif p.suffix.lower() in private_ext:private_selected[name]=p
            else:excluded.append(dict(source=str(p),bytes=p.stat().st_size,reason='unrecognized runtime artifact; retained in original workspace'))
    aliases=read(V/'CPU_test_bindings_v1.json')['local_aliases'];needed={}
    q=read(V/'TRACE_D0_execution_request_v1.json')
    for r in [*q['implementation'].values(),q['mother_source'],q['helper'],q['static_config'],q['probe_asset'],q['head_initialization']]:
        src=Path(aliases[r['path']]);assert src.stat().st_size==r['bytes'] and sha(src)==r['sha256']
        target='bound_shared_sources/'+r['sha256'][:12]+'_'+src.name;needed[r['path']]=dict(archive_path=target,**r)
        (selected if src.suffix.lower() in public_ext else private_selected)[target]=src
    snapshot=R/'deliverables/spcg_20261117_v1/public_payload/parent_source_snapshot'
    for p in allfiles(snapshot):
        if p.suffix in {'.py','.yaml','.yml','.json'} or p.name=='LICENSE':selected['parent_source_snapshot/'+p.relative_to(snapshot).as_posix()]=p
    for p in [R/'outputs/spcg_implementation_20261116_v1/test_spcg_cpu_v1.py',R/'outputs/spcg_native_prediction_preparation_20261117_v1/implementation_v1/test_spcg_native_CPU_v2.py',R/'outputs/spcg_native_prediction_preparation_20261117_v1/implementation_v1/local_metadata_map_v1.json',R/'outputs/spcg_score_implementation_20261117_v1/bcsp_spcg_three_arm_score_v1.py',R/'outputs/cranial_bcsp_geov1_20261024/blue_pair_eval_v1/bcsp_eval_metrics_v1.py',R/'outputs/spcg_score_implementation_20261117_v1/unified_scores_v1/case_metrics.jsonl',R/'outputs/spcg_score_freeze_20261117_v1/frozen_research_summary_v1.json',R/'outputs/spcg_scientific_decision_20261117_v1/scientific_decision_record_v1.json',Path(__file__),R/'local_tools/publish_TRACE_20261117_v1.py']:
        selected['inherited_evidence/'+p.relative_to(R).as_posix()]=p
    public_manifest=[];priv_manifest=[]
    for target,p in sorted(selected.items()):
        b=p.read_bytes();assert len(b)<40*1024**2
        assert not any(re.search(pat,b) for pat in patterns),('SECRET_PATTERN_STOP',target)
        put(pub/target,b);public_manifest.append(dict(path=target,source=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
    for target,p in sorted(private_selected.items()):
        if p.suffix in {'.bin','.html'}:
            # Raw logs/HTML may contain private content: still reject credential patterns.
            assert not any(re.search(pat,p.read_bytes()) for pat in patterns),('PRIVATE_SECRET_PATTERN_STOP',target)
        copy(p,private/target);priv_manifest.append(dict(path='local_attachments/'+target,source=str(p),bytes=p.stat().st_size,sha256=sha(p),note='Artificial fixture or diagnostic binary, not a newly trained TRACE weight'))
    # Preserve full raw diagnostic archive plus its three sidecars locally only.
    original=B/'2026-11-17_D0_memory_evidence/development_predictions_v1.tar.gz';assert sha(original)=='509dde04102c49ab0de13f9e1d8821491a6371109cf5f1934d8cc585ad03feb9'
    for suffix in ('','.sha256','.bytes','.contents.sha256'):
        p=Path(str(original)+suffix);dest=private/'D0_native_memory_evidence'/p.name;copy(p,dest);priv_manifest.append(dict(path=dest.relative_to(D).as_posix(),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    old=read(V/'CPU_analysis_preparation_v1/TRACE_D0_CPU_analysis_execution_request_v1.json')
    js(pub/'external_data_references_v1.json',dict(note='Raw medical data/reference NPZ and existing historical SPCG prediction arrays remain in original local backups; identities retained, not published or redundantly copied.',historical_prediction_archive=old['prediction_archive'],case_manifest=old['case_manifest'],reference_bindings=old['reference_bindings']))
    js(pub/'inherited_exact_bindings_v1.json',needed)
    js(pub/'source_file_manifest_v1.json',public_manifest)
    js(pub/'local_only_manifest_v1.json',priv_manifest)
    js(pub/'excluded_runtime_artifacts_v1.json',excluded)
    report=R/'outputs/trace_experiment_report_20261117_v1/Cranial_BCSP_FullMamba_BCSP_TRACE_完整实验报告_zh_v1.md';copy(report,pub/'REPORT_zh.md')
    put(pub/'README.md',b'# BCSP-TRACE closed diagnostic stage, 2026-11-17\n\nRead [the complete Chinese report](REPORT_zh.md). Four frozen SPCG G1/G2 C/D models, 40 fixed sources/cases and 80 zero-update full forward calls. All80 Q/P are byte-identical to the historical predictions. Main nonpressure association: C17 Spearman0.1422 / adjusted0.0558; D18 -0.0671 / adjusted0.3307. The preregistered crossfold budget condition was not met. Current stage closed; conditional G3 A=S and six training runs were not started. No claim all spatial conditioning is ineffective.\n\nThis snapshot contains exact code, source dependencies, artificial test and failure records, P3, installation/execution/freezes, CPU case evidence, report and closure. Historical requests and authorizations are inert evidence, never reusable grants. Raw arrays, compiled dependencies, real checkpoints, artificial state_dict fixtures and raw binary logs are excluded from GitHub and retained privately. Windows paths are historical local evidence, not server commands. No server changes or new experiments are performed by this archive.\n\nParent SPCG annotated tag: cranial-bcsp-spcg-20261117-v2; commit8527cdf92044a0e6b8cf5afa5bfc23ce466b88e8. TRACE creates no new checkpoint. The four parent G1_C/G2_C/G1_D/G2_D final weights are separately verified and backed up locally.\n')
    put(pub/'RESTORATION.md',b'# Restoration boundaries\n\nExact bytes do not prove an executable restore. Public source/reference bindings preserve provenance; raw SkullBreak point/reference NPZ, historical SPCG predictions, initial U/H bytes, provider/CUDA binaries and four trained parent weights are local-only and must be restored independently. Do not download/upgrade dependencies implicitly. Prior requests/control files are records, not authorization. No inference, checkpoint deserialization or restore execution has been performed during archival.\n')
    files=allfiles(pub);put(pub/'public_files.sha256',''.join(sha(p)+'  '+p.relative_to(pub).as_posix()+'\n' for p in files).encode())
    print(json.dumps(dict(stage='public_private_snapshot_ready',public_files=len(files)+1,private_files=len(priv_manifest))),flush=True)
    ar,entries=pack(D,allfiles(pub)+allfiles(private),D/'trace_code_results_20261117_v1.tar.gz')
    verification=dict(status='TRACE_CODE_RESULTS_ALL_MEMBERS_HASH_VERIFIED',archive=ar,public_files=len(allfiles(pub)),private_files=len(allfiles(private)),new_checkpoints=0,real_weights_included=False,secret_pattern_scan='NO_MATCHES',server_operations=0,new_experiments=0)
    js(D/'archive_verification_v1.json',verification)
    dest=B/'2026-11-17_code_results_v1';assert not dest.exists();dest.mkdir()
    for p in [Path(ar['path']),*[Path(ar['path']+s) for s in ['.sha256','.bytes','.contents.sha256']],D/'archive_verification_v1.json']:copy(p,dest/p.name)
    verify_tar(dest/Path(ar['path']).name,entries)
    backup=dict(status='TRACE_LONG_TERM_BACKUP_ALL_MEMBER_READBACK_PASS',directory=str(dest),archive=rec(dest/Path(ar['path']).name),members=len(entries),public_files=verification['public_files'],private_files=verification['private_files'],server_writes=0,server_deletions=0)
    js(D/'long_term_backup_receipt_v1.json',backup);js(dest/'long_term_backup_receipt_v1.json',backup);print(json.dumps(backup),flush=True)

def checkpoints():
    source=Path('E:/ResearchBackups/AdaPoinTr/BCSP_FULLMAMBA_SPCG/SPCG_final_archival_receipt_20261117_v1.json');parent=read(source)
    selected=[r for r in parent['weights'] if r['run'] in {'G1_C','G2_C','G1_D','G2_D'}];assert len(selected)==4
    q=read(V/'TRACE_D0_execution_request_v1.json');dest=B/'2026-11-17_key_parent_checkpoints_v1';assert not dest.exists();dest.mkdir();rows=[]
    for r in selected:
        p=Path(r['path']);assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'] and q['checkpoints'][r['run']]['sha256']==r['sha256']
        out=dest/'weights'/p.name;copy(p,out);rows.append(dict(run=r['run'],source=str(p),**rec(out),kind='PARENT_SPCG_FINAL_WEIGHT_NOT_NEW_TRACE_TRAINING'))
        print(json.dumps(dict(stage='parent_weight_copied_verified',run=r['run'])),flush=True)
    js(dest/'parent_checkpoint_manifest_v1.json',dict(status='TRACE_FOUR_PARENT_WEIGHTS_COPIED_AND_VERIFIED',weights=rows,parent_final_receipt=rec(source),new_TRACE_checkpoints=0,deserialized=False,restore_execution=False,GitHub=False))
    ar,entries=pack(dest,allfiles(dest),dest/'trace_key_parent_checkpoints_20261117_v1.tar.gz')
    result=dict(status='TRACE_FOUR_PARENT_CHECKPOINTS_LOCAL_AND_ARCHIVE_MEMBERS_VERIFIED',weights=rows,archive=ar,new_TRACE_checkpoints=0,checkpoint_deserialized=False,restore_execution=False,server_downloads=0,server_deletions=0,weights_uploaded_to_GitHub=False)
    js(dest/'local_verification_receipt_v1.json',result);js(D/'parent_checkpoint_backup_receipt_v1.json',result);print(json.dumps(dict(status=result['status'],weights=4,archive=ar)),flush=True)

if __name__=='__main__':
    if sys.argv[1]=='code_results':code_results()
    elif sys.argv[1]=='checkpoints':checkpoints()
    else:raise ValueError('code_results or checkpoints')
